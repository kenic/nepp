# Network Earth Position Protocol (NEPP)

## Earth Date Synchronization and Location-Local Solar Phase

### draft-iwata-nepp-03

Intended status: Experimental  
Kenichi Iwata, Tottori University  
31 August 2026

## Status of This Memo

This is an author working draft for discussion, not an Internet-Draft submitted
to the IETF. It is not an Internet Standard. The Version 2 layout, field codes,
and astronomical profile below remain proposals. A local experimental V2-only
server exists, but independent astronomical validation is pending. Publication
does not assert interoperability or production deployment.

The English edition is authoritative. The Japanese edition is for reference.
Draft revision `-03`, protocol Version 2, and application version `0.0.2` are
independent identifiers. Revisions `-00`, `-01`, and `-02` remain historical documents.

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
or prescribe civil time zones. V1 and V2 are not wire-compatible. Continued V1
service and operation of existing V1 clients are NOT guaranteed after migration.
V2-only servers and clients are permitted; V1 support is optional.

## 1. Changes and Scope

Compared with `-02`, this revision:

- separates coordinate definitions, source realizations, and network distribution;
- identifies the current clock/ephemeris implementation as an experimental,
  provisional realization, not a required source architecture;
- retains SI seconds for elapsed time without requiring UTC/NTP synchronization;
- distinguishes unavailable coordinates from available coordinates with unknown
  uncertainty, independently for ED and Solar Phase (SP);
- specifies the of-date ecliptic/true-equinox geometry and the included and
  omitted effects of a basic solar-direction model;
- separates provenance, supply state, prediction information, uncertainty, and
  validity, without requiring an IERS-based source;
- retains the Stratum 0 reference-source / Stratum 1 network-entry distinction
  and requires source-to-server epoch alignment.

Section 6 concretizes these policies as a NEW, REVIEWABLE 160-octet V2 layout.
The field assignments are a proposal in this revision, not previously agreed
or deployed wire behavior. It replaces the unimplemented 128-octet V2 proposal
in `-02`; the two proposals are not wire-interoperable. Neither layout is an
established V2 standard. V1's 76-octet base format is unchanged.
Retaining its description does not require implementations to provide V1.
This revision explicitly permits a beta-service migration requiring client
updates, without a continuing V1 endpoint or automatic V1 fallback.

This document is self-contained for V1 and the proposed V2. It distributes
instantaneous state, not GPS coordinates or appointments. Sunrise, sunset,
solar altitude, maps, civil-zone conversion, metadata transport, and
authentication framing remain outside the base exchange.

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

ED Model ID 1 denotes the experimental basic coordinate model below. Its
intended geometry is clarified here; compliance and numerical equivalence of
deployed V1 implementations have NOT been established. A model identifier alone
does not prove accuracy. See Sections 12 and 13 before changing a deployed source.

#### 3.2.1. Epoch, plane, and origin

The epoch `t` is the event being represented, not the time at which a computer
happens to perform the calculation. All coordinate axes below are evaluated
at `t`, including for past or future queries.

The ecliptic follows IAU 2006 Resolution B1, recommendation 4: its pole is the
mean orbital angular-momentum direction of the Earth-Moon barycenter in BCRS.
It is NOT an instantaneous plane obtained merely from Earth's position and
velocity. The of-date realization uses IAU 2006/P03 precession.

The origin is the TRUE equinox of date, incorporating IAU 2000A nutation with
the IAU 2006 adjustments. It is not a fixed J2000 origin, a mean equinox, or an
origin frozen at that year's March crossing. The observer is Earth's center;
the target is the Sun's center, not its limb or a brightness-weighted disk point.

#### 3.2.2. Basic solar-direction model

The following mathematical model defines the target direction. A source MAY
calculate it locally or obtain an equivalent coordinate from a reference source.
The computation below is not a required server architecture.

Use BCRS-compatible barycentric positions `x_E(t)`, `x_S(te)` and Earth's
barycentric velocity `v_E(t)`, with ephemeris time arguments and units consistently
converted (typically TDB-compatible positions, velocities, and light speed).
Find the retarded emission epoch by solving

```text
te = t - |x_S(te) - x_E(t)| / c
p = (x_S(te) - x_E(t)) / |x_S(te) - x_E(t)|
```

This is Euclidean light-time iteration, without gravitational propagation delay.
The observer remains at the reception event `t`; simply evaluating both bodies
at `te`, or subtracting a fixed eight minutes from the resulting longitude,
does not implement this definition.

Apply special-relativistic aberration for the geocenter's barycentric velocity.
With `b = v_E(t)/c`, `g = sqrt(1 - b dot b)`, and `w = p dot b`, define

```text
s = normalize(g*p + (1 + w/(1+g))*b)
```

This is the pure Lorentz aberration prescription, with the observer velocity
sign as written. Do not apply aberration again to an already corrected input.
The basic model omits gravitational light deflection by all bodies,
gravitational light-time delay, and gravitational-potential terms in the
direction transformation. This does NOT remove gravity or relativistic dynamics
from the ephemeris used to obtain the bodies' positions.

SOFA `iauAb` is a useful reference but includes a solar gravitational-potential
term; it is not exactly the pure prescription above. Likewise `iauLdsun` is a
distant-source light-deflection routine, not a recipe for the Sun's own center.
Implementers MUST check included effects rather than label any generic routine
"apparent" and assume equivalence.

The resulting direction is a deliberately specified BASIC MODEL apparent
direction. No claim is made that omitted effects are below a particular bound,
or that it represents an exact physical observation. A new definition adding
omitted effects must be explicitly distinguished, normally with a new Model ID.
More accurate evaluation of the SAME definition does not itself require one.

#### 3.2.3. Conversion to ED and the shared solar direction

Evaluate at `TT(t)` the bias-precession-nutation matrix `B(t)` equivalent to
SOFA `iauPnm06a` (IAU 2006/2000A), the mean obliquity `eps_A` equivalent to
`iauObl06`, and nutation in obliquity `deps` from `iauNut06a`.
Let `(x,y,z) = B(t)*s` and `eps = eps_A + deps`. Define:

```text
xe = x
ye = cos(eps)*y + sin(eps)*z
ze = -sin(eps)*y + cos(eps)*z
lambda = atan2(ye, xe) modulo 2*pi
alpha_app = atan2(y, x) modulo 2*pi
ED = Y + lambda/(2*pi)
```

These operations specify the axes and signs without mandating a language or
library. SOFA `iauEcm06` alone uses the MEAN equinox and is not this conversion.
The same `s` and `alpha_app` define Solar Model 1 in Section 5. Geocentric
coordinates exclude topocentric parallax, diurnal observer aberration,
atmospheric refraction, local vertical, and horizon effects.

A specific ephemeris product or numerical library is not mandated. Realizations
MUST disclose their choices and known limitations. Unknown uncertainty is
allowed by V2; it does not license silently substituting another coordinate
definition. Independent numerical vectors are still required before claiming
validated interoperability or a finite accuracy bound.

### 3.3. Time Scales and Earth Date Rate

SI seconds are the units of elapsed time, network delay, and coordinate rates.
A monotonic oscillator provides elapsed intervals in a realization; each device
need not contain an atomic clock. Neither UTC synchronization nor NTP is a
protocol prerequisite. Oscillator scale error, drift, and epoch-transfer error
contribute to uncertainty and MUST NOT be assumed zero when unknown.

TT/TDB and UT1 are used where required by a computational realization. A UTC
input must be converted consistently, including leap seconds. ED inserts no
civil leap day or leap second of its own. Using SI seconds does not equate ED
to a fixed number of seconds per year.

The rate `R = dED/dt` is in ED per SI second; `Q` in Section 5 is in turns per
SI second. Algorithms using TDB or another coordinate time must consistently
convert rates to the realization's elapsed-SI-second convention; TT is the
reference terrestrial time argument here. Uncertainty includes imperfections
in realizing that convention. Derivatives crossing a March boundary MUST use
continuous complete ED, not a wrapped fraction. Linear propagation is local,
not an indefinite astronomical prediction.

### 3.4. Reference Sources and Distribution

The current clock-plus-ephemeris implementation is provisional software for
experiments and validation. Its host-clock dependency is not a NEPP requirement.
Future reference sources are envisaged to supply more accurate coordinates with
verifiable quality; that is a development goal, not an automatic guarantee.

Stratum 0 denotes the reference system generating coordinates. Stratum 1 is the
NEPP network entry directly connected to that system. A server synchronized
through an upstream Stratum 1 NEPP source is Stratum 2, and so on. Network
synchronization sources advertise 1 through 15, never 0. Reference-source
connections can be internal calls, hardware interfaces, or separately defined
links; NEPP does not require a new network protocol between Stratum 0 and 1.

The source interface MUST associate each coordinate with the event it represents.
The receiving server must relate that event to its local elapsed-time anchor,
account for transfer and processing delay, and propagate to the response epoch.
A UTC timestamp is one possible method, not the only one. Unknown transfer
error must remain unknown in quality reporting.

Network links between NEPP servers use the same exchange as client links; the
existing four-event method is retained. Different ED and SP sources must be
aligned to the SAME response epoch. Stratum denotes NEPP source distance, not
the number of NTP hops inside a realization or a certificate of accuracy.

## 4. Version 1 Specification

This section specifies V1 independently of previous revisions. V2's token,
160-octet length, zero-padding rules, and solar fields MUST NOT be required of
V1 clients. The V1 packet format and field meanings remain unchanged.
This section applies only to implementations that elect to support V1; it is
not a requirement for a V2-only implementation to implement or serve V1.

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

A primary server directly obtains ED from a reference realization; secondary
servers obtain it through upstream NEPP servers. Local astronomical computation
is one reference realization, not a mandatory primary-server operation.
Section 3.4 defines Stratum 0 and network entry at Stratum 1.

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
V1 has no explicit unknown-uncertainty encoding. A server unable to supply a
finite truthful bound MUST NOT advertise a usable V1 synchronization sample;
it may send Status 3 / Stratum 16 or decline to offer V1 synchronization.
This does not prevent V2 from supplying an explicitly unassessed coordinate.
Keeping V1 wire compatibility does not justify a false zero dispersion.

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

A basic V1 server supplies Profile 1 ED, E2/E3 timestamping, ED
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

SP abbreviates Solar Phase; LSP abbreviates Local Solar Phase. `P_G` is the
reference SP and `P_L` the LSP. Solar Model ID 1 uses the basic solar direction
from Section 3.2 and IAU 2006/2000A GAST, equivalent to SOFA `iauGst06a` with
consistent UT1 and TT inputs. Solar and ED Model IDs are separate namespaces.

An astronomical realization may derive UT1 from IERS `UT1-UTC`. This is one
source path, not a required SP server architecture. Direct-coordinate sources
must produce the same model quantity and disclose their provenance.
UT1-UTC is a time offset, not an angle, and MUST NOT be added directly to phase.
Interpolation across UTC leap seconds must handle the discontinuity correctly.
Unknown UT1 correction must not silently become UT1 = UTC.

IERS observed/rapid and predicted data are useful inputs, not quality ranks.
Recent data may be predicted; older data may be an appropriate observation.
Sources SHOULD cache inputs and refresh them outside packet processing. Failed
downloads MUST NOT reset publication age or extend coverage. Authenticated
retrieval and atomic replacement are RECOMMENDED.

Servers MUST publish known provenance and limitations in operational
documentation, including applicable ephemeris/EOP releases, model and software
versions, prediction coverage, interpolation, omitted effects, and uncertainty
method. They MUST explicitly identify unknown information. Section 6 carries
frequently needed per-coordinate facts. A machine-readable detailed-metadata
service is future work, not an invented extension to the base packet.

### 5.4. Rate and Common Epoch

Let `Q = d(unwrapped P_G)/dt`, in turns per SI second. Derivatives MUST unwrap
0/1 crossings. Fixed `1/86400` is a rough magnitude, not the defined rate.

Response `P_G`, `Q`, `E3`, and `R` MUST refer to the same transmit event
`t3`. Source updates or caches must not mix epochs. Propagation to `t3` is
allowed even with unknown uncertainty, but MUST NOT invent a finite bound.
A reference update occurring during response construction must be handled
consistently, for example with an atomic snapshot. E2 remains the receive event.

## 6. Version 2 Packet Proposal

Both request and response are exactly 160 octets. Offsets 0 through 75 use the
Section 4 layout, with Version 2 and the explicit V2 qualifications below.
Offsets 76 onward are NEW in this revision:

| Offset | Octets | Field |
|---:|---:|---|
| 76 | 16 | Request Token |
| 92 | 8 | Reference Solar Phase |
| 100 | 8 | Solar Phase Rate |
| 108 | 4 | Solar Model ID |
| 112 | 24 | ED Quality Descriptor |
| 136 | 24 | SP Quality Descriptor |

All integers are big endian, signed integers two's complement. There is no
extension trailer. Reject any other length, including the 128-octet proposal
from `-02`; never guess which V2 layout was intended. Experimental endpoints
must coordinate this revision out of band before testing.

### 6.1. Request Token

Each request, including retries, MUST use a fresh, nonzero, CSPRNG-generated
128-bit token. The server echoes it byte-for-byte. Accept it only for the
matching unconsumed outstanding request, then consume it. Token lifetime and
outstanding state must be bounded. This is correlation, not authentication,
and must not encode location or a stable device identifier.

### 6.2. Coordinate and Rate Encoding

ED timestamps retain Section 4.2 encoding. Encode SP as `floor(P_G * 2^64)`;
zero is a valid midnight phase, not a missing marker. A descriptor signals
availability. Encode Q as signed `round(Q * 2^63)`, nearest with ties to even.
For V2 use the same rounding convention for R. Reject overflow; never wrap.
Model 1 requires positive R and Q for usable state. Precision is resolution,
not accuracy. ED arithmetic includes the year; SP differences are circular.

### 6.3. Per-Coordinate Quality Descriptor

The following relative offsets apply independently at 112 and 136:

| Relative offset | Octets | Field |
|---:|---:|---|
| 0 | 1 | Supply State |
| 1 | 1 | Source Kind |
| 2 | 1 | Quality Flags |
| 3 | 1 | Coordinate Stratum |
| 4 | 4 | Coordinate Reference ID |
| 8 | 4 | Coordinate Uncertainty |
| 12 | 4 | Validity |
| 16 | 4 | Source Data Age |
| 20 | 4 | Source Update Age |

Supply State:
0 unavailable; 1 tracking an available source within its supported coverage;
2 holdover after updates were lost or coverage exceeded;
3 available, but supply state unknown; 4–255 reserved.
Tracking does NOT imply observed rather than predicted input or evaluated
accuracy. Holdover can carry either known or unknown uncertainty.

Source Kind:
0 unknown; 1 astronomical computation; 2 direct coordinate source;
3 upstream NEPP; 4 combination of sources; 5–255 reserved.
These describe the immediate supply path, not accuracy classes. Detailed
upstream provenance belongs in documentation.

Quality Flags:
bit 0 = uncertainty evaluated (1) or unknown (0);
bits 2:1 = prediction information: 0 unknown, 1 no prediction, 2 prediction
used, 3 reserved; bits 7:3 reserved zero.
"Prediction used" means supporting inputs were forecast or extrapolated beyond
observational coverage; ordinary interpolation inside coverage is not prediction.
It covers inputs needed over the advertised interval. Local propagation already
covered by a validated rate/interval is not by itself an additional prediction
classification. If the interval or input classification is unknown, report
unknown unless prediction use is already known. A downstream source must not
turn an unknown upstream fact into a known one.

Coordinate Stratum is 1–15 when known, 0 when unknown; 16–255 are invalid for an
available descriptor. ED stratum MUST be known and equal the base Stratum.
SP may have a different source path and stratum. A relaying server increments
the coordinate's upstream stratum; if that would exceed 15 it must not supply
that coordinate as usable. Source Kind 4 reports the largest contributing
known stratum, or unknown if any relevant path is unknown. This cannot satisfy
the ED-known-stratum requirement if any relevant ED path is unknown.

Reference IDs are 32-bit identifiers scoped to the server's documented
provenance, not authenticated global identities; zero means unspecified.
The ED descriptor Reference ID MUST equal the base Reference ID.
Different coordinate IDs or kinds do not alone prove independent sources.

An unavailable descriptor is all zero; SP phase/rate/model fields must also be
zero when SP is unavailable. A zero SP with an available descriptor is midnight.
A successful exchange requires available ED (Section 7); SP remains optional.
Unknown Supply State, reserved flag bits, or reserved prediction bits invalidate
that coordinate block. Unknown Source Kind is treated as unknown provenance,
not a reason by itself to discard the coordinate.

### 6.4. Uncertainty, Validity, and Ages

Coordinate Uncertainty is unsigned `ceil(B * 2^32)`: ED units for ED, turns
for SP. If bit 0 is clear it MUST be `0xffffffff`, meaning unknown, NOT zero.
If bit 0 is set it MUST be at most `0xfffffffe`; SP additionally requires less
than `0x80000000`, since a half-turn bound carries no useful phase constraint.
Overflow or inability to justify the bound must be reported as unknown, not
saturated or as unavailable solely for that reason.

An evaluated B is a conservative estimated maximum absolute ED error or
circular SP error throughout the stated interval, using the transmitted linear
rate. It is not a statistical standard deviation or an unconditional guarantee.
It includes source uncertainty, realization error, epoch transfer, host oscillator,
computation, quantization, and propagation errors relative to the defined model.
Effects excluded by Section 3.2 are outside this MODEL error bound and must not
be represented as tested physical accuracy. Receiver/network and location
errors are additional client contributions.

Validity is unsigned SI seconds from `t3`: 0 means at `t3` only; 1–3600 means
a stated forward interval; `0xffffffff` means unknown; other values are reserved.
An evaluated bound requires a known Validity. Unknown uncertainty MAY accompany
a known intended usage interval; that is not a promise of numerical accuracy.
Unknown validity does not mean indefinite validity. Clients may display such
values under a bounded local freshness policy, explicitly unassessed.

An evaluated ED bound also covers E2 at reception (as well as the forward E3/R
interval), so that timing acceptance cannot treat the receive timestamp as
perfect. If the source cannot support this it reports ED uncertainty unknown.

Source Data Age is the ceiling of SI seconds since the oldest relevant input
product's publication. Source Update Age is the ceiling of SI seconds since
the reference-source event last successfully incorporated, not packet reception
or cache-read time. Both are relative to `t3`, with `0xffffffff` unknown or
unrepresentable; zero means a known age of zero. Neither is a quality guarantee.
Relays must preserve or advance ages appropriately, not reset them at each hop.
Unknown source-event mapping must yield unknown age. Unavailable descriptors
instead use their canonical all-zero representation.

Base Root Dispersion in V2 uses `0xffffffff` as UNKNOWN (unlike V1).
Finite values retain unsigned 16.16 SI-second units and require a justified
time-error estimate; they MUST NOT contradict the ED descriptor. If ED
uncertainty is unknown, Root Dispersion MUST also be unknown. A known ED bound
may coexist with unknown time dispersion when a conservative conversion is not
available. In V2, zero is never a substitute for unknown. Root Delay retains
its V1 meaning; when its accumulated value cannot be estimated, V2 likewise
uses `0xffffffff` for unknown, never as a measured huge delay.

Base Flags describe ED supply: tracking permits Status 0 or 1, holdover uses 2,
unknown supply state uses 1, unavailable ED uses 3 / Stratum 16.
An unevaluated bound alone does not force unsynchronized status. V2 clients
must evaluate the descriptor and must not infer accuracy from Status 0.
For unavailable ED the base Reference ID, Reference/E2/E3/R/Model fields are
zero and its descriptor is zero; Origin and Token still echo the request.

Clients decide whether known quality meets their use case. They MAY accept
available ED/SP with unknown uncertainty, but MUST NOT label it precision-
verified. They MAY reject it for precision-sensitive use. Invalid structure,
unknown coordinate model, and absent values are distinct from unknown quality.
A malformed SP block does not require rejecting otherwise valid ED.

### 6.5. Freshness and Propagation

Clients must account for age since `t3`, including transit, not restart Validity
at receipt. To claim a server bound still applies, the upper estimated age must
fit the stated interval and client timing/location errors must be included.
If timing uncertainty is unknown, no guaranteed age or total bound may be claimed.

After expiry, display may continue only as explicitly stale or separately
identified local prediction, not within the server's original validity claim.
Unknown validity requires a bounded local policy and no server-validity claim.
Relaying servers must propagate upstream uncertainty and validity conservatively;
a fresh outgoing packet cannot renew an expired upstream bound. Independent
source evaluation is needed to justify any new finite bound.

## 7. Requests, Responses, and Validation

### 7.1. Version Dispatch and Amplification

A server MUST inspect the Version bits before choosing a supported parser.
An empty datagram, unsupported version, malformed request, or unsupported mode
is silently discarded. This proposal defines no version-negotiation error packet.

If V1 service is enabled, V1 requests receive V1 responses under Section 4.
A V2-only server MUST silently discard V1 requests, without interpreting them
as V2 or returning a V2 response. For accepted V2 requests, return V2, including
when solar state is unavailable. A server MUST NOT answer a request using a
different Version. V1 clients are not expected to understand V2.

A V2 request MUST be 160 octets; a 76-octet packet with its Version bits changed
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
Reference ED identifies the ED at the reference event last incorporated, or zero
if unavailable; it is not the time a file was downloaded.
The response token is copied from the request. Reserved bits remain zero.
Response ED descriptor fields must agree with base fields as in Section 6.4.
Each available coordinate reports known facts and explicitly marks unknowns.

### 7.3. Client Acceptance

Record monotonic receive instant `m4` and destination ED `E4`, if available.
Before using a V2 response, a client MUST check:

- exact length 160, Version 2, Server Mode 4, and valid structural fields;
- source IP address and UDP port match the selected request endpoint;
- token matches an unconsumed outstanding V2 request;
- Origin matches the request Transmit bytes, including a bootstrap zero;
- Flags Status is not 3, Stratum is 1 through 15, and ED Model ID is supported;
- E2 and E3 are present, R is positive, and the ED descriptor is consistent;
- known timing and uncertainty meet local policy; unknowns are handled explicitly.

SP descriptor, Solar Model ID, positive Q, uncertainty, and validity are then
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
and nonnegative delays within measurement uncertainty. With unassessed input,
these remain provisional estimates, not established bounds. Inconsistent samples
MUST be rejected; small negative residuals may only be clamped within a stated
measurement tolerance. One-half path delay is a symmetry assumption. A client
MUST allow for asymmetry; the full nonnegative path delay plus measurement
uncertainty provides a conservative transit-age upper estimate, not half alone,
only when the server timestamps/rate and elapsed-time errors are sufficiently
bounded. Otherwise the transit-age uncertainty remains unknown.

Use the same elapsed-time anchor for ED and phase. If elapsed monotonic time
since receipt is `u`, advance each using its own rate. For the local display:

```text
P_L(now) = frac(P_G_at_receive + Q * u + L(now) / 360 degrees)
```

Changing longitude changes the local display, not ED or the server state.
Server validity requires the upper estimate of age since `t3`, including `u`,
to remain within the coordinate's known Validity. Unknown Validity is handled
by Section 6.5, not silently treated as infinite. Clients add timing uncertainty multiplied by
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
permission to extrapolate forever. V2 has separate ED and SP Validity fields. The two intervals may differ.

Repeated exchanges SHOULD discipline the ED clock. Small corrections normally
should be smoothed; large corrections may require a step and re-establishment
of the common local anchor. Under normal operation a live ED display SHOULD
not move backward. A deliberate correction must not be hidden by reporting a
false accuracy. Phase wrapping and location changes are distinct from ED steps.

Higher-reliability clients SHOULD use independent sources. Selection may consider
stratum, known root delay/dispersion, per-coordinate uncertainty and validity,
measured delay, historical stability, model ID,
astronomical provenance, and source independence. Unknown values must not be
ranked as zero error; unassessed sources may be used only under explicit policy. Different hostnames do not
necessarily mean independent models or observations. A materially inconsistent
source SHOULD be excluded unless the discrepancy fits explained uncertainty or
model differences. Multiple unauthenticated sources do not by themselves create
cryptographic trust; synchronization loops and shared source failures remain risks.

## 9. Version Compatibility and Fallback

V1 and V2 are distinct, non-wire-compatible protocols. Servers and clients MAY
implement V2 only. Continued service to V1 clients is NOT REQUIRED, and users of
V1-only applications must update to use a V2-only endpoint. Keeping the V1
format documented or optionally implemented is not a backward-compatibility
promise for a deployment. Operators MAY retire the beta V1 service.

| Client | Server | Result |
|---|---|---|
| V1 | V1 | Existing ED exchange |
| V1 | Dual V1/V2 | Unchanged V1 ED exchange |
| V1 | V2-only | Request discarded; client update required |
| V2-only | V2-only or dual | V2 exchange; no V1 fallback |
| V2-only | V1-only | No compatible response; unavailable |
| V2-capable | Dual V1/V2 | V2 ED and solar state, or ED with solar unavailable |
| Dual client with fallback enabled | V1 | Separate V1 transaction may supply ED only |

A V2 client sends V2 requests. A RECOMMENDED initial timeout is two seconds.
Automatic V1 fallback is NOT REQUIRED. A client that separately implements V1
MAY fall back only when its explicit availability policy permits; a V2-only
client reports unavailability instead. A timeout means no usable V2 response
arrived; it does not prove lack of support.
A V1 packet arriving in reply to a V2 attempt MUST NOT be accepted as a downgrade.
Fallback uses a separately tracked V1 transaction with the rules in Section 4.

For clients opting into fallback, avoid probing V2 on every V1 poll; a suggested retry interval is
15 minutes with jitter, or after a network/server change. Version preferences
are cached per endpoint with a bounded lifetime, not permanently by hostname.
Clients MAY require V2 and decline fallback. Failure of a solar block within a
valid V2 response is not a reason to downgrade.

When optional fallback is enabled, dropping V2 traffic can force a client toward V1. This
is an unauthenticated downgrade risk and MUST be documented. Neither version
provides integrity simply because a successful response was received.

Before switching a public beta endpoint to V2-only, operators SHOULD announce
the cutover and required client update, including that old clients may stop
working. Providing an overlap period or a separate V1 endpoint is optional.
Publication of this draft is not itself a service cutover.

## 10. Related Work and Design Rationale

### 10.1. UTC, TAI, and UT1

UTC/TAI provide atomic-time foundations; UT1 represents Earth rotation.
NEPP distributes astronomical coordinates rather than replacing time metrology.
A source need not obtain coordinates through a UTC/NTP-based calculation.
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
evaluation, but neither is a mandatory source dependency. NEPP-network hops
use NEPP; the connection from a reference system to Stratum 1 is implementation-
specific, with epoch-transfer responsibility as in Section 3.4.

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
astronomy. Reference-input retrieval SHOULD be scheduled independently, with an explicit
failure policy. Unavailability of solar data must not unnecessarily interrupt
ED service in an enabled version; this does not require continued V1 service.
Transport uses a configurable experimental
dynamic/private UDP port; `56377` is a deployment choice, not an IANA assignment.

## 12. Encoding Examples and Validation Plan

These are synthetic encoding examples, not astronomical predictions:

| Quantity | Input | Expected result |
|---|---|---|
| V2 bootstrap flags | Status 3, Version 2, Mode 3 | `d3` |
| V2 tracking server flags | Status 0, Version 2, Mode 4 | `14` |
| Reference SP | 0.5 | `80 00 00 00 00 00 00 00` |
| Reference SP | 0.25 | `40 00 00 00 00 00 00 00` |
| Local SP | P_G=0.9, L=+90 degrees | 0.15 |
| Local SP | P_G=0.1, L=-90 degrees | 0.85 |
| Rate Q | 2^-16 turns/s | signed integer 2^47 |
| Uncertainty | B=2^-20 ED or turns | unsigned integer 4096 |
| Unknown uncertainty | bit 0 clear | `ff ff ff ff` |
| Evaluated, prediction unknown | Quality Flags | `01` |
| Unevaluated, prediction used | Quality Flags | `04` |

A synthetic 160-octet bootstrap request has byte 0 `d3`, byte 1 `10`, byte 2
`06`, bytes 76–91 `01 02 ... 10`, and all other bytes zero. Fixed tokens are
for tests only. Requests do not carry response quality.

Example available but unassessed SP descriptor: state 1, kind 1, flags 0,
stratum 1, reference ID zero, uncertainty `ffffffff`, validity 60, both ages
`ffffffff`. This is not unavailable, even if its phase value is zero.
Example unavailable SP descriptor: 24 zero octets, with phase/rate/model zero.

Before deployment test:

1. All offsets, byte order, signedness, rounding, overflow and exact length 160;
   reject length 128 and malformed/reserved fields.
2. V2-only operation: silently discard V1 requests and never answer them as V2.
   If V1 is optionally supported, test V1 wire regression and existing iOS
   requests, including the truthful V1 unknown-error policy.
3. Wrong endpoint/token/Origin, duplicates, timeout, bounded state and no
   response amplification; all fallback combinations in Section 9.
4. ED year and SP wrap, negative longitude, polar/manual-location cases.
5. The unavailable / available-unknown / available-evaluated matrix independently
   for ED and SP; separate provenance/strata/ages and unknown predictions.
6. Known zero error versus unknown, unknown validity versus expired validity,
   source loss/holdover and conservative multi-hop propagation.
7. Coherent E2/E3/R/SP/Q timestamps, source-transfer delay, atomic cache updates,
   host-clock steps, suspend/resume, oscillator drift and asymmetric paths.
8. Leap-second-safe EOP interpolation, observed/predicted transitions, source
   data refresh failure, and non-IERS direct-source operation.

Independent astronomical vectors MUST document reception epoch, TT/TDB/UT1,
ephemeris and constants, emission epoch, aberration prescription, B/obliquity,
lambda, alpha_app, GAST, ED/R, P_G/Q and local longitude. Cover seasons, wraps,
and different dates. Compare only matching definitions; a service using different
precession or light-deflection models is not automatically a golden reference.
Test tolerances must be justified rather than inferred from packet bit width.

This revision supplies no independently validated astronomical vectors or
numerical accuracy guarantee. Round-trip tests against one library alone are
insufficient for that claim.

## 13. Implementation Status and Open Questions

Existing V1 Python/iOS operation is experimental experience, not verification
of every requirement here. A local experimental V2-only Python server implements
the 160-octet layout, quality descriptors, and provisional basic-model calculation.
Both coordinate uncertainties are unassessed. Historical EOP sanity tests and
UDP loopback tests are not independent astronomical validation. The Python V1
client remains available. A local iOS 0.0.2 V2 client is under test; the distributed
0.0.1 app and running server are not upgraded by this document.

The five design policies in Section 1 are the basis of this revision. The
160-octet field allocation, enumerations, 3600-second interval ceiling, and
fixed-point ranges are concrete proposals for review, not independently
agreed deployment parameters.

Before freezing V2, review:

- the numerical realization and independent vectors for Section 3.2, including
  omitted physical effects, consistent time/rate conventions, and supported epochs;
- differences from existing Model ID 1 calculations and a migration decision:
  never silently redefine a deployed coordinate if differences change its meaning;
- the layout, unknown markers, ranges, and mixed-source stratum conventions;
- how reference systems establish epochs and justified uncertainty;
- detailed metadata discovery/transport, without adding unsolicited URLs;
- authentication, authenticated version negotiation, and registry policy;
- client usability for unassessed values, expiry, optional V1 fallback, and
  the announced beta client-update/cutover plan.

The model boundary is deliberate: improving its evaluation and introducing a
different physical model are separate changes. Future high-precision sources
may improve quality, but source kind or low stratum never guarantees it.

## 14. IANA Considerations

This working revision requests no IANA action. Version 2 and Solar Model ID 1
are experimental proposal values, not IANA registrations. Future work may
request a service port and registries for astronomical models and extensions.

## 15. References

### 15.1. Definition and Model References

- [IAU 2006 Resolution B1](https://iauarchive.eso.org/static/resolutions/IAU2006_Resol1.pdf), recommendations 2 and 4.
- [SOFA Earth Attitude](https://www.iausofa.org/s/sofa_pn_c.pdf), IAU 2006/2000A routines, especially Pnm06a, Nut06a, Obl06, and Gst06a.
- [SOFA Miscellaneous Topics](https://www.iausofa.org/s/sofa_misc_c.pdf), Section 1.1; mean-equinox ecliptic transformations are distinguished from this profile.
- [SOFA Astrometry](https://www.iausofa.org/s/sofa_ast_c.pdf), Sections 4.3–4.4; its gravitational terms are not silently incorporated into the basic model.
- [USNO Astronomical Almanac Glossary](https://aa.usno.navy.mil/faq/asa_glossary), terminology for geometric and apparent positions.

The explicit basic-model equations in Section 3.2 determine NEPP's selected
subset of effects; citing these references does not claim to implement every
physical effect or the entirety of any library.

- BCP 14: [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html),
  [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html).
- [IERS Conventions (2010), Technical Note 36](https://iers-conventions.obspm.fr/conventions/content/tn36.pdf),
  including IAU 2006/2000A celestial models and time/rotation transformations.
- [USNO: The Equation of Time](https://aa.usno.navy.mil/faq/eqtime),
  for the apparent solar time/hour-angle convention.

### 15.2. Informative and Operational References

- [NEPP revision -02](draft-iwata-nepp-02.md), historical comparison only;
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
