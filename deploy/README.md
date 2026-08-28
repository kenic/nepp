# Deploying the public NEPP server

This targets a small Ubuntu Lightsail instance with public IPv4 and IPv6. The
recommended minimum is 1 GB RAM because installing and importing Astropy can be
memory intensive.

## 1. Network

Attach a Lightsail static IPv4 address. In the Lightsail firewall, add only a
custom `UDP 56377` rule for all IPv4 and IPv6 clients. Restrict SSH/TCP 22 to an
administrative source address where practical.

Create DNS `A` and `AAAA` records such as `nepp.example.org`. Test both address
families before making the hostname the iOS default.

## 2. Install

```sh
sudo apt update
sudo apt install --yes git python3 python3-venv
sudo git clone https://github.com/kenic/nepp.git /opt/nepp
sudo python3 -m venv /opt/nepp/venv
sudo /opt/nepp/venv/bin/pip install --upgrade pip
sudo /opt/nepp/venv/bin/pip install '/opt/nepp[astronomy]'
```

Install and start the hardened systemd unit:

```sh
sudo cp /opt/nepp/deploy/nepp.service /etc/systemd/system/nepp.service
sudo systemctl daemon-reload
sudo systemctl enable --now nepp.service
sudo systemctl status nepp.service
```

The unit uses a dynamic unprivileged account, starts after networking, restarts
after failure, and applies filesystem, kernel, address-family, file-descriptor,
and memory restrictions. To override defaults, copy `nepp.env.example` to
`/etc/nepp/nepp.env`, edit it, and restart the service.

## 3. Verify and operate

From another machine with NEPP installed:

```sh
nepp-client nepp.example.org --port 56377
```

Inspect logs:

```sh
sudo journalctl --unit nepp.service --since today
```

Deploy an update:

```sh
cd /opt/nepp
sudo git pull --ff-only
sudo /opt/nepp/venv/bin/pip install '/opt/nepp[astronomy]'
sudo systemctl restart nepp.service
```

Take a Lightsail snapshot before operating-system upgrades. Use an external UDP
probe over both IPv4 and IPv6; an HTTP-only monitor cannot verify NEPP. Watch
memory, CPU, packet rate, restarts, astronomical refresh errors, and response
validity.

## Security notes

NEPP Version 1 is unauthenticated. The server applies a per-source token bucket
and replies with no more data than it receives, reducing but not eliminating
UDP abuse. Source addresses can be spoofed. Keep responses small, do not add
reflection-amplifying behavior, patch the host, and retain the ability to
firewall abusive traffic. Authentication is future protocol work.
