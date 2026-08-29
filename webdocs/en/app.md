# NEPP for iPhone

NEPP for iOS is a SwiftUI client that connects to the public server while the
app is in the foreground and displays the current Earth Date.

```text
now:
2026.4320123456
```

## How the display works

The app synchronizes with `nepp.kenic.jp:56377/UDP`, then advances the display
locally from the received Earth Date and Earth Date Rate. It does not query the
network for every screen update: it resynchronizes about once per minute and
uses a monotonic device clock between queries.

- Updates `now:` at approximately 0.01-second intervals
- Shows stratum and the latest synchronization time
- Reveals conventional date and time when the value is tapped
- Keeps server and port configuration behind the gear button
- Stops network activity in the background

## Current status

The app has completed an end-to-end exchange from a physical iPhone to the
public NEPP server. UI polish, accessibility, the app icon, TestFlight, and App
Store distribution are the next steps.

Source and build instructions are available in
[`ios/`](https://github.com/kenic/nepp/tree/main/ios).

See [NEPP Support](support.md) for assistance and the
[Privacy Policy](privacy.md) for information-handling details.
