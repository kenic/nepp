# NEPP

Reference implementation of the Network Earth Position Protocol (NEPP), a
real-valued calendar and synchronization protocol based on Earth's orbital
position.

NEPP represents an Earth Date as `ED = Earth Year + apparent solar longitude /
360 degrees` and exchanges it using an NTP-inspired UDP protocol. This
repository implements the Version 1, 76-octet base packet in
[`spec/draft-iwata-nepp-01.md`](spec/draft-iwata-nepp-01.md).

## Status

This is experimental software and an evolving protocol draft. It must not be
used as a civil-time source or for safety-critical synchronization. No UDP port
has been assigned by IANA; the tools use a configurable private port.

## Install and run

Python 3.9 or newer is required.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[astronomy]'
nepp-server --host 127.0.0.1 --port 41234
```

In another terminal:

```sh
nepp-client 127.0.0.1 --port 41234
```

The astronomical extra supplies Astropy for the experimental Profile 1 clock.
The packet codec and test suite have no third-party runtime dependencies.

## Test

```sh
python -m unittest discover -s tests -v
```

The suite covers timestamp boundaries, packet layout and validation,
request/response behavior, origin verification, and a UDP loopback exchange.

## Layout

```text
src/nepp/       timestamp, packet, clock, server, and client
spec/           protocol draft
tests/          unit and interoperability tests
```

## License

BSD 3-Clause. See [`LICENSE`](LICENSE).
