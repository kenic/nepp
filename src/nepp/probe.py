"""One-shot V2 diagnostic, without network-delay correction or clock discipline."""
import argparse
import json
import socket
import time
from .v2 import V2Packet


def query(host, port=56377, timeout=3.0):
    errors = []
    for family, kind, protocol, _, address in socket.getaddrinfo(
            host, port, socket.AF_UNSPEC, socket.SOCK_DGRAM):
        with socket.socket(family, kind, protocol) as sock:
            try:
                sock.connect(address)
                request = V2Packet.request()
                start = time.monotonic()
                sock.send(request.pack())
                while True:
                    remaining = timeout - (time.monotonic() - start)
                    if remaining <= 0:
                        raise TimeoutError('no matching V2 response')
                    sock.settimeout(remaining)
                    data = sock.recv(65535)
                    try:
                        response = V2Packet.unpack(data)
                    except ValueError:
                        continue
                    if response.token != request.token or response.base.origin != request.base.transmit:
                        continue
                    response.validate_for(request)
                    response.validate_sp()
                    return response
            except OSError as error:
                errors.append(str(error))
    raise OSError('; '.join(errors) or 'no UDP endpoint')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host')
    parser.add_argument('--port', type=int, default=56377)
    args = parser.parse_args()
    r = query(args.host, args.port)
    print(json.dumps({
        'ed_at_server_transmit': str(r.base.transmit.as_decimal()),
        'greenwich_solar_phase_at_server_transmit': r.phase / 2**64 if r.validate_sp() else None,
        'ed_quality': r.ed_quality.__dict__, 'sp_quality': r.sp_quality.__dict__,
        'note': '4294967295 means unknown. NOT corrected for network delay.'
    }, indent=2))


if __name__ == '__main__':
    main()
