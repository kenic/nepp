# Network Earth Position Protocol (NEPP)

## Earth Date Synchronization and Location-Local Solar Phase

### draft-iwata-nepp-02

Intended status: Experimental  
Kenichi Iwata, Tottori University  
31 August 2026

## Status of This Memo

This is an author working draft for discussion, not an Internet-Draft submitted
to the IETF. It is not an Internet Standard. The Version 2 layout, field codes,
and astronomical profile below are proposed and have not been implemented or
independently validated. Publication does not assert interoperability.

The English edition is authoritative. The Japanese edition is for reference.
Draft revision `-02`, protocol Version 2, and application version `0.0.2` are
independent identifiers. Revisions `-00` and `-01` remain historical documents.

This revision contains the complete proposed NEPP specification for both V1
and V2. Earlier revisions are not prerequisites. References to external
astronomical standards remain necessary; unresolved realization details are
identified here rather than delegated to an earlier NEPP draft.

## Abstract

NEPP synchronizes Earth Date (ED), a continuous calendar coordinate based on
apparent geocentric solar longitude. This revision proposes a Version 2
exchange that also supplies a reference solar phase and its local rate. A
client combines the reference phase with a locally selected longitude to
describe the daily solar cycle without sending its location to the server.

The design separates a globally shared instant from a place-dependent daily
phase. It does not redefine apparent solar time, replace atomic timekeeping,
or prescribe civil time zones. Version 1 remains available to existing clients.

## 1. Changes and Scope

Compared with `-01`, this revision:

- retains the Earth Date definition and Version 1 exchange;
- proposes Version 2 with solar phase, validity, quality, and request correlation;
- specifies version dispatch and fallback independently of packet-layout reuse;
- defines a longitude-only, model solar phase and its observational limitations;
- distinguishes Earth Date quality from solar phase availability;
- documents related work, privacy, downgrade risks, and unresolved validation work.

The wire format distributes instantaneous state, not a service for sending GPS
coordinates or scheduling appointments. Sunrise, sunset, solar altitude, maps,
time-zone conversion, and authentication framing are outside this revision.

## 2. Requirements Language

The capitalized key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD,
SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL are interpreted as in BCP 14
([RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html) and
[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html)). In this working draft,
these words specify the proposed protocol, not capabilities of deployed code.

## 3. Two Coordinates, Two Purposes

### 3.1. Earth Date and Earth Year

Earth Date is:

```text
ED(t) = Y + lambda(t) / 360 degrees
```

`lambda` is apparent geocentric solar longitude in the adopted NEPP astronomical
profile, normalized to `[0, 360)` degrees. Earth Year `Y` begins at its March
equinox crossing and uses the Gregorian year containing that crossing as its
integer label. Before that crossing, the previous Earth Year applies.

The orbital fraction is angular, not an elapsed fraction of a fixed-length
year. Quarter-turn seasonal markers are associated with equinoxes and solstices;
their physical-time intervals are unequal. Seasons experienced locally also
depend on hemisphere, latitude, and climate.

Solar phase is a separate, cyclic coordinate. ED is the same for all observers
of the same instant and model; local phase depends on the selected longitude.
ED alone does not supply a rotation angle by taking its fractional part.

Neither a constant number of days per Earth Year nor a constant number of SI
seconds per solar-phase turn is defined. SI seconds remain the units of network
delay, oscillator elapsed time, and local interpolation rates.

### 3.2. Earth Date Astronomical Profile 1

ED Model ID 1 identifies the experimental NEPP Astronomical Profile 1 in both
versions. Its definition uses the apparent direction of the Sun as seen from
the center of the Earth, not the direction at a particular observing site.
The adopted reference geometry uses the IAU definition of the ecliptic,
IAU 2006 precession, IAU 2000A nutation, and transformations consistent with
the IERS Conventions. Longitude increases in the direction of apparent annual
solar motion from the March-equinox direction and is normalized to `[0, 360)`.

A Profile 1 realization SHALL:

1. Obtain Earth and Sun states from a high-precision solar-system ephemeris at
   an identified epoch in the time scale required by that ephemeris.
2. Determine the geocentric solar direction, including light-time, aberration,
   and other apparent-place corrections required by the adopted models.
3. Apply consistent precession/nutation and reference-frame transformations.
4. Construct the applicable ecliptic plane and equinox origin, project the
   apparent direction onto that plane, and compute the oriented longitude.
5. Determine the Earth Year from the March-equinox crossing, and encode ED
   using Section 4.2 rather than an elapsed fraction of a civil year.
6. Evaluate and report a local ED rate and an uncertainty appropriate to the
   ephemeris, transformations, timestamping, and prediction being used.

A constant circular-orbit model or an uncorrected two-body Keplerian ellipse
MUST NOT be substituted for the normative astronomical definition. SOFA-consistent
algorithms are RECOMMENDED reference tools, not a required programming language.
Different ephemerides may implement the profile only if their differences fit
the reported uncertainty; sharing a Model ID alone does not demonstrate agreement.

The exact pinned ephemeris, ecliptic/equinox realization, numerical procedure,
and independently checked accuracy remain open work in Section 13. This is an
explicit incompleteness of the experimental profile, not a reference to missing
rules in `-01`. Implementations MUST identify their realization in documentation
and MUST NOT claim validated astronomical interoperability on the identifier alone.

### 3.3. Time Scales and Earth Date Rate

Physical elapsed time is measured in SI seconds. TT/TDB and other time scales
are used where required by the astronomical algorithms; UTC may supply the
input epoch after appropriate conversion. Earth Date has no leap-day or
leap-second insertion of its own, but a realization using UTC MUST correctly
handle UTC leap seconds and MUST NOT introduce an artificial ED discontinuity.

The local rate is `R = dED/dt` in ED per SI second. It supports interpolation
and delay estimation; it does not define ED. Rate estimates crossing a March
equinox MUST use continuous full ED values rather than a wrapped fraction.
Long-range prediction requires an astronomical model, not indefinite linear
extrapolation. The local-linear synchronization approximation and holdover
behavior are specified in Section 8.

## 4. Version 1 Specification

This section specifies V1 independently of previous revisions. V2's token,
128-octet length, zero-padding rules, and solar fields MUST NOT be required of
V1 clients. The V1 packet format and field meanings remain unchanged.

### 4.1. Base Layout and Version Dispatch

All integers are big endian; signed integers use two's complement.
The common Flags octet is `Status:2 | Version:3 | Mode:3`, most significant
bits first. Version is extracted as `(flags >> 3) & 7`.

| Offset | Octets | Field |
|---:|---:|---|
| 0 | 1 | Flags |
| 1 | 1 | Stratum |
| 2 | 1 | Poll (signed) |
| 3 | 1 | Precision (signed) |
| 4 | 4 | Root Delay |
| 8 | 4 | Root Dispersion |
| 12 | 4 | Reference ID |
| 16 | 12 | Reference Earth Date |
| 28 | 12 | Origin Earth Date |
| 40 | 12 | Receive Earth Date |
| 52 | 12 | Transmit Earth Date |
| 64 | 8 | Earth Date Rate |
| 72 | 4 | Model ID |

A V1 base packet is 76 octets with Version 1. A datagram shorter than 76 octets
is invalid. Additional octets are extension data, not V2 fields. No extension
type/length framing or critical-extension mechanism is defined by this document.
A base-only V1 implementation ignores the trailing data and emits a 76-octet
base response; it MUST NOT interpret a trailer as authentication or solar state.
An extension-aware implementation needs a separately specified extension
agreement. This draft does not make such an agreement a V1 prerequisite.

### 4.2. Timestamp and Rate Encoding

A timestamp is signed 32-bit Earth Year followed by unsigned 64-bit fraction
`U = floor(F * 2^64)`. Decode as `Y + U / 2^64`. All-zero timestamps mean absent
where permitted, not a trustworthy synchronization epoch. Differences MUST be
computed as complete ED values, including crossings of an Earth Year boundary.

Earth Date Rate is signed 64-bit `round(R * 2^63)`, decoded as ED per SI second.
Status values are 0 synchronized, 1 degraded, 2 holdover, and 3 unsynchronized;
they are not NTP leap indicators. Client Mode is 3 and Server Mode is 4.
Stratum 0 denotes a reference source, 1 a primary server, 2 through 15 secondary
servers, and 16 unsynchronized; 17 through 255 are reserved. A network source
used for synchronization has Stratum 1 through 15.

Poll recommends an interval of `2^Poll` SI seconds. Precision describes nominal
ED resolution `2^Precision`, not guaranteed accuracy. Root Delay and Root
Dispersion are unsigned 16.16 SI seconds representing accumulated round-trip
delay and synchronization uncertainty, respectively. Reference ID identifies a
source; Model ID identifies the ED astronomical profile defined in Section 3.2.

### 4.3. Field Semantics

Status 0 indicates a synchronized ED source; 1 indicates degraded astronomical
source quality; 2 indicates prediction-only or holdover operation; 3 means ED
is unsynchronized and MUST NOT be used for synchronization. Clients may reject
degraded or holdover sources according to their quality policy.

Mode codes are 0 reserved, 1 symmetric active, 2 symmetric passive, 3 client,
4 server, 5 broadcast, and 6/7 reserved. Only client/server operation is specified
here. A basic implementation MUST support 3/4 and MUST NOT infer a working
symmetric or broadcast protocol from the other assigned names.

A primary server computes ED from astronomical reference data; secondary servers
derive it through upstream NEPP servers. Stratum is logical source distance,
not an accuracy or authenticity guarantee. Sources at Stratum 0 include
ephemerides and astronomical calculation systems, not ordinary network servers.

Poll and Precision cover signed 8-bit values `-128..127`. Poll 6 recommends
64 SI seconds. Clients MUST bound actual polling and resource use by local policy
rather than blindly exponentiating an untrusted recommendation.

For Root Delay or Root Dispersion, an unsigned wire integer `W` represents
`W / 65536` SI seconds. The range is 0 through `65535 + 65535/65536` seconds.
Root Delay estimates accumulated round-trip communication delay to the reference;
Root Dispersion is an upper estimate of accumulated synchronization uncertainty.
Astronomical uncertainty MUST be included in Root Dispersion or a separately
specified extension understood by the client. In the base-only exchange it
belongs in Root Dispersion. Zero MUST NOT be treated as a special unknown marker.
An unrepresentable uncertainty cannot be claimed as a finite accurate bound;
the source must be treated as unusable for synchronization.

Reference ID is a 32-bit source identifier. At Stratum 1 it identifies a source
or profile; at secondary strata it can identify an upstream source and help
detect loops. There is no global registry defined here. It is not necessarily
an IPv4 address, and an ASCII label does not prove traceability. ED Model ID is
an unsigned 32-bit profile identifier; 1 has the definition in Section 3.2.
An unknown model cannot safely be assumed equivalent to Profile 1.

### 4.4. V1 Request and Response

The four exchange events are client transmit E1, server receive E2, server
transmit E3, and client destination E4. E4 is recorded locally, not transmitted.
A client sends Version 1, Mode 3, Transmit = E1, and zero Origin and Receive.
Reference is implementation-defined or zero. An unsynchronized/bootstrap client
uses Status 3 and Stratum 16 and MAY set E1 to zero when no ED estimate exists.
Client poll/precision describe its policy; response-only information may be zero.
V1 has no random Request Token and MUST NOT acquire V2's extra request checks.

A server records E2 upon receipt, copies request Transmit bytes into response
Origin, and records E3 as near transmission as practical. The response uses
Version 1, Mode 4, its own status/stratum/source/quality information, Receive = E2,
Transmit = E3, and a local ED rate. Reference denotes the reference ED state used
for synchronization, or zero if not supplied. The server SHOULD evaluate or
propagate the ED rate to the response transmit epoch. A base-only response is
76 octets, even if the request included ignored extension data.

The client records E4 from its ED clock on receipt. Normal exchanges use Section
8.1. Bootstrap with no E1/E4 uses the ED-only parts of Section 8.2; no solar terms
exist in V1. A zero Origin can correlate a zero-E1 request but provides little
protection against forged or replayed responses. Implementations MUST NOT invent
solar state from a V1 response.

### 4.5. V1 Acceptance, Errors, and Minimum Implementation

A V1 client MUST NOT synchronize from an unsupported Version, non-server Mode,
unsynchronized Status, Origin different from the sent E1, malformed timestamp,
packet shorter than 76 octets, prohibited reserved value, or Root Dispersion
above its acceptance threshold. Clients MUST validate the request/response
Origin association; they SHOULD also match the selected network endpoint,
discard duplicates, and reject implausible timing or source information.
No V2 token check, V2 exact-length check, or V2 solar check applies.

Servers silently discard malformed packets, unsupported versions, and modes
they do not implement. A response from the wrong version is not version
negotiation. Transport is the UDP request/response service in Sections 7.1 and
11; a basic V1 exchange does not require continuous connectivity.

A basic V1 server implements Profile 1 ED calculation, E2/E3 timestamping, ED
rate, stratum, delay, and dispersion. A basic synchronizing V1 client implements
E1/E4 capture when available, Origin validation, offset estimation, clock
discipline, and holdover. A bootstrap-only display is a limited client, not
evidence of full synchronization accuracy. Quality and source-selection behavior
for either version is described in Section 8.4. Existing implementation gaps
are not repaired merely by publishing this specification.

## 5. Reference and Local Solar Phase

### 5.1. Definition

Define `frac(x) = x - floor(x)`, including for negative inputs. For the proposed
Solar Model 1, let `alpha_app(t)` be the apparent geocentric solar right ascension
in the true equator/equinox-of-date system, and let `GAST(t)` be Greenwich apparent
sidereal time in the matching system. Express both as angles in radians.

```text
H_G(t) = GAST(t) - alpha_app(t)
P_G(t) = frac(0.5 + H_G(t) / (2*pi))
P_L(t, L) = frac(P_G(t) + L / 360 degrees)
```

`L` is east-positive longitude relative to the Greenwich reference meridian;
west longitude is negative. A client SHOULD normalize it to `[-180, 180)` degrees.
The reference meridian is the adopted coordinate origin, not a civil time zone
or a claim about a particular historical physical meridian marker.

The resulting `P_L` is in `[0, 1)`. At model upper meridian transit it is `0.5`
(local model apparent noon); at lower transit it wraps from almost 1 to 0.
This is apparent solar time expressed in turns, using the hour-angle definition
described by [USNO](https://aa.usno.navy.mil/faq/eqtime), not a newly discovered
astronomical time scale.

GAST MUST NOT be replaced by Earth Rotation Angle while retaining equinox-based
right ascension. A CIO-based alternative must transform both quantities
consistently. Units, reference origin, and sign conventions MUST agree.

### 5.2. Scope of the Longitude-Only Model

Solar Model 1 is an idealized geocentric, longitude-only apparent solar phase.
Clients normally obtain geodetic longitude from the device's location service
(commonly WGS 84), or use a manually selected longitude. The longitude is applied
directly by the formula above. Observer-specific polar-motion corrections,
topocentric parallax, local vertical deflection, elevation, and atmospheric
refraction are not applied to this phase model.

Consequently `0.5` denotes model transit, not a guarantee of an exact observed
solar culmination at every site. Full terrestrial-to-celestial transformations
involve polar motion as described in the
[IERS Conventions, Chapter 5](https://iers-conventions.obspm.fr/content/chapter5/icc5.pdf).
A model requiring those corrections may need latitude and additional state and
is not silently interchangeable with this longitude-only model.

Neither `0.25` nor `0.75` is defined as sunrise or sunset. Determining daylight
also needs latitude, solar declination, and horizon assumptions. A phase value
does not prove that the Sun is above the horizon, including in polar regions.
At a geographic pole, location-derived longitude has no unique physical meaning;
a client MUST use an explicitly selected reference longitude or mark local phase
unavailable rather than suggest a uniquely determined local noon.

### 5.3. Astronomy and Earth Orientation

The proposed Solar Model ID 1 uses apparent geocentric solar direction, IAU 2006
precession, IAU 2000A nutation, and a matching GAST computation. It is a separate
identifier namespace from the ED Model ID, even when both identifiers equal 1.
It remains provisional pending a pinned realization and independent vectors.

The server derives UT1 using `UT1-UTC` from an IERS Earth orientation product.
UT1 governs Earth rotation; TT and, as needed, TDB are used for the astronomical
calculations appropriate to each algorithm. UT1-UTC is a time-scale offset in
seconds, not a phase offset. It MUST NOT be added directly to `P_G`.

IERS [Bulletin A products](https://maia.usno.navy.mil/products/bulletin-a)
provide rapid determinations and predictions. A current result may rely on a
prediction, not a final observation of the current instant. Interpolation MUST
respect UTC leap-second boundaries; naïvely interpolating through a jump in
UT1-UTC is invalid. Unknown correction data MUST NOT silently mean UT1 = UTC.

Servers SHOULD cache ephemeris and Earth orientation data, refresh it outside
the packet-processing path, and retain provenance and error estimates. A failed
download does not invalidate still-usable cached data, but MUST NOT reset its
age or extend the source's supported prediction horizon. Authenticated retrieval
and atomic cache replacement are RECOMMENDED. SOFA's
[time-scale and astronomy guidance](https://www.iausofa.org/cookbooks) is relevant.

Implementations MUST disclose their ephemeris, software/model release, EOP
product and release, interpolation method, coverage, and uncertainty policy
in operational documentation. The packet carries a compact quality summary,
not the full provenance record. No particular Python package is normative.

### 5.4. Rate and Common Epoch

Let `Q = d(unwrapped P_G)/dt`, in turns per SI second. A numerical derivative
MUST unwrap phase around 0/1 before differencing. A fixed `1/86400` is a useful
rough magnitude, not the normative rate.

Reference phase `P_G`, phase rate `Q`, ED `E3`, and ED rate `R` in an accepted
V2 response MUST refer to the same server transmit instant `t3`. Servers MAY
interpolate cached astronomical state to `t3` within their advertised bounds.
Combining ED from one instant with phase from another without propagating both
to a common epoch is invalid.

## 6. Version 2 Packet Proposal

V2 uses exactly 128 octets for both request and response, on the same configured
UDP endpoint as V1. It reuses offsets 0 through 75 from Section 4, except that
the Version bits equal 2. This reuse simplifies implementation, but a V2 packet
MUST NOT be parsed as V1. The following fields complete the V2 packet:

| Offset | Octets | Field | Encoding |
|---:|---:|---|---|
| 76 | 16 | Request Token | Opaque random octets, echoed |
| 92 | 1 | Solar Status | Unsigned enumeration |
| 93 | 3 | Reserved | Zero |
| 96 | 8 | Reference Solar Phase | Unsigned fraction, units `2^-64` turns |
| 104 | 8 | Solar Phase Rate | Signed integer, units `2^-63` turns/s |
| 112 | 4 | Solar Uncertainty | Unsigned fraction, units `2^-32` turns |
| 116 | 4 | Solar Validity | Unsigned whole SI seconds from `t3` |
| 120 | 4 | EOP Data Age | Unsigned whole SI seconds, or unknown |
| 124 | 4 | Solar Model ID | Unsigned model identifier |

All multi-octet integers use network byte order. V2 in this proposal has no
extension trailer: shorter or longer datagrams MUST be rejected as V2. Reserved
octets MUST be sent as zero and nonzero values MUST cause V2 packet rejection.
Future format changes require an explicit specification, not heuristic parsing.

### 6.1. Request Token

A client MUST generate a fresh, nonzero 128-bit token using a cryptographically
secure random generator for each new request, including retries. A server MUST
echo it byte-for-byte. Clients MUST accept it only for the matching outstanding
request and consume it after one response. The token is useful even during
bootstrap when E1 is absent. It does not authenticate the server or defeat an
on-path adversary. Tokens MUST NOT contain stable device identifiers.

### 6.2. Phase and Rate Encoding

Encode reference phase as `floor(P_G * 2^64)` and decode by dividing by `2^64`.
Zero is a valid phase, not a missing-value marker. Availability is determined
by Solar Status. Encode rate as `round(Q * 2^63)` and decode by multiplying by
`2^-63`; round-to-nearest, ties-to-even is used for this new field. A usable
Solar Model 1 rate MUST be positive. Encoders MUST reject overflow rather than
wrap it; clients SHOULD enforce model-appropriate sanity limits.

The fine fixed-point resolution is not a claim of equivalent physical accuracy.
Phase differences use circular arithmetic; rates use an unwrapped phase.

### 6.3. Independent Solar Status

| Value | Meaning |
|---:|---|
| 0 | Unavailable; no usable solar state |
| 1 | Evaluated using observed/final or rapid EOP values over the validity interval |
| 2 | At least part of the validity interval uses published EOP predictions |
| 3 | Holdover/extrapolation beyond the source's supplied coverage, with an explicit bound |
| 4–255 | Reserved |

The classification covers all data supporting the phase, derivative, and
advertised validity interval; the least favorable applicable class is used.
An observed bracket combined with a predicted bracket is class 2, not class 1.
Class 3 MUST NOT be used without a justified extrapolation error bound.

The Flags Status and Stratum describe the ED service. Solar Status is independent:
an ED-synchronized server may return Solar Status 0. Failure of solar data alone
MUST NOT force a switch to V1 or discard otherwise usable ED.

For Solar Status 0, phase, rate, uncertainty, validity, and Solar Model ID MUST
be zero; EOP Data Age MUST be `0xffffffff` (unknown). Clients MUST NOT display
these zero phase bytes as solar midnight. Unknown Solar Status or Solar Model
ID makes the solar block unusable but need not invalidate a valid ED exchange.

### 6.4. Uncertainty, Validity, and Age

Solar Uncertainty encodes `ceil(B * 2^32)`, where `B` is a conservative estimate
of the maximum circular phase error throughout the validity interval when
using the transmitted phase and linear rate. It includes astronomical model,
EOP prediction, computation, quantization, server epoch error, and interpolation
errors relative to the defined model. It is not a statistical confidence level.
It excludes client longitude error and client/network propagation error.
Physical effects intentionally outside Solar Model 1 are also outside this bound.

`0xffffffff` means unknown uncertainty. For a usable solar block, the encoded
bound MUST be less than `0x80000000` (half a turn), and Solar Validity MUST be
between 1 and 3600 seconds inclusive. The actual interval SHOULD be short
(for example 60 seconds) unless an error analysis supports a longer interval.
A server unable to provide such a bound and interval MUST send Solar Status 0.

Solar Validity is the interval `0 <= t - t3 <= V`, not a freshness duration
starting at receipt. A client MUST account for estimated packet age and timing
uncertainty, and stop presenting the state as valid once that bound can exceed V.
Outside it, clients MAY show explicitly stale information or a separately
identified local prediction, but MUST NOT extend the server's validity claim.

EOP Data Age is the ceiling of elapsed SI seconds from the publication epoch
of the EOP product used to `t3`. For multiple products, use the oldest relevant
publication. `0xffffffff` means unknown or unrepresentable age. Download time
MUST NOT substitute for publication time. Age is descriptive, not a guarantee
of accuracy: a recent product may contain predictions and an older product may
contain good historical observations. Clients MAY reject solar state based on
their own age, quality, and uncertainty limits.

## 7. Requests, Responses, and Validation

### 7.1. Version Dispatch and Amplification

A dual-version server MUST inspect the Version bits before choosing a parser.
An empty datagram, unsupported version, malformed request, or unsupported mode
is silently discarded. This proposal defines no version-negotiation error packet.

For V1 requests, return the unchanged V1 response. For V2 requests, return V2,
including when solar state is unavailable. A server MUST NOT send V2 in response
to V1. V1 clients are not expected to understand V2.

A V2 request MUST be 128 octets; a 76-octet packet with its Version bits changed
to 2 is not a valid V2 request. Each accepted unicast request elicits at most
one response, whose UDP payload MUST NOT exceed the request payload. Rate limits,
bounded caches, and bounded per-request computation are REQUIRED. Equal-sized
payloads reduce amplification but do not eliminate spoofed-source reflection.

### 7.2. V2 Client Request

Set Flags to Status 3, Version 2, Mode 3 (`0xd3`), Stratum to 16, Poll to a
locally chosen value (6 by default), and Precision to 0. Set E1 in Transmit
Earth Date if available; otherwise use twelve zero octets for bootstrap.
Set a fresh Request Token. All other request fields MUST be zero. Servers
MUST reject a V2 request not following these rules.

Record a local monotonic send instant `m1`. The server records receive ED `E2`,
copies request Transmit into response Origin unchanged, and evaluates transmit
ED `E3`, `R`, and solar state at `t3`. The response carries the server's ED
status, stratum, source information, Poll recommendation, and Precision.
Reference ED identifies the last successful reference update, or zero if absent.
The response token is copied from the request. Reserved bytes remain zero.

### 7.3. Client Acceptance

Record monotonic receive instant `m4` and destination ED `E4`, if available.
Before using a V2 response, a client MUST check:

- exact length 128, Version 2, Server Mode 4, and zero Reserved bytes;
- source IP address and UDP port match the selected request endpoint;
- token matches an unconsumed outstanding V2 request;
- Origin matches the request Transmit bytes, including a bootstrap zero;
- Flags Status is not 3, Stratum is 1 through 15, and ED Model ID is supported;
- E2 and E3 are present, R is positive, and timing/dispersion values meet policy.

Solar Status, Solar Model ID, positive Q, uncertainty, and validity are then
checked separately. A malformed or unsupported solar block MUST NOT be used as
phase state; clients MAY retain the validated ED portion. Unknown solar support
is not evidence that the server lacks V2.

Model disagreement, excessive delay, or implausible changes SHOULD cause sample
rejection. Advertised precision and stratum are not evidence of trust.

## 8. Synchronization and Display

### 8.1. Four-Coordinate ED Synchronization

Where ED rates are locally compatible over the exchange:

```text
theta_ED = ((E2 - E1) + (E3 - E4)) / 2
delta_ED = (E4 - E1) - (E3 - E2)
```

Positive theta means the client is behind. Conversion of delta_ED into SI
seconds uses the applicable local ED rate, not a universal year length. Clients
requiring better accuracy MUST use a common physical-time mapping or a higher
order model. These estimates inherit the delay-asymmetry limitation of NTP-style
exchanges; they are not exact one-way delay measurements.

### 8.2. Bootstrap and a Common Local Anchor

With absent E1/E4, the client MUST NOT insert zero into the four-coordinate
formula as though it were a valid ED epoch. A limited bootstrap estimate can use:

```text
d_total = m4 - m1
d_server ~= (E3 - E2) / R
d_path = d_total - d_server
d_oneway_estimate = d_path / 2
ED_at_receive ~= E3 + R * d_oneway_estimate
P_G_at_receive ~= frac(P_G_at_transmit + Q * d_oneway_estimate)
```

This approximation requires a stable monotonic oscillator, locally valid R/Q,
and nonnegative delays within measurement uncertainty. Inconsistent samples
MUST be rejected; small negative residuals may only be clamped within a stated
measurement tolerance. One-half path delay is a symmetry assumption. A client
MUST allow for asymmetry; the full nonnegative path delay plus measurement
uncertainty provides a conservative transit-age upper estimate, not half alone.

Use the same elapsed-time anchor for ED and phase. If elapsed monotonic time
since receipt is `u`, advance each using its own rate. For the local display:

```text
P_L(now) = frac(P_G_at_receive + Q * u + L(now) / 360 degrees)
```

Changing longitude changes the local display, not ED or the server state.
Server validity requires the upper estimate of age since `t3`, including `u`,
to remain within Solar Validity. Clients add timing uncertainty multiplied by
the phase rate and longitude uncertainty divided by 360 degrees to the phase
error budget. Time corrections, sleep/resume, or oscillator discontinuities
require re-evaluation or a fresh sample. A wall-clock step MUST NOT be interpreted
as a physical elapsed interval.

### 8.3. Presentation and Appointments

Clients SHOULD distinguish ED synchronization, solar quality, selected location,
and stale state. A manual reference location MUST be labeled as such. Location
permission denial need not disable ED. A circular display naturally represents
the 1-to-0 wrap; an application MUST NOT call that normal wrap a clock fault.

A bare local phase does not uniquely identify an instant: it recurs every solar
cycle. An appointment requires a place/reference longitude and an identified
occurrence, such as an ED search interval. Conversion to a future ED requires an
astronomical prediction; a current packet's short validity interval is not a
long-range scheduling guarantee. Selecting Shibuya rather than the current GPS
location is a client choice, not a new protocol time zone.

### 8.4. ED Holdover, Clock Discipline, and Multiple Sources

For either protocol version, an ED client may retain the last synchronized
anchor `(ED0, R0)` and use `ED ~= ED0 + R0 * delta_t` over a short interval.
For longer intervals it SHOULD use a justified higher-order model, such as
`ED0 + R0*delta_t + 0.5*A0*delta_t^2`, or an astronomical prediction. Here
`A0 = dR/dt`; it is not transmitted by either base packet in this draft.

Clients MUST NOT require continuous connectivity, but MUST distinguish a new
synchronized measurement from prediction/holdover. They SHOULD track growth of
uncertainty and stop claiming usable synchronization when local quality limits
are exceeded. V1 has no explicit validity field: absence of that field is not
permission to extrapolate forever. V2 Solar Validity limits solar state only
and does not define an ED holdover lifetime.

Repeated exchanges SHOULD discipline the ED clock. Small corrections normally
should be smoothed; large corrections may require a step and re-establishment
of the common local anchor. Under normal operation a live ED display SHOULD
not move backward. A deliberate correction must not be hidden by reporting a
false accuracy. Phase wrapping and location changes are distinct from ED steps.

Higher-reliability clients SHOULD use independent sources. Selection may consider
stratum, root delay/dispersion, measured delay, historical stability, model ID,
astronomical provenance, and source independence. Different hostnames do not
necessarily mean independent models or observations. A materially inconsistent
source SHOULD be excluded unless the discrepancy fits explained uncertainty or
model differences. Multiple unauthenticated sources do not by themselves create
cryptographic trust; synchronization loops and shared source failures remain risks.

## 9. Version Compatibility and Fallback

| Client | Server | Result |
|---|---|---|
| V1 | V1 | Existing ED exchange |
| V1 | Dual V1/V2 | Unchanged V1 ED exchange |
| V2-capable | Dual V1/V2 | V2 ED and solar state, or ED with solar unavailable |
| V2-capable | V1 | V2 unanswered; explicit V1 request supplies ED only |

A V2 client SHOULD first try V2. A RECOMMENDED initial timeout is two seconds,
followed by a separate V1 request if availability policy permits. A timeout
means no usable V2 response arrived; it does not prove lack of support.
A V1 packet arriving in reply to a V2 attempt MUST NOT be accepted as a downgrade.
Fallback uses a separately tracked V1 transaction with the rules in Section 4.

Clients SHOULD avoid probing V2 on every V1 poll; a suggested retry interval is
15 minutes with jitter, or after a network/server change. Version preferences
are cached per endpoint with a bounded lifetime, not permanently by hostname.
Clients MAY require V2 and decline fallback. Failure of a solar block within a
valid V2 response is not a reason to downgrade.

Dropping V2 traffic can force an availability-oriented client toward V1. This
is an unauthenticated downgrade risk and MUST be documented. Neither version
provides integrity simply because a successful response was received.

## 10. Related Work and Design Rationale

### 10.1. UTC, TAI, and UT1

UTC/TAI provide atomic-time foundations; UT1 represents Earth rotation.
NEPP distributes an astronomical coordinate rather than replacing these inputs.
Its independence from a fixed seconds-per-year definition is not independence
from time metrology in a realization. See
[BIPM Time Metrology](https://www.bipm.org/en/time-metrology).

### 10.2. NTP and PTP

[NTPv4](https://www.rfc-editor.org/rfc/rfc5905.html) provides the direct precedent
for four-event offset/delay estimates, polling, strata, and clock discipline.
NEPP adapts that pattern to a nonuniform ED coordinate and transmits rates.
Its 96-bit timestamps and flags are not wire-compatible with NTP, and it MUST
NOT use the NTP service port as if it were NTP.

[IEEE 1588/PTP](https://www.nist.gov/el/intelligent-systems-division-73500/ieee-1588-systems)
coordinates clocks within a time-distribution system. NEPP does not claim to
match PTP accuracy, implement its mechanisms, or make a high-quality underlying
clock unnecessary. NTP/PTP can support the host clock used for astronomical
evaluation; ED and solar phase describe what coordinates are then distributed.

### 10.3. Unix Time and Julian Date

[POSIX seconds since the Epoch](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap04.html#tag_04_16)
and [Julian Date](https://aa.usno.navy.mil/data/JulianDate) already express dates
numerically. NEPP does not claim novelty merely for replacing a calendar string
with a number. Julian Date is a day count with a fractional part; precise use
requires identifying the underlying time scale. ED instead assigns its fraction
to solar longitude, preserving orbital phase rather than uniform elapsed time.

### 10.4. Decimal Time and Swatch Internet Time

Decimal subdivision alone is not a new contribution. A display in tenths or
thousandths can be applied to many time conventions without changing their
physical definition. [Swatch Internet Time](https://www.swatch.com/th-th/internet-time.html)
divides a conventional 24-hour day into 1000 beats referenced to Biel Mean Time.
NEPP's local solar phase instead depends continuously on selected longitude and
apparent solar motion. It is not a fixed civil day rescaled into decimal units.

### 10.5. Mean and Apparent Solar Time; Civil Time Zones

Mean solar time regularizes solar motion; apparent solar time follows the Sun's
hour angle. Their difference includes the equation of time. The proposed phase
is a normalized expression of the latter, not UTC plus longitude alone.
The astronomical distinction is described by
[USNO](https://aa.usno.navy.mil/faq/eqtime).

Civil zones provide useful shared schedules at the cost of differences from
local solar time. NEPP neither assigns civil authority nor requires abolishing
zones. It separates global instant exchange from local daily context. The
contribution proposed here is the combination of ED synchronization, explicit
reference phase/rate/quality, and private client-side localization, not the
invention of solar time or proof that society should adopt it.

## 11. Security, Privacy, and Operations

Both versions in this draft are unauthenticated. Spoofing, replay, malicious
source selection, delay manipulation, false uncertainty, and denial of service
remain possible. V2's random token improves off-path correlation but is not a
MAC, signature, or source authentication mechanism. V1's Origin correlation is
particularly weak during zero-timestamp bootstrap. These limitations MUST NOT
be described as secure synchronization.

[Network Time Security](https://www.rfc-editor.org/rfc/rfc8915.html) is a relevant
NTP security precedent, not a protocol automatically usable with NEPP packets.
Authenticated NEPP framing and downgrade protection require separate design.
High-integrity uses need an appropriate authenticated, reviewed mechanism.

Requests contain no latitude, longitude, place name, or persistent user ID.
Clients MUST NOT encode location in the token or reserved/request padding.
Location services and manual-place storage remain client-side. The server still
sees source IP addresses and query times; it MUST NOT claim network anonymity.
Operators SHOULD minimize retained logs and bound transient rate-limit state.

Servers SHOULD perform version/length checks and rate limiting before expensive
astronomy. EOP retrieval SHOULD be scheduled independently, with an explicit
failure policy. Unavailability of solar data must not unnecessarily interrupt
the established V1 ED service. Transport uses a configurable experimental
dynamic/private UDP port; `56377` is a deployment choice, not an IANA assignment.

## 12. Encoding Examples and Validation Plan

The following are synthetic arithmetic examples, not astronomical predictions:

| Quantity | Input | Expected result |
|---|---|---|
| V2 bootstrap flags | Status 3, Version 2, Mode 3 | `d3` |
| V2 synchronized server flags | Status 0, Version 2, Mode 4 | `14` |
| Reference phase wire | `P_G = 0.5` | `80 00 00 00 00 00 00 00` |
| Reference phase wire | `P_G = 0.25` | `40 00 00 00 00 00 00 00` |
| Local phase | `P_G = 0.9`, `L = +90 degrees` | `0.15` |
| Local phase | `P_G = 0.1`, `L = -90 degrees` | `0.85` |
| Exact rate test | `Q = 2^-16 turns/s` | signed integer `2^47` |
| Exact uncertainty test | `B = 2^-20 turns` | unsigned integer `4096` |

A synthetic 128-octet bootstrap request has byte 0 = `d3`, byte 1 = `10`,
byte 2 = `06`, token bytes 76 through 91 = `01 02 ... 10`, and all other bytes
zero. That fixed token is for an encoding test only, never production randomness.

Required tests before deployment include:

1. Exact field offsets, signedness, sizes, and short/oversized packet rejection.
2. V1 regression: unchanged requests/responses and continued iOS 0.0.1 operation.
3. Unknown version/mode, nonzero reserved bytes, wrong endpoint/token/Origin,
   duplicate and late replies, and equal request/response payload lengths.
4. ED bootstrap without using absent coordinates in offset formulas; year wrap.
5. Solar wrap in both longitude signs, derivative unwrapping, and shared epoch.
6. Solar unavailable, reserved status, unsupported model, and ED-only operation.
7. Expired validity including packet age, clock jumps, suspend/resume, EOP
   download failure, prediction boundaries, and leap-second-safe interpolation.
8. All combinations in Section 9, including timeout that was caused by loss.

Astronomical vectors MUST identify epoch and time scale, UTC/TAI/UT1 conversion
inputs, EOP product/version, ephemeris, celestial reference system, model/software
version, GAST, apparent solar right ascension, ED/R, P_G/Q, longitude, and expected
local phase with tolerances. Vectors MUST include noon, wrap, seasonal points,
and observed/predicted transitions. Independent computation is REQUIRED before
calling them normative interoperability vectors. None are supplied as validated
astronomical vectors by this revision.

## 13. Implementation Status and Open Questions

The repository contains an experimental V1 Python server/client and iOS client;
the author has reported successful public-server and TestFlight use of iOS
0.0.1. This is operational experience, not independent verification of the full
astronomical profile. V2 and the proposed solar feature are not implemented.
This draft alone changes neither the running server nor the app.

Before freezing V2, review:

- the 128-octet layout and quality/validity encodings;
- a reproducible ED Profile 1 realization, including reference geometry;
- pinned solar-model algorithms, supported epochs, and ephemeris versions;
- justified model/rate/clock uncertainty bounds and extrapolation limits;
- a client timing policy for bootstrap, asymmetry, and location error;
- whether a future higher-precision model should include polar motion;
- authentication, authenticated version negotiation, and registry policy.

The longitude-only simplification is deliberate and reviewable. An exact
observational-noon claim or a numerical accuracy claim must wait for a model
and error analysis that supports it.

## 14. IANA Considerations

This working revision requests no IANA action. Version 2 and Solar Model ID 1
are experimental proposal values, not IANA registrations. Future work may
request a service port and registries for astronomical models and extensions.

## 15. References

### 15.1. Definition and Model References

- BCP 14: [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html),
  [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html).
- [IERS Conventions (2010), Technical Note 36](https://iers-conventions.obspm.fr/conventions/content/tn36.pdf),
  including IAU 2006/2000A celestial models and time/rotation transformations.
- [USNO: The Equation of Time](https://aa.usno.navy.mil/faq/eqtime),
  for the apparent solar time/hour-angle convention.

### 15.2. Informative and Operational References

- [NEPP revision -01](draft-iwata-nepp-01.md), historical comparison only;
  not required to implement the specification in this document.

- [IAU SOFA cookbooks](https://www.iausofa.org/cookbooks).
- [IERS rapid service / Bulletin A products](https://maia.usno.navy.mil/products/bulletin-a).
- [BIPM Time Metrology](https://www.bipm.org/en/time-metrology).
- [RFC 5905: NTPv4](https://www.rfc-editor.org/rfc/rfc5905.html).
- [RFC 8915: Network Time Security](https://www.rfc-editor.org/rfc/rfc8915.html).
- [NIST: IEEE 1588 Systems](https://www.nist.gov/el/intelligent-systems-division-73500/ieee-1588-systems).
- [POSIX: Seconds Since the Epoch](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap04.html#tag_04_16).
- [USNO: Julian Date](https://aa.usno.navy.mil/data/JulianDate).
- [Swatch: Internet Time](https://www.swatch.com/th-th/internet-time.html).

## Author

Kenichi Iwata  
Tottori University, Japan  
Project: [nepp.kenic.jp](https://nepp.kenic.jp/)  
Contact: support@kenic.jp
