#!/bin/bash
# RS2 INL UAV Demo — Raspberry Pi Setup
# Run this once on each Pi after unzipping the package.
# Requires: Python 3.8+ (standard on Raspberry Pi OS Bullseye+)

set -e

echo "========================================"
echo "RS2 INL UAV Demo — Pi Setup"
echo "========================================"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Installing Python 3..."
    sudo apt-get update -qq && sudo apt-get install -y python3
fi

PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python $PYVER found."

# Create logs directory
mkdir -p logs
echo "Logs directory ready."

# Check for drone_config.json
if [ ! -f drone_config.json ]; then
    HOSTNAME=$(hostname)
    cat > drone_config.json <<EOF
{
  "drone_id": "$HOSTNAME",
  "governing_authority": "urn:liverion:authority:inl-uav-center",
  "jurisdiction": "US-ID"
}
EOF
    echo "Created drone_config.json with drone_id: $HOSTNAME"
    echo "  Edit drone_config.json to set the correct drone_id before running."
else
    echo "drone_config.json already exists:"
    cat drone_config.json
fi

echo ""
echo "Setup complete."
echo ""
echo "To start the drone agent:"
echo "  python3 drone_agent.py"
echo ""
echo "The agent will listen on port 9200."
echo "Make sure your laptop and this Pi are on the same WiFi network."
