#!/bin/bash
#
# audit_permissions.sh
#
# Purpose:
#   Audits file and directory ownership and permissions for the Flask application
#   deployment under /srv/webapps/platform. This script identifies potential security issues
#   and misconfigurations related to file permissions and ownership.
#
# Usage:
#   ./audit_permissions.sh
#
# Output:
#   Prints a detailed report of ownership and permission issues to stdout.
#
# Exit Codes:
#   0 - Script completed successfully
#   1 - Critical errors encountered (e.g., /srv/webapps/platform does not exist)
#
# Dependencies:
#   Standard POSIX tools: find, stat, ls, awk, grep
#
# Notes:
#   - This script does NOT modify any files or permissions
#   - All findings are reported for manual review
#   - Run with appropriate privileges to read all directories

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/docs}"
REPORT_FILE="${REPORT_FILE:-$LOG_DIR/audit_permissions_$(date +%Y%m%d_%H%M%S).log}"

mkdir -p "$LOG_DIR"
exec > >(tee "$REPORT_FILE") 2>&1

# Color codes for output (if terminal supports it)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Configuration
WEBAPP_ROOT="${WEBAPP_ROOT:-/srv/webapps/platform}"
REPORT_HEADER="=== FILE PERMISSIONS AND OWNERSHIP AUDIT ==="

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

# Check if webapp root exists
if [ ! -d "$WEBAPP_ROOT" ]; then
    print_error "Web application root directory '$WEBAPP_ROOT' does not exist."
    exit 1
fi

echo "$REPORT_HEADER"
echo "Audit Date: $(date)"
echo "Target Directory: $WEBAPP_ROOT"
echo "Report File: $REPORT_FILE"
echo ""

# 1. Check overall directory ownership
print_header "Directory Ownership Analysis"
echo "Checking ownership of $WEBAPP_ROOT and subdirectories..."
echo ""

# Find all directories and check ownership
find "$WEBAPP_ROOT" -type d -exec ls -ld {} \; 2>/dev/null | while read -r line; do
    dir=$(echo "$line" | awk '{print $NF}')
    owner=$(echo "$line" | awk '{print $3}')
    group=$(echo "$line" | awk '{print $4}')
    perms=$(echo "$line" | awk '{print $1}')
    
    # Check for world-writable directories (security risk)
    if echo "$perms" | grep -q '...w..w..w.'; then
        print_warning "World-writable directory: $dir (owner: $owner, group: $group, perms: $perms)"
    fi
    
    # Check for directories owned by root (may indicate deployment issues)
    if [ "$owner" = "root" ]; then
        print_warning "Directory owned by root: $dir (should typically be owned by application user)"
    fi
done

# 2. Check file ownership and permissions
print_header "File Ownership and Permissions Analysis"
echo "Scanning files in $WEBAPP_ROOT..."
echo ""

# Find all files and check ownership/permissions
find "$WEBAPP_ROOT" -type f -exec ls -l {} \; 2>/dev/null | while read -r line; do
    file=$(echo "$line" | awk '{print $NF}')
    owner=$(echo "$line" | awk '{print $3}')
    group=$(echo "$line" | awk '{print $4}')
    perms=$(echo "$line" | awk '{print $1}')
    
    # Check for world-writable files (critical security risk)
    if echo "$perms" | grep -q '...w..w..w.'; then
        print_error "World-writable file: $file (owner: $owner, group: $group, perms: $perms)"
    fi
    
    # Check for files owned by root
    if [ "$owner" = "root" ]; then
        print_warning "File owned by root: $file (should typically be owned by application user)"
    fi
    
    # Check for executable files (may indicate scripts or binaries)
    if echo "$perms" | grep -q 'x'; then
        # Python files should be executable, but check others
        if ! echo "$file" | grep -qE '\.(py|sh)$'; then
            print_info "Executable file found: $file (owner: $owner, perms: $perms)"
        fi
    fi
done

# 3. Check for sensitive files with incorrect permissions
print_header "Sensitive Files Check"
echo "Checking for configuration files, secrets, and sensitive data..."
echo ""

# Common sensitive file patterns
SENSITIVE_PATTERNS=(
    "*.key"
    "*.pem"
    "*.crt"
    "*.env"
    "*.secret"
    "config.py"
    "settings.py"
    ".env"
    "secrets.json"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    find "$WEBAPP_ROOT" -name "$pattern" -type f 2>/dev/null | while read -r file; do
        perms=$(stat -c "%a" "$file" 2>/dev/null || stat -f "%OLp" "$file" 2>/dev/null || echo "unknown")
        owner=$(stat -c "%U" "$file" 2>/dev/null || stat -f "%Su" "$file" 2>/dev/null || echo "unknown")
        
        # Check if file is readable by others (should typically be 600 or 640)
        if [ "$perms" != "unknown" ] && [ "${perms: -1}" -ge 4 ]; then
            print_warning "Sensitive file may be readable by others: $file (perms: $perms, owner: $owner)"
        fi
    done
done

# 4. Check for files with setuid/setgid bits
print_header "SetUID/SetGID Bit Check"
echo "Checking for files with setuid or setgid bits set..."
echo ""

find "$WEBAPP_ROOT" -type f \( -perm -4000 -o -perm -2000 \) -exec ls -l {} \; 2>/dev/null | while read -r line; do
    file=$(echo "$line" | awk '{print $NF}')
    perms=$(echo "$line" | awk '{print $1}')
    print_warning "File with setuid/setgid bit: $file (perms: $perms)"
done

# 5. Summary statistics
print_header "Summary Statistics"
echo "Collecting summary statistics..."
echo ""

total_files=$(find "$WEBAPP_ROOT" -type f 2>/dev/null | wc -l)
total_dirs=$(find "$WEBAPP_ROOT" -type d 2>/dev/null | wc -l)
root_owned_files=$(find "$WEBAPP_ROOT" -type f -user root 2>/dev/null | wc -l)
root_owned_dirs=$(find "$WEBAPP_ROOT" -type d -user root 2>/dev/null | wc -l)

echo "Total files: $total_files"
echo "Total directories: $total_dirs"
echo "Files owned by root: $root_owned_files"
echo "Directories owned by root: $root_owned_dirs"
echo ""

# 6. Check expected application structure
print_header "Application Structure Check"
echo "Verifying expected Flask application structure..."
echo ""

# Check for common Flask application files
if [ -f "$WEBAPP_ROOT/app.py" ] || [ -f "$WEBAPP_ROOT/application.py" ] || [ -f "$WEBAPP_ROOT/wsgi.py" ]; then
    print_info "Flask application entry point found"
else
    print_warning "No standard Flask entry point found (app.py, application.py, or wsgi.py)"
fi

# Check for requirements.txt or similar
if [ -f "$WEBAPP_ROOT/requirements.txt" ] || [ -f "$WEBAPP_ROOT/Pipfile" ]; then
    print_info "Python dependencies file found"
else
    print_warning "No Python dependencies file found (requirements.txt or Pipfile)"
fi

# Check for virtual environment
if [ -d "$WEBAPP_ROOT/venv" ] || [ -d "$WEBAPP_ROOT/.venv" ] || [ -d "$WEBAPP_ROOT/env" ]; then
    print_info "Virtual environment directory found"
else
    print_warning "No virtual environment directory found (venv, .venv, or env)"
fi

echo ""
echo "=== AUDIT COMPLETE ==="
echo "Review the findings above and address any security concerns manually."
