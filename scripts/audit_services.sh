#!/bin/bash
#
# audit_services.sh
#
# Purpose:
#   Audits systemd unit files and service configurations for the Flask application
#   and related services (Gunicorn, NGINX). This script identifies inconsistencies
#   between service configurations and actual deployment structure.
#
# Usage:
#   ./audit_services.sh
#
# Output:
#   Prints a detailed report of systemd service configuration issues to stdout.
#
# Exit Codes:
#   0 - Script completed successfully
#   1 - Critical errors encountered (e.g., systemd not available)
#
# Dependencies:
#   Standard POSIX tools: systemctl, grep, awk, find, test
#   Requires systemd (standard on modern Linux distributions)
#
# Notes:
#   - This script does NOT modify any systemd unit files or services
#   - May require sudo privileges to check service status
#   - All findings are reported for manual review
#   - Assumes standard systemd unit file locations

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/docs}"
REPORT_FILE="${REPORT_FILE:-$LOG_DIR/audit_services_$(date +%Y%m%d_%H%M%S).log}"

mkdir -p "$LOG_DIR"
exec > >(tee "$REPORT_FILE") 2>&1

# Color codes for output (if terminal supports it)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SYSTEMD_SYSTEM_DIR="${SYSTEMD_SYSTEM_DIR:-/etc/systemd/system}"
SYSTEMD_USER_DIR="${SYSTEMD_USER_DIR:-$HOME/.config/systemd/user}"
WEBAPP_ROOT="${WEBAPP_ROOT:-/srv/webapps/platform}"
REPORT_HEADER="=== SYSTEMD SERVICES AUDIT ==="
SUDO_BIN="${SUDO_BIN:-$(command -v sudo || true)}"
SYSTEMCTL_BIN="${SYSTEMCTL_BIN:-$(command -v systemctl || true)}"

# Function to print section headers
print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Function to print warnings
print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Function to print errors
print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

# Function to print info
print_info() {
    echo -e "${GREEN}INFO:${NC} $1"
}

# Function to print detail
print_detail() {
    echo -e "${BLUE}DETAIL:${NC} $1"
}

run_with_sudo() {
    if [ -n "$SUDO_BIN" ]; then
        "$SUDO_BIN" "$@"
    else
        "$@"
    fi
}

echo "$REPORT_HEADER"
echo "Audit Date: $(date)"
echo "Systemd System Directory: $SYSTEMD_SYSTEM_DIR"
echo "Web Application Root: $WEBAPP_ROOT"
echo "Report File: $REPORT_FILE"
echo ""

# 1. Check if systemd is available
print_header "Systemd Availability Check"

if [ -z "$SYSTEMCTL_BIN" ]; then
    print_error "systemctl command not found. This script requires systemd."
    exit 1
else
    print_info "systemd is available"
fi

# 2. Check for Gunicorn service
print_header "Gunicorn Service Check"

# Look for Gunicorn-related service files
gunicorn_services=$(find "$SYSTEMD_SYSTEM_DIR" -name "*gunicorn*.service" -type f 2>/dev/null || true)

if [ -z "$gunicorn_services" ]; then
    print_warning "No Gunicorn service files found in $SYSTEMD_SYSTEM_DIR"
    print_info "Expected service file pattern: *gunicorn*.service"
else
    echo "$gunicorn_services" | while read -r service_file; do
        service_name=$(basename "$service_file")
        print_info "Found Gunicorn service file: $service_name"
        
        # Check if service is enabled
        if run_with_sudo "$SYSTEMCTL_BIN" is-enabled "$service_name" >/dev/null 2>&1; then
            enabled_status=$(run_with_sudo "$SYSTEMCTL_BIN" is-enabled "$service_name")
            if [ "$enabled_status" = "enabled" ]; then
                print_info "  Service is enabled"
            else
                print_warning "  Service is not enabled (status: $enabled_status)"
            fi
        else
            print_warning "  Could not determine enable status (may need sudo)"
        fi
        
        # Check service status
        if run_with_sudo "$SYSTEMCTL_BIN" is-active "$service_name" >/dev/null 2>&1; then
            active_status=$(run_with_sudo "$SYSTEMCTL_BIN" is-active "$service_name")
            if [ "$active_status" = "active" ]; then
                print_info "  Service is active (running)"
            else
                print_error "  Service is not active (status: $active_status)"
            fi
        else
            print_warning "  Could not determine active status (may need sudo)"
        fi
        
        # Analyze service file contents
        print_detail "Analyzing service file: $service_file"
        
        # Check for WorkingDirectory
        if grep -q "^WorkingDirectory=" "$service_file" 2>/dev/null; then
            work_dir=$(grep "^WorkingDirectory=" "$service_file" 2>/dev/null | cut -d= -f2)
            print_detail "  WorkingDirectory: $work_dir"
            
            if [ -d "$work_dir" ]; then
                print_info "  Working directory exists: $work_dir"
                
                # Check if it matches webapp root
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
        
        # Check for ExecStart (Gunicorn command)
        if grep -q "^ExecStart=" "$service_file" 2>/dev/null; then
            exec_start=$(grep "^ExecStart=" "$service_file" 2>/dev/null | cut -d= -f2-)
            print_detail "  ExecStart: $exec_start"
            
            # Check if it references the webapp directory
            if echo "$exec_start" | grep -q "$WEBAPP_ROOT"; then
                print_info "  ExecStart references webapp root"
            else
                print_warning "  ExecStart does not reference webapp root: $WEBAPP_ROOT"
            fi
            
            # Check for socket or bind configuration
            if echo "$exec_start" | grep -qE "(unix:|--bind)"; then
                print_info "  Gunicorn socket/bind configuration found"
                
                # Extract socket path if present
                if echo "$exec_start" | grep -q "unix:"; then
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
        
        # Check for User
        if grep -q "^User=" "$service_file" 2>/dev/null; then
            service_user=$(grep "^User=" "$service_file" 2>/dev/null | cut -d= -f2)
            print_detail "  User: $service_user"
            
            # Check if user exists
            if id "$service_user" >/dev/null 2>&1; then
                print_info "  Service user exists: $service_user"
            else
                print_error "  Service user does not exist: $service_user"
            fi
        else
            print_warning "  No User specified (will run as root, which is a security risk)"
        fi
        
        # Check for Group
        if grep -q "^Group=" "$service_file" 2>/dev/null; then
            service_group=$(grep "^Group=" "$service_file" 2>/dev/null | cut -d= -f2)
            print_detail "  Group: $service_group"
        fi
        
        # Check for Environment variables
        if grep -qE "^Environment=" "$service_file" 2>/dev/null; then
            env_count=$(grep -cE "^Environment=" "$service_file" 2>/dev/null || echo "0")
            print_detail "  Environment variables: $env_count"
        fi
    done
fi

# 3. Check NGINX service
print_header "NGINX Service Check"

if run_with_sudo "$SYSTEMCTL_BIN" list-unit-files | grep -q "nginx.service"; then
    print_info "NGINX service unit file found"

    # Check if NGINX is enabled
    if run_with_sudo "$SYSTEMCTL_BIN" is-enabled nginx >/dev/null 2>&1; then
        nginx_enabled=$(run_with_sudo "$SYSTEMCTL_BIN" is-enabled nginx)
        if [ "$nginx_enabled" = "enabled" ]; then
            print_info "NGINX service is enabled"
        else
            print_warning "NGINX service is not enabled (status: $nginx_enabled)"
        fi
    fi

    # Check if NGINX is active
    if run_with_sudo "$SYSTEMCTL_BIN" is-active nginx >/dev/null 2>&1; then
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

# 4. Check for other Flask/Python application services
print_header "Other Application Services Check"

# Look for other potential application service files
app_services=$(find "$SYSTEMD_SYSTEM_DIR" -name "*.service" -type f 2>/dev/null | grep -iE "(flask|python|app|web)" || true)

if [ -z "$app_services" ]; then
    print_info "No other obvious application service files found"
else
    echo "$app_services" | while read -r service_file; do
        service_name=$(basename "$service_file")
        # Skip if we already checked this as a Gunicorn service
        if echo "$service_name" | grep -qv "gunicorn"; then
            print_info "Found potential application service: $service_name"
        fi
    done
fi

# 5. Check service dependencies and ordering
print_header "Service Dependencies Check"

echo "$gunicorn_services" | while read -r service_file; do
    service_name=$(basename "$service_file")
    
    # Check for After/Requires/Wants directives
    if grep -qE "^(After|Requires|Wants)=" "$service_file" 2>/dev/null; then
        print_detail "Dependencies for $service_name:"
        grep -E "^(After|Requires|Wants)=" "$service_file" 2>/dev/null | while read -r dep_line; do
            print_detail "  $dep_line"
        done
        
        # Check if NGINX is in dependencies
        if grep -qE "^(After|Requires|Wants)=.*nginx" "$service_file" 2>/dev/null; then
            print_info "NGINX dependency found in $service_name"
        else
            print_warning "No NGINX dependency found in $service_name (Gunicorn should start after NGINX)"
        fi
    else
        print_warning "No dependency directives found in $service_name"
    fi
done

# 6. Check service file permissions
print_header "Service File Permissions Check"

find "$SYSTEMD_SYSTEM_DIR" -name "*.service" -type f 2>/dev/null | while read -r service_file; do
    perms=$(stat -c "%a" "$service_file" 2>/dev/null || stat -f "%OLp" "$service_file" 2>/dev/null || echo "unknown")
    owner=$(stat -c "%U" "$service_file" 2>/dev/null || stat -f "%Su" "$service_file" 2>/dev/null || echo "unknown")
    
    # Service files should typically be 644 (readable by all, writable by owner)
    if [ "$perms" != "unknown" ] && [ "${perms: -1}" -ge 4 ]; then
        # World-readable is typically OK for service files, but check for world-writable
        if [ "${perms: -1}" -ge 6 ]; then
            print_warning "Service file may be world-writable: $service_file (perms: $perms, owner: $owner)"
        fi
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
