# Deploying the public NEPP server

**Migration warning:** this checkout serves draft-03 V2 only. Existing V1 beta
apps and `nepp-client` will time out. Do not apply the restart/update commands to
the current public V1 service until the client upgrade and cutover are planned.
First run an isolated local test with `nepp-server --host 127.0.0.1 --port 56378`
and `python -m nepp.probe 127.0.0.1 --port 56378`. No production deployment is
implied by these source changes. Keep the old release available for rollback.

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
python -m nepp.probe nepp.example.org --port 56377
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

NEPP Version 2 is unauthenticated; its echoed random token is not authentication.
The server applies per-source and aggregate token buckets with bounded source state
and replies with no more data than it receives, reducing but not eliminating
UDP abuse. Source addresses can be spoofed. Keep responses small, do not add
reflection-amplifying behavior, patch the host, and retain the ability to
firewall abusive traffic. Authentication is future protocol work.

## Documentation website

The bilingual MkDocs site is served as static files by Caddy. Install its build
dependencies into the existing virtual environment:

```sh
sudo /opt/nepp/venv/bin/pip install '/opt/nepp[docs]'
sudo apt install --yes rsync
sudo mkdir -p /srv/nepp-site
```

Build and publish after each update with the repository-provided command:

```sh
sudo /opt/nepp/deploy/update-site.sh
```

The command pulls the latest `main` branch with fast-forward-only semantics,
updates the documentation dependencies, performs a strict clean build, and
atomically synchronizes the generated files into `/srv/nepp-site`. It also
installs `rsync` on its first run if necessary. Caddy does not need a reload
when only static site files change.

### Versioned draft archive

The archive lives at `/drafts/` (Japanese) and `/en/drafts/` (English).
`deploy/docs_hooks.py` includes originals from repository-root `draft-iwata-nepp-NN.md`
and `draft-iwata-nepp-NN-jp.md`
at build time, without keeping a second editable copy under `webdocs/`.
Each original is published as:

- `/drafts/draft-iwata-nepp-NN/` — rendered HTML
- `/drafts/source/draft-iwata-nepp-NN.txt` — byte-identical Markdown source

Japanese editions use these paths with `-jp` appended to the draft name.
Rendered pages add language and source links; downloaded originals are unchanged.
The shorter `spec/draft-iwata-nepp-01.md` is kept separate at
`/drafts/implementation-snapshot-v1/`.

Preserve published originals. Add a new numbered source for revisions, and
update both archive indexes and the archive navigation in `mkdocs.yml`.
Clearly identify working drafts versus IETF submissions, and distinguish the
latest draft from the protocol version supported by deployed implementations.
Do not list an unavailable historical revision as a downloadable document.

The Caddy site block is:

```caddyfile
nepp.kenic.jp {
    encode zstd gzip
    root * /srv/nepp-site
    file_server
}
```

Allow inbound TCP ports 80 and 443 for IPv4 and IPv6 in the Lightsail firewall,
validate `/etc/caddy/Caddyfile`, and reload Caddy. Caddy obtains and renews the
HTTPS certificate automatically while DNS points to the instance.
