# Privacy Policy

**Effective date: August 29, 2026**  
**Last updated: August 31, 2026**

This Privacy Policy explains how Kenichi Iwata ("the Developer") handles
information in the NEPP iOS app, the public NEPP server, and the related
website.

## Information the app does not collect

The NEPP app does not collect:

- Names, email addresses, telephone numbers, or other contact information
- Contacts, photos, health information, or financial information
- Advertising identifiers, device identifiers, or purchase history
- Analytics derived from in-app activity

NEPP has no user accounts, advertising, in-app purchases, or third-party
advertising or analytics SDKs.

## Optional on-device location (0.0.2)

The 0.0.2 client can use location with your When In Use permission to calculate
local solar phase. This processing takes place on your device. Coordinates are
not sent to the NEPP server, logged by the app, or saved persistently by the app.
You can decline permission, stop location use in Settings, or enter a manual
reference longitude. ED remains available without location permission.
Location updates stop when the app leaves the foreground. Version 0.0.1 does
not use location. This describes the new client; distribution is a separate step.

## Network communication

To obtain the current Earth Date, the app sends requests to
`nepp.kenic.jp:56377/UDP` by default. If a user configures another server, the
app connects to that server instead.

Because of how Internet communication works, a destination server and network
providers can process technical information such as a source IP address and
communication time. The current public NEPP server operated by the Developer
temporarily uses source IP addresses in memory to limit excessive requests. It
does not use this information to create user profiles, advertise, or track
users, and it does not intentionally write IP addresses to the NEPP application
log or retain them persistently.

A third-party NEPP server selected by a user is governed by that operator's own
privacy practices.

## Website

The experimental Web app at `/web/` obtains ED and Greenwich solar phase over
HTTPS. Optional location processing stays in the browser: coordinates are not
included in API requests or persisted, including manually entered longitude.
Only language and location-mode preferences are stored locally. Requests stop
when the page is hidden, and no analytics or service worker is used. A random
per-request nonce correlates responses; it is not a persistent user identifier.

The related website may process IP addresses and other standard network
information through its hosting infrastructure as necessary to deliver pages.
The Developer currently uses no advertising cookies, behavioral tracking, or
third-party web analytics.

## Sale and sharing of information

The Developer does not sell personal information through NEPP. Personal
information is not disclosed to third parties except when necessary to comply
with law, protect the service, or operate the underlying infrastructure.

## Children's privacy

NEPP is a general-purpose time and calendar display tool. It has no feature
designed to knowingly collect personal information from children.

## Changes to this policy

This policy may be updated when features, operating practices, or applicable
law change. The "Last updated" date on this page will be revised when changes
are made.

## Contact

For questions about this policy or NEPP's information practices, contact:

[support@kenic.jp](mailto:support@kenic.jp)

[日本語版](../privacy.md)
