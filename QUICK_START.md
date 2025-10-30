# 🚀 MQTT Input Remapper - Quick Start Guide

## 📥 What You Have

✅ **mqtt-input-remapper.zip** - Complete working application (37KB)
✅ **PROJECT_SUMMARY.md** - Detailed project overview
✅ **GITHUB_PUSH_INSTRUCTIONS.md** - How to upload to GitHub
✅ **PROJECT_STRUCTURE.txt** - File structure reference
✅ **QUICK_START.md** - This guide

---

## ⚡ Fast Installation (3 minutes)

### Step 1: Download and Extract
```bash
# Download the zip file from this conversation
# Then extract it:
unzip mqtt-input-remapper.zip
cd mqtt-input-remapper
```

### Step 2: Install
```bash
# Run the automated installer (requires root)
sudo bash scripts/install.sh
```

That's it! The installer will:
- Install all dependencies
- Set up the systemd service
- Start the application automatically

### Step 3: Access the Web UI
Open your browser and go to:
```
http://localhost:8080
```

Or from another device:
```
http://YOUR_DEVICE_IP:8080
```

---

## 🎯 First Time Setup (5 minutes)

### 1. Configure MQTT Broker

1. Click **"MQTT Settings"** in the navigation
2. Enter your MQTT broker details:
   - Broker: `192.168.1.160` (or your broker IP)
   - Port: `1883`
   - Username: `mqttuser`
   - Password: `mqttuser`
   - Topic: `key_remap/events`
3. Click **"Test Connection"** to verify
4. Click **"Save Settings"**

### 2. Add Your First Device

1. Click **"Devices"** in the navigation
2. Find your keyboard/remote in the **USB Devices** or **Bluetooth Devices** list
3. Click **"Add to Remapped"**
4. Toggle the switch to **enable** the device

### 3. Configure Key Mappings

1. Click **"Mappings"** in the navigation
2. Select your device from the dropdown
3. For each key you want to use:
   - Type the text to send to MQTT (e.g., "Turn-on-lights")
   - Leave blank to ignore that key
4. Click **"Save Mappings"**

### 4. Test It!

1. Click **"Logs"** to see real-time activity
2. Press a key on your remapped device
3. You should see:
   - Log entry showing the key was detected
   - Log entry showing MQTT message was sent
4. Check your MQTT broker to confirm messages arrive

---

## 🔥 Common Use Cases

### Home Automation Remote
```
KEY_POWER → "lights-off"
KEY_VOLUMEUP → "volume-up"
KEY_VOLUMEDOWN → "volume-down"
KEY_MUTE → "mute-audio"
KEY_PLAYPAUSE → "play-pause-media"
```

### Desk Control Pad
```
KEY_F13 → "standing-desk-up"
KEY_F14 → "standing-desk-down"
KEY_F15 → "toggle-monitor"
KEY_F16 → "focus-mode"
```

### Custom Keyboard Shortcuts
```
KEY_MACRO1 → "trigger-automation-1"
KEY_MACRO2 → "trigger-automation-2"
KEY_MACRO3 → "trigger-automation-3"
```

---

## 📱 Using with Home Assistant

### Subscribe to Messages

Add to your `configuration.yaml`:
```yaml
mqtt:
  sensor:
    - name: "Remote Command"
      state_topic: "key_remap/events"
      value_template: "{{ value_json.pressed_key }}"
```

### Create Automations

```yaml
automation:
  - alias: "Remote Button - Lights On"
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

---

## 🔧 Service Management

### Check Status
```bash
sudo systemctl status mqtt-remapper
```

### View Real-time Logs
```bash
sudo journalctl -u mqtt-remapper -f
```

### Restart Service
```bash
sudo systemctl restart mqtt-remapper
```

### Stop Service
```bash
sudo systemctl stop mqtt-remapper
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u mqtt-remapper -n 50

# Verify Python packages
pip3 list | grep -E 'fastapi|uvicorn|paho-mqtt|evdev'

# Try manual start
cd /opt/mqtt-remapper
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
```

### Can't Connect to MQTT
```bash
# Test broker connection
mosquitto_sub -h YOUR_BROKER_IP -t test -v

# Check firewall
sudo ufw status
sudo ufw allow 1883
```

### Device Not Detected
```bash
# List input devices
ls -la /dev/input/

# Check permissions
sudo usermod -a -G input root

# For Bluetooth
sudo systemctl status bluetooth
bluetoothctl
```

### Keys Not Remapping

1. ✅ Is the device in "Remapped Devices"?
2. ✅ Is the device toggle **enabled**?
3. ✅ Is the **Master Toggle** on?
4. ✅ Are the mappings saved?
5. ✅ Check logs for key events

---

## 🌟 Pro Tips

1. **Start Simple**: Test with one device first
2. **Use Logs**: Keep the logs page open while testing
3. **Backup Config**: Export your configuration regularly
4. **Test MQTT First**: Make sure MQTT works before adding devices
5. **Ignore Noisy Keys**: Add repeating keys to the ignored list

---

## 📚 Full Documentation

For complete documentation, see:
- **README.md** - Comprehensive guide
- **PROJECT_SUMMARY.md** - Project overview
- Web UI - Built-in help tooltips

---

## 🆘 Need Help?

1. Check the **Logs** page in the web UI
2. Run: `sudo journalctl -u mqtt-remapper -f`
3. Review **README.md** troubleshooting section
4. Check GitHub issues (once uploaded)

---

## 📤 Upload to GitHub

The project is ready to push! See **GITHUB_PUSH_INSTRUCTIONS.md** for details.

You'll need to generate a new GitHub Personal Access Token:
1. Go to: https://github.com/settings/tokens
2. Generate new token with `repo` scope
3. Follow instructions in GITHUB_PUSH_INSTRUCTIONS.md

---

## ✅ Next Steps

1. ✅ Download **mqtt-input-remapper.zip**
2. ✅ Extract and run `sudo bash scripts/install.sh`
3. ✅ Access http://localhost:8080
4. ✅ Configure MQTT settings
5. ✅ Add your first device
6. ✅ Configure key mappings
7. ✅ Test with your MQTT broker
8. ✅ Upload to GitHub

---

**Ready to go! Enjoy your MQTT Input Remapper! 🎉**
