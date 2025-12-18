# Deployment Script Implementation Summary

## Problem Statement

After normalizing the GH-etc repository, we needed a deployment mechanism to:
1. Sync the skeleton structure from `GH-etc/srv/webapps/` to `/srv/webapps/`
2. Preserve runtime state (venv, .git, __pycache__)
3. Restart services to serve updated code
4. Make updated website design visible at https://fruitfulnetworkdevelopment.com/

## Solution: `synch_srv.sh`

A new deployment script that safely syncs skeleton code to live runtime while preserving runtime artifacts.

## Script Implementation

### Location
`/home/admin/GH-etc/scripts/synch_srv.sh`

### Key Features

1. **Safe Rsync with Exclusions**
   - Excludes: `.git`, `venv/`, `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, `.DS_Store`, `*.log`
   - Preserves runtime dependencies and git repositories in live system
   - Updates source code without breaking runtime state

2. **Selective Sync**
   - `all` - Sync everything (default)
   - `platform` - Sync backend code only
   - `clients` - Sync frontend code only

3. **Service Management**
   - Automatically restarts `platform.service` (Flask/Gunicorn backend)
   - Reloads nginx (static file serving)
   - Optional `--no-restart` flag for manual control

4. **Error Handling**
   - Uses `set -euo pipefail` for strict error handling
   - Validates source and destination paths
   - Clear error messages

## Rationale for Exclusions

| Exclusion | Rationale |
|-----------|-----------|
| `.git` | Live system may have git repos; skeleton doesn't need them |
| `venv/` | Python virtual environments are runtime dependencies, not source code |
| `__pycache__/` | Compiled bytecode cache, regenerated automatically |
| `*.pyc`, `*.pyo`, `*.pyd` | Compiled Python files, regenerated as needed |
| `.DS_Store` | macOS metadata, not needed in deployment |
| `*.log` | Runtime log files, shouldn't be overwritten by skeleton |

**Critical:** These exclusions ensure the skeleton remains clean (no runtime state) while the live system maintains its operational state (venv for Python dependencies, .git for version control if present).

## Deployment Command

### For Frontend Updates (Website Design)

```bash
cd /home/admin/GH-etc
./scripts/synch_srv.sh clients
```

This will:
1. Sync frontend files from `GH-etc/srv/webapps/clients/` to `/srv/webapps/clients/`
2. Reload nginx to serve updated static files
3. Make changes visible at https://fruitfulnetworkdevelopment.com/

### For Backend Updates

```bash
cd /home/admin/GH-etc
./scripts/synch_srv.sh platform
```

This will:
1. Sync platform code from `GH-etc/srv/webapps/platform/` to `/srv/webapps/platform/`
2. Restart `platform.service` to load new Python code
3. Reload nginx for any configuration changes

### For Full Stack Deployment

```bash
cd /home/admin/GH-etc
./scripts/synch_srv.sh
```

Syncs both platform and clients, then restarts all services.

## Confirmation: Updated Design at URL

After running `./scripts/synch_srv.sh clients`:

1. **Frontend files are updated** in `/srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/`
2. **Nginx is reloaded** to serve the new files
3. **Browser visit to https://fruitfulnetworkdevelopment.com/** shows updated design

**Note:** You may need to:
- Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- Wait a few seconds for nginx to finish reloading
- Check nginx is serving the correct files: `ls -la /srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/`

## Infrastructure Invariant Compliance

✅ **Invariant 6: Deployment Script Consistency**
- Syncs from GH-etc to live system paths (`/srv/webapps`)
- Uses sudo for appropriate permissions
- No references to removed intermediate directories

✅ **Invariant 7: Skeleton Bootstrap Capability**
- Syncs from clean skeleton (no runtime artifacts)
- Preserves runtime state in live system
- Enables fresh instance bootstrap

✅ **Path References**
- All paths use standard system locations
- No home directory references
- Respects live system structure

## Workflow Integration

### Current Deployment Scripts

1. **`synch.sh`** - Syncs configuration templates (`GH-etc/etc/` → `/etc/`)
2. **`synch_srv.sh`** - Syncs application code (`GH-etc/srv/webapps/` → `/srv/webapps/`) **[NEW]**
3. **`pull_app.sh`** - Pulls updates from flask-app git repository to `/home/admin/srv/webapps`
4. **`pull_etc.sh`** - Pulls updates from aws-etc git repository to `/home/admin/GH-etc`

### Typical Deployment Flow

```bash
# 1. Update configuration (if needed)
cd /home/admin/GH-etc
./scripts/synch.sh nginx-site fruitfulnetworkdevelopment.com

# 2. Update application code
./scripts/synch_srv.sh clients

# 3. Verify services
sudo systemctl status platform.service nginx
```

## Testing Recommendations

Before deploying to production:

1. **Test script syntax:**
   ```bash
   bash -n scripts/synch_srv.sh
   ```

2. **Verify source structure:**
   ```bash
   ls -la /home/admin/GH-etc/srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/
   ```

3. **Dry-run sync (manual):**
   ```bash
   sudo rsync -av --dry-run --exclude='venv' --exclude='.git' \
     /home/admin/GH-etc/srv/webapps/clients/ /srv/webapps/clients/
   ```

4. **Check service status after deployment:**
   ```bash
   sudo systemctl status platform.service
   sudo systemctl status nginx
   ```

## Summary

The `synch_srv.sh` script fills the deployment gap by:
- ✅ Providing safe sync from skeleton to live system
- ✅ Preserving runtime state (venv, .git, cache files)
- ✅ Automatically restarting services for code changes
- ✅ Supporting selective deployment (platform/clients/all)
- ✅ Maintaining infrastructure invariants
- ✅ Enabling updated website design to be visible at https://fruitfulnetworkdevelopment.com/

The script is ready for use and fully documented.
