#!/bin/bash
# Builds a self-contained zip for deployment to Raspberry Pi.
# Run from the repository root on your Mac.
#
# Output: rs2-inl-uav-demo.zip
# Transfer to Pi with: scp rs2-inl-uav-demo.zip pi@<pi-ip>:~/
# On Pi: unzip rs2-inl-uav-demo.zip && cd rs2-inl-uav-demo && bash setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STAGING="$SCRIPT_DIR/_staging/rs2-inl-uav-demo"
ZIP_OUT="$SCRIPT_DIR/rs2-inl-uav-demo.zip"

echo "Building Pi deployment package..."

# Clean staging
rm -rf "$STAGING"
mkdir -p "$STAGING/logs"

# Copy demo scripts
cp "$SCRIPT_DIR/audit_log.py"      "$STAGING/"
cp "$SCRIPT_DIR/drone_agent.py"    "$STAGING/"
cp "$SCRIPT_DIR/ground_station.py" "$STAGING/"
cp "$SCRIPT_DIR/demo_local.py"     "$STAGING/"
cp "$SCRIPT_DIR/setup.sh"          "$STAGING/"
cp "$SCRIPT_DIR/README.md"         "$STAGING/"

# Copy the bundled RS2 engine (identity + revocation constructors)
cp -r "$SCRIPT_DIR/rs2"            "$STAGING/"

# Touch placeholder for logs dir
touch "$STAGING/logs/.keep"

# Zip
cd "$SCRIPT_DIR/_staging"
zip -r "$ZIP_OUT" rs2-inl-uav-demo/ -x "*.pyc" -x "*/__pycache__/*"
cd "$SCRIPT_DIR"

# Cleanup staging
rm -rf "$SCRIPT_DIR/_staging"

echo ""
echo "Package built: $ZIP_OUT"
echo ""
echo "Deploy to Pi:"
echo "  scp rs2-inl-uav-demo.zip pi@<pi-ip>:~/"
echo "  ssh pi@<pi-ip>"
echo "  unzip rs2-inl-uav-demo.zip"
echo "  cd rs2-inl-uav-demo"
echo "  nano drone_config.json    # set drone_id"
echo "  bash setup.sh"
echo "  python3 drone_agent.py"
