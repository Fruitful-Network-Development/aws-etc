# srv/webapps Deployment Script Documentation

## Overview

The `synch_srv.sh` script syncs the skeleton structure from `GH-etc/srv/webapps/` to the live system `/srv/webapps/` directory. This script safely updates source code while preserving runtime state.

## Purpose

**Problem:** After normalizing the GH-etc repository structure, we have:
- A skeleton under `GH-etc/srv/webapps/` with source files (no venv, .git, runtime state)
- Live runtime at `/srv/webapps/` with deployed code (has venv, potentially has .git, has runtime state)
- No automated way to deploy updates from the skeleton to the live system

**Solution:** `synch_srv.sh` provides safe, controlled deployment that:
- Syncs source code from skeleton to live system
- Preserves runtime artifacts (venv, .git, __pycache__)
- Restarts services to serve updated code

## Script Features

### Safe Exclusions

The script uses `rsync` with exclusions to preserve runtime state:

- `.git` - Preserves any git repositories in the live system
- `venv/` - Preserves Python virtual environments (runtime dependency)
- `__pycache__/` - Preserves Python bytecode cache
- `*.pyc`, `*.pyo`, `*.pyd` - Preserves compiled Python files
- `.DS_Store` - Excludes macOS metadata
- `*.log` - Excludes log files

**Rationale:** These exclusions ensure that:
1. Runtime dependencies (venv) are not overwritten
2. Git repositories in live system remain intact
3. Compiled artifacts are regenerated as needed
4. The skeleton remains a clean reference without runtime state

### Service Management

After syncing, the script optionally restarts services:
- `platform.service` - Restarts the Flask/Gunicorn backend
- `nginx` - Reloads configuration (graceful, no downtime)

**Rationale:** Code changes require service restarts to be served:
- Backend code changes need Gunicorn restart to load new Python modules
- Frontend changes are served by nginx (reload is sufficient for static files)
- Service restart is optional via `--no-restart` flag for manual control

## Usage

### Basic Usage

```bash
# Sync everything and restart services (default)
./scripts/synch_srv.sh

# Sync without restarting services
./scripts/synch_srv.sh --no-restart

# Sync only platform code
./scripts/synch_srv.sh platform

# Sync only client frontends
./scripts/synch_srv.sh clients

# Combine options
./scripts/synch_srv.sh platform --no-restart
```

### Environment Variables

```bash
# Override source repository root
GH_ROOT=/custom/path ./scripts/synch_srv.sh

# Override destination root
SRV_ROOT=/custom/srv ./scripts/synch_srv.sh

# Disable service restart via environment
RESTART_SERVICES=no ./scripts/synch_srv.sh
```

## Deployment Workflow

### Standard Deployment

For deploying updated website design to https://fruitfulnetworkdevelopment.com/:

1. **Update GH-etc skeleton:**
   ```bash
   # Edit files in GH-etc/srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/
   # Or update from flask-app repository if that's your source
   ```

2. **Sync to live system:**
   ```bash
   cd /home/admin/GH-etc
   ./scripts/synch_srv.sh clients
   ```

3. **Verify deployment:**
   - Visit https://fruitfulnetworkdevelopment.com/
   - Check service status: `sudo systemctl status platform.service`
   - Check nginx logs: `sudo tail -f /var/log/nginx/error.log`

### Full Stack Deployment

To deploy both backend and frontend updates:

```bash
cd /home/admin/GH-etc
./scripts/synch_srv.sh
```

This will:
1. Sync platform code from `GH-etc/srv/webapps/platform/` to `/srv/webapps/platform/`
2. Sync client frontends from `GH-etc/srv/webapps/clients/` to `/srv/webapps/clients/`
3. Restart `platform.service` (loads new backend code)
4. Reload nginx (serves new frontend files)

## Infrastructure Invariant Compliance

### ✅ Invariant 6: Deployment Script Consistency
- Scripts sync from GH-etc to live system paths (`/srv/webapps`)
- Uses appropriate permissions (sudo for `/srv/webapps` writes)
- No references to removed intermediate directories

### ✅ Invariant 7: Skeleton Bootstrap Capability
- Syncs from skeleton structure (no runtime state)
- Preserves runtime artifacts in live system
- Allows fresh instance bootstrap from skeleton

### ✅ Path References
- All paths use standard system locations (`/srv/webapps`)
- No home directory path references
- Respects live system structure

## Safety Features

1. **Dry-run capability:** Use `rsync --dry-run` manually if needed
2. **Selective sync:** Can sync platform or clients independently
3. **Service control:** Can skip service restart for manual control
4. **Error handling:** Script exits on errors (set -euo pipefail)
5. **Logging:** Clear log messages show what's happening

## Examples

### Deploy Frontend Update Only

```bash
# Make changes to frontend files in GH-etc
cd /home/admin/GH-etc
vim srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/index.html

# Deploy to live system
./scripts/synch_srv.sh clients

# Verify at https://fruitfulnetworkdevelopment.com/
```

### Deploy Backend Update Only

```bash
# Make changes to platform code in GH-etc
cd /home/admin/GH-etc
vim srv/webapps/platform/app.py

# Deploy to live system
./scripts/synch_srv.sh platform

# Check service status
sudo systemctl status platform.service
```

### Deploy Without Service Restart (Manual Control)

```bash
# Sync code
./scripts/synch_srv.sh --no-restart

# Review changes manually, then restart when ready
sudo systemctl restart platform.service
sudo systemctl reload nginx
```

## Troubleshooting

### Service Won't Start After Restart

Check service logs:
```bash
sudo journalctl -u platform.service -n 50
```

Common issues:
- Syntax errors in Python code
- Missing dependencies in requirements.txt
- Permission issues

### Files Not Updating

Verify sync completed:
```bash
# Check if files were actually synced
ls -la /srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/
```

Check rsync exclusions didn't prevent updates:
```bash
# Manual rsync with verbose output
sudo rsync -av --dry-run --exclude='venv' --exclude='.git' \
  /home/admin/GH-etc/srv/webapps/clients/ /srv/webapps/clients/
```

### Nginx Not Serving Updated Files

Clear browser cache or check nginx is reloaded:
```bash
sudo systemctl status nginx
sudo systemctl reload nginx
```

Check file permissions:
```bash
ls -la /srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/
# Should be readable by www-data or world-readable
```
