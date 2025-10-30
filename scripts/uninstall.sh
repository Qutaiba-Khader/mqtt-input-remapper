#!/bin/bash
# MQTT Input Remapper Uninstallation Script

set -e

echo "Uninstalling MQTT Input Remapper..."

if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root (use sudo)"
   exit 1
fi

echo "[1/4] Stopping service..."
systemctl stop mqtt-remapper.service || true

echo "[2/4] Disabling service..."
systemctl disable mqtt-remapper.service || true

echo "[3/4] Removing service file..."
rm -f /etc/systemd/system/mqtt-remapper.service
systemctl daemon-reload

echo "[4/4] Removing installation..."
rm -rf /opt/mqtt-remapper

echo ""
echo "Uninstallation complete!"
echo ""
echo "Configuration preserved in /etc/mqtt-remapper/"
echo "To remove config: sudo rm -rf /etc/mqtt-remapper"
echo ""
