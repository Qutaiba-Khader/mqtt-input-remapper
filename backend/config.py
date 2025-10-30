"""
Configuration Management Module
Handles loading, saving, and managing application configuration
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = "/etc/mqtt-remapper"
LOCAL_CONFIG_DIR = os.path.expanduser("~/.config/mqtt-remapper")
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "mqtt": {
        "broker": "192.168.1.160",
        "port": 1883,
        "username": "mqttuser",
        "password": "mqttuser",
        "topic": "key_remap/events",
        "keepalive": 60,
        "qos": 0,
        "auto_reconnect": True,
        "retain": False
    },
    "service": {
        "web_port": 8080,
        "bind_address": "0.0.0.0",
        "debug_mode": False,
        "log_level": "INFO",
        "auto_start": True
    },
    "devices": {
        "remapped_devices": {},
        "ignored_keys": {}
    },
    "mappings": {},
    "master_enabled": True
}


class Config:
    """Configuration manager class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager"""
        if config_path:
            self.config_dir = os.path.dirname(config_path)
            self.config_file = config_path
        else:
            # Try to use system config directory, fall back to user directory
            if os.access(DEFAULT_CONFIG_DIR, os.W_OK):
                self.config_dir = DEFAULT_CONFIG_DIR
            else:
                self.config_dir = LOCAL_CONFIG_DIR
            
            self.config_file = os.path.join(self.config_dir, CONFIG_FILE)
        
        self.config = DEFAULT_CONFIG.copy()
        self._ensure_config_dir()
        self.load()
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Configuration directory: {self.config_dir}")
    
    def load(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._merge_config(self.config, loaded_config)
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.info("No existing configuration found, using defaults")
                self.save()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
    
    def _merge_config(self, default: Dict, loaded: Dict):
        """Recursively merge loaded config into default config"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def save(self):
        """Save configuration to file atomically"""
        try:
            # Write to temporary file first
            temp_file = self.config_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Atomic rename
            os.replace(temp_file, self.config_file)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any, save: bool = True):
        """Set configuration value by dot notation key"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
        if save:
            self.save()
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """Get MQTT configuration"""
        return self.config.get('mqtt', {})
    
    def set_mqtt_config(self, mqtt_config: Dict[str, Any]):
        """Set MQTT configuration"""
        self.config['mqtt'].update(mqtt_config)
        self.save()
    
    def get_device_config(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific device"""
        return self.config['devices']['remapped_devices'].get(device_id)
    
    def add_device(self, device_id: str, device_info: Dict[str, Any]):
        """Add device to remapped devices"""
        self.config['devices']['remapped_devices'][device_id] = device_info
        if device_id not in self.config['mappings']:
            self.config['mappings'][device_id] = {}
        if device_id not in self.config['devices']['ignored_keys']:
            self.config['devices']['ignored_keys'][device_id] = []
        self.save()
    
    def remove_device(self, device_id: str):
        """Remove device from remapped devices"""
        self.config['devices']['remapped_devices'].pop(device_id, None)
        self.config['mappings'].pop(device_id, None)
        self.config['devices']['ignored_keys'].pop(device_id, None)
        self.save()
    
    def get_mappings(self, device_id: str) -> Dict[str, str]:
        """Get key mappings for a device"""
        return self.config['mappings'].get(device_id, {})
    
    def set_mappings(self, device_id: str, mappings: Dict[str, str]):
        """Set key mappings for a device"""
        self.config['mappings'][device_id] = mappings
        self.save()
    
    def get_ignored_keys(self, device_id: str) -> list:
        """Get ignored keys for a device"""
        return self.config['devices']['ignored_keys'].get(device_id, [])
    
    def set_ignored_keys(self, device_id: str, keys: list):
        """Set ignored keys for a device"""
        self.config['devices']['ignored_keys'][device_id] = keys
        self.save()
    
    def is_master_enabled(self) -> bool:
        """Check if master remapping is enabled"""
        return self.config.get('master_enabled', True)
    
    def set_master_enabled(self, enabled: bool):
        """Set master remapping enabled state"""
        self.config['master_enabled'] = enabled
        self.save()
    
    def export_config(self) -> str:
        """Export configuration as JSON string"""
        return json.dumps(self.config, indent=2)
    
    def import_config(self, config_json: str) -> bool:
        """Import configuration from JSON string"""
        try:
            imported = json.loads(config_json)
            self.config = imported
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False
    
    def backup_config(self, backup_path: str) -> bool:
        """Create a backup of the configuration"""
        try:
            with open(backup_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error backing up configuration: {e}")
            return False


# Global configuration instance
config = Config()
