# NEPP for iOS

The iOS app queries a configurable NEPP Version 1 UDP server while the app is
active. It displays the server's Earth Date as a live `now:` clock and uses the
returned Earth Date Rate to interpolate locally between 60-second polls. The
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
it leaves the foreground. The first implementation uses a bootstrap request
with a zero transmit timestamp, so it displays and interpolates server time but
does not yet discipline a local four-coordinate NEPP clock.

`Package.swift` exposes the packet and network code as `NEPPCore` for standalone
tests. A matching Xcode/Command Line Tools installation is required to run it.
