# NEPP

<p class="lead">One planet. One continuous date.</p>

<div class="language-switch">
  <a href="/" class="md-button md-button--primary" lang="ja">日本語版</a>
</div>

<div class="earth-date" aria-label="NEPP Earth Date example">
  <span>now:</span>
  <strong data-live-earth-date>2026.4320</strong>
</div>

The **Network Earth Position Protocol (NEPP)** is an experimental calendar and
synchronization protocol. It represents Earth's position within its annual
orbit as one continuous real-valued date and exchanges that coordinate over a
network.

Instead of expressing the present with a hierarchy of years, months, days,
hours, minutes, and seconds, an Earth Date is a single number:

```text
2026.4320
```

The integer part is the Earth Year. The fractional part describes the orbital
position within that year. An Earth Year begins at the March equinox and
advances as the apparent solar longitude completes one revolution.

## It is running now

Use NEPP Web to view Earth Date and your local Solar Phase directly in a
browser—no app installation required. Your location remains on your device and
is not sent to the NEPP server.

[Open NEPP Web](https://nepp.kenic.jp/web/){ .md-button .md-button--primary }

The public NEPP server is available at:

```text
nepp.kenic.jp:56377/UDP
```

The Python reference client and the iPhone app can obtain the same Earth Date.
The server, protocol implementation, specification, and iOS client are all
published on [GitHub](https://github.com/kenic/nepp).

## Explore

- [Calendar](calendar.md) — the idea behind Earth Date
- [Protocol](protocol.md) — UDP packets and synchronization
- [iPhone App](app.md) — a NEPP client in your hand

!!! warning "Experimental"
    NEPP Version 1 is experimental. Do not use it as a civil-time source or for
    navigation, financial transactions, or safety-critical synchronization.
