# Network Earth Position Protocol (NEPP)
## draft-iwata-nepp-00
## Packet Format and Synchronization Model

### 1. Overview

NEPP uses an NTP-like request/response exchange to synchronize a client's Earth Date Clock with one or more reference servers.

A client maintains a local estimate of Earth Date and periodically compares that estimate with an NEPP server.

An NEPP exchange provides four Earth Date coordinates:

    E1  client transmit
    E2  server receive
    E3  server transmit
    E4  client receive

The server transmits E1, E2, and E3.

E4 is recorded locally by the client when the reply is received.

These four coordinates are used to estimate network delay and Earth Date offset.


### 2. NEPP Timestamp Format

An NEPP timestamp represents an Earth Date.

The canonical timestamp SHALL consist of:

    +-------------------------------+
    |       Earth Year (32)         |
    +-------------------------------+
    |                               |
    |     Orbital Fraction (64)     |
    |                               |
    +-------------------------------+

The Earth Year field SHALL be a signed 32-bit integer.

The Orbital Fraction field SHALL be an unsigned 64-bit fixed-point fraction representing:

    lambda / 2*pi

in the interval:

    0 <= F < 1

with:

    ED = Y + F.

The numerical value of the fraction field SHALL be:

    floor(F * 2^64).

This representation provides substantially greater precision than is required for ordinary human calendar display while avoiding dependence on floating-point implementation.


### 3. Earth Date Rate

Because Earth Date does not progress uniformly with SI time, an NEPP server SHALL provide an estimate of the local Earth Date rate.

The rate is:

    R = d(ED)/dt

where t is measured in SI seconds.

The rate SHALL be transmitted as a signed fixed-point quantity expressed in:

    Earth Date units per SI second.

The Earth Date rate does not define the Earth Date.

It is predictive information used to interpolate the astronomically defined coordinate between synchronization events.


### 4. NEPP Packet Header

The basic NEPP packet SHALL contain the following fields:

    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1

    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    | LI | VN  |Mode |    Stratum    |     Poll      | Precision   |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                         Root Delay                            |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                       Root Uncertainty                        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                        Reference ID                           |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |                    Reference Earth Date                       |
    |                         (96 bits)                             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |                     Origin Earth Date                         |
    |                         (96 bits)                             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |                     Receive Earth Date                        |
    |                         (96 bits)                             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |                    Transmit Earth Date                        |
    |                         (96 bits)                             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |                     Earth Date Rate                           |
    |                         (64 bits)                             |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                       Model Identifier                        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Optional extension fields MAY follow the basic header.


### 5. Header Fields

#### 5.1. LI

The two-bit Leap/Status Indicator field SHALL indicate the synchronization state of the server.

Unlike NTP, this field does not indicate a leap second.

Suggested values are:

    0   synchronized
    1   astronomical source degraded
    2   prediction-only state
    3   unsynchronized

NEPP has no leap-day or leap-second indication.


#### 5.2. Version Number

VN identifies the NEPP protocol version.

This document specifies:

    VN = 1.


#### 5.3. Mode

Mode identifies the association type.

Initial values are:

    0   reserved
    1   symmetric active
    2   symmetric passive
    3   client
    4   server
    5   broadcast
    6   reserved
    7   reserved

Implementations of the basic client/server protocol SHOULD use modes 3 and 4.


#### 5.4. Stratum

Stratum identifies the distance from an astronomical reference source.

    0   astronomical reference source
    1   primary NEPP server
    2   secondary NEPP server
    ...
    15  maximum synchronized stratum
    16  unsynchronized

A Stratum 0 source is not normally an NEPP network server.

Examples of Stratum 0 sources include:

    * authoritative solar-system ephemerides;
    * astronomical reference systems;
    * recognized Earth/Sun positional data products.

A Stratum 1 server derives its Earth Date directly from one or more Stratum 0 sources.


#### 5.5. Poll

Poll is a signed integer representing the recommended maximum interval between synchronization messages as a power of two in SI seconds:

    interval = 2^Poll seconds.

The SI second is used only to specify a physical communication interval.


#### 5.6. Precision

Precision is a signed integer expressing the approximate precision of the local Earth Date Clock in powers of two Earth Date units.

The precise encoding SHALL be defined in a subsequent revision.


#### 5.7. Root Delay

Root Delay represents the accumulated network propagation delay to the primary reference source.

The value SHALL be expressed in SI seconds.

This quantity is not part of Earth Date.


#### 5.8. Root Uncertainty

Root Uncertainty represents the accumulated uncertainty of the server's Earth Date relative to its astronomical source.

This field includes, as applicable:

    * network synchronization uncertainty;
    * local oscillator uncertainty;
    * ephemeris uncertainty;
    * astronomical-model uncertainty.


#### 5.9. Reference ID

Reference ID identifies the source from which the server derives its Earth Date.

For a Stratum 1 server, symbolic identifiers MAY include values such as:

    JPLD
    IERS
    SOFA

Actual identifiers and registration rules remain to be specified.

For higher strata, the field SHOULD identify the upstream NEPP server in a manner suitable for detection of synchronization loops.


### 6. Earth Date Fields

#### 6.1. Reference Earth Date

The Reference Earth Date is the Earth Date at which the server's Earth Date Clock was last synchronized or recalculated from its reference source.


#### 6.2. Origin Earth Date

The Origin Earth Date is the client's Earth Date when its request departed.

It corresponds to E1.


#### 6.3. Receive Earth Date

The Receive Earth Date is the server's Earth Date when the request arrived.

It corresponds to E2.


#### 6.4. Transmit Earth Date

The Transmit Earth Date is the server's Earth Date when the reply departed.

It corresponds to E3.


#### 6.5. Destination Earth Date

The Destination Earth Date is the client's Earth Date when the reply arrives.

It corresponds to E4.

E4 SHALL NOT be transmitted as part of the server response.

It is captured locally by the client.


### 7. Synchronization Calculation

For an exchange short enough that the rate of Earth Date can be regarded as locally constant, define:

    E1 = client transmit Earth Date
    E2 = server receive Earth Date
    E3 = server transmit Earth Date
    E4 = client receive Earth Date.

The client estimates Earth Date offset using an NTP-like expression:

    theta_ED =
        ((E2 - E1) + (E3 - E4)) / 2.

A positive theta_ED indicates that the client's Earth Date Clock is behind the server.

The network round-trip interval SHALL first be evaluated as a physical-time quantity where sufficient precision is required.

For short ordinary network exchanges, an implementation MAY use the local Earth Date rate R to convert Earth Date differences to SI-second intervals:

    delta_t ~= delta_ED / R.

An implementation MUST NOT assume that R is a universal constant.


### 8. Non-Uniform Earth Date Rate

Unlike a conventional uniform timescale:

    d(ED)/dt != constant.

The server therefore provides the Earth Date rate R applicable near the transmit event E3.

A client MAY approximate Earth Date after synchronization by:

    ED(t) ~= ED3 + R3 * delta_t

for sufficiently short intervals.

For longer holdover periods, the client SHOULD use either:

    * an astronomical prediction model; or
    * higher-order derivatives provided by NEPP extensions.

A second-order extension MAY provide:

    A = d^2(ED)/dt^2

allowing:

    ED(t) ~= ED0
             + R0 * delta_t
             + 1/2 A0 * delta_t^2.


### 9. Astronomical Model Identifier

The Model Identifier identifies the astronomical realization used by the server.

The identifier SHOULD allow a client to determine at least:

    * ephemeris family and version;
    * IAU precession-nutation model;
    * relevant IERS convention version.

Example conceptual identifiers include:

    DE440/IAU2006/2000A

or equivalent registered compact representations.

Two servers using different astronomical realizations MAY report slightly different Earth Dates.

Such differences MUST be included in their advertised uncertainty where relevant.


### 10. Client Operation

A basic NEPP client SHALL:

    1. maintain a local Earth Date Clock;

    2. transmit its current Earth Date as E1;

    3. receive E1, E2, E3 and the server state;

    4. record E4 immediately upon packet reception;

    5. estimate network delay and Earth Date offset;

    6. reject responses that are stale, inconsistent, replayed, or
       insufficiently trustworthy;

    7. discipline its local Earth Date Clock;

    8. use the received Earth Date rate or a local astronomical model
       between synchronization events; and

    9. periodically repeat synchronization.


### 11. Clock Discipline

Small Earth Date corrections SHOULD be applied gradually to avoid unnecessary discontinuities.

Large errors MAY be corrected by stepping the local Earth Date Clock.

An implementation SHOULD maintain separate representations of:

    * raw local oscillator state;
    * predicted Earth Date;
    * synchronization correction;
    * uncertainty.

The Earth Date displayed to an application SHOULD be monotonic except across an Earth Year boundary, where:

    Y.111111... -> (Y + 1).000000...

is the normal representation transition.


### 12. Multiple Servers

Clients SHOULD query multiple independent NEPP servers where reliability is important.

Source-selection algorithms MAY consider:

    * stratum;
    * root uncertainty;
    * network delay;
    * historical stability;
    * astronomical model;
    * source independence.

A client SHOULD reject a source that differs substantially from a majority of otherwise consistent high-quality sources unless the difference can be explained by uncertainty or model version.


### 13. Relationship to NTP

NEPP deliberately follows the proven architecture of NTP where that architecture is applicable.

Both protocols contain the concepts of:

    * reference source;
    * hierarchical strata;
    * polling;
    * local precision;
    * root delay;
    * root uncertainty or dispersion;
    * reference coordinate;
    * origin coordinate;
    * receive coordinate;
    * transmit coordinate;
    * destination coordinate;
    * clock discipline;
    * holdover; and
    * multiple-source selection.

The fundamental quantity differs.

NTP synchronizes a conventional time coordinate.

NEPP synchronizes Earth Date.

NTP timestamp progression is locally based on a uniform unit of physical time.

NEPP Earth Date progression is astronomically defined and is therefore non-uniform with respect to SI time.

NEPP consequently adds explicit representation of:

    d(ED)/dt

and astronomical model identity.


### 14. Relationship to SI Time

The SI second SHALL NOT define the Earth Date.

No fixed value SHALL be specified for:

    Earth Date units per SI second.

No fixed value SHALL be specified for:

    SI seconds per Earth Year.

SI seconds MAY be used for:

    * network propagation delay;
    * polling intervals;
    * oscillator measurement;
    * interpolation;
    * prediction;
    * holdover;
    * uncertainty characterization.

The distinction is fundamental:

    SI time tells an implementation how much physical duration has
    elapsed.

    Earth Date tells an implementation where the Earth is in its
    annual cycle.


### 15. Extension Fields

NEPP MAY support extension fields following the basic packet header.

Potential extensions include:

    * Earth Date acceleration;
    * complete ephemeris metadata;
    * server certificate information;
    * authenticated astronomical state;
    * prediction horizon;
    * source provenance;
    * additional uncertainty terms.


### 16. Transport

The initial NEPP transport SHOULD use UDP request/response operation.

A separate service port SHOULD be assigned if NEPP advances to a protocol requiring IANA registration.

Alternative transports MAY be specified in future documents.


### 17. Security

NEPP synchronization is vulnerable to classes of attack similar to network time synchronization, including:

    * forged server responses;
    * replay attacks;
    * delay attacks;
    * source impersonation;
    * malicious stratum advertisements;
    * synchronization loops.

Cryptographic authentication SHOULD be supported.

Future revisions SHOULD define an authenticated mechanism suitable for modern deployment rather than relying solely on legacy shared-secret packet authentication.


### 18. Design Summary

The fundamental NEPP synchronization cycle is:

    astronomy
        |
        v
    authoritative Earth Date
        |
        v
    Stratum 1 NEPP server
        |
        v
    NEPP synchronization
        |
        v
    local Earth Date Clock
        |
        v
    2026.xxxxxxxxx

The client uses SI seconds to predict the motion of the coordinate.

The astronomical state defines the coordinate itself.

The network keeps the prediction synchronized with the Earth.

The Earth does not conform to the clock.

The clock conforms to the Earth.