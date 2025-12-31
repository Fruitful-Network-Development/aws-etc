# aws-box

This repository is the **infrastructure sandbox** for the EC2 instance that
hosts the shared Flask platform and multiple client frontends. It mirrors key
parts of `/etc/` and `/srv/webapps/` and provides scripts for auditing and
deploying changes safely.

---

## Environment Overview

This infrastructure runs on a freshly rebuilt EC2 instance (Debian-based).

Key components:

- **Nginx**: virtual hosting, static file serving, and reverse-proxy for backend APIs.
- **Gunicorn**: application server for the Flask platform.
- **Flask**: shared backend platform serving multiple client sites.
- **Certbot / Let’s Encrypt**: automatic TLS certificate provisioning and renewal.

This instance replaces an older degraded EC2 instance and incorporates
additional recovery and access mechanisms not previously present.

---

## Directory Structure & Ownership

Primary sources of truth and where this repo exists are on the server as:

```text
home/admin/srv/webapps/
├── platform/
│   ├── app.py
│   ├── data_access.py
│   ├── venv/                  # Python virtual environment (NOT in git)
│   ├── requirements.txt
│   └── platform.service       # systemd service (installed under /etc/systemd)
├── clients/
├── fruitfulnetworkdevelopment.com/
│   └── frontend/
│       ├── index.html
│       ├── assets/
│       └── msn_<userId>.json
├── cuyahogaterravita.com/
│   └── frontend/
│       └── msn_<userId>.json

home/admin/etc/
├── nginx/
│   ├── nginx.conf
│   ├── mime.types
│   ├──sites-available/
│   │   ├── fruitfulnetworkdevelopment.com.conf
│   │   └── cuyahogaterravita.com.conf
│   └── sites-enabled/
│       └── (symlinks only — default site removed)
└── systemd/system/
    └── platform.service
```

Notes:

- Each client domain has its own frontend directory and manifest JSON.
- The platform backend is shared and domain-agnostic.
- The default Nginx site is removed to prevent accidental serving of stale content.

This repo is then mirrored by the 'live' directories under:
```text
/etc/
/srv/webapps/
```
---

## Python Virtual Environments (venv)

All Python services are run inside explicit virtual environments.

Example setup:

```bash
cd /srv/webapps/platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Important:

- The `venv` directory is intentionally **not** version controlled.
- Each backend service should manage its own `venv`.
- systemd services explicitly reference the `venv` binary paths.

---

## Access Methods

### SSH (Primary)

- Access is performed using a PEM key:

  ```bash
  ssh -i ~/.ssh/aws-main-key.pem admin@<Elastic-IP>
  ```

- The `admin` user’s `~/.ssh/authorized_keys` contains the public key material.

## System Services

### Gunicorn (Flask Platform)

- Managed by systemd via `platform.service`.
- Restart via:

  ```bash
  sudo systemctl restart platform.service
  ```

### Nginx

- Managed by systemd.
- Validate config with:

  ```bash
  sudo nginx -t
  ```

- Reload after config changes:

  ```bash
  sudo systemctl reload nginx
  ```

### Logging & Disk Safety

- `journald` limits enforced:

  ```text
  SystemMaxUse=200M
  RuntimeMaxUse=200M
  ```

- Prevents disk exhaustion from runaway logs.

---

## SSL & DNS

- DNS `A` records for all domains point to the Elastic IP of this instance.
- Certificates are managed by Certbot using the nginx authenticator.
- Renewal can be tested via:

  ```bash
  sudo certbot renew --dry-run
  ```

- Port 80 must remain open for HTTP-01 challenges.

---

## Troubleshooting & Differences from Old Instance

- The original instance suffered SSH banner hangs due to system-level corruption.
- Recovery was not possible without rebuilding.
- This instance was rebuilt cleanly with:
  - Explicit systemd services
  - Enforced logging limits
  - SSM access for recovery
  - Cleaner separation of platform vs client assets

---

## Multi-tenant Platform & Manifests (MSN)

At a high level, the platform follows a **manifest-first** design:

- One manifest per client: `msn_<userId>.json` contains site configuration and
  `backend_data` whitelists.
- Nginx serves static frontends from `/srv/webapps/clients/<domain>/frontend`.
- The shared Flask backend in `/srv/webapps/platform` discovers these manifests
  and serves APIs and data according to each manifest.

For details on how the manifests are used, see:

- `flask-app-main/platform/README.md` (backend behavior)
- Each client’s `README.md` under `flask-app-main/clients/<domain>/`

---

## WorkFlow

### Update the repo on the server
Run on the instance:
```bash
cd /home/admin/aws-box
git fetch origin
git pull --ff-only
```
If `git pull --ff-only` fails, stop (it means local drift). Don’t “fix” it in prod. Reset to origin (see the drift section below).

### Deploy `/srv` payload (static sites + platform code)
Only if your commit includes changes under srv/:
```bash
sudo rsync -a --delete /home/admin/aws-box/srv/ /srv/
sudo chown -R admin:admin /srv/webapps
```
To Check what files would be updated before deploying run:
```bash
sudo rsync -av --delete --dry-run /home/admin/aws-box/srv/ /srv/
```

### Deploy `/etc` payload (nginx, systemd, etc.)
Only if your commit includes changes under `etc/`:
```bash
sudo rsync -a --delete /home/admin/aws-box/etc/ /etc/
```
To Check what files would be updated before deploying run:
```bash
sudo rsync -av --delete --dry-run /home/admin/aws-box/etc/ /etc/
```

### Apply service changes safely
Nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
```

systemd units (only if you changed etc/systemd/system/*.service)
```bash
sudo systemctl daemon-reload
sudo systemctl restart platform.service
sudo systemctl status platform.service --no-pager
```
### Sanity checks
```bash
curl -I https://fruitfulnetworkdevelopment.com | head -10
curl -I https://cuyahogaterravita.com | head -10
sudo certbot renew --dry-run
```
