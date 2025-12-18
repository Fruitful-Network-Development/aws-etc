thin GH-etc

## System Path References

### 4. Configuration Files Reference Live System Paths Only
- Nginx configuration files in `GH-etc/etc/nginx/` must reference:
  - `/srv/webapps/...` (not `/home/admin/srv/...`)
  - `/etc/letsencrypt/...` (not home directory paths)
- Systemd unit files in `GH-etc/etc/systemd/system/` must reference:
  - `/srv/webapps/...` (not `/home/admin/srv/...`)
  - Absolute system paths only

### 5. No Home Directory Path References in Live Configs
- No nginx includes or configuration references to `/home/admin/*`
- No systemd unit files reference `/home/admin/etc` or `/home/admin/srv`
- All paths must use standard system locations (`/etc`, `/srv`, `/var`, etc.)
# Infrastructure Invariants

This document defines the required invariants for the GH-etc repository structure and deployment workflow. These rules must be maintained to ensure safe, predictable infrastructure management.

## Repository Structure Invariants

### 1. Single Canonical Directories
- **Exactly one `etc/` directory** exists at the top level of GH-etc (`GH-etc/etc/`)
  - Contains nginx and systemd configuration templates
  - Must be the single source of truth for configuration
- **Exactly one `srv/webapps/` directory** exists at the top level of GH-etc (`GH-etc/srv/webapps/`)
  - Contains skeleton layout only (no runtime state)
  - Excludes: `.git/`, `venv/`, `__pycache__/`, `*.pyc` files
  - Includes: source files, configuration templates, frontend assets

### 2. No Runtime Artifacts
GH-etc must contain NO:
- `.git` directories (except the root `.git/` for the repo itself)
- `venv/` or virtual environment directories
- `__pycache__/` directories
- Compiled Python files (`*.pyc`, `*.pyo`)
- Runtime logs or state files
- Database files or caches

### 3. No Nested Duplicates
- No nested paths like `GH-etc/home/...` containing duplicate `etc/` or `srv/` structures
- No duplicate directories wi
## Deployment Safety

### 6. Deployment Script Consistency
- Deployment scripts must sync from GH-etc to live system paths (`/etc`, `/srv/webapps`)
- Scripts must not reference removed intermediate directories (e.g., `/home/admin/etc`)
- Scripts must use appropriate permissions (sudo where needed for `/etc` writes)

### 7. Skeleton Bootstrap Capability
- The `GH-etc/srv/webapps/` skeleton must be sufficient to bootstrap a fresh instance
- Must include all source files, templates, and structure needed for deployment
- Must exclude runtime state that is generated during deployment (venv, .git clones)

## Verification Commands

Use these commands to verify invariants:

```bash
# Verify single etc/ and srv/webapps/ exist
find /home/admin/GH-etc -maxdepth 1 -type d -name "etc" -o -name "srv" | wc -l
# Should return: 2

# Verify no .git except root
find /home/admin/GH-etc -type d -name ".git" | wc -l
# Should return: 1

# Verify no venv or runtime artifacts
find /home/admin/GH-etc -type d \( -name "venv" -o -name "__pycache__" \) ! -path "*/.git/*"
# Should return: (empty)

# Verify nginx configs use system paths
grep -r "/home/admin" /home/admin/GH-etc/etc/nginx/
# Should return: (empty or only in comments)

# Verify systemd units use system paths
grep -r "/home/admin" /home/admin/GH-etc/etc/systemd/
# Should return: (empty)
```

## Current Structure

```
GH-etc/
├── .git/                    # Git repository (only .git allowed)
├── docs/                    # Documentation and audit logs
├── etc/                     # ✅ Single canonical nginx + systemd configs
│   ├── nginx/
│   └── systemd/
├── scripts/                 # Deployment and audit scripts
├── srv/                     # ✅ Single canonical skeleton
│   └── webapps/
│       ├── platform/        # Flask app skeleton (no venv, no .git)
│       └── clients/         # Client frontend skeletons
└── README.md
```

## Violation Reporting

If any invariant is violated:
1. Document the violation explicitly
2. Propose corrective actions
3. Do NOT make destructive changes without confirmation
4. Update this document if invariants change
