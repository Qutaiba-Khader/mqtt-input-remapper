"""
Device Manager Module
Handles detection and management of USB and Bluetooth HID devices
"""
import logging
import os
import glob
from typing import Dict, List, Optional
import evdev
from evdev import InputDevice, ecodes

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages USB and Bluetooth HID devices"""
    
    def __init__(self):
        """Initialize device manager"""
        self.devices = {}  # device_path: device_info
        self.input_devices = {}  # device_path: evdev.InputDevice
        self.scan_devices()
    
    def scan_devices(self) -> Dict[str, dict]:
        """Scan for all available input devices"""
        logger.info("🔍 Scanning for input devices...")
        devices = {}

        try:
            # Get all input device paths
            all_paths = evdev.list_devices()
            logger.debug(f"Found {len(all_paths)} total input device(s) in /dev/input/")
            device_paths = [evdev.InputDevice(path) for path in all_paths]
            
            for device in device_paths:
                try:
                    # Filter for devices with key capabilities (keyboards, remotes, etc.)
                    capabilities = device.capabilities()
                    
                    # Check if device has key events (EV_KEY)
                    if ecodes.EV_KEY in capabilities:
                        device_info = self._get_device_info(device)

                        # Filter out obvious non-HID devices
                        name_lower = device_info['name'].lower()

                        # Skip pure mouse/touchpad devices (no keyboard keys)
                        skip_patterns = ['touchpad', 'trackpoint', 'mouse pointer', 'pen stylus']
                        should_skip = False

                        for pattern in skip_patterns:
                            if pattern in name_lower:
                                should_skip = True
                                logger.debug(f"Skipping non-keyboard device: {device_info['name']}")
                                break

                        # Check if device has actual keyboard keys (not just BTN_*)
                        if not should_skip:
                            key_caps = capabilities.get(ecodes.EV_KEY, [])
                            has_keyboard_keys = any(k >= ecodes.KEY_ESC and k <= ecodes.KEY_MICMUTE for k in key_caps)

                            if not has_keyboard_keys and len(key_caps) < 10:
                                logger.debug(f"Skipping device with too few keys: {device_info['name']}")
                                should_skip = True

                        if not should_skip:
                            devices[device.path] = device_info
                            logger.info(f"Found device: {device_info['name']} at {device.path}")
                except Exception as e:
                    logger.error(f"Error reading device {device.path}: {e}")
        except Exception as e:
            logger.error(f"✗ Error scanning devices: {e}")

        self.devices = devices
        logger.info(f"✓ Scan complete - found {len(devices)} usable input device(s)")

        if len(devices) == 0:
            logger.warning("⚠ No input devices found. Check permissions (need root or input group)")
        else:
            logger.info("Available devices:")
            for dev in devices.values():
                logger.info(f"  - {dev['name']} ({dev['bustype']}) at {dev['path']}")

        return devices
    
    def _get_device_info(self, device: InputDevice) -> dict:
        """Extract device information"""
        info = {
            "path": device.path,
            "name": device.name,
            "phys": device.phys or "Unknown",
            "uniq": device.uniq or "Unknown",
            "vendor": f"{device.info.vendor:04x}" if device.info.vendor else "0000",
            "product": f"{device.info.product:04x}" if device.info.product else "0000",
            "version": device.info.version,
            "bustype": self._get_bustype_name(device.info.bustype),
            "capabilities": self._format_capabilities(device.capabilities())
        }
        
        # Generate unique device ID
        info["device_id"] = self._generate_device_id(info)
        
        return info
    
    def _generate_device_id(self, device_info: dict) -> str:
        """Generate unique device ID"""
        # Use unique identifier if available, otherwise use name + vendor + product
        if device_info["uniq"] and device_info["uniq"] != "Unknown":
            return f"{device_info['uniq']}"
        else:
            return f"{device_info['name']}_{device_info['vendor']}_{device_info['product']}"
    
    def _get_bustype_name(self, bustype: int) -> str:
        """Get human-readable bus type name"""
        bustypes = {
            0x03: "USB",
            0x05: "Bluetooth",
            0x10: "I2C",
            0x11: "SPI",
            0x19: "Atmel"
        }
        return bustypes.get(bustype, f"Unknown ({bustype})")
    
    def _format_capabilities(self, capabilities: dict) -> dict:
        """Format device capabilities"""
        formatted = {}
        
        if ecodes.EV_KEY in capabilities:
            key_count = len(capabilities[ecodes.EV_KEY])
            formatted["keys"] = key_count
            
            # Get some sample keys
            sample_keys = []
            for key_code in list(capabilities[ecodes.EV_KEY])[:5]:
                try:
                    key_name = ecodes.KEY[key_code]
                    sample_keys.append(key_name)
                except KeyError:
                    sample_keys.append(f"KEY_{key_code}")
            
            formatted["sample_keys"] = sample_keys
        
        return formatted
    
    def get_device_by_id(self, device_id: str) -> Optional[dict]:
        """Get device info by device ID"""
        for device_info in self.devices.values():
            if device_info["device_id"] == device_id:
                return device_info
        return None
    
    def get_device_by_path(self, path: str) -> Optional[dict]:
        """Get device info by path"""
        return self.devices.get(path)
    
    def get_all_devices(self) -> List[dict]:
        """Get list of all devices"""
        return list(self.devices.values())
    
    def get_usb_devices(self) -> List[dict]:
        """Get list of USB devices only"""
        return [dev for dev in self.devices.values() if dev["bustype"] == "USB"]
    
    def get_bluetooth_devices(self) -> List[dict]:
        """Get list of Bluetooth devices only"""
        return [dev for dev in self.devices.values() if dev["bustype"] == "Bluetooth"]
    
    def open_device(self, device_path: str) -> Optional[InputDevice]:
        """Open an input device for reading"""
        try:
            if device_path not in self.input_devices:
                device = InputDevice(device_path)
                self.input_devices[device_path] = device
                logger.info(f"Opened device: {device.name} at {device_path}")
            return self.input_devices[device_path]
        except Exception as e:
            logger.error(f"Error opening device {device_path}: {e}")
            return None
    
    def close_device(self, device_path: str):
        """Close an input device"""
        if device_path in self.input_devices:
            try:
                self.input_devices[device_path].close()
                del self.input_devices[device_path]
                logger.info(f"Closed device: {device_path}")
            except Exception as e:
                logger.error(f"Error closing device {device_path}: {e}")
    
    def grab_device(self, device_path: str) -> bool:
        """Grab exclusive access to device (block events from OS)"""
        device = self.open_device(device_path)
        if device:
            try:
                device.grab()
                logger.info(f"Grabbed exclusive access to device: {device.name}")
                return True
            except Exception as e:
                logger.error(f"Error grabbing device {device_path}: {e}")
                return False
        return False
    
    def ungrab_device(self, device_path: str) -> bool:
        """Release exclusive access to device"""
        if device_path in self.input_devices:
            try:
                self.input_devices[device_path].ungrab()
                logger.info(f"Released device: {device_path}")
                return True
            except Exception as e:
                logger.error(f"Error releasing device {device_path}: {e}")
                return False
        return False
    
    def get_device_keys(self, device_path: str) -> List[str]:
        """Get list of all keys supported by device"""
        device = self.open_device(device_path)
        if not device:
            return []
        
        keys = []
        capabilities = device.capabilities()
        
        if ecodes.EV_KEY in capabilities:
            for key_code in capabilities[ecodes.EV_KEY]:
                try:
                    key_name = ecodes.KEY[key_code]
                    keys.append(key_name)
                except KeyError:
                    keys.append(f"KEY_{key_code}")
        
        return sorted(keys)
    
    def is_device_available(self, device_path: str) -> bool:
        """Check if device is still available"""
        return os.path.exists(device_path)
    
    def refresh_devices(self) -> Dict[str, dict]:
        """Refresh device list"""
        # Close all currently open devices
        for device_path in list(self.input_devices.keys()):
            self.close_device(device_path)
        
        # Rescan
        return self.scan_devices()
