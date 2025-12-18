# aws-etc

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

Primary directories of interest on the server:

```text
/srv/webapps/
├── platform/
│   ├── app.py
│   ├── data_access.py
│   ├── venv/                  # Python virtual environment (NOT in git)
│   ├── requirements.txt
│   └── platform.service       # systemd service (installed under /etc/systemd)
/srv/webapps/clients/
├── fruitfulnetworkdevelopment.com/
│   └── frontend/
│       ├── index.html
│       ├── assets/
│       └── msn_<userId>.json
├── cuyahogaterravita.com/
│   └── frontend/
│       └── msn_<userId>.json

/etc/nginx/
├── sites-available/
│   ├── fruitfulnetworkdevelopment.com.conf
│   └── cuyahogaterravita.com.conf
├── sites-enabled/
│   └── (symlinks only — default site removed)
```

Notes:

- Each client domain has its own frontend directory and manifest JSON.
- The platform backend is shared and domain-agnostic.
- The default Nginx site is removed to prevent accidental serving of stale content.

This repo mirrors those directories under:

```text
etc/            # Nginx + systemd templates
srv/webapps/    # Layout reference only (no live venvs or git clones)
scripts/        # Deployment and audit helpers
docs/           # Audit outputs and operational notes
```

Agents should treat this repo as the **source of truth for configuration** and
use scripts to sync into the live system, rather than editing `/etc` directly.

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

### AWS Systems Manager (Secondary / Recovery)

- The instance runs `amazon-ssm-agent`.
- The IAM role `AmazonSSMManagedInstanceCore` is attached.
- Session Manager provides browser-based shell access if SSH fails.

This access path did not exist on the original instance and is a deliberate
resilience improvement.

---

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

## Scripts & Operational Workflow

- Audit scripts mirror their output into `docs/` with timestamped log files so
  agents can review findings without touching the deployed `/etc` tree.
- Deployment scripts (e.g., `scripts/*.sh`) provide granular functions for
  syncing Nginx or systemd content from this sandbox into the live `/etc`
  directory and for pulling updated app/client code into `/srv/webapps`.

Current key scripts:

- `scripts/pull_etc.sh` — updates the local `GH-etc` clone from the
  `Fruitful-Network-Development/aws-etc` GitHub repository (branch `main`).
- `scripts/pull_app.sh` — updates the deployed Flask application clone under
  `/home/admin/srv/webapps` from the `Fruitful-Network-Development/flask-app`
  GitHub repository.
- `scripts/synch.sh` — syncs individual configuration files from this repo into
  `/home/admin/etc`, one file at a time (with helpers for common nginx files).
- `scripts/audit.sh` — consolidated audit entrypoint providing subcommands for
  nginx syntax, nginx configuration, file permissions, and systemd services.

Agents should:

- Propose and test changes in this repo.
- Use the scripts to sync configuration to the server.
- Avoid manual, ad-hoc edits in `/etc` and `/srv/webapps` whenever possible.
