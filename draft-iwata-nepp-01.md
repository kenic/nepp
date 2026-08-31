# Network Earth Position Protocol (NEPP)
## Real-Valued Calendar Representation and Synchronization Based on the Earth's Annual Orbital Position
### draft-iwata-nepp-01

Internet-Draft  
Intended status: Experimental  
K. Iwata  
Tottori University  
August 2026

---

## Abstract

This document specifies the Network Earth Position Protocol (NEPP), an experimental protocol for representing and synchronizing a continuous terrestrial calendar coordinate called the Earth Date.

Conventional civil calendars construct a year using discrete units historically derived from the rotation of the Earth. However, the rotational and orbital motions of the Earth are physically independent, and one annual revolution is not an integer number of terrestrial rotations. Conventional calendars therefore require corrective mechanisms such as leap days.

NEPP does not construct a year from an integer number of days.

NEPP defines an angular quantity called the NEPP Solar Longitude, lambda, using the apparent geocentric direction of the Sun and internationally standardized astronomical reference systems and models. The Earth Date (ED) is then defined as:

    ED = Y + lambda / 360 degrees

where Y is the Earth Year and lambda is in the interval:

    0 <= lambda < 360 degrees.

NEPP further defines an NTP-like network synchronization mechanism. A client exchanges four Earth Date coordinates with an NEPP server in order to estimate the offset of its local Earth Date Clock and to maintain synchronization with an authoritative Earth Date.

This revision extends draft-iwata-nepp-00 by defining the fixed-point Earth Date representation, the NEPP Version 1 base packet format, four-coordinate synchronization, Earth Date Rate representation, strata, uncertainty fields, and the minimum requirements necessary for reference implementations.

---

# 1. Changes from draft-iwata-nepp-00

draft-iwata-nepp-01 adds or clarifies the following:

1. A 96-bit fixed-point NEPP Timestamp format.
2. The byte layout of the NEPP Version 1 base packet.
3. Network byte order for multi-octet fields.
4. NTP-like Origin, Receive, Transmit, and Destination coordinate exchange.
5. A wire representation for Earth Date Rate.
6. Encoding of Root Delay and Root Dispersion.
7. Definitions of Stratum, Status, Mode, Poll, and Precision.
8. Basic client and server behavior.
9. Synchronization rules accounting for the non-uniform progression of Earth Date.
10. The concept of an NEPP Astronomical Profile.
11. A format for reference-implementation test vectors and interoperability testing.

The fundamental astronomical definition of Earth Date is unchanged from draft-iwata-nepp-00.

---

# 2. Requirements Language

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in the English version of this document are to be interpreted as described in BCP 14, RFC 2119 and RFC 8174, when, and only when, they appear in all capitals.

---

# 3. Earth Date

## 3.1. Fundamental Definition

Earth Date, ED, is defined as:

    ED = Y + lambda / 360 degrees

where:

    Y

is the Earth Year, and:

    0 degrees <= lambda < 360 degrees

is the NEPP Solar Longitude.

---

## 3.2. Seasonal Coordinates

The principal seasonal points correspond approximately to:

    March equinox        Y.000000000...
    June solstice        Y.250000000...
    September equinox    Y.500000000...
    December solstice    Y.750000000...
    next March equinox   (Y+1).000000000...

These are angular coordinates.

They do not represent equal intervals of physical time.

---

## 3.3. Earth Year

Earth Year Y begins when the NEPP Solar Longitude reaches 0 degrees and ends when lambda completes one full revolution and next reaches 0 degrees.

For initial deployment, Y SHALL use the same integer as the Gregorian calendar year containing the March equinox that begins the corresponding Earth Year.

The Gregorian calendar is used only to provide an integer label for the Earth Year.

It does not define the fractional component of Earth Date.

---

# 4. NEPP Solar Longitude

## 4.1. Astronomical Basis

NEPP Solar Longitude SHALL be determined using:

    * the apparent geocentric direction of the Sun;
    * the IAU definition of the ecliptic;
    * the IAU 2006 precession model;
    * the IAU 2000A nutation model; and
    * astronomical calculations consistent with the IERS Conventions.

---

## 4.2. Solar Direction

The solar direction SHALL be the apparent direction of the Sun as observed from the center of the Earth.

A simple geometric Earth-Sun vector from an uncorrected two-body model MUST NOT be used as the normative definition of Earth Date.

Light-time, aberration, and other corrections required by the adopted astronomical standards SHALL be applied.

---

## 4.3. Longitude

The apparent geocentric direction of the Sun SHALL be projected onto the applicable ecliptic plane.

NEPP Solar Longitude lambda is the oriented angle from the March-equinox direction, increasing in the direction of apparent annual solar motion.

lambda SHALL be normalized to:

    0 degrees <= lambda < 360 degrees.

---

## 4.4. No Circular-Orbit or Ideal-Ellipse Assumption

NEPP MUST NOT assume uniform circular motion of the Earth around the Sun.

NEPP also MUST NOT use an ideal two-body Keplerian ellipse as the normative definition of Earth Date.

Earth Date follows the astronomical state produced by the selected high-precision ephemeris and astronomical reference models.

---

# 5. Relationship to SI Time

## 5.1. The SI Second Does Not Define Earth Date

The SI second is not a defining component of Earth Date.

NEPP SHALL NOT define a fixed relationship of the form:

    1 Earth Year = N SI seconds.

NEPP SHALL NOT define a universal constant K such that:

    ED(t + 1 s) = ED(t) + K.

---

## 5.2. Uses of the SI Second

The SI second MAY be used for:

    * communication delay;
    * poll intervals;
    * local oscillator measurement;
    * Earth Date interpolation;
    * Earth Date prediction;
    * holdover; and
    * synchronization-error estimation.

---

## 5.3. Earth Date Rate

The Earth Date Rate R is defined as:

    R = dED/dt

where t is measured in SI seconds.

The unit of R is therefore:

    ED per SI second.

R is not part of the definition of Earth Date.

It is state information used by an Earth Date Clock to interpolate between synchronization events.

---

# 6. NEPP Timestamp

## 6.1. Format

An NEPP Version 1 Earth Date Timestamp SHALL be 96 bits long.

    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                       Earth Year                              |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    +                    Orbital Fraction                           +
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Earth Year SHALL be a signed 32-bit integer.

Orbital Fraction SHALL be an unsigned 64-bit integer.

---

## 6.2. Orbital Fraction

Let F be the fractional part of Earth Date:

    F = ED - Y

with:

    0 <= F < 1.

The 64-bit wire value U SHALL be:

    U = floor(F * 2^64).

The receiver reconstructs the fraction as:

    F = U / 2^64.

---

## 6.3. Byte Order

All multi-octet integer values in NEPP Version 1 MUST be transmitted in network byte order, that is, big endian.

---

## 6.4. Earth Year Boundary

A transition such as:

    2026.999999...
        ->
    2027.000000...

is a normal progression of Earth Date.

Implementations computing Earth Date differences MUST NOT subtract the Earth Year and Orbital Fraction fields independently.

They MUST interpret the timestamp as the logical real-valued quantity:

    Y + U / 2^64.

---

# 7. Earth Date Rate Wire Representation

Earth Date Rate SHALL be transmitted as a signed 64-bit two's-complement integer.

Let SR be the transmitted integer.

The represented rate is:

    R = SR * 2^-63 ED/s.

Conversely:

    SR = round(R * 2^63).

Under normal terrestrial orbital motion, R is positive.

A signed representation is retained for arithmetic convenience and possible future extensions.

---

# 8. NEPP Version 1 Base Packet

The NEPP Version 1 base packet SHALL be 76 octets long.

All offsets are counted from the beginning of the packet.

    Offset   Length   Field
    ------   ------   -------------------------
       0       1      Flags
       1       1      Stratum
       2       1      Poll
       3       1      Precision

       4       4      Root Delay
       8       4      Root Dispersion
      12       4      Reference ID

      16      12      Reference Earth Date
      28      12      Origin Earth Date
      40      12      Receive Earth Date
      52      12      Transmit Earth Date

      64       8      Earth Date Rate
      72       4      Model ID

    Total: 76 octets

Extension Fields MAY follow octet 76.

---

# 9. Flags

The Flags octet SHALL be encoded as follows:

    +---+---+---+---+---+---+---+---+
    | S | S | V | V | V | M | M | M |
    +---+---+---+---+---+---+---+---+

where:

    S = Status Indicator   2 bits
    V = Version Number     3 bits
    M = Mode               3 bits

---

# 10. Status Indicator

The Status Indicator values are:

    0    synchronized
    1    degraded astronomical source
    2    prediction-only / holdover
    3    unsynchronized

This field occupies the same bit position as the NTP Leap Indicator but has different semantics.

NEPP does not use this field to indicate leap seconds.

NEPP Earth Date has neither leap days nor leap seconds.

---

# 11. Version Number

This document specifies:

    VN = 1.

---

# 12. Mode

The Mode field is defined as:

    0    reserved
    1    symmetric active
    2    symmetric passive
    3    client
    4    server
    5    broadcast
    6    reserved
    7    reserved

A basic NEPP Version 1 reference implementation MUST support Modes 3 and 4.

---

# 13. Stratum

Stratum identifies the logical distance from an astronomical reference source.

    0       reference astronomical source
    1       primary NEPP server
    2-15    secondary NEPP server
    16      unsynchronized
    17-255  reserved

A Stratum 0 source is not normally an NEPP network server.

Examples include:

    * high-precision solar-system ephemerides;
    * recognized astronomical data products; and
    * authoritative astronomical calculation systems.

A Stratum 1 server derives Earth Date directly from one or more Stratum 0 sources.

---

# 14. Poll

Poll SHALL be represented as a signed 8-bit integer.

The recommended synchronization interval is:

    2^Poll SI seconds.

For example:

    Poll = 6

represents an interval of approximately 64 seconds.

The SI second in this field specifies a network operation interval only.

It does not define Earth Date.

---

# 15. Precision

Precision SHALL be represented as a signed 8-bit integer P.

The nominal resolution of the server's Earth Date Clock is:

    2^P ED.

P will normally be negative.

---

# 16. Root Delay

Root Delay SHALL use a 32-bit unsigned 16.16 fixed-point representation.

Its unit is the SI second.

Root Delay represents the estimated accumulated round-trip communication delay between the server and its primary reference source.

---

# 17. Root Dispersion

Root Dispersion SHALL use a 32-bit unsigned 16.16 fixed-point representation.

Its unit is the SI second.

Root Dispersion represents an upper estimate of accumulated synchronization uncertainty relative to the reference source.

If uncertainty in the astronomical model itself is non-negligible, its effect MUST be reflected either in Root Dispersion or in a suitable Extension Field.

---

# 18. Reference ID

Reference ID SHALL be a 32-bit field.

At Stratum 1 it identifies the astronomical reference source or profile used by the server.

At higher strata it MAY be used to identify an upstream NEPP server and to assist in detection of synchronization loops.

NEPP Version 1 does not request a global IANA registry for Reference IDs.

---

# 19. Model ID

Model ID SHALL be a 32-bit field.

Model ID identifies the astronomical realization profile used to derive Earth Date.

This document defines:

    NEPP Astronomical Profile 1.

Profile 1 uses:

    * a high-precision solar-system ephemeris;
    * IAU 2006 precession;
    * IAU 2000A nutation; and
    * an apparent geocentric solar direction consistent with the
      IERS Conventions.

The exact reference procedure and test-vector format for Profile 1 are specified in Appendices A and B.

Implementations using different ephemerides MAY be treated as Profile 1 compatible if differences remain below the advertised uncertainty.

---

# 20. Four-Coordinate Synchronization

## 20.1. Events

A basic NEPP request/response exchange uses four Earth Date coordinates:

    E1    Client Transmit Earth Date
    E2    Server Receive Earth Date
    E3    Server Transmit Earth Date
    E4    Client Destination Earth Date

---

## 20.2. Client Request

In a client request:

    Origin Earth Date       = 0
    Receive Earth Date      = 0
    Reference Earth Date    = implementation-defined or 0
    Transmit Earth Date     = E1

---

## 20.3. Server Response

When the request is received, the server records E2.

The response SHALL contain:

    Origin Earth Date       = request Transmit Earth Date
    Receive Earth Date      = E2
    Transmit Earth Date     = E3

E3 SHOULD be captured as close as practical to the actual packet transmission event.

---

## 20.4. Client Destination Coordinate

When the client receives the response, it records E4.

E4 is not transmitted on the wire.

---

# 21. Earth Date Clock Offset

When the synchronization exchange is sufficiently short that Earth Date Rate can be treated as locally constant, the client MAY estimate Earth Date Clock offset as:

    theta_ED =
       ((E2 - E1) + (E3 - E4)) / 2.

If:

    theta_ED > 0

the client Earth Date Clock is behind the server.

If:

    theta_ED < 0

the client Earth Date Clock is ahead of the server.

---

# 22. Non-Uniform Progression

Earth Date satisfies:

    dED/dt != constant.

The equation in Section 21 is therefore formally a local approximation.

For ordinary network synchronization intervals, the variation in Earth Date Rate is expected to be sufficiently small that this approximation is valid at practical synchronization precision.

An implementation whose required precision cannot tolerate the local-linear approximation MUST use Earth Date Rate, and where necessary higher-order terms, to map coordinate differences onto a common physical-time basis before estimating delay and offset.

---

# 23. Holdover

An NEPP Client MUST NOT require continuous connectivity to an NEPP Server.

Let the latest synchronized state be:

    ED0
    R0.

After an elapsed SI-time interval delta_t, a short-term estimate MAY be:

    ED ~= ED0 + R0 * delta_t.

For longer intervals, a client SHOULD use:

    ED ~= ED0
          + R0 * delta_t
          + 1/2 A0 * delta_t^2
          + ...

or a local astronomical prediction model.

---

# 24. Clock Discipline

A client SHOULD discipline its Earth Date Clock using repeated synchronization exchanges.

Small offsets SHOULD normally be corrected smoothly.

Large offsets MAY be corrected by stepping the Earth Date Clock.

Under normal operation, an Earth Date display SHOULD NOT move backward.

---

# 25. Multiple Servers

Applications requiring higher reliability SHOULD use multiple independent NEPP Servers.

Source selection MAY consider:

    * Stratum;
    * Root Delay;
    * Root Dispersion;
    * network delay;
    * historical stability;
    * Model ID; and
    * independence of astronomical reference sources.

A source that significantly disagrees with otherwise consistent high-quality sources SHOULD be excluded unless the discrepancy is explained by uncertainty or model differences.

---

# 26. UDP Transport

The basic NEPP Version 1 transport SHALL use UDP request/response operation.

Until an official service port is assigned by IANA, experimental implementations MUST use a configurable port in the dynamic/private port range.

An implementation MUST NOT treat any temporary experimental port number as part of the protocol specification.

---

# 27. Security Considerations

NEPP is subject to attacks similar to those affecting network time synchronization, including:

    * forged responses;
    * server impersonation;
    * replay attacks;
    * delay attacks;
    * false stratum advertisements;
    * synchronization loops; and
    * denial of service.

A Version 1 reference implementation MUST at minimum validate request-response association using the Origin Earth Date.

Applications requiring high integrity SHOULD use an authenticated transport or an NEPP authentication extension.

---

# 28. Error Handling

A client MUST NOT use a response for synchronization if any of the following applies:

    * the Version is unsupported;
    * the Mode is invalid;
    * Status indicates unsynchronized;
    * Origin Earth Date does not match the transmitted E1;
    * timestamp encoding is invalid;
    * Root Dispersion exceeds the implementation's acceptance limit;
    * the packet is shorter than 76 octets; or
    * a reserved value is used in a manner prohibited by this
      specification.

Unknown Extension Fields MAY be ignored unless the extension is explicitly defined as critical.

---

# 29. Reference Implementation Requirements

A basic NEPP Version 1 reference server MUST implement at least:

    * Profile 1 Earth Date calculation;
    * UDP server mode;
    * E2 and E3 capture;
    * Earth Date Rate;
    * Stratum;
    * Root Delay; and
    * Root Dispersion.

A basic NEPP Version 1 reference client MUST implement at least:

    * UDP client mode;
    * E1 and E4 capture;
    * Origin validation;
    * offset estimation;
    * Earth Date Clock discipline; and
    * holdover.

---

# 30. Appendix A: NEPP Astronomical Profile 1

NEPP Astronomical Profile 1 is the reference astronomical realization for NEPP Version 1.

A Profile 1 implementation SHALL:

1. Obtain the state of the Earth and Sun for a specified astronomical epoch from a high-precision solar-system ephemeris.

2. Determine the direction of the Sun as observed from the center of the Earth.

3. Apply the required light-propagation and aberration corrections to obtain the apparent geocentric solar direction.

4. Apply the IAU 2006 precession model and IAU 2000A nutation model.

5. Construct the applicable ecliptic and equatorial reference geometry in a manner consistent with the IERS Conventions.

6. Determine the NEPP Solar Longitude lambda, using the March-equinox direction as 0 degrees.

7. Compute:

       ED = Y + lambda / 360 degrees.

Algorithms consistent with the IAU Standards of Fundamental Astronomy (SOFA) SHOULD be used as a reference realization.

The normative definition of NEPP does not depend on a particular programming language or on specific SOFA function names.

---

# 31. Appendix B: Test Vectors

The NEPP specification SHALL provide test vectors for interoperability verification.

Each test vector SHOULD contain at least:

    * astronomical input epoch;
    * Model ID;
    * expected NEPP Solar Longitude lambda;
    * expected Earth Year Y;
    * expected 64-bit Orbital Fraction;
    * expected 96-bit Earth Date Timestamp; and
    * expected Earth Date Rate.

Example format:

    Vector ID: TV-01

    Astronomical Profile:
        NEPP Profile 1

    Input epoch:
        [reference astronomical epoch]

    Solar longitude:
        [generated by reference implementation]

    Earth Date:
        [generated value]

    Earth Year bytes:
        xx xx xx xx

    Orbital Fraction bytes:
        xx xx xx xx xx xx xx xx

Actual numerical vectors SHALL be generated from the first reference implementation and independently checked before being treated as normative interoperability tests.

Placeholder values MUST NOT be used as normative test vectors.

---

# 32. IANA Considerations

This revision requests no IANA actions.

A future revision may request registration of:

    * an NEPP UDP service port;
    * a Model ID registry;
    * an Extension Type registry; and
    * Reference Source identifiers.

---

# 33. Implementation Status

At the time of writing, no interoperable NEPP Version 1 implementation has been verified.

The initial reference implementation is expected to consist of:

    nepp-server
    nepp-client

After completion of the reference implementation, the test vectors in Appendix B will be generated and this section will be updated.

---

# 34. Design Principles

NEPP is based on the following principles:

1. A year is not an integer number of days.

2. Earth Date follows the actual annual astronomical state of the Earth.

3. Earth Date is not defined by accumulation of SI seconds.

4. SI seconds may be used to measure, predict, interpolate, and synchronize Earth Date.

5. Earth Date need not progress uniformly with SI time.

6. Earth rotation and Earth revolution are separate coordinates.

7. NEPP provides not only Earth Date calculation but also network synchronization.

8. Synchronization concepts proven by NTP are reused where they remain applicable to the properties of Earth Date.

9. The Earth is not approximated to fit the calendar; the calendar follows the Earth.

In short:

    The Earth does not conform to the calendar.

    The calendar conforms to the Earth.

---

# 35. References

## 35.1. Normative References

RFC 2119  
Key words for use in RFCs to Indicate Requirement Levels.

RFC 8174  
Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words.

IAU 2006 Resolution B1  
Adoption of the P03 Precession Theory and Definition of the Ecliptic.

IAU 2000A  
IAU 2000A Nutation Model.

IERS Conventions (2010)  
IERS Technical Note 36.

## 35.2. Informative References

RFC 5905  
Network Time Protocol Version 4: Protocol and Algorithms Specification.

IAU SOFA  
Standards of Fundamental Astronomy.

---

# Author

Kenichi Iwata  
Tottori University  
Japan
