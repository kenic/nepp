"""Loopback-only HTTP adapter for the existing V2 source cache.

This JSON interface is experimental, not an additional NEPP wire protocol.
Serve behind Caddy; no user coordinates, configurable upstreams or CORS.
"""
import json
import mimetypes
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from .source import build_response
from .v2 import V2Packet, UNKNOWN


def quality_json(q):
    return {
        'state': int(q.state), 'source_kind': int(q.source_kind),
        'stratum': q.stratum, 'reference_id': q.reference_id,
        'evaluated': q.evaluated, 'prediction': q.prediction,
        'uncertainty': None if q.uncertainty == UNKNOWN else q.uncertainty / 2**32,
        'validity_seconds': None if q.validity == UNKNOWN else q.validity,
        'data_age_seconds': None if q.data_age == UNKNOWN else q.data_age,
        'update_age_seconds': None if q.update_age == UNKNOWN else q.update_age,
    }


def state_json(cache, nonce, received):
    sample, failed = cache.snapshot()
    transmitted = cache.monotonic()
    response = build_response(V2Packet.request(), sample, received, transmitted,
                              max_age=cache.max_age, failed=failed)
    if not response.ed_quality.state:
        return None
    ed = response.base.transmit
    from decimal import Decimal
    return {
        'schema': 'nepp-web-1', 'protocol_version': 2, 'nonce': nonce,
        'processing_seconds': transmitted - received,
        'max_extrapolation_seconds': max(0, min(300, cache.max_age - (transmitted - sample.epoch))),
        'ed': {'year': ed.year, 'fraction': str(Decimal(ed.fraction) / Decimal(2**64)),
               'rate': response.base.rate / 2**63, 'model_id': response.base.model_id,
               'quality': quality_json(response.ed_quality)},
        'solar': {'phase': response.phase / 2**64, 'rate': response.phase_rate / 2**63,
                  'model_id': response.solar_model, 'quality': quality_json(response.sp_quality)}
                 if response.validate_sp() else None,
    }


def make_http_server(cache, port, web_root=None):
    root = Path(web_root).resolve() if web_root else None
    assets = {'index.html', 'style.css', 'app.js', 'core.mjs', 'manifest.webmanifest', 'icon.png'}

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            self.request.settimeout(3)
            super().setup()

        def log_message(self, *_args):
            pass  # No IP addresses or URLs in application logs.

        def reply(self, status, body, content_type='application/json; charset=utf-8'):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Permissions-Policy', 'geolocation=(self)')
            self.send_header('Content-Security-Policy', "default-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            received = cache.monotonic()
            path = urlsplit(self.path)
            if root and path.path in ('/', '/web'):
                self.send_response(302)
                self.send_header('Location', '/web/')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            if path.path == '/api/v2/state':
                params = parse_qs(path.query, keep_blank_values=True)
                nonce = params.get('nonce', [''])[0]
                if set(params) != {'nonce'} or len(params['nonce']) != 1 or not re.fullmatch(r'[0-9a-f]{32}', nonce):
                    self.reply(400, b'{"error":"expected one random 32-hex nonce"}')
                    return
                state = state_json(cache, nonce, received)
                if state is None:
                    self.reply(503, b'{"error":"source unavailable"}')
                else:
                    self.reply(200, json.dumps(state, allow_nan=False).encode())
                return
            name = path.path.removeprefix('/web/') if path.path.startswith('/web/') else ''
            if root and (name in assets or path.path == '/web/'):
                file = root / (name or 'index.html')
                if file.is_file():
                    self.reply(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
                    return
            self.reply(404, b'{"error":"not found"}')

    return HTTPServer(('127.0.0.1', port), Handler)


def start_http(cache, port, web_root=None):
    server = make_http_server(cache, port, web_root)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name='nepp-web')
    thread.start()
    return server
