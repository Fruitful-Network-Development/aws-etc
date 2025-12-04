# awsDev

## Overview
- Multi-tenant Flask platform on Debian EC2 behind Nginx.
- Each client is defined by a single `msn_<userId>.json` manifest and a universal `index.html` that references it via MSN meta tags.
- Nginx serves static frontends from `/srv/webapps/clients/<domain>/frontend` and proxies `/api/` traffic to the shared Flask backend in `/srv/webapps/platform`.

## Architecture
- **Nginx**: virtual host per domain, static asset hosting, reverse proxy for `/api/`.
- **Flask (app.py)**: discovers client manifests, serves the correct frontend entry, and gates backend file access according to each manifest’s whitelist.
- **Modules**: reusable APIs under `platform/modules/`, e.g., the Open-Meteo-backed weather endpoint.

## Repository layout
```text
etc/
  nginx/                 # Nginx config and vhost definitions
srv/webapps/
  platform/
    app.py               # Flask app and manifest-driven routing
    data_access.py       # Manifest loading + backend data path validation
    modules/
      weather.py         # Weather Blueprint (Open-Meteo daily forecast)
  clients/
    cuyahogaterravita.com/
      frontend/          # Universal index + msn_<userId>.json + assets
      data/              # Optional backend_data files referenced by manifest
    fruitfulnetworkdevelopment.com/
      frontend/
      data/
scripts/                 # Deployment helpers (update_code, deploy_srv, deploy_nginx, deploy_all)
```

## MSN standardization
- One manifest per client: `msn_<userId>.json` contains all site configuration and `backend_data` whitelists.
- Universal `index.html` embeds `<meta name="msn-id">` and `<meta name="msn-config">` pointing to that manifest.
- Flask resolves the client by host, reads the manifest for `default_entry` and allowed data files, and serves consistent APIs for every domain.

## Deployment
- Use `scripts/update_code.sh` to pull new commits.
- Use `scripts/deploy_srv.sh` and `scripts/deploy_nginx.sh` (or `deploy_all.sh`) to restart the Flask app and reload Nginx.
