# synch.sh Script Analysis & Update Plan

## Current State Analysis

### Outdated References Identified

1. **Line 5, 10, 20:** References to `/home/admin/etc` (removed during normalization)
   - Comment: "Sync individual configuration files from the GH-etc repo clone into the `/home/admin/etc` deployment tree"
   - Default: `ETC_ROOT="${ETC_ROOT:-/home/admin/etc}"`
   - Help text: "ETC_ROOT  Destination tree (default: /home/admin/etc)"

2. **Current Behavior:**
   - Syncs from `GH-etc/etc/` → `/home/admin/etc/` (broken - directory doesn't exist)
   - Uses regular `cp` command (no sudo, would fail on `/etc` anyway)
   - Only handles `etc/` files (no srv/webapps capability)

### Issues

1. **Directory doesn't exist:** `/home/admin/etc` was removed as redundant duplicate
2. **Wrong target:** Should sync to `/etc` (live system path) not home directory
3. **Missing permissions:** Requires `sudo` for `/etc` writes
4. **Limited scope:** Only handles `etc/` files, no `srv/webapps/` skeleton sync

## Required Changes

### 1. Update Target Path
- Change `ETC_ROOT` default from `/home/admin/etc` to `/etc`
- Maintains infrastructure invariant: "Deployment scripts must sync from GH-etc to live system paths (`/etc`, `/srv/webapps`)"

### 2. Add Sudo Support
- Use `sudo` for `/etc` operations (standard user can't write to `/etc`)
- Preserves safety: only syncs configuration, doesn't modify live runtime state

### 3. Update Documentation
- Fix comments and help text to reflect new target path
- Clarify that script syncs to live system paths

### 4. Consider Adding srv/webapps Sync (Optional Enhancement)
- Add command to sync skeleton from `GH-etc/srv/webapps/` to `/srv/webapps/`
- Must exclude: `.git/`, `venv/`, `__pycache__/`, `*.pyc`
- Would use `rsync` with exclusions for safety

## Infrastructure Invariant Alignment

**Invariant 6: Deployment Script Consistency**
- ✅ Scripts sync from GH-etc to live system paths (`/etc`, `/srv/webapps`)
- ✅ Scripts don't reference removed intermediate directories
- ✅ Scripts use appropriate permissions (sudo for `/etc` writes)

**Invariant 4: System Path References**
- ✅ Script syncs to system paths (`/etc`), not home directory paths
- ✅ Maintains separation: GH-etc is source, `/etc` is target

## Proposed Changes

1. **ETC_ROOT default:** `/home/admin/etc` → `/etc`
2. **Use sudo:** Add `sudo` wrapper for file operations to `/etc`
3. **Update comments:** Reflect new deployment target
4. **Add safety check:** Warn if syncing to wrong location
5. **Keep backward compatibility:** Allow ETC_ROOT override via environment variable
