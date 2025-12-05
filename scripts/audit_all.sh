#!/bin/bash
#
# audit_all.sh
#
# Purpose:
#   Master script that runs all audit scripts in sequence and generates
#   a comprehensive system audit report. This provides a unified view
#   of the entire system configuration and security posture.
#
# Usage:
#   ./audit_all.sh [output_file]
#
# Arguments:
#   output_file (optional) - Path to save the audit report. If not provided,
#                            output is sent to stdout.
#
# Output:
#   Comprehensive audit report combining results from all individual audit scripts.
#
# Exit Codes:
#   0 - All audits completed successfully
#   1 - One or more audits failed
#
# Dependencies:
#   - audit_permissions.sh
#   - audit_nginx_config.sh
#   - audit_services.sh
#   All scripts must be in the same directory as this script.
#
# Notes:
#   - This script does NOT modify any system files
#   - May require sudo privileges for some audit checks
#   - Run from the scripts directory or ensure audit scripts are in PATH
#   - All individual audit scripts are executed in sequence

set -euo pipefail

# Color codes for output (if terminal supports it)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Audit script names
AUDIT_PERMISSIONS="$SCRIPT_DIR/audit_permissions.sh"
AUDIT_NGINX="$SCRIPT_DIR/audit_nginx_config.sh"
AUDIT_SERVICES="$SCRIPT_DIR/audit_services.sh"

# Output file (if provided)
OUTPUT_FILE="${1:-}"

# Function to print section headers
print_header() {
    echo ""
    echo "============================================================"
    echo -e "${BOLD}$1${NC}"
    echo "============================================================"
}

# Function to print errors
print_error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
}

# Function to print info
print_info() {
    echo -e "${GREEN}INFO:${NC} $1"
}

# Function to run an audit script and capture output
run_audit() {
    local script_name="$1"
    local script_path="$2"
    local audit_name="$3"
    
    print_header "Running: $audit_name"
    
    if [ ! -f "$script_path" ]; then
        print_error "Audit script not found: $script_path"
        return 1
    fi
    
    if [ ! -x "$script_path" ]; then
        print_error "Audit script is not executable: $script_path"
        print_info "Attempting to make it executable..."
        chmod +x "$script_path" || {
            print_error "Failed to make script executable"
            return 1
        }
    fi
    
    # Run the audit script
    if "$script_path"; then
        print_info "$audit_name completed successfully"
        return 0
    else
        print_error "$audit_name failed with exit code $?"
        return 1
    fi
}

# Main execution function
main() {
    local exit_code=0
    local start_time=$(date +%s)
    
    # Print master header
    echo ""
    echo "============================================================"
    echo -e "${BOLD}COMPREHENSIVE SYSTEM AUDIT REPORT${NC}"
    echo "============================================================"
    echo "Audit Start Time: $(date)"
    echo "Hostname: $(hostname 2>/dev/null || echo 'unknown')"
    echo "User: $(whoami)"
    echo "Script Directory: $SCRIPT_DIR"
    echo ""
    
    # Redirect output to file if specified
    if [ -n "$OUTPUT_FILE" ]; then
        print_info "Saving audit report to: $OUTPUT_FILE"
        exec > >(tee "$OUTPUT_FILE")
        exec 2>&1
    fi
    
    # Run individual audits
    print_header "AUDIT EXECUTION SUMMARY"
    echo "This comprehensive audit will check:"
    echo "  1. File permissions and ownership"
    echo "  2. NGINX configuration alignment"
    echo "  3. Systemd service configurations"
    echo ""
    
    # 1. Permissions audit
    if ! run_audit "audit_permissions.sh" "$AUDIT_PERMISSIONS" "File Permissions Audit"; then
        exit_code=1
    fi
    
    # 2. NGINX configuration audit
    if ! run_audit "audit_nginx_config.sh" "$AUDIT_NGINX" "NGINX Configuration Audit"; then
        exit_code=1
    fi
    
    # 3. Services audit
    if ! run_audit "audit_services.sh" "$AUDIT_SERVICES" "Systemd Services Audit"; then
        exit_code=1
    fi
    
    # Final summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_header "AUDIT SUMMARY"
    echo "Audit End Time: $(date)"
    echo "Total Duration: ${duration} second(s)"
    echo ""
    
    if [ $exit_code -eq 0 ]; then
        print_info "All audits completed successfully"
    else
        print_error "One or more audits encountered errors (see details above)"
    fi
    
    echo ""
    echo "============================================================"
    echo -e "${BOLD}RECOMMENDATIONS${NC}"
    echo "============================================================"
    echo "1. Review all WARNING and ERROR messages above"
    echo "2. Verify file ownership matches application user (not root)"
    echo "3. Ensure NGINX configuration paths match actual deployment"
    echo "4. Confirm Gunicorn socket/port matches NGINX proxy settings"
    echo "5. Verify systemd services are enabled and running"
    echo "6. Check that sensitive files have restrictive permissions (600 or 640)"
    echo "7. Ensure HTTPS is properly configured in NGINX"
    echo "8. Verify service dependencies are correctly set"
    echo ""
    
    if [ -n "$OUTPUT_FILE" ]; then
        print_info "Full audit report saved to: $OUTPUT_FILE"
    fi
    
    echo "============================================================"
    echo -e "${BOLD}AUDIT COMPLETE${NC}"
    echo "============================================================"
    
    return $exit_code
}

# Execute main function
main "$@"
