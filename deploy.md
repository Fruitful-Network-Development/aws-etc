# Debian EC2 Rebuild Guide (aws-etc)

> **Scope:** Manual, step-by-step rebuild instructions for a new Debian EC2 instance using the **single** repository `Fruitful-Network-Development/aws-etc`. This guide does **not** use `deploy_platform.sh`.

## 1) Provision the EC2 instance
1. Launch a **Debian** EC2 instance.
2. Open inbound security group ports: **22**, **80**, **443**.
3. Confirm DNS A records point to the new instance IP:
   - fruitfulnetworkdevelopment.com
   - www.fruitfulnetworkdevelopment.com
   - cuyahogaterravita.com
   - www.cuyahogaterravita.com

## 2) Login and install base packages (Debian)
```bash
ssh admin@<public-ip>

sudo apt-get update
sudo apt-get install -y git rsync nginx python3 python3-venv python3-pip certbot python3-certbot-nginx
```
> Note: The legacy docs mention UFW installation in the old script; use it only if you already manage firewalls with UFW on Debian.

## 3) Clone the single repo to GH-etc
```bash
cd /home/admin

git clone git@github.com:Fruitful-Network-Development/aws-etc.git GH-etc
cd /home/admin/GH-etc
```

## 4) Set required environment variables
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"

export FND_SECRET_KEY="paste-generated-key-here"
export FND_CONTACT_EMAIL="your-email@fruitfulnetworkdevelopment.com"
```

## 5) Ensure the skeleton and live paths exist
```bash
sudo mkdir -p /srv/webapps
```
The repository already contains the **skeleton** in:
- `/home/admin/GH-etc/srv/webapps/`

Do **not** add runtime artifacts (e.g., `.git`, `venv`, `__pycache__`) inside GH-etc.

## 6) Sync configuration templates to /etc (updated synch.sh)
> Use the **updated** `scripts/synch.sh` which targets `/etc` and uses `sudo`.
```bash
cd /home/admin/GH-etc

# Example: sync core nginx configuration
./scripts/synch.sh nginx-core

# Example: sync specific site config
./scripts/synch.sh nginx-site fruitfulnetworkdevelopment.com
```

If you update systemd templates, sync them similarly:
```bash
./scripts/synch.sh one etc/systemd/system/platform.service
```

## 7) Sync the app skeleton to /srv/webapps
```bash
cd /home/admin/GH-etc

# Sync everything (platform + clients)
./scripts/synch_srv.sh

# Or target only clients/frontends
# ./scripts/synch_srv.sh clients
```
This sync preserves runtime state in `/srv/webapps` (e.g., venv, .git).

## 8) Configure systemd and nginx
```bash
sudo systemctl daemon-reload
sudo systemctl enable platform.service
sudo systemctl restart platform.service

sudo nginx -t
sudo systemctl reload nginx
```

## 9) Obtain SSL certificates (Certbot)
```bash
sudo certbot --nginx -d fruitfulnetworkdevelopment.com -d www.fruitfulnetworkdevelopment.com \
  -d cuyahogaterravita.com -d www.cuyahogaterravita.com
```

## 10) Validate deployments and caching
```bash
sudo systemctl status platform.service
sudo systemctl status nginx

ls -la /srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/
```
**Caching checks:**
- Hard refresh in browser (Ctrl+Shift+R / Cmd+Shift+R).
- Confirm `Cache-Control` headers are as expected.
- Verify nginx is serving updated files from `/srv/webapps/...`.

## 11) Verify infrastructure invariants (optional but recommended)
```bash
# Verify single etc/ and srv/webapps/ exist (top-level in GH-etc)
find /home/admin/GH-etc -maxdepth 1 -type d -name "etc" -o -name "srv" | wc -l

# Verify no .git except root
find /home/admin/GH-etc -type d -name ".git" | wc -l

# Verify no venv or runtime artifacts
find /home/admin/GH-etc -type d \( -name "venv" -o -name "__pycache__" \) ! -path "*/.git/*"

# Verify nginx configs use system paths
rg "/home/admin" /home/admin/GH-etc/etc/nginx/

# Verify systemd units use system paths
rg "/home/admin" /home/admin/GH-etc/etc/systemd/
```

## 12) Ongoing updates
```bash
cd /home/admin/GH-etc

git pull
./scripts/synch.sh nginx-core
./scripts/synch_srv.sh
```

---

**Reminder:** Only `aws-etc` is used. Do not deploy from any other repositories or scripts such as `deploy_platform.sh`.
