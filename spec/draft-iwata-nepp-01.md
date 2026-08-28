# Network Earth Position Protocol (NEPP)

## Real-Valued Calendar Representation and Synchronization Based on Earth's Annual Orbital Position

### draft-iwata-nepp-01 (implementation snapshot)

Intended status: Experimental  
K. Iwata, Tottori University  
August 2026

## Abstract

NEPP represents and synchronizes the Earth Date (ED), a continuous terrestrial
calendar coordinate based on apparent geocentric solar longitude. This snapshot
specifies the Version 1 wire representation implemented by this repository. It
is not an IETF submission and remains subject to change.

## 1. Earth Date

Earth Date is `ED = Y + lambda / 360 degrees`, where `Y` is the Earth Year and
`0 <= lambda < 360 degrees`. Earth Year begins at the March equinox and uses the
Gregorian year containing that equinox as its integer label. The coordinate is
angular and non-uniform in SI time. Its local rate is `R = dED/dt` ED per SI
second.

## 2. Timestamp

A timestamp is 96 bits in network byte order:

| Offset | Size | Field | Encoding |
|---:|---:|---|---|
| 0 | 4 | Earth Year | signed 32-bit integer |
| 4 | 8 | Orbital Fraction | unsigned 64-bit integer |

For fractional ED `F`, the wire value is `floor(F * 2^64)`. Receivers recover
`F = U / 2^64`. Differences MUST be calculated as complete ED values across
year boundaries. Twelve zero octets denote an absent timestamp where permitted.

## 3. Version 1 base packet

The base packet is 76 octets. Additional octets are extension data.

| Offset | Size | Field |
|---:|---:|---|
| 0 | 1 | Flags: Status (2), Version (3), Mode (3) |
| 1 | 1 | Stratum |
| 2 | 1 | Poll, signed |
| 3 | 1 | Precision, signed |
| 4 | 4 | Root Delay, unsigned 16.16 SI seconds |
| 8 | 4 | Root Dispersion, unsigned 16.16 SI seconds |
| 12 | 4 | Reference ID |
| 16 | 12 | Reference Earth Date |
| 28 | 12 | Origin Earth Date |
| 40 | 12 | Receive Earth Date |
| 52 | 12 | Transmit Earth Date |
| 64 | 8 | Earth Date Rate, signed integer times `2^-63` ED/s |
| 72 | 4 | Model ID |

Version is 1. Status values are synchronized (0), degraded (1), holdover (2),
and unsynchronized (3). Required modes are client (3) and server (4). Stratum 0
is an astronomical source, 1 is a primary server, 2 through 15 are secondary,
and 16 is unsynchronized. Poll recommends `2^Poll` SI seconds between queries.
Precision `P` represents a nominal resolution of `2^P` ED.

## 4. Exchange and calculation

A client sets Transmit to E1 and Origin and Receive to zero. The server records
E2 on receipt, copies E1 to Origin, and records E3 near transmission. The client
records destination E4 locally.

```text
offset = ((E2 - E1) + (E3 - E4)) / 2
round_trip = (E4 - E1) - (E3 - E2)
```

Positive offset means the client is behind. A client MUST reject an unsupported
version, non-server mode, unsynchronized server, mismatched Origin, or packet
shorter than 76 octets.

## 5. Astronomy profile

Model ID 1 identifies experimental Profile 1: apparent geocentric solar
direction, an IAU-consistent ecliptic, IAU 2006 precession, IAU 2000A nutation,
and IERS-consistent calculations. A production profile still requires fixed
ephemeris versions, a reference procedure, uncertainty rules, and independently
generated test vectors. The included Astropy clock is experimental, not yet the
normative astronomical test-vector authority.

## 6. Transport and security

Version 1 uses UDP request/response. Until IANA assigns a port, deployments MUST
use a configurable dynamic/private port. The base protocol is unauthenticated
and is vulnerable to spoofing, replay, delay manipulation, false stratum, and
denial of service. Origin validation correlates a response but does not
authenticate it. Trusted uses require authenticated transport or a future
authentication extension.
