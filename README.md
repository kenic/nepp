# NEPP

Reference implementation of the Network Earth Position Protocol (NEPP), a
real-valued calendar and synchronization protocol based on Earth's orbital
position.

NEPP represents an Earth Date as `ED = Earth Year + apparent solar longitude /
360 degrees` and exchanges it using an NTP-inspired UDP protocol. This
repository now contains a **V2-only experimental server** implementing the
160-octet proposal in [`draft-iwata-nepp-03.md`](draft-iwata-nepp-03.md).
The Python `nepp-client` remains V1-only. The local iOS 0.0.2 app supports V2;
the already distributed 0.0.1 app cannot query this server.

## Status

This is experimental software and an evolving protocol draft. It must not be
used as a civil-time source or for safety-critical synchronization. No UDP port
has been assigned by IANA; the tools use a configurable private port.

This is a local prototype, not a production cutover. Do not restart an existing
V1 deployment with this version until beta clients have been updated. Independent
astronomical validation and error bounds are still pending; both coordinates are
explicitly reported as **accuracy unassessed**, never zero error.

## Install and run

Python 3.9 or newer is required.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[astronomy]'
nepp-server --host 127.0.0.1 --port 56377
```

In another terminal:

```sh
python -m nepp.probe 127.0.0.1 --port 56377
```

The probe reports coordinates at server transmit time, not network-delay-corrected
local time. It is not a full synchronization client. `nepp-client` remains V1-only.

The astronomical extra supplies Astropy/ERFA. The provisional model uses `epv00`,
iterated light time, pure Lorentz aberration, IAU 2006/2000A precession/nutation,
and UT1/GAST for Greenwich solar phase. Its supported interval is 1900–2100.
IERS retrieval runs outside request handling; missing/out-of-range EOP makes SP
unavailable without suppressing ED. `--offline` uses bundled IERS data only.
Source publication age is unknown; cache refreshes do not invent publication dates.
The server requests no GPS location. The iOS client can optionally use location
on-device to calculate local phase; it never sends location to the server.

Snapshots refresh every 60 seconds, have a 300-second intended extrapolation
interval, and expire completely after `--max-age` (default 3600 seconds).
Failed/expired refreshes become unassessed holdover; a detected host-clock step
over one second suppresses the snapshot until refreshed. These are operational
limits, not certified accuracy bounds. The host clock remains an experimental input.

## Test

```sh
python -m unittest discover -s tests -v
```

The suite covers timestamp boundaries, packet layout and validation,
request/response behavior, token/origin verification, bounded cache/holdover,
silent V1 rejection, and a UDP loopback exchange. Optional astronomy tests use
bundled historical EOP without network access; they are sanity checks, not
independent astronomical accuracy certification.

## Public server

The production entry point defaults to dual-stack UDP port `56377`. It caches
the expensive astronomical calculation, interpolates responses from that state,
limits requests per source address, logs lifecycle statistics, and exits cleanly
on `SIGINT` or `SIGTERM`.

See the [Lightsail and systemd deployment guide](deploy/README.md) for the
hardened service unit, firewall configuration, verification, and updates.

## Layout

```text
src/nepp/       timestamp, packet, clock, server, and client
spec/           protocol draft
tests/          unit and interoperability tests
ios/            SwiftUI client and shared Swift NEPP codec
deploy/         systemd unit and public-server operations guide
webdocs/        Japanese and English source for nepp.kenic.jp
mkdocs.yml      documentation-site configuration
```

The initial [iOS client](ios/README.md) receives NEPP while it is in the
foreground and presents the current coordinate as `today: 2026.0457`.

## License

BSD 3-Clause. See [`LICENSE`](LICENSE).
