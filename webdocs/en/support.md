# NEPP Support

Thank you for using NEPP. This page provides basic support information for the
iPhone app and the public NEPP server.

## Contact

For bug reports, questions, or feature suggestions, email:

[support@kenic.jp](mailto:support@kenic.jp)

When possible, include:

- The NEPP app Version and Build
- Your iPhone model and iOS version
- Whether you were using Wi-Fi or a mobile network
- The error message shown by the app
- Steps that reproduce the problem

Do not send passwords, authentication codes, or other sensitive information.

## Basic use

When launched, the app connects to the default public server at
`nepp.kenic.jp:56377/UDP` and obtains the current Earth Date. After
synchronization, it advances the display locally using the Earth Date Rate
received from the server.

- Refresh button: synchronize immediately
- Tap the Earth Date: show the conventional date and time
- Gear button: server, port, Version, and website

## If synchronization fails

1. Confirm that Wi-Fi or mobile data is available.
2. Open the gear screen and confirm that the server is `nepp.kenic.jp` and the
   port is `56377`.
3. Some networks restrict UDP traffic. Try switching between Wi-Fi and a mobile
   network.
4. Quit and relaunch the app.

## Service status and source code

NEPP is an experimental protocol. The public server may be maintained or
temporarily unavailable without prior notice. The specification, known
limitations, and source code are published on
[GitHub](https://github.com/kenic/nepp).

Do not use NEPP as a civil-time source or for navigation, financial
transactions, or safety-critical synchronization.

- [Privacy Policy](privacy.md)
- [日本語サポート](../support.md)
