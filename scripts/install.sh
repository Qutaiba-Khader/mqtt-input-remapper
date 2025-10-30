#!/bin/bash
# MQTT Input Remapper Installation Script

set -e

echo "================================"
echo "MQTT Input Remapper Installer"
echo "================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root (use sudo)"
   exit 1
fi

echo "[1/7] Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv bluez python3-dbus python3-gi gir1.2-glib-2.0 \
    pkg-config libcairo2-dev libgirepository1.0-dev gcc python3-dev

echo "[2/7] Creating installation directory..."
mkdir -p /opt/mqtt-remapper
cp -r . /opt/mqtt-remapper/
cd /opt/mqtt-remapper

echo "[3/7] Installing Python dependencies..."
pip3 install --break-system-packages -r requirements.txt

echo "[4/7] Creating configuration directory..."
mkdir -p /etc/mqtt-remapper
if [ ! -f /etc/mqtt-remapper/config.json ]; then
    cp config/default_config.json /etc/mqtt-remapper/config.json
    echo "Default configuration installed"
fi

echo "[5/7] Installing systemd service..."
cp systemd/mqtt-remapper.service /etc/systemd/system/
systemctl daemon-reload

echo "[6/7] Enabling service..."
systemctl enable mqtt-remapper.service

echo "[7/7] Starting service..."
systemctl start mqtt-remapper.service

echo ""
echo "================================"
echo "Installation Complete!"
echo "================================"
echo ""
echo "Service Status:"
systemctl status mqtt-remapper.service --no-pager || true
echo ""
echo "Access the web interface at:"
echo "  http://localhost:8080"
echo "  or http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status mqtt-remapper   # Check status"
echo "  sudo systemctl restart mqtt-remapper  # Restart service"
echo "  sudo systemctl stop mqtt-remapper     # Stop service"
echo "  sudo journalctl -u mqtt-remapper -f   # View logs"
echo ""
