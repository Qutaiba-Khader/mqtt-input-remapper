"""
Bluetooth Manager Module
Handles Bluetooth device scanning, pairing, and management via BlueZ DBus
"""
import logging
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)

# Try to import DBus libraries (may not be available on all systems)
try:
    from pydbus import SystemBus
    from gi.repository import GLib
    DBUS_AVAILABLE = True
except ImportError:
    logger.warning("DBus libraries not available - Bluetooth features will be limited")
    DBUS_AVAILABLE = False


class BluetoothManager:
    """Manages Bluetooth devices via BlueZ"""
    
    def __init__(self):
        """Initialize Bluetooth manager"""
        self.bus = None
        self.adapter = None
        self.adapter_path = None
        self.devices = {}
        self.scanning = False
        
        if DBUS_AVAILABLE:
            self._init_dbus()
        else:
            logger.warning("Bluetooth manager initialized without DBus support")
    
    def _init_dbus(self):
        """Initialize DBus connection"""
        try:
            self.bus = SystemBus()
            self._find_adapter()
        except Exception as e:
            logger.error(f"Error initializing DBus: {e}")
            logger.warning("Bluetooth features will not be available")
    
    def _find_adapter(self):
        """Find Bluetooth adapter"""
        try:
            # Get ObjectManager
            om = self.bus.get('org.bluez', '/')
            objects = om.GetManagedObjects()
            
            # Find first adapter
            for path, interfaces in objects.items():
                if 'org.bluez.Adapter1' in interfaces:
                    self.adapter_path = path
                    self.adapter = self.bus.get('org.bluez', path)
                    logger.info(f"Found Bluetooth adapter: {path}")
                    return
            
            logger.warning("No Bluetooth adapter found")
        except Exception as e:
            logger.error(f"Error finding Bluetooth adapter: {e}")
    
    def is_available(self) -> bool:
        """Check if Bluetooth is available"""
        return DBUS_AVAILABLE and self.adapter is not None
    
    def start_scan(self, timeout: int = 10) -> bool:
        """Start scanning for Bluetooth devices"""
        if not self.is_available():
            logger.warning("Bluetooth not available")
            return False
        
        try:
            logger.info("Starting Bluetooth scan...")
            self.adapter.StartDiscovery()
            self.scanning = True
            
            # Scan for specified timeout
            time.sleep(timeout)
            
            self.stop_scan()
            return True
        except Exception as e:
            logger.error(f"Error starting Bluetooth scan: {e}")
            return False
    
    def stop_scan(self):
        """Stop scanning for Bluetooth devices"""
        if not self.is_available():
            return
        
        try:
            if self.scanning:
                self.adapter.StopDiscovery()
                self.scanning = False
                logger.info("Stopped Bluetooth scan")
        except Exception as e:
            logger.error(f"Error stopping Bluetooth scan: {e}")
    
    def get_devices(self, scan_first: bool = False) -> List[Dict]:
        """Get list of discovered Bluetooth devices"""
        if not self.is_available():
            return []
        
        if scan_first:
            self.start_scan()
        
        devices = []
        
        try:
            om = self.bus.get('org.bluez', '/')
            objects = om.GetManagedObjects()
            
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' in interfaces:
                    device = interfaces['org.bluez.Device1']
                    
                    device_info = {
                        "path": path,
                        "address": device.get('Address', 'Unknown'),
                        "name": device.get('Name', device.get('Alias', 'Unknown Device')),
                        "alias": device.get('Alias', device.get('Name', 'Unknown Device')),
                        "paired": device.get('Paired', False),
                        "connected": device.get('Connected', False),
                        "trusted": device.get('Trusted', False),
                        "blocked": device.get('Blocked', False),
                        "rssi": device.get('RSSI', 0),
                        "uuids": device.get('UUIDs', [])
                    }
                    
                    # Try to get battery level if available
                    try:
                        battery = self.bus.get('org.bluez', path)
                        if hasattr(battery, 'Percentage'):
                            device_info['battery'] = battery.Percentage
                    except:
                        device_info['battery'] = None
                    
                    devices.append(device_info)
            
            self.devices = {dev['address']: dev for dev in devices}
            logger.debug(f"Found {len(devices)} Bluetooth devices")
        except Exception as e:
            logger.error(f"Error getting Bluetooth devices: {e}")
        
        return devices
    
    def get_device_by_address(self, address: str) -> Optional[Dict]:
        """Get device info by address"""
        return self.devices.get(address)
    
    def pair_device(self, address: str) -> bool:
        """Pair with a Bluetooth device"""
        if not self.is_available():
            return False
        
        try:
            # Find device path
            device_path = self._get_device_path(address)
            if not device_path:
                logger.error(f"Device {address} not found")
                return False
            
            device = self.bus.get('org.bluez', device_path)
            logger.info(f"Pairing with device {address}...")
            
            device.Pair()
            logger.info(f"Successfully paired with {address}")
            return True
        except Exception as e:
            logger.error(f"Error pairing with device {address}: {e}")
            return False
    
    def unpair_device(self, address: str) -> bool:
        """Unpair a Bluetooth device"""
        if not self.is_available():
            return False
        
        try:
            device_path = self._get_device_path(address)
            if not device_path:
                return False
            
            logger.info(f"Removing device {address}...")
            self.adapter.RemoveDevice(device_path)
            logger.info(f"Successfully removed device {address}")
            return True
        except Exception as e:
            logger.error(f"Error removing device {address}: {e}")
            return False
    
    def connect_device(self, address: str) -> bool:
        """Connect to a paired Bluetooth device"""
        if not self.is_available():
            return False
        
        try:
            device_path = self._get_device_path(address)
            if not device_path:
                return False
            
            device = self.bus.get('org.bluez', device_path)
            logger.info(f"Connecting to device {address}...")
            
            device.Connect()
            logger.info(f"Successfully connected to {address}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to device {address}: {e}")
            return False
    
    def disconnect_device(self, address: str) -> bool:
        """Disconnect from a Bluetooth device"""
        if not self.is_available():
            return False
        
        try:
            device_path = self._get_device_path(address)
            if not device_path:
                return False
            
            device = self.bus.get('org.bluez', device_path)
            logger.info(f"Disconnecting from device {address}...")
            
            device.Disconnect()
            logger.info(f"Successfully disconnected from {address}")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from device {address}: {e}")
            return False
    
    def trust_device(self, address: str, trusted: bool = True) -> bool:
        """Trust/untrust a Bluetooth device"""
        if not self.is_available():
            return False
        
        try:
            device_path = self._get_device_path(address)
            if not device_path:
                return False
            
            device = self.bus.get('org.bluez', device_path)
            device.Trusted = trusted
            
            logger.info(f"Device {address} {'trusted' if trusted else 'untrusted'}")
            return True
        except Exception as e:
            logger.error(f"Error setting trust for device {address}: {e}")
            return False
    
    def set_alias(self, address: str, alias: str) -> bool:
        """Set device alias (friendly name)"""
        if not self.is_available():
            return False
        
        try:
            device_path = self._get_device_path(address)
            if not device_path:
                return False
            
            device = self.bus.get('org.bluez', device_path)
            device.Alias = alias
            
            logger.info(f"Set alias for device {address} to '{alias}'")
            return True
        except Exception as e:
            logger.error(f"Error setting alias for device {address}: {e}")
            return False
    
    def _get_device_path(self, address: str) -> Optional[str]:
        """Get DBus path for device by address"""
        try:
            # Normalize address format
            address_normalized = address.replace(':', '_')
            device_path = f"{self.adapter_path}/dev_{address_normalized}"
            return device_path
        except Exception as e:
            logger.error(f"Error getting device path for {address}: {e}")
            return None
    
    def get_adapter_info(self) -> Optional[Dict]:
        """Get Bluetooth adapter information"""
        if not self.is_available():
            return None
        
        try:
            info = {
                "address": self.adapter.Address,
                "name": self.adapter.Name,
                "alias": self.adapter.Alias,
                "powered": self.adapter.Powered,
                "discoverable": self.adapter.Discoverable,
                "pairable": self.adapter.Pairable,
                "discovering": self.adapter.Discovering
            }
            return info
        except Exception as e:
            logger.error(f"Error getting adapter info: {e}")
            return None
    
    def set_adapter_powered(self, powered: bool) -> bool:
        """Power on/off Bluetooth adapter"""
        if not self.is_available():
            return False
        
        try:
            self.adapter.Powered = powered
            logger.info(f"Bluetooth adapter {'powered on' if powered else 'powered off'}")
            return True
        except Exception as e:
            logger.error(f"Error setting adapter power: {e}")
            return False
