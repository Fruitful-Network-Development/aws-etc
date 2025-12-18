#!/bin/bash
# audit.sh
#
# Consolidated audit entrypoint for nginx configuration, nginx syntax,
# file permissions, and systemd services related to the Flask app.
#
# This script exposes separate subcommands that mirror and refactor the
# behavior of the previous scripts:
#   - audit_nginx_config.sh
#   - audit_permissions.sh
#   - audit_services.sh
#   - 03_audit_nginx.sh
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AUDIT_DIR="${AUDIT_DIR:-$PROJECT_ROOT/docs/audit}"
mkdir -p "$AUDIT_DIR"

# Color codes for output (if terminal supports it)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
  echo ""
  echo "=========================================="
  echo "$1"
  echo "=========================================="
}

print_warning() {
  echo -e "${YELLOW}WARNING:${NC} $1"
}

print_error() {
  echo -e "${RED}ERROR:${NC} $1"
}

print_info() {
  echo -e "${GREEN}INFO:${NC} $1"
}

print_detail() {
  echo -e "${BLUE}DETAIL:${NC} $1"
}

run_with_sudo() {
  local sudo_bin
  sudo_bin="${SUDO_BIN:-$(command -v sudo || true)}"
  if [ -n "$sudo_bin" ]; then
    "$sudo_bin" "$@"
  else
    "$@"
  fi
}

run_with_log() {
  # run_with_log REPORT_FILE command [args...]
  local report_file="$1"; shift
  {
    "$@"
  } 2>&1 | tee "$report_file"
}

###############################
# nginx syntax/basic audit
###############################

audit_nginx_syntax_and_basic() {
  local ts report_file
  ts="$(date +%Y%m%d_%H%M%S)"
  report_file="$AUDIT_DIR/nginx_syntax_${ts}.txt"

  run_with_log "$report_file" _audit_nginx_syntax_body
}

_audit_nginx_syntax_body() {
  print_header "NGINX Configuration Syntax Test"
  echo "Timestamp: $(date)"
  echo "Report file will be mirrored in $AUDIT_DIR"
  echo "========================================="

  if command -v nginx >/dev/null 2>&1; then
    run_with_sudo nginx -t
  else
    print_error "nginx binary not found in PATH; cannot run syntax test."
    return 1
  fi
}

###############################
# nginx configuration audit
###############################

audit_nginx_config() {
  local ts report_file
  ts="$(date +%Y%m%d_%H%M%S)"
  report_file="$AUDIT_DIR/audit_nginx_config_${ts}.log"

  run_with_log "$report_file" _audit_nginx_config_body
}

_audit_nginx_config_body() {
  local NGINX_CONFIG_DIR NGINX_SITES_ENABLED NGINX_MAIN_CONFIG WEBAPP_ROOT REPORT_HEADER NGINX_BIN config_files

  NGINX_CONFIG_DIR="${NGINX_CONFIG_DIR:-/etc/nginx}"
  NGINX_SITES_ENABLED="$NGINX_CONFIG_DIR/sites-enabled"
  NGINX_MAIN_CONFIG="$NGINX_CONFIG_DIR/nginx.conf"
  WEBAPP_ROOT="${WEBAPP_ROOT:-/srv/webapps/platform}"
  REPORT_HEADER="=== NGINX CONFIGURATION AUDIT ==="

  echo "$REPORT_HEADER"
  echo "Audit Date: $(date)"
  echo "NGINX Config Directory: $NGINX_CONFIG_DIR"
  echo "Web Application Root: $WEBAPP_ROOT"
  echo ""

  # 1. Check if NGINX is installed and config directory exists
  print_header "NGINX Installation Check"

  if [ ! -d "$NGINX_CONFIG_DIR" ]; then
    print_error "NGINX configuration directory '$NGINX_CONFIG_DIR' does not exist."
    print_info "NGINX may not be installed or using non-standard configuration location."
    return 1
  else
    print_info "NGINX configuration directory found: $NGINX_CONFIG_DIR"
  fi

  # 2. Enabled site configurations (no nginx -t here; syntax handled separately)
  print_header "Enabled Site Configurations"

  if [ -d "$NGINX_SITES_ENABLED" ]; then
    local enabled_sites
    enabled_sites=$(find "$NGINX_SITES_ENABLED" -type f -name "*.conf" -o -name "*" ! -name "default" 2>/dev/null | wc -l)
    print_info "Found $enabled_sites enabled site configuration(s)"

    find "$NGINX_SITES_ENABLED" -type f \( -name "*.conf" -o ! -name "default" \) 2>/dev/null | while read -r config_file; do
      echo "  - $(basename "$config_file")"
    done
  else
    print_warning "sites-enabled directory not found: $NGINX_SITES_ENABLED"
  fi

  # 3. Analyze server blocks and application paths
  print_header "Server Block and Path Analysis"

  config_files=$(find "$NGINX_CONFIG_DIR" -name "*.conf" -type f 2>/dev/null)

  if [ -z "$config_files" ]; then
    print_warning "No .conf files found in $NGINX_CONFIG_DIR"
  else
    echo "$config_files" | while read -r config_file; do
      print_detail "Analyzing: $config_file"

      local server_blocks
      server_blocks=$(grep -c "^[[:space:]]*server[[:space:]]*{" "$config_file" 2>/dev/null || echo "0")
      if [ "$server_blocks" -gt 0 ]; then
        print_info "Found $server_blocks server block(s) in $config_file"
      fi

      if grep -q "root[[:space:]]*$WEBAPP_ROOT" "$config_file" 2>/dev/null; then
        print_info "Found root directive pointing to $WEBAPP_ROOT in $config_file"
        local root_path
        root_path=$(grep "root[[:space:]]*$WEBAPP_ROOT" "$config_file" 2>/dev/null | head -1 | awk '{print $2}' | tr -d ';')
        if [ -d "$root_path" ]; then
          print_info "Root path exists: $root_path"
        else
          print_error "Root path does not exist: $root_path (configured in $config_file)"
        fi
      fi

      if grep -q "proxy_pass" "$config_file" 2>/dev/null; then
        print_info "Found proxy_pass directive(s) in $config_file (likely Gunicorn configuration)"
        grep "proxy_pass" "$config_file" 2>/dev/null | while read -r line; do
          local proxy_url
          proxy_url=$(echo "$line" | awk '{print $2}' | tr -d ';')
          print_detail "  Proxy target: $proxy_url"
        done
      fi

      if grep -qE "(location[[:space:]]+/(static|media|assets))" "$config_file" 2>/dev/null; then
        print_info "Found static file location block(s) in $config_file"
      fi
    done
  fi

  # 4. Security checks
  print_header "Security Configuration Checks"

  echo "$config_files" | while read -r config_file; do
    if grep -q "server_tokens" "$config_file" 2>/dev/null; then
      if grep "server_tokens[[:space:]]*on" "$config_file" >/dev/null 2>&1; then
        print_warning "server_tokens is ON in $config_file (should be OFF in production)"
      fi
    else
      print_warning "server_tokens directive not found in $config_file (defaults to ON)"
    fi

    if grep -qE "listen[[:space:]]+80" "$config_file" 2>/dev/null && ! grep -qE "return[[:space:]]+301" "$config_file" 2>/dev/null; then
      print_warning "HTTP (port 80) listener found without redirect to HTTPS in $config_file"
    fi

    if grep -qE "listen[[:space:]]+443" "$config_file" 2>/dev/null; then
      print_info "HTTPS (port 443) listener found in $config_file"
      if grep -q "ssl_certificate" "$config_file" 2>/dev/null; then
        local cert_path
        cert_path=$(grep "ssl_certificate[[:space:]]" "$config_file" 2>/dev/null | head -1 | awk '{print $2}' | tr -d ';')
        if [ -f "$cert_path" ]; then
          print_info "SSL certificate file exists: $cert_path"
        else
          print_error "SSL certificate file not found: $cert_path (configured in $config_file)"
        fi
      fi
    fi

    if ! grep -q "access_log" "$config_file" 2>/dev/null; then
      print_warning "No access_log directive found in $config_file (logging may be disabled)"
    fi

    if ! grep -q "error_log" "$config_file" 2>/dev/null; then
      print_warning "No error_log directive found in $config_file (error logging may be disabled)"
    fi
  done

  # 5. Gunicorn integration checks
  print_header "Gunicorn Integration Check"

  echo "$config_files" | while read -r config_file; do
    if grep -q "^[[:space:]]*upstream" "$config_file" 2>/dev/null; then
      print_info "Found upstream block(s) in $config_file"
      grep -A 5 "^[[:space:]]*upstream" "$config_file" 2>/dev/null | while read -r line; do
        if echo "$line" | grep -qE "(server|unix:)" 2>/dev/null; then
          print_detail "  $line"
        fi
      done
    fi

    if grep -qE "unix:" "$config_file" 2>/dev/null; then
      local socket_path
      socket_path=$(grep "unix:" "$config_file" 2>/dev/null | head -1 | awk '{print $2}' | tr -d ';' | tr -d '"')
      print_info "Unix socket reference found: $socket_path"
      if [ -S "$socket_path" ]; then
        print_info "Unix socket exists: $socket_path"
      else
        print_warning "Unix socket does not exist: $socket_path (Gunicorn may not be running or misconfigured)"
      fi
    fi

    if grep -qE "proxy_pass.*127\.0\.0\.1:[0-9]+" "$config_file" 2>/dev/null || grep -qE "proxy_pass.*localhost:[0-9]+" "$config_file" 2>/dev/null; then
      local port
      port=$(grep -oE "127\.0\.0\.1:[0-9]+|localhost:[0-9]+" "$config_file" 2>/dev/null | head -1 | cut -d: -f2)
      print_info "Localhost port reference found: $port"
      print_detail "Verify this matches Gunicorn configuration"
    fi
  done

  # 6. Configuration file permissions
  print_header "Configuration File Permissions"

  find "$NGINX_CONFIG_DIR" -name "*.conf" -type f 2>/dev/null | while read -r config_file; do
    local perms owner
    perms=$(stat -c "%a" "$config_file" 2>/dev/null || stat -f "%OLp" "$config_file" 2>/dev/null || echo "unknown")
    owner=$(stat -c "%U" "$config_file" 2>/dev/null || stat -f "%Su" "$config_file" 2>/dev/null || echo "unknown")

    if [ "$perms" != "unknown" ] && [ "${perms: -1}" -ge 4 ]; then
      print_warning "Configuration file may be world-readable: $config_file (perms: $perms, owner: $owner)"
    fi
  done

  # 7. Summary
  print_header "Summary"
  echo "NGINX configuration audit complete."
  echo "Review the findings above and ensure:"
  echo "  - All paths point to existing directories"
  echo "  - Gunicorn socket/port matches NGINX proxy configuration"
  echo "  - Security best practices are followed (HTTPS, server_tokens off, etc.)"
  echo "  - Logging is properly configured"
}

###############################
# permissions audit
###############################

audit_permissions() {
  local ts report_file
  ts="$(date +%Y%m%d_%H%M%S)"
  report_file="$AUDIT_DIR/audit_permissions_${ts}.log"

  run_with_log "$report_file" _audit_permissions_body
}

_audit_permissions_body() {
  local WEBAPP_ROOT REPORT_HEADER

  WEBAPP_ROOT="${WEBAPP_ROOT:-/srv/webapps/platform}"
  REPORT_HEADER="=== FILE PERMISSIONS AND OWNERSHIP AUDIT ==="

  if [ ! -d "$WEBAPP_ROOT" ]; then
    print_error "Web application root directory '$WEBAPP_ROOT' does not exist."
    return 1
  fi

  echo "$REPORT_HEADER"
  echo "Audit Date: $(date)"
  echo "Target Directory: $WEBAPP_ROOT"
  echo "Report Directory: $AUDIT_DIR"
  echo ""

  # 1. Directory ownership
  print_header "Directory Ownership Analysis"
  echo "Checking ownership of $WEBAPP_ROOT and subdirectories..."
  echo ""

  find "$WEBAPP_ROOT" -type d -exec ls -ld {} \; 2>/dev/null | while read -r line; do
    local dir owner group perms
    dir=$(echo "$line" | awk '{print $NF}')
    owner=$(echo "$line" | awk '{print $3}')
    group=$(echo "$line" | awk '{print $4}')
    perms=$(echo "$line" | awk '{print $1}')

    if echo "$perms" | grep -q '...w..w..w.'; then
      print_warning "World-writable directory: $dir (owner: $owner, group: $group, perms: $perms)"
    fi

    if [ "$owner" = "root" ]; then
      print_warning "Directory owned by root: $dir (should typically be owned by application user)"
    fi
  done

  # 2. File ownership/permissions
  print_header "File Ownership and Permissions Analysis"
  echo "Scanning files in $WEBAPP_ROOT..."
  echo ""

  find "$WEBAPP_ROOT" -type f -exec ls -l {} \; 2>/dev/null | while read -r line; do
    local file owner group perms
    file=$(echo "$line" | awk '{print $NF}')
    owner=$(echo "$line" | awk '{print $3}')
    group=$(echo "$line" | awk '{print $4}')
    perms=$(echo "$line" | awk '{print $1}')

    if echo "$perms" | grep -q '...w..w..w.'; then
      print_error "World-writable file: $file (owner: $owner, group: $group, perms: $perms)"
    fi

    if [ "$owner" = "root" ]; then
      print_warning "File owned by root: $file (should typically be owned by application user)"
    fi

    if echo "$perms" | grep -q 'x'; then
      if ! echo "$file" | grep -qE '\\.(py|sh)$'; then
        print_info "Executable file found: $file (owner: $owner, perms: $perms)"
      fi
    fi
  done

  # 3. Sensitive files
  print_header "Sensitive Files Check"
  echo "Checking for configuration files, secrets, and sensitive data..."
  echo ""

  local SENSITIVE_PATTERNS=("*.key" "*.pem" "*.crt" "*.env" "*.secret" "config.py" "settings.py" ".env" "secrets.json")
  local pattern
  for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    find "$WEBAPP_ROOT" -name "$pattern" -type f 2>/dev/null | while read -r file; do
      local perms owner
      perms=$(stat -c "%a" "$file" 2>/dev/null || stat -f "%OLp" "$file" 2>/dev/null || echo "unknown")
      owner=$(stat -c "%U" "$file" 2>/dev/null || stat -f "%Su" "$file" 2>/dev/null || echo "unknown")
      if [ "$perms" != "unknown" ] && [ "${perms: -1}" -ge 4 ]; then
        print_warning "Sensitive file may be readable by others: $file (perms: $perms, owner: $owner)"
      fi
    done
  done

  # 4. SetUID/SetGID
  print_header "SetUID/SetGID Bit Check"
  echo "Checking for files with setuid or setgid bits set..."
  echo ""

  find "$WEBAPP_ROOT" -type f \( -perm -4000 -o -perm -2000 \) -exec ls -l {} \; 2>/dev/null | while read -r line; do
    local file perms
    file=$(echo "$line" | awk '{print $NF}')
    perms=$(echo "$line" | awk '{print $1}')
    print_warning "File with setuid/setgid bit: $file (perms: $perms)"
  done

  # 5. Summary statistics
  print_header "Summary Statistics"
  echo "Collecting summary statistics..."
  echo ""

  local total_files total_dirs root_owned_files root_owned_dirs
  total_files=$(find "$WEBAPP_ROOT" -type f 2>/dev/null | wc -l)
  total_dirs=$(find "$WEBAPP_ROOT" -type d 2>/dev/null | wc -l)
  root_owned_files=$(find "$WEBAPP_ROOT" -type f -user root 2>/dev/null | wc -l)
  root_owned_dirs=$(find "$WEBAPP_ROOT" -type d -user root 2>/dev/null | wc -l)

  echo "Total files: $total_files"
  echo "Total directories: $total_dirs"
  echo "Files owned by root: $root_owned_files"
  echo "Directories owned by root: $root_owned_dirs"
  echo ""

  # 6. Basic application structure
  print_header "Application Structure Check"
  echo "Verifying expected Flask application structure..."
  echo ""

  if [ -f "$WEBAPP_ROOT/app.py" ] || [ -f "$WEBAPP_ROOT/application.py" ] || [ -f "$WEBAPP_ROOT/wsgi.py" ]; then
    print_info "Flask application entry point found"
  else
    print_warning "No standard Flask entry point found (app.py, application.py, or wsgi.py)"
  fi

  if [ -f "$WEBAPP_ROOT/requirements.txt" ] || [ -f "$WEBAPP_ROOT/Pipfile" ]; then
    print_info "Python dependencies file found"
  else
    print_warning "No Python dependencies file found (requirements.txt or Pipfile)"
  fi

  if [ -d "$WEBAPP_ROOT/venv" ] || [ -d "$WEBAPP_ROOT/.venv" ] || [ -d "$WEBAPP_ROOT/env" ]; then
    print_info "Virtual environment directory found"
  else
    print_warning "No virtual environment directory found (venv, .venv, or env)"
  fi

  echo ""
  echo "=== AUDIT COMPLETE ==="
}

###############################
# services audit
###############################

audit_services() {
  local ts report_file
  ts="$(date +%Y%m%d_%H%M%S)"
  report_file="$AUDIT_DIR/audit_services_${ts}.log"

  run_with_log "$report_file" _audit_services_body
}

_audit_services_body() {
  local SYSTEMD_SYSTEM_DIR SYSTEMD_USER_DIR WEBAPP_ROOT REPORT_HEADER SYSTEMCTL_BIN

  SYSTEMD_SYSTEM_DIR="${SYSTEMD_SYSTEM_DIR:-/etc/systemd/system}"
  SYSTEMD_USER_DIR="${SYSTEMD_USER_DIR:-$HOME/.config/systemd/user}"
  WEBAPP_ROOT="${WEBAPP_ROOT:-/srv/webapps/platform}"
  REPORT_HEADER="=== SYSTEMD SERVICES AUDIT ==="
  SYSTEMCTL_BIN="${SYSTEMCTL_BIN:-$(command -v systemctl || true)}"

  echo "$REPORT_HEADER"
  echo "Audit Date: $(date)"
  echo "Systemd System Directory: $SYSTEMD_SYSTEM_DIR"
  echo "Web Application Root: $WEBAPP_ROOT"
  echo "Report Directory: $AUDIT_DIR"
  echo ""

  # 1. Systemd availability
  print_header "Systemd Availability Check"

  if [ -z "$SYSTEMCTL_BIN" ]; then
    print_error "systemctl command not found. This script requires systemd."
    return 1
  else
    print_info "systemd is available"
  fi

  # 2. Gunicorn service
  print_header "Gunicorn Service Check"

  local gunicorn_services
  gunicorn_services=$(find "$SYSTEMD_SYSTEM_DIR" -name "*gunicorn*.service" -type f 2>/dev/null || true)

  if [ -z "$gunicorn_services" ]; then
    print_warning "No Gunicorn service files found in $SYSTEMD_SYSTEM_DIR"
    print_info "Expected service file pattern: *gunicorn*.service"
  else
    echo "$gunicorn_services" | while read -r service_file; do
      local service_name
      service_name=$(basename "$service_file")
      print_info "Found Gunicorn service file: $service_name"

      if run_with_sudo "$SYSTEMCTL_BIN" is-enabled "$service_name" >/dev/null 2>&1; then
        local enabled_status
        enabled_status=$(run_with_sudo "$SYSTEMCTL_BIN" is-enabled "$service_name")
        if [ "$enabled_status" = "enabled" ]; then
          print_info "  Service is enabled"
        else
          print_warning "  Service is not enabled (status: $enabled_status)"
        fi
      else
        print_warning "  Could not determine enable status (may need sudo)"
      fi

      if run_with_sudo "$SYSTEMCTL_BIN" is-active "$service_name" >/dev/null 2>&1; then
        local active_status
        active_status=$(run_with_sudo "$SYSTEMCTL_BIN" is-active "$service_name")
        if [ "$active_status" = "active" ]; then
          print_info "  Service is active (running)"
        else
          print_error "  Service is not active (status: $active_status)"
        fi
      else
        print_warning "  Could not determine active status (may need sudo)"
      fi

      print_detail "Analyzing service file: $service_file"

      if grep -q "^WorkingDirectory=" "$service_file" 2>/dev/null; then
        local work_dir
        work_dir=$(grep "^WorkingDirectory=" "$service_file" 2>/dev/null | cut -d= -f2)
        print_detail "  WorkingDirectory: $work_dir"
        if [ -d "$work_dir" ]; then
          print_info "  Working directory exists: $work_dir"
          if [ "$work_dir" = "$WEBAPP_ROOT" ] || echo "$work_dir" | grep -q "$WEBAPP_ROOT"; then
            print_info "  Working directory aligns with webapp root"
          else
            print_warning "  Working directory does not match expected webapp root: $WEBAPP_ROOT"
          fi
        else
          print_error "  Working directory does not exist: $work_dir"
        fi
      else
        print_warning "  No WorkingDirectory specified in service file"
      fi

      if grep -q "^ExecStart=" "$service_file" 2>/dev/null; then
        local exec_start
        exec_start=$(grep "^ExecStart=" "$service_file" 2>/dev/null | cut -d= -f2-)
        print_detail "  ExecStart: $exec_start"

        if echo "$exec_start" | grep -q "$WEBAPP_ROOT"; then
          print_info "  ExecStart references webapp root"
        else
          print_warning "  ExecStart does not reference webapp root: $WEBAPP_ROOT"
        fi

        if echo "$exec_start" | grep -qE "(unix:|--bind)"; then
          print_info "  Gunicorn socket/bind configuration found"
          if echo "$exec_start" | grep -q "unix:"; then
            local socket_path
            socket_path=$(echo "$exec_start" | grep -oE "unix:[^[:space:]]+" | cut -d: -f2)
            if [ -S "$socket_path" ]; then
              print_info "  Socket file exists: $socket_path"
            else
              print_warning "  Socket file does not exist: $socket_path (service may not be running)"
            fi
          fi
        else
          print_warning "  No socket or bind configuration found in ExecStart"
        fi
      else
        print_error "  No ExecStart directive found in service file"
      fi

      if grep -q "^User=" "$service_file" 2>/dev/null; then
        local service_user
        service_user=$(grep "^User=" "$service_file" 2>/dev/null | cut -d= -f2)
        print_detail "  User: $service_user"
        if id "$service_user" >/dev/null 2>&1; then
          print_info "  Service user exists: $service_user"
        else
          print_error "  Service user does not exist: $service_user"
        fi
      else
        print_warning "  No User specified (will run as root, which is a security risk)"
      fi

      if grep -q "^Group=" "$service_file" 2>/dev/null; then
        local service_group
        service_group=$(grep "^Group=" "$service_file" 2>/dev/null | cut -d= -f2)
        print_detail "  Group: $service_group"
      fi

      if grep -qE "^Environment=" "$service_file" 2>/dev/null; then
        local env_count
        env_count=$(grep -cE "^Environment=" "$service_file" 2>/dev/null || echo "0")
        print_detail "  Environment variables: $env_count"
      fi
    done
  fi

  # 3. NGINX service
  print_header "NGINX Service Check"

  if run_with_sudo "$SYSTEMCTL_BIN" list-unit-files | grep -q "nginx.service"; then
    print_info "NGINX service unit file found"

    if run_with_sudo "$SYSTEMCTL_BIN" is-enabled nginx >/dev/null 2>&1; then
      local nginx_enabled
      nginx_enabled=$(run_with_sudo "$SYSTEMCTL_BIN" is-enabled nginx)
      if [ "$nginx_enabled" = "enabled" ]; then
        print_info "NGINX service is enabled"
      else
        print_warning "NGINX service is not enabled (status: $nginx_enabled)"
      fi
    fi

    if run_with_sudo "$SYSTEMCTL_BIN" is-active nginx >/dev/null 2>&1; then
      local nginx_active
      nginx_active=$(run_with_sudo "$SYSTEMCTL_BIN" is-active nginx)
      if [ "$nginx_active" = "active" ]; then
        print_info "NGINX service is active (running)"
      else
        print_error "NGINX service is not active (status: $nginx_active)"
      fi
    fi
  else
    print_warning "NGINX service unit file not found"
  fi

  # 4. Other app services
  print_header "Other Application Services Check"

  local app_services
  app_services=$(find "$SYSTEMD_SYSTEM_DIR" -name "*.service" -type f 2>/dev/null | grep -iE "(flask|python|app|web)" || true)

  if [ -z "$app_services" ]; then
    print_info "No other obvious application service files found"
  else
    echo "$app_services" | while read -r service_file; do
      local service_name
      service_name=$(basename "$service_file")
      if echo "$service_name" | grep -qv "gunicorn"; then
        print_info "Found potential application service: $service_name"
      fi
    done
  fi

  # 5. Dependencies
  print_header "Service Dependencies Check"

  echo "$gunicorn_services" | while read -r service_file; do
    [ -n "$service_file" ] || continue
    local service_name
    service_name=$(basename "$service_file")

    if grep -qE "^(After|Requires|Wants)=" "$service_file" 2>/dev/null; then
      print_detail "Dependencies for $service_name:"
      grep -E "^(After|Requires|Wants)=" "$service_file" 2>/dev/null | while read -r dep_line; do
        print_detail "  $dep_line"
      done

      if grep -qE "^(After|Requires|Wants)=.*nginx" "$service_file" 2>/dev/null; then
        print_info "NGINX dependency found in $service_name"
      else
        print_warning "No NGINX dependency found in $service_name (Gunicorn should start after NGINX)"
      fi
    else
      print_warning "No dependency directives found in $service_name"
    fi
  done

  # 6. Service file permissions
  print_header "Service File Permissions Check"

  find "$SYSTEMD_SYSTEM_DIR" -name "*.service" -type f 2>/dev/null | while read -r service_file; do
    local perms owner
    perms=$(stat -c "%a" "$service_file" 2>/dev/null || stat -f "%OLp" "$service_file" 2>/dev/null || echo "unknown")
    owner=$(stat -c "%U" "$service_file" 2>/dev/null || stat -f "%Su" "$service_file" 2>/dev/null || echo "unknown")

    if [ "$perms" != "unknown" ] && [ "${perms: -1}" -ge 6 ]; then
      print_warning "Service file may be world-writable: $service_file (perms: $perms, owner: $owner)"
    fi
  done

  # 7. Summary
  print_header "Summary"
  echo "Systemd services audit complete."
  echo "Review the findings above and ensure:"
  echo "  - Gunicorn service is enabled and running"
  echo "  - NGINX service is enabled and running"
  echo "  - Service WorkingDirectory matches actual deployment location"
  echo "  - Service User is set (not running as root)"
  echo "  - Socket paths in service files match NGINX configuration"
  echo "  - Service dependencies are properly configured"
  echo ""
  echo "=== AUDIT COMPLETE ==="
}

###############################
# CLI dispatcher
###############################

print_usage() {
  cat <<EOF
Usage: $0 <command>

Commands:
  nginx-syntax    Run nginx configuration syntax/basic audit (nginx -t).
  nginx-config    Run detailed nginx configuration audit.
  permissions     Run file ownership/permissions audit for the webapp.
  services        Run systemd services audit for Gunicorn/NGINX/app.
  all             Run all of the above audits in sequence.
  help            Show this help message.
EOF
}

main() {
  local cmd
  cmd="${1:-}" || true

  case "$cmd" in
    nginx-syntax)
      audit_nginx_syntax_and_basic
      ;;
    nginx-config)
      audit_nginx_config
      ;;
    permissions)
      audit_permissions
      ;;
    services)
      audit_services
      ;;
    all)
      audit_nginx_syntax_and_basic
      audit_nginx_config
      audit_permissions
      audit_services
      ;;
    help|--help|-h|"")
      print_usage
      ;;
    *)
      print_error "Unknown command: $cmd"
      print_usage
      return 1
      ;;
  esac
}

main "$@"
