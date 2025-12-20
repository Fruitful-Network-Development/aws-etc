# Debian EC2 Rebuild Guide (aws-box)

> **Scope:** Manual, step-by-step rebuild instructions for a new Debian EC2 instance using the **single** repository `Fruitful-Network-Development/aws-box`.

### 0) Provision the EC2 instance
1. Launch a **Debian** EC2 instance.
2. Open inbound security group ports: **22**, **80**, **443**.
3. Confirm DNS A records point to the new instance IP:
   - fruitfulnetworkdevelopment.com
   - www.fruitfulnetworkdevelopment.com
   - cuyahogaterravita.com
   - www.cuyahogaterravita.com

### 1) One-time base packages and permissions (Debian)
```bash
ssh admin@<public-ip>

sudo apt-get update
sudo apt-get install -y git rsync nginx python3 python3-venv python3-pip certbot python3-certbot-nginx
```
Enable nginx:
```bash
sudo systemctl enable --now nginx
```
Create live app directories:
```
sudo mkdir -p /srv/webapps/platform /srv/webapps/clients
sudo chown -R admin:admin /srv/webapps
```

### 2) Set up GitHub access from the server

#### 2.A) Generate an SSH key on the server
```bash
ssh-keygen -t ed25519 -C "admin@$(hostname)-aws-box"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```
The program will prompted  for a "file in which to save the key."
      Pressed Enter (leaving it blank), defaulting it to: /home/admin/.ssh/id_ed25519
Copy the printed public key into GitHub:
      GitHub → Settings → SSH and GPG keys → New SSH key

Test auth
```bash
ssh -T git@github.com
```

#### 2.B) Clone your aws-box repo to become the only source-of-truth
```bash
cd /home/admin
git clone git@github.com:Fruitful-Network-Development/aws-box.git
cd /home/admin/aws-box
git status
```

### 3) Install the repo’s system configs into live `/etc` safely

#### 3.A) Deploy nginx from repo → live
```bash
sudo rsync -a --delete /home/admin/aws-box/etc/nginx/ /etc/nginx/
```
Remove the default site (prevents wrong site being served):
```bash
sudo rm -f /etc/nginx/sites-enabled/default
```
Validate and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### 3.B) Deploy systemd units from repo → live
```bash
sudo rsync -a /home/admin/aws-box/etc/systemd/system/ /etc/systemd/system/
sudo systemctl daemon-reload
```
Do not start services yet unless platform code exists.


### 4) Set required environment variables
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"

export FND_SECRET_KEY="paste-generated-key-here"
export FND_CONTACT_EMAIL="your-email@fruitfulnetworkdevelopment.com"
```

### 5) Ensure the skeleton and live paths exist
```bash
sudo mkdir -p /srv/webapps
```
The repository already contains the **skeleton** in:
- `/home/admin/aws-box/srv/webapps/`

Do **not** add runtime artifacts (e.g., `.git`, `venv`, `__pycache__`) inside aws-box.

### 6) Deploy configuration to /etc
> Use the deployment scripts which target `/etc` and use `sudo`.
```bash
cd /home/admin/aws-box

# Deploy nginx configuration
./scripts/deploy_nginx.sh

# Deploy systemd unit files
./scripts/deploy_systemd.sh
```

### 7) Sync the app skeleton to /srv/webapps
```bash
cd /home/admin/aws-box

# Sync everything (platform + clients)
./scripts/synch_srv.sh

# Or target only clients/frontends
# ./scripts/synch_srv.sh clients
```
This sync preserves runtime state in `/srv/webapps` (e.g., venv, .git).

### 8) Configure systemd and nginx
```bash
sudo systemctl daemon-reload
sudo systemctl enable platform.service
sudo systemctl restart platform.service

sudo nginx -t
sudo systemctl reload nginx
```

### 9) Obtain SSL certificates (Certbot)
```bash
sudo certbot --nginx -d fruitfulnetworkdevelopment.com -d www.fruitfulnetworkdevelopment.com \
  -d cuyahogaterravita.com -d www.cuyahogaterravita.com
```

## Ongoing updates
### 1.) Set Required Environment Variables

### Generate a strong secret:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Export environment variables:

```bash
export FND_SECRET_KEY="paste-generated-key-here"
export FND_CONTACT_EMAIL="your-email@fruitfulnetworkdevelopment.com"
```

Run the deployment script using:

```bash
sudo -E bash deploy_platform.sh
```

(`-E` preserves your exported environment variables.)

---

### 2.) Deployment Script Behavior

The script:

1. Installs Python, Git, Nginx, Certbot, UFW  
2. Creates:
   - `/srv/webapps/platform`
   - `/srv/webapps/clients/<domain>/frontend`
   - `/home/admin/aws-box`
3. Clones or updates the aws-box repository
4. Deploys system configuration from `aws-box`
5. Sets up Python virtualenv + installs dependencies
6. Creates systemd service `platform.service`
7. Tests + reloads Nginx
8. Obtains HTTPS certificates via Certbot
9. Prints deployment summary

Afterward, visit:

```
https://fruitfulnetworkdevelopment.com
https://cuyahogaterravita.com
```

---

### 3.) Updating an Existing Server

To apply changes made in GitHub:

```bash
cd /home/admin/aws-box
git pull
./scripts/deploy_nginx.sh
./scripts/deploy_systemd.sh
./scripts/synch_srv.sh
```

This keeps the server synchronized with the configuration repo.

---
