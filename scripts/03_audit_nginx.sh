# This is pure read-only — test nginx config and log a report.
#!/bin/bash
#
# Audit nginx configuration and write results into GH-etc/docs/audit.
#
set -euo pipefail

TIMESTAMP=$(date +"%Y%m%dT%H%M%S")
AUDIT_DIR="$HOME/GH-etc/docs/audit"
REPORT_FILE="$AUDIT_DIR/nginx_test_${TIMESTAMP}.txt"

mkdir -p "$AUDIT_DIR"

{
  echo "Nginx configuration test"
  echo "Timestamp: $TIMESTAMP"
  echo "========================================="
  sudo nginx -t
} &> "$REPORT_FILE"

echo "Audit report written to: $REPORT_FILE"

# Make it executable:
    # chmod +x ~/GH-etc/scripts/03_audit_nginx.sh

# Usage:
    # bash ~/GH-etc/scripts/03_audit_nginx.sh
# You’ll get files like docs/audit/nginx_test_20251208T010203.txt that agents can read.
