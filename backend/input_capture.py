"""
Input Capture Module
Captures input events from devices and processes remappings
"""
import logging
import asyncio
from typing import Dict, Optional, Callable
from evdev import InputDevice, categorize, ecodes
from threading import Thread
import time

logger = logging.getLogger(__name__)


class InputCapture:
    """Captures and processes input events from HID devices"""
    
    def __init__(self, device_manager, mqtt_client, config):
        """Initialize input capture"""
        self.device_manager = device_manager
        self.mqtt_client = mqtt_client
        self.config = config
        
        self.active_captures = {}  # device_id: capture_info
        self.capture_threads = {}  # device_id: thread
        self.running = False
        
        logger.info("Input capture initialized")
    
    def start_capture(self, device_id: str) -> bool:
        """Start capturing input from a device"""
        # Get device info
        device_info = self.device_manager.get_device_by_id(device_id)
        if not device_info:
            logger.error(f"Device {device_id} not found")
            return False

        device_path = device_info['path']

        # Check if already capturing
        if device_id in self.active_captures:
            logger.warning(f"Already capturing from device {device_id}")
            return True

        # Get device configuration
        device_config = self.config.get_device_config(device_id)
        if not device_config:
            logger.error(f"No configuration found for device {device_id}")
            return False

        # Check if device is enabled
        if not device_config.get('enabled', False):
            logger.info(f"Device {device_id} is disabled, not starting capture")
            return False

        # Check if device path exists
        if not self.device_manager.is_device_available(device_path):
            logger.error(f"Device path does not exist: {device_path}")
            return False

        # Open device
        input_device = self.device_manager.open_device(device_path)
        if not input_device:
            logger.error(f"Failed to open device {device_path}. Check permissions (need root or input group)")
            return False

        # Grab exclusive access (with better error handling)
        try:
            if not self.device_manager.grab_device(device_path):
                logger.error(f"Failed to grab exclusive access to device {device_path}")
                return False
        except PermissionError as e:
            logger.error(f"Permission denied when grabbing device {device_path}. Run as root or add user to input group: {e}")
            return False
        except Exception as e:
            logger.error(f"Error grabbing device {device_path}: {e}")
            return False
        
        # Get mappings and ignored keys
        mappings = self.config.get_mappings(device_id)
        ignored_keys = self.config.get_ignored_keys(device_id)
        
        # Create capture info
        capture_info = {
            'device_id': device_id,
            'device_path': device_path,
            'device_name': device_info['name'],
            'input_device': input_device,
            'mappings': mappings,
            'ignored_keys': ignored_keys,
            'enabled': True
        }
        
        self.active_captures[device_id] = capture_info
        
        # Start capture thread
        thread = Thread(target=self._capture_loop, args=(device_id,), daemon=True)
        thread.start()
        self.capture_threads[device_id] = thread
        
        logger.info(f"Started capturing from device: {device_info['name']}")
        return True
    
    def stop_capture(self, device_id: str) -> bool:
        """Stop capturing input from a device"""
        if device_id not in self.active_captures:
            logger.warning(f"Not capturing from device {device_id}")
            return False
        
        capture_info = self.active_captures[device_id]
        capture_info['enabled'] = False
        
        # Release device
        device_path = capture_info['device_path']
        self.device_manager.ungrab_device(device_path)
        self.device_manager.close_device(device_path)
        
        # Remove from active captures
        del self.active_captures[device_id]
        
        # Wait for thread to finish (with timeout)
        if device_id in self.capture_threads:
            thread = self.capture_threads[device_id]
            thread.join(timeout=2)
            del self.capture_threads[device_id]
        
        logger.info(f"Stopped capturing from device {device_id}")
        return True
    
    def _capture_loop(self, device_id: str):
        """Main capture loop for a device"""
        capture_info = self.active_captures.get(device_id)
        if not capture_info:
            logger.error(f"No capture info found for device {device_id}")
            return

        input_device = capture_info['input_device']
        device_name = capture_info['device_name']

        logger.info(f"✓ Capture loop STARTED for {device_name} - Waiting for key events...")

        try:
            event_count = 0
            for event in input_device.read_loop():
                # Check if still enabled
                if not capture_info.get('enabled', False):
                    logger.info(f"Device {device_name} disabled, stopping capture loop")
                    break

                # Check if master is enabled
                if not self.config.is_master_enabled():
                    continue

                # Only process key events
                if event.type == ecodes.EV_KEY:
                    # Only process key down events (value 1)
                    if event.value == 1:
                        event_count += 1
                        logger.debug(f"Key event #{event_count} received from {device_name}")
                        self._process_key_event(capture_info, event)
        except OSError as e:
            logger.error(f"Device {device_name} disconnected or inaccessible: {e}")
        except PermissionError as e:
            logger.error(f"Permission error reading from {device_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in capture loop for {device_name}: {e}", exc_info=True)
        finally:
            logger.info(f"✗ Capture loop ENDED for {device_name}")
    
    def _process_key_event(self, capture_info: dict, event):
        """Process a key event"""
        device_id = capture_info['device_id']
        device_name = capture_info['device_name']
        mappings = capture_info['mappings']
        ignored_keys = capture_info['ignored_keys']

        # Get key name
        try:
            key_name = ecodes.KEY[event.code]
        except KeyError:
            key_name = f"KEY_{event.code}"

        logger.info(f"🔑 Key pressed: {key_name} on device {device_name}")

        # Check if key is in ignored list
        if key_name in ignored_keys:
            logger.info(f"⊘ Key {key_name} is in ignored list - skipping")
            return

        # Check if key has a mapping
        if key_name in mappings:
            remapped_text = mappings[key_name]

            # Only send if remapped text is not empty
            if remapped_text and remapped_text.strip():
                logger.info(f"📤 Remapping: {key_name} → '{remapped_text}'")

                # Publish to MQTT
                success = self.mqtt_client.publish_key_event(device_name, remapped_text)

                if success:
                    logger.info(f"✓ Successfully published to MQTT")
                else:
                    logger.warning(f"✗ Failed to publish key event for {key_name}")
            else:
                logger.info(f"⊘ Key {key_name} has empty mapping - ignoring")
        else:
            logger.info(f"⊘ Key {key_name} has no mapping - configure it in the Mappings page")
    
    def update_device_mappings(self, device_id: str):
        """Update mappings for a device that's being captured"""
        if device_id in self.active_captures:
            mappings = self.config.get_mappings(device_id)
            self.active_captures[device_id]['mappings'] = mappings
            logger.info(f"Updated mappings for device {device_id}")
    
    def update_device_ignored_keys(self, device_id: str):
        """Update ignored keys for a device that's being captured"""
        if device_id in self.active_captures:
            ignored_keys = self.config.get_ignored_keys(device_id)
            self.active_captures[device_id]['ignored_keys'] = ignored_keys
            logger.info(f"Updated ignored keys for device {device_id}")
    
    def start_all_configured_devices(self):
        """Start capturing from all configured and enabled devices"""
        logger.info("Starting capture for all configured devices...")
        
        remapped_devices = self.config.config['devices']['remapped_devices']
        
        for device_id, device_config in remapped_devices.items():
            if device_config.get('enabled', False):
                try:
                    self.start_capture(device_id)
                except Exception as e:
                    logger.error(f"Error starting capture for device {device_id}: {e}")
    
    def stop_all_captures(self):
        """Stop all active captures"""
        logger.info("Stopping all captures...")
        
        device_ids = list(self.active_captures.keys())
        for device_id in device_ids:
            try:
                self.stop_capture(device_id)
            except Exception as e:
                logger.error(f"Error stopping capture for device {device_id}: {e}")
    
    def get_active_captures(self) -> list:
        """Get list of currently active captures"""
        return [
            {
                'device_id': info['device_id'],
                'device_name': info['device_name'],
                'device_path': info['device_path']
            }
            for info in self.active_captures.values()
        ]
    
    def is_capturing(self, device_id: str) -> bool:
        """Check if currently capturing from a device"""
        return device_id in self.active_captures
