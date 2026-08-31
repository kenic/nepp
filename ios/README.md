# NEPP for iOS

The local 0.0.2 (build 2) app queries a draft-03 **Version 2-only** UDP server
while active. It displays Earth Date and solar phase, using their independent
rates and one shared monotonic receipt anchor between 60-second polls. The
default public server is `nepp.kenic.jp:56377`; connection settings are available
from the gear button. The settings screen also shows the app version and build.
It links to the English project website at `https://nepp.kenic.jp/en/`, which
offers an immediate switch to the Japanese edition.
Public releases use a simple sequential version (`0.0.1`, `0.0.2`, ...).
The AppIcon artwork combines Earth with a continuous orbit, representing the
real-valued Earth Date. Its 1024-pixel, alpha-free master is stored in the asset
catalog and Xcode generates the required device sizes.

## Open and run

1. Open `NEPP.xcodeproj` in Xcode.
2. Select the NEPP target and choose your Apple Development team under Signing.
3. Run on an iPhone or iOS Simulator.
4. Enter the server host and private UDP port used by `nepp-server`.

For an iPhone to reach a server running on your Mac, use the Mac's LAN address,
not `127.0.0.1`, and allow the local-network prompt. The app stops polling when
it leaves the foreground, cancels outstanding requests and discards old anchors.
The client uses a fresh random token and a zero-ED bootstrap request, with the
Section 8.2 half-path-delay estimate. It rejects negative or over-three-second
exchange timing, rather than claiming precision from unknown server errors.
It does not discipline a local four-coordinate NEPP clock. Display refresh is
30 Hz, not a claim of hundredth-second accuracy.

The public server is still V1 until separately deployed. There is **no V1
fallback**. Test first against a local V2 server; no TestFlight upload is implied.

## Solar phase and quality

Settings offers current location (When In Use, permission required), manual longitude
(east positive, −180…180°), or an explicitly labelled Greenwich reference.
Current location is selected on a fresh install and iOS asks permission on first
foreground use, with a localized explanation. An explicitly saved Off remains Off
across launches and upgrades; coordinates are not persisted. Denial leaves ED
usable and allows selection of a manual longitude or Greenwich reference.

The interface, detailed status/errors, accessibility labels and permission prompts
support English and Japanese, following the iPhone/app language preference.
`Resources/en.lproj` and `Resources/ja.lproj` contain matching translation tables.
Only longitude affects the local phase; location is never included in requests.
Location denial/failure does not disable ED. While active, one-shot location
requests run every 60 seconds even when stationary. A previously accepted fix
is retained in memory after transient failure or five-minute aging, clearly
labelled Last known location. Its original timestamp is never refreshed by reuse.
An unavailable current-location selection never silently switches to Greenwich.
The Stop button or permission revocation clears the fix. Background callbacks
and near-pole automatic longitude are not used. Updates stop in background;
foregrounding requests a fresh fix while retaining the last known place.

ED and SP quality are independent. Invalid/unavailable SP does not hide valid
ED. Advertised expiry is measured from estimated transmit age, including transit;
expired samples are labelled local prediction. Unknown validity is explicit.
All samples are discarded after a five-minute local limit or leaving foreground.
Failed network polls retry after 2, 4, 8, 16, 30, then 60 seconds; success restores
the normal 60-second interval. Manual refresh preserves the last sample and
location. Connection state does not replace or extend coordinate validity.
The main display shows only values, place and short status. Tap either value or
Details for source stratum, uncertainty, validity, ages and network errors.
Total display accuracy remains unassessed even when a server provides a bound:
network asymmetry, oscillator and location uncertainty are not established.

## Test

```sh
swift test --package-path ios
.venv/bin/python tests/run_swift_interop.py
```

Run these from the repository root. The second test starts a temporary localhost
Python V2 server with historical astronomical/EOP inputs, runs the Swift suite
including real UDP, and stops the server. It never contacts production.
Before TestFlight, check actual iPhone location permission/denial, manual negative
longitude, background/resume, server changes, loss of connectivity, and small-screen
layout. Simulator compilation alone does not verify those device interactions.

`Package.swift` exposes the packet and network code as `NEPPCore` for standalone
tests. A matching Xcode/Command Line Tools installation is required to run it.
