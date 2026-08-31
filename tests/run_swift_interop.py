"""Local-only historical astronomy -> V2 UDP -> Swift integration test.

Run with .venv/bin/python tests/run_swift_interop.py on a Mac with Xcode.
No production server, GPS, or downloaded EOP is used; listener closes on exit.
"""
from dataclasses import replace
import os
from pathlib import Path
import queue
import socket
import subprocess
import threading
from astropy.time import Time
from astropy.utils import iers
from nepp.astronomy import BasicAstronomicalSource
from nepp.source import CachedSource
from nepp.server import serve


def main():
    iers.conf.auto_download = False
    astro = BasicAstronomicalSource(iers_table=iers.IERS_B.open(iers.IERS_B_FILE),
        wall_clock=lambda: Time('2020-06-21T12:00:00', scale='utc').unix)
    class HistoricalSource:
        def acquire(self):
            # Deliberately simulated civil epoch, real monotonic network timing.
            return replace(astro.acquire(), wall_epoch=None)
    cache = CachedSource(HistoricalSource())
    if cache.snapshot()[0] is None:
        raise RuntimeError('historical source failed')
    ready = queue.Queue()
    stop = threading.Event()
    thread = threading.Thread(target=serve, args=('127.0.0.1', 0, cache, stop.is_set),
                              kwargs={'on_bound': ready.put}, daemon=True)
    thread.start()
    silent = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    silent.bind(('127.0.0.1', 0))
    try:
        _, port = ready.get(timeout=5)
        env = dict(os.environ, NEPP_TEST_PORT=str(port),
                   NEPP_SILENT_PORT=str(silent.getsockname()[1]))
        result = subprocess.run(['swift', 'test', '--package-path', 'ios'],
                                cwd=Path(__file__).resolve().parents[1], env=env)
        return result.returncode
    finally:
        stop.set(); thread.join(2); cache.close(); silent.close()


if __name__ == '__main__':
    raise SystemExit(main())
