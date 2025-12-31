# Git-First Minimal Steps to Add a New Client Website

## Decide the client identifiers (no commands yet)
You need only:
    Domain: newclient.com
    Repo directory: srv/webapps/clients/newclient.com/frontend
    Whether it uses the platform backend (most do)

## Add the nginx site config (IN REPO)
Create:
```txt
etc/nginx/sites-available/newclient.com.conf
```
Minimal standard config:
```txt
etc/nginx/sites-available/newclient.com.conf
```
Also add the symlink file (IN REPO):
```txt
server {
    listen 80;
    server_name newclient.com www.newclient.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name newclient.com www.newclient.com;

    root /srv/webapps/clients/newclient.com/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Only if this client uses the shared Flask platform
    # location /api/ {
    #     proxy_pass http://127.0.0.1:8000;
    #     include proxy_params;
    # }

    ssl_certificate /etc/letsencrypt/live/newclient.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/newclient.com/privkey.pem;
}
```
This should be a symlink in Git, pointing to:
```txt
../sites-available/newclient.com.conf
```
Commit both.

## DNS: point the domain at your server (outside Git)
Create A records:
```txt
newclient.com        → <Elastic IP>
www.newclient.com    → <Elastic IP>
```
Wait for propagation.

## Deploy using only your standard commands (ON SERVER)
```bash
cd /home/admin/aws-box
git fetch origin
git pull --ff-only

sudo rsync -a --delete /home/admin/aws-box/srv/ /srv/
sudo rsync -a --delete /home/admin/aws-box/etc/ /etc/

sudo nginx -t
sudo systemctl reload nginx
```
If nginx -t fails, stop and fix the repo — do not patch /etc.

## Issue TLS certs (runtime action, not in Git)
```txt
sudo certbot --nginx -d newclient.com -d www.newclient.com
```
Test:
```txt
sudo certbot renew --dry-run
```

## Verify
```txt
curl -I https://newclient.com
```
Browser:
    Confirm correct site
    Confirm no default site leakage
