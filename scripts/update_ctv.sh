# pull latest from GitHub
#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

git pull --ff-only

# Grant execute permissions to the script:
  # chmod +x update_ctv.sh
# Add the script's directory to the system's PATH environment variable by adding the following line to your shell's configuration file:
  # export PATH=$PATH:/aws/aws/GH-aws/scripts
