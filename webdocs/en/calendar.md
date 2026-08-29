# A real-valued calendar

## Earth Date

NEPP defines Earth Date (ED) as:

```text
ED = Y + λ / 360°
```

- `Y` is the Earth Year.
- `λ` is apparent geocentric solar longitude, where `0° ≤ λ < 360°`.

An Earth Year begins at the March equinox and carries the Gregorian year label
of that equinox. Therefore, `2026.0` denotes the March equinox of 2026, while
`2026.5` denotes half a revolution later in orbital angle.

## Why a continuous value?

Years, months, days, hours, minutes, and seconds are useful for civil life.
They also introduce rollovers, variable month lengths, time zones, and many
rules when the present needs to be handled as a single quantity.

Earth Date is not intended to replace civil calendars. It is another
coordinate: a way to view "now" as one real number referenced to Earth's annual
motion.

## Not uniform in SI seconds

Earth's orbital speed is not constant. Consequently, an Earth Date based on
apparent solar longitude does not advance perfectly uniformly with SI time.
NEPP transmits the instantaneous Earth Date Rate `R = dED/dt`. A client uses
the received value and rate to interpolate between synchronizations.

## A feel for the digits

As rough averages, Earth Date intervals correspond to:

| ED | Approximate duration |
|---:|---:|
| `1` | 1 year |
| `0.01` | 3.65 days |
| `0.001` | 8 h 46 min |
| `0.0001` | 52 min 36 s |
| `0.000001` | 31.6 s |

The exact relationship to SI time varies slightly with orbital speed.
