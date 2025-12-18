# synch.sh Update Summary

## Changes Applied

### 1. Updated Target Path (Lines 5, 10, 23, 120)

**Before:**
```bash
# Sync individual configuration files from the GH-etc repo clone into the
# `/home/admin/etc` deployment tree, one file at a time.
ETC_ROOT="${ETC_ROOT:-/home/admin/etc}"
```

**After:**
```bash
# Sync individual configuration files from the GH-etc repo clone into the
# live system `/etc` directory, one file at a time.
ETC_ROOT="${ETC_ROOT:-/etc}"
```

**Why:** The `/home/admin/etc` directory was removed during normalization as a redundant duplicate. The script must sync directly to the live system path `/etc` per infrastructure invariants.

### 2. Added Sudo Support (Lines 65-67)

**Before:**
```bash
log "Copying $src -> $dest"
mkdir -p "$(dirname "$dest")"
cp -v "$src" "$dest"
```

**After:**
```bash
log "Copying $src -> $dest"
# Use sudo for /etc operations (standard user cannot write to /etc)
sudo mkdir -p "$(dirname "$dest")"
sudo cp -v "$src" "$dest"
```

**Why:** Standard users cannot write to `/etc`. The script now uses `sudo` to create directories and copy files, enabling proper deployment to live system paths.

### 3. Updated Documentation (Lines 17-18, 120)

Added clarifying note:
```bash
# Note: This script uses sudo to write to /etc. It syncs configuration
# templates from GH-etc to the live system paths.
```

Updated help text:
```
ETC_ROOT  Destination tree (default: /etc)
```

**Why:** Documentation must accurately reflect the script's behavior and target paths.

## Infrastructure Invariant Alignment

### ✅ Invariant 6: Deployment Script Consistency
- **Requirement:** "Deployment scripts must sync from GH-etc to live system paths (`/etc`, `/srv/webapps`)"
- **Compliance:** Script now syncs to `/etc` (live system path), not `/home/admin/etc`
- **Requirement:** "Scripts must not reference removed intermediate directories"
- **Compliance:** Removed all references to `/home/admin/etc`
- **Requirement:** "Scripts must use appropriate permissions (sudo where needed for `/etc` writes)"
- **Compliance:** Added `sudo` for all `/etc` operations

### ✅ Invariant 4: System Path References
- **Requirement:** "All paths must use standard system locations (`/etc`, `/srv`, `/var`, etc.)"
- **Compliance:** Script now targets `/etc` instead of home directory paths

## Current Script Behavior

The updated script:
1. **Source:** Reads from `GH-etc/etc/` (canonical source)
2. **Target:** Writes to `/etc` (live system path)
3. **Permissions:** Uses `sudo` for `/etc` writes
4. **Scope:** Handles `etc/` configuration files only (nginx, systemd)

## Future Enhancement Consideration

**Note:** The script currently only handles `etc/` file syncing. If needed, a separate command or enhancement could be added to sync the skeleton structure from `GH-etc/srv/webapps/` to `/srv/webapps/` using `rsync` with exclusions for `.git/`, `venv/`, `__pycache__/`, and `*.pyc` files. This would align with the skeleton bootstrap capability requirement.

## Backward Compatibility

The script maintains backward compatibility via the `ETC_ROOT` environment variable. Users can override the target if needed:
```bash
ETC_ROOT=/custom/path ./synch.sh nginx-core
```

However, the default now points to `/etc` as the canonical target.

## Testing Recommendations

1. **Test with dry-run equivalent:** Verify file paths resolve correctly
2. **Test sudo permissions:** Ensure user has sudo access for `/etc` writes
3. **Test individual file sync:** `./synch.sh one etc/nginx/nginx.conf`
4. **Test nginx-core:** `./synch.sh nginx-core`
5. **Test nginx-site:** `./synch.sh nginx-site fruitfulnetworkdevelopment.com`

## Patch Summary

**Files Modified:**
- `scripts/synch.sh`

**Lines Changed:**
- Line 5: Comment updated (target path)
- Line 10: Comment updated (ETC_ROOT default)
- Line 17-18: Added sudo usage note
- Line 23: ETC_ROOT default changed to `/etc`
- Line 65-67: Added sudo for mkdir and cp operations
- Line 120: Help text updated (ETC_ROOT default)

**No functional logic changes** - only path updates and permission handling added.
