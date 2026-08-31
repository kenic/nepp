from dataclasses import replace
import http.client
import json
import threading
import time
import unittest
from pathlib import Path

from nepp.source import SourceSample, CachedSource
from nepp.timestamp import EarthDate
from nepp.v2 import Quality
from nepp.web import state_json, make_http_server

NONCE = '0123456789abcdef0123456789abcdef'


class Provider:
    def acquire(self):
        q = Quality.unassessed(reference_id=123, validity=300)
        return SourceSample(time.monotonic(), EarthDate.from_decimal('2026.4'),
                            3.2e-8, q, .4, 1 / 86400, q)


class WebTests(unittest.TestCase):
    def setUp(self):
        self.cache = CachedSource(Provider())

    def test_shared_sample_and_unknown_quality(self):
        data = state_json(self.cache, NONCE, time.monotonic())
        self.assertEqual(data['schema'], 'nepp-web-1')
        self.assertEqual(data['nonce'], NONCE)
        self.assertEqual(data['ed']['year'], 2026)
        self.assertAlmostEqual(float(data['ed']['fraction']), .4, places=6)
        self.assertAlmostEqual(data['solar']['phase'], .4, places=4)
        self.assertIsNone(data['ed']['quality']['uncertainty'])
        self.assertFalse(data['ed']['quality']['evaluated'])
        self.assertLessEqual(data['max_extrapolation_seconds'], 300)
        json.dumps(data, allow_nan=False)

    def test_unavailable_and_holdover(self):
        self.cache._sample = replace(self.cache._sample, epoch=time.monotonic()-4000)
        self.assertIsNone(state_json(self.cache, NONCE, time.monotonic()))
        self.cache.refresh()
        self.cache.last_error = ValueError('failed')
        data = state_json(self.cache, NONCE, time.monotonic())
        self.assertEqual(data['ed']['quality']['state'], 2)
        self.assertIsNone(data['ed']['quality']['uncertainty'])

    def test_ed_without_sp(self):
        self.cache._sample = replace(self.cache._sample, phase=None, phase_rate=0, sp_quality=Quality())
        self.assertIsNone(state_json(self.cache, NONCE, time.monotonic())['solar'])

    def test_http_contract(self):
        server = make_http_server(self.cache, 0, Path(__file__).resolve().parents[1] / 'webapp')
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            def get(path):
                connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                try:
                    connection.request('GET', path)
                    r = connection.getresponse()
                    return r.status, dict(r.getheaders()), r.read()
                finally:
                    connection.close()
            code, headers, body = get('/api/v2/state?nonce='+NONCE)
            self.assertEqual(code, 200)
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertNotIn('Access-Control-Allow-Origin', headers)
            self.assertEqual(json.loads(body)['nonce'], NONCE)
            for path in ['/api/v2/state', '/api/v2/state?nonce=bad',
                         '/api/v2/state?nonce='+NONCE+'&longitude=139',
                         '/api/v2/state?nonce='+NONCE+'&nonce='+NONCE]:
                self.assertEqual(get(path)[0], 400)
            for path in ['/web/../../pyproject.toml', '/web/README.md', '/other']:
                self.assertEqual(get(path)[0], 404)
            for path in ['/web/', '/web/app.js', '/web/core.mjs', '/web/icon.png']:
                self.assertEqual(get(path)[0], 200)
            self.cache._sample = None
            self.assertEqual(get('/api/v2/state?nonce='+NONCE)[0], 503)
        finally:
            server.shutdown(); server.server_close(); thread.join(2)
