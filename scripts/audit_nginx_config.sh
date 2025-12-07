#!/bin/bash
#
# audit_nginx_config.sh
#
# Purpose:
#   Audits NGINX configuration files to ensure alignment with the actual
#   application deployment structure under /srv/webapps/platform. This script identifies
#   configuration mismatches, security issues, and best practice violations.
#
# Usage:
#   ./audit_nginx_config.sh
#
# Output:
#   Prints a detailed report of NGINX configuration issues to stdout.
#
# Exit Codes:
#   0 - Script completed successfully
#   1 - NGINX configuration files not found or critical errors
#
# Dependencies:
#   Standard POSIX tools: grep, awk, find, test, nginx (for config test)
#
# Notes:
#   - This script does NOT modify any NGINX configuration files
#   - Requires read access to NGINX configuration files (may need sudo)
#   - All findings are reported for manual review
#   - Assumes standard NGINX configuration locations

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/docs}"
REPORT_FILE="${REPORT_FILE:-$LOG_DIR/audit_nginx_$(date +%Y%m%d_%H%M%S).log}"

mkdir -p "$LOG_DIR"

# Persist output to the audit log while still streaming to stdout for agents in
# the deployed environment.
exec > >(tee "$REPORT_FILE") 2>&1

# Color codes for output (if terminal supports it)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (override with environment variables when needed)
NGINX_CONFIG_DIR="${NGINX_CONFIG_DIR:-/etc/nginx}"
NGINX_SITES_AVAILABLE="$NGINX_CONFIG_DIR/sites-available"
NGINX_SITES_ENABLED="$NGINX_CONFIG_DIR/sites-enabled"
NGINX_MAIN_CONFIG="$NGINX_CONFIG_DIR/nginx.conf"
WEBAPP_ROOT="${WEBAPP_ROOT:-/srv/webapps/platform}"
REPORT_HEADER="=== NGINX CONFIGURATION AUDIT ==="
SUDO_BIN="${SUDO_BIN:-$(command -v sudo || true)}"

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
echo "NGINX Config Directory: $NGINX_CONFIG_DIR"
echo "Web Application Root: $WEBAPP_ROOT"
echo "Report File: $REPORT_FILE"
echo ""

# 1. Check if NGINX is installed and config directory exists
print_header "NGINX Installation Check"

if [ ! -d "$NGINX_CONFIG_DIR" ]; then
    print_error "NGINX configuration directory '$NGINX_CONFIG_DIR' does not exist."
    print_info "NGINX may not be installed or using non-standard configuration location."
    exit 1
else
    print_info "NGINX configuration directory found: $NGINX_CONFIG_DIR"
fi

# 2. Test NGINX configuration syntax
print_header "NGINX Configuration Syntax Check"

NGINX_BIN="${NGINX_BIN:-$(command -v nginx || true)}"

if [ -n "$NGINX_BIN" ]; then
    if run_with_sudo "$NGINX_BIN" -t 2>&1 | grep -q "syntax is ok"; then
        print_info "NGINX configuration syntax is valid"
    else
        print_error "NGINX configuration syntax errors detected:"
        run_with_sudo "$NGINX_BIN" -t 2>&1 | grep -v "syntax is ok" || true
    fi
else
    print_warning "nginx command not found in PATH (cannot test configuration syntax)"
fi

# 3. Check for enabled site configurations
print_header "Enabled Site Configurations"

if [ -d "$NGINX_SITES_ENABLED" ]; then
    enabled_sites=$(find "$NGINX_SITES_ENABLED" -type f -name "*.conf" -o -name "*" ! -name "default" 2>/dev/null | wc -l)
    print_info "Found $enabled_sites enabled site configuration(s)"
    
    # List enabled sites
    find "$NGINX_SITES_ENABLED" -type f \( -name "*.conf" -o ! -name "default" \) 2>/dev/null | while read -r config_file; do
        echo "  - $(basename "$config_file")"
    done
else
    print_warning "sites-enabled directory not found: $NGINX_SITES_ENABLED"
fi

# 4. Analyze server blocks and application paths
print_header "Server Block and Path Analysis"

# Find all NGINX configuration files
config_files=$(find "$NGINX_CONFIG_DIR" -name "*.conf" -type f 2>/dev/null)

if [ -z "$config_files" ]; then
    print_warning "No .conf files found in $NGINX_CONFIG_DIR"
else
    echo "$config_files" | while read -r config_file; do
        print_detail "Analyzing: $config_file"
        
        # Check for server blocks
        server_blocks=$(grep -c "^[[:space:]]*server[[:space:]]*{" "$config_file" 2>/dev/null || echo "0")
        if [ "$server_blocks" -gt 0 ]; then
            print_info "Found $server_blocks server block(s) in $config_file"
        fi
        
        # Check for root directives pointing to webapp directory
        if grep -q "root[[:space:]]*$WEBAPP_ROOT" "$config_file" 2>/dev/null; then
            print_info "Found root directive pointing to $WEBAPP_ROOT in $config_file"
            
            # Extract the root path
            root_path=$(grep "root[[:space:]]*$WEBAPP_ROOT" "$config_file" 2>/dev/null | head -1 | awk '{print $2}' | tr -d ';')
            
            # Check if the path exists
            if [ -d "$root_path" ]; then
                print_info "Root path exists: $root_path"
            else
                print_error "Root path does not exist: $root_path (configured in $config_file)"
            fi
        fi
        
        # Check for proxy_pass directives (Gunicorn)
        if grep -q "proxy_pass" "$config_file" 2>/dev/null; then
            print_info "Found proxy_pass directive(s) in $config_file (likely Gunicorn configuration)"
            
            # Extract proxy_pass URLs
            grep "proxy_pass" "$config_file" 2>/dev/null | while read -r line; do
                proxy_url=$(echo "$line" | awk '{print $2}' | tr -d ';')
                print_detail "  Proxy target: $proxy_url"
            done
        fi
        
        # Check for static file serving
        if grep -qE "(location[[:space:]]+/(static|media|assets))" "$config_file" 2>/dev/null; then
            print_info "Found static file location block(s) in $config_file"
        fi
    done
fi

# 5. Security checks
print_header "Security Configuration Checks"

# Check all config files for security-related settings
echo "$config_files" | while read -r config_file; do
    # Check for server_tokens (should be off in production)
    if grep -q "server_tokens" "$config_file" 2>/dev/null; then
        if grep "server_tokens[[:space:]]*on" "$config_file" >/dev/null 2>&1; then
            print_warning "server_tokens is ON in $config_file (should be OFF in production)"
        fi
    else
        print_warning "server_tokens directive not found in $config_file (defaults to ON)"
    fi
    
    # Check for HTTP (should redirect to HTTPS in production)
    if grep -qE "listen[[:space:]]+80" "$config_file" 2>/dev/null && ! grep -qE "return[[:space:]]+301" "$config_file" 2>/dev/null; then
        print_warning "HTTP (port 80) listener found without redirect to HTTPS in $config_file"
    fi
    
    # Check for SSL configuration
    if grep -qE "listen[[:space:]]+443" "$config_file" 2>/dev/null; then
        print_info "HTTPS (port 443) listener found in $config_file"
        
        # Check for SSL certificate paths
        if grep -q "ssl_certificate" "$config_file" 2>/dev/null; then
            cert_path=$(grep "ssl_certificate[[:space:]]" "$config_file" 2>/dev/null | head -1 | awk '{print $2}' | tr -d ';')
            if [ -f "$cert_path" ]; then
                print_info "SSL certificate file exists: $cert_path"
            else
                print_error "SSL certificate file not found: $cert_path (configured in $config_file)"
            fi
        fi
    fi
    
    # Check for access logs
    if ! grep -q "access_log" "$config_file" 2>/dev/null; then
        print_warning "No access_log directive found in $config_file (logging may be disabled)"
    fi
    
    # Check for error logs
    if ! grep -q "error_log" "$config_file" 2>/dev/null; then
        print_warning "No error_log directive found in $config_file (error logging may be disabled)"
    fi
done

# 6. Check for Gunicorn socket/port alignment
print_header "Gunicorn Integration Check"

# Look for upstream or proxy_pass configurations that might reference Gunicorn
echo "$config_files" | while read -r config_file; do
    # Check for upstream blocks (common for Gunicorn)
    if grep -q "^[[:space:]]*upstream" "$config_file" 2>/dev/null; then
        print_info "Found upstream block(s) in $config_file"
        grep -A 5 "^[[:space:]]*upstream" "$config_file" 2>/dev/null | while read -r line; do
            if echo "$line" | grep -qE "(server|unix:)" 2>/dev/null; then
                print_detail "  $line"
            fi
        done
    fi
    
    # Check for unix socket references
    if grep -qE "unix:" "$config_file" 2>/dev/null; then
        socket_path=$(grep "unix:" "$config_file" 2>/dev/null | head -1 | awk '{print $2}' | tr -d ';' | tr -d '"')
        print_info "Unix socket reference found: $socket_path"
        
        if [ -S "$socket_path" ]; then
            print_info "Unix socket exists: $socket_path"
        else
            print_warning "Unix socket does not exist: $socket_path (Gunicorn may not be running or misconfigured)"
        fi
    fi
    
    # Check for localhost port references (common Gunicorn setup)
    if grep -qE "proxy_pass.*127\.0\.0\.1:[0-9]+" "$config_file" 2>/dev/null || grep -qE "proxy_pass.*localhost:[0-9]+" "$config_file" 2>/dev/null; then
        port=$(grep -oE "127\.0\.0\.1:[0-9]+|localhost:[0-9]+" "$config_file" 2>/dev/null | head -1 | cut -d: -f2)
        print_info "Localhost port reference found: $port"
        print_detail "Verify this matches Gunicorn configuration"
    fi
done

# 7. Check file permissions on config files
print_header "Configuration File Permissions"

find "$NGINX_CONFIG_DIR" -name "*.conf" -type f 2>/dev/null | while read -r config_file; do
    perms=$(stat -c "%a" "$config_file" 2>/dev/null || stat -f "%OLp" "$config_file" 2>/dev/null || echo "unknown")
    owner=$(stat -c "%U" "$config_file" 2>/dev/null || stat -f "%Su" "$config_file" 2>/dev/null || echo "unknown")
    
    # Config files should typically be readable by owner/group only (640 or 644)
    if [ "$perms" != "unknown" ] && [ "${perms: -1}" -ge 4 ]; then
        print_warning "Configuration file may be world-readable: $config_file (perms: $perms, owner: $owner)"
    fi
done

# 8. Summary
print_header "Summary"

echo "NGINX configuration audit complete."
echo "Review the findings above and ensure:"
echo "  - All paths point to existing directories"
echo "  - Gunicorn socket/port matches NGINX proxy configuration"
echo "  - Security best practices are followed (HTTPS, server_tokens off, etc.)"
echo "  - Logging is properly configured"
echo ""

echo "=== AUDIT COMPLETE ==="
