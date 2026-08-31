# NEPP Web 0.0.2

Standalone English/Japanese Web client, published at `/web/`. Existing `/app/`
and `/en/app/` remain the native-app documentation. No JavaScript dependencies,
analytics, remote fonts, service worker or offline coordinate cache.

## Local preview

From the repository with the astronomy extra installed:

```sh
.venv/bin/python -m nepp.server --host 127.0.0.1 --port 56379 --http-port 8765 --web-root webapp
```

Open http://127.0.0.1:8765/web/ . UDP 56379 avoids the existing development
server on 56378. `--offline` uses bundled EOP tables for development; old tables
can make solar phase unavailable. Do not use offline data to imply current accuracy.
The HTTP listener always binds loopback. For iPhone testing use the eventual
HTTPS deployment: LAN plain HTTP does not provide browser geolocation access.

## Architecture and timing

The optional HTTP adapter shares **the same CachedSource instance** as UDP V2.
It runs independently of the UDP request loop and performs no astronomy in a
request. This JSON interface is experimental, not a standardized NEPP transport.
`GET /api/v2/state?nonce=<32 lowercase random hex digits>` returns:

- `schema=nepp-web-1`, protocol version and echoed random nonce;
- ED year and decimal fraction string, ED/SI-second rate, model and quality;
- Greenwich solar phase/rate/model/quality, or null independently of ED;
- server processing interval and remaining extrapolation budget (at most 300 s).

Coordinates refer to the server's transmit anchor. The client estimates one-way
delay as half of HTTP round-trip minus server processing. Serialization, proxies,
browser scheduling and network asymmetry remain unassessed. Source uncertainty
is **not** an end-to-end browser accuracy bound. Unknown fields use JSON null.
Each update uses a fresh random nonce and no-store; stale/cached mismatches are
rejected. Invalid solar data can leave ED usable. No client calendar clock is
used to produce ED; Date.now is only a clock-step/suspend sanity check.

Refresh every 60 s; failures retry after 2/4/8/16/32/60 s (capped at 60).
Retain the previous snapshot temporarily with an estimated label. Expired source
validity is labelled stale; the extrapolation budget is never renewed on failure.
After 300 s or the earlier server budget, show no coordinate. Backgrounding
aborts requests and clears the sample; foregrounding acquires a new sample.

Location is optional, on-device only, requested with browser permission. Declining
does not silently substitute Greenwich. Current-location fixes are refreshed
each minute while visible; an older retained fix is explicitly labelled.
No coordinates are persisted (manual longitude also clears on reload). Only
language and location-mode preferences are saved in localStorage. The browser's
one-shot location request cannot be cancelled, but late/background callbacks are
discarded. There are no background watches. Home-screen installation uses the
manifest and existing app icon; an internet connection is required.

Location errors distinguish permission denial (1), unavailable position (2),
browser timeout (3), unsupported/insecure contexts and invalid fixes. A separate
20-second watchdog bounds permission waiting or missing browser callbacks;
this is labelled "no response", not misreported as permission denial. Settings
includes a retry button. Timed-out callbacks are ignored, and a previous good
fix is retained with a last-known-location label after a failed refresh.

### Safari location timestamp workaround

A standalone reproduction on macOS Safari returned a timestamp exactly
978,307,200 seconds behind Unix time (plus 23 ms acquisition age), consistent
with the 2001 Apple reference epoch. The Web client first accepts ordinary Unix
timestamps using its existing freshness check. Only an otherwise old timestamp
whose value plus 978307200000 ms is between 0 and 300 seconds old is rescued.
Future corrected timestamps and still-stale fixes remain rejected. This is an
inferred compatibility workaround, shown in Details, not proof of the browser's
internal epoch. Normal browser responses are never double-corrected. The flag
and corrected timestamp remain in memory only and do not affect ED or API data.
`tools/repro/geolocation-timestamp.html` intentionally remains uncorrected.

## Production (not performed automatically)

**The server code is V2-only. Switching it breaks released V1 clients.** First
finish V2 native-client testing and arrange its release. This app does not make
the current V1 production service compatible by itself.

1. Commit/push the tested changes and update `/opt/nepp` intentionally.
2. Install the updated Python package in `/opt/nepp/venv`.
3. Install `deploy/nepp-web.conf` as
   `/etc/systemd/system/nepp.service.d/web.conf` (create that directory first).
   Then run `sudo systemctl daemon-reload` and `sudo systemctl restart nepp`.
4. Build/publish docs with the existing `deploy/update-site.sh` workflow. The
   MkDocs hook copies `webapp/` into `site/web/`, so rsync --delete retains it.
5. Merge `deploy/Caddyfile.example` into `/etc/caddy/Caddyfile`, preserving any
   unrelated hosts/configuration. Validate with `sudo caddy validate --config
   /etc/caddy/Caddyfile`, then `sudo systemctl reload caddy`.
6. Check `/web/`, `/api/v2/state?nonce=0123456789abcdef0123456789abcdef`, existing
   docs and UDP V2. Use a fresh nonce for real requests.

Do not open port 8080 in Lightsail. Caddy proxies it locally over existing HTTPS
443. The small standard-library HTTP adapter is loopback-only, with a 3 s socket
timeout and no request logging. It is not intended as an internet-facing server.
Caddy access logging is not enabled by this example; hosting infrastructure may
process technical connection information.

## Tests

```sh
.venv/bin/python -m unittest discover -s tests
node --test webapp/core.test.mjs
.venv/bin/mkdocs build --clean --strict
```
