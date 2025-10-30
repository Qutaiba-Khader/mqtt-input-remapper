# MQTT Input Remapper

A cross-platform Linux service with a local Web UI that captures input events from USB and Bluetooth HID devices (keyboards, mice, remotes), allows remapping each key to custom text strings, and publishes the results to an MQTT broker.

## Features

- ✅ **USB HID Device Support** - Keyboards, mice, remotes, and other HID devices
- ✅ **Bluetooth HID Support** - Full Bluetooth device management (scan, pair, connect)
- ✅ **Per-Device Key Remapping** - Map each key to custom MQTT message text
- ✅ **Exclusive Grab** - Block original key events from reaching the OS
- ✅ **Web-Based UI** - Modern, responsive interface accessible from any browser
- ✅ **MQTT Publishing** - Send remapped keys as JSON messages to MQTT broker
- ✅ **Master Toggle** - Global enable/disable for all remapping
- ✅ **Per-Device Toggle** - Enable/disable remapping for specific devices
- ✅ **Ignored Keys** - Define keys to skip (useful for noisy repeated keys)
- ✅ **Configuration Persistence** - All settings saved and restored on boot
- ✅ **Auto-Start** - Runs as systemd service, starts on boot
- ✅ **Real-Time Logs** - View system logs and debug information
- ✅ **Backup & Restore** - Export/import full configuration as JSON

## Supported Platforms

- Debian 12 (Bookworm)
- Debian 13 (Trixie)
- Ubuntu 22.04 LTS and newer
- Raspberry Pi OS Lite (Bookworm & Trixie)
- Works on VMs (Proxmox, VirtualBox, etc.)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Qutaiba-Khader/mqtt-input-remapper.git
cd mqtt-input-remapper

# Run installation script (requires root)
sudo bash scripts/install.sh
```

The installation script will:
1. Install system dependencies (Python, BlueZ, DBus)
2. Install Python packages
3. Create configuration directory
4. Install and enable systemd service
5. Start the service

### Access the Web UI

After installation, access the web interface:

```
http://localhost:8080
```

Or from another device on your network:

```
http://<your-device-ip>:8080
```

## Configuration

### MQTT Settings

Default MQTT configuration (editable in Web UI):

```json
{
  "broker": "192.168.1.160",
  "port": 1883,
  "username": "mqttuser",
  "password": "mqttuser",
  "topic": "key_remap/events"
}
```

### MQTT Message Format

When a mapped key is pressed, the service publishes a JSON message:

```json
{
  "device_name": "Logitech Keyboard",
  "pressed_key": "Turn-on-lights"
}
```

- `device_name`: The name of the device that triggered the event
- `pressed_key`: The custom text string you configured for that key

## Usage Guide

### 1. Add a Device to Remapped Collection

1. Go to **Devices** page
2. Find your device in the list (USB or Bluetooth)
3. Click **"Add to Remapped"**
4. Enable the device with the toggle switch

### 2. Configure Key Mappings

1. Go to **Mappings** page
2. Select your device from the dropdown
3. For each key you want to remap:
   - Enter the text to send to MQTT in the input box
   - Leave empty to ignore that key
4. Click **"Save Mappings"**

### 3. Test Your Configuration

1. Ensure MQTT broker is running and accessible
2. Go to **MQTT Settings** and click **"Test Connection"**
3. Press keys on your remapped device
4. Check **Logs** page to verify MQTT messages are being sent

### 4. Using with Home Automation

Example Node-RED flow to receive messages:

```json
[
    {
        "id": "mqtt-in",
        "type": "mqtt in",
        "topic": "key_remap/events",
        "broker": "your-mqtt-broker",
        "name": "Key Remapper"
    }
]
```

Example Home Assistant automation:

```yaml
automation:
  - alias: "Handle Remote Button"
    trigger:
      platform: mqtt
      topic: "key_remap/events"
    condition:
      condition: template
      value_template: "{{ trigger.payload_json.pressed_key == 'Turn-on-lights' }}"
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room
```

## Web UI Pages

### Dashboard
- System status overview
- MQTT connection status
- Active device count
- Recent activity log

### Devices
- List all USB and Bluetooth devices
- Add/remove devices from remapped collection
- Enable/disable per-device remapping
- Bluetooth: scan, pair, connect, disconnect

### Mappings
- Configure key-to-text mappings
- Set ignored keys per device
- Real-time mapping updates

### MQTT Settings
- Configure broker connection
- Test MQTT connectivity
- Update credentials and topic

### Logs
- Real-time system logs
- Filter by log level (INFO, WARNING, ERROR, DEBUG)
- Clear log buffer

### Settings
- Export configuration as JSON
- Import configuration from backup
- About and version information

## Service Management

### Check Status

```bash
sudo systemctl status mqtt-remapper
```

### Start/Stop/Restart

```bash
sudo systemctl start mqtt-remapper
sudo systemctl stop mqtt-remapper
sudo systemctl restart mqtt-remapper
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u mqtt-remapper -f

# Last 100 lines
sudo journalctl -u mqtt-remapper -n 100
```

### Enable/Disable Auto-Start

```bash
sudo systemctl enable mqtt-remapper   # Enable auto-start
sudo systemctl disable mqtt-remapper  # Disable auto-start
```

## Configuration Files

### Main Configuration

Location: `/etc/mqtt-remapper/config.json`

This file contains:
- MQTT broker settings
- Service configuration
- Device list and mappings
- Ignored keys per device
- Master enable state

### Manual Configuration

You can manually edit `/etc/mqtt-remapper/config.json` and restart the service:

```bash
sudo systemctl restart mqtt-remapper
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status mqtt-remapper

# Check detailed logs
sudo journalctl -u mqtt-remapper -n 50

# Verify Python packages installed
pip3 list | grep -E 'fastapi|uvicorn|paho-mqtt|evdev|pydbus'
```

### MQTT Connection Issues

1. Verify broker is running: `mosquitto_sub -h <broker> -t test`
2. Check firewall: `sudo ufw allow 1883`
3. Test connection in Web UI: MQTT Settings → Test Connection

### Device Not Detected

```bash
# List input devices
ls -la /dev/input/

# Check permissions
sudo usermod -a -G input root

# For Bluetooth devices
sudo systemctl status bluetooth
bluetoothctl
```

### Keys Not Being Remapped

1. Verify device is in "Remapped Devices" collection
2. Check device toggle is enabled
3. Ensure Master toggle is ON
4. Check mappings are saved
5. View logs for key events

### Bluetooth Issues

```bash
# Ensure BlueZ is running
sudo systemctl status bluetooth

# Start BlueZ if not running
sudo systemctl start bluetooth

# Check Bluetooth adapter
bluetoothctl list
```

## Uninstallation

```bash
cd mqtt-input-remapper
sudo bash scripts/uninstall.sh
```

This will:
- Stop and disable the service
- Remove service files
- Delete installation directory

Configuration in `/etc/mqtt-remapper/` is preserved. To remove it:

```bash
sudo rm -rf /etc/mqtt-remapper
```

## Development

### Project Structure

```
mqtt-input-remapper/
├── backend/                 # Python backend
│   ├── main.py             # FastAPI application
│   ├── config.py           # Configuration management
│   ├── mqtt_client.py      # MQTT client
│   ├── device_manager.py   # Device detection
│   ├── bluetooth_manager.py # Bluetooth management
│   ├── input_capture.py    # Input event capture
│   └── logger.py           # Logging system
├── frontend/               # Web UI
│   ├── index.html          # Dashboard
│   ├── devices.html        # Device management
│   ├── mappings.html       # Key mappings
│   ├── mqtt.html           # MQTT settings
│   ├── logs.html           # Log viewer
│   ├── settings.html       # Settings & backup
│   └── static/
│       ├── css/style.css   # Styles
│       └── js/
│           ├── api.js      # API client
│           └── app.js      # App utilities
├── systemd/
│   └── mqtt-remapper.service # Systemd service
├── scripts/
│   ├── install.sh          # Installation script
│   └── uninstall.sh        # Uninstallation script
├── config/
│   └── default_config.json # Default configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Running in Development Mode

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run directly (not as service)
cd mqtt-input-remapper
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

### API Documentation

Once running, access the auto-generated API docs at:

```
http://localhost:8080/docs
```

## Security Considerations

- Web UI binds to `0.0.0.0` by default (accessible on LAN)
- No authentication required (designed for local network use)
- All data stored locally, no external telemetry
- MQTT credentials stored in plaintext in config file
- Service runs as root (required for device access)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on Debian/Ubuntu/Raspberry Pi
5. Submit a pull request

## Support

For issues, questions, or feature requests:

- Create an issue on GitHub
- Check the troubleshooting section above
- Review logs: `sudo journalctl -u mqtt-remapper -f`

## Acknowledgments

- Built with FastAPI, Python evdev, and BlueZ
- Uses Paho MQTT client for reliable messaging
- Inspired by the need for flexible HID device remapping

---

**Version:** 1.0.0  
**Author:** Qutaiba Khader  
**Repository:** https://github.com/Qutaiba-Khader/mqtt-input-remapper
