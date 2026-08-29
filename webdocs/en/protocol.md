# Network Earth Position Protocol

NEPP Version 1 is an experimental UDP request/response synchronization
protocol inspired by NTP. The public server uses the unassigned private port
`56377/UDP`.

## Try it

With the reference implementation installed, run:

```bash
nepp-client nepp.kenic.jp --port 56377
```

Example response:

```text
earth_date=2026.431818261511104238
offset_ed=5.499863888505608E-9
round_trip_ed=1.3356719301708866E-8
stratum=1
model_id=1
```

## Version 1 packet

The base packet is 76 octets.

| Offset | Size | Field |
|---:|---:|---|
| 0 | 1 | Status, Version, and Mode |
| 1 | 1 | Stratum |
| 4 | 4 | Root Delay |
| 8 | 4 | Root Dispersion |
| 16 | 12 | Reference Earth Date |
| 28 | 12 | Origin Earth Date |
| 40 | 12 | Receive Earth Date |
| 52 | 12 | Transmit Earth Date |
| 64 | 8 | Earth Date Rate |
| 72 | 4 | Model ID |

An Earth Date timestamp contains a signed 32-bit Earth Year and an unsigned
64-bit orbital fraction, all in network byte order.

## Exchange and correction

Let `E1` through `E4` be client transmit, server receive, server transmit, and
client receive. Offset and round-trip delay are:

```text
offset = ((E2 - E1) + (E3 - E4)) / 2
round_trip = (E4 - E1) - (E3 - E2)
```

See the complete implementation snapshot,
[`draft-iwata-nepp-01`](https://github.com/kenic/nepp/blob/main/spec/draft-iwata-nepp-01.md).

## Security

Version 1 is unauthenticated and is vulnerable to spoofing, replay, delay
manipulation, false stratum, and denial of service. Origin validation correlates
a response but does not authenticate its sender. Trusted uses require an
authenticated transport or a future authentication extension.
