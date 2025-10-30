"""
MQTT Client Module
Handles connection to MQTT broker and publishing messages
"""
import json
import logging
import time
from typing import Optional, Callable
import paho.mqtt.client as mqtt
from threading import Thread, Lock

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client with auto-reconnect functionality"""
    
    def __init__(self, broker: str, port: int, username: str, password: str,
                 topic: str, keepalive: int = 60, qos: int = 0, retain: bool = False):
        """Initialize MQTT client"""
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.keepalive = keepalive
        self.qos = qos
        self.retain = retain
        
        self.client = None
        self.connected = False
        self.lock = Lock()
        self.reconnect_thread = None
        self.should_reconnect = True
        self.connection_callbacks = []
        
        self._setup_client()
    
    def _setup_client(self):
        """Set up MQTT client with callbacks"""
        self.client = mqtt.Client(client_id="mqtt-input-remapper", clean_session=True)
        
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        
        logger.info("MQTT client configured")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker {self.broker}:{self.port}")
            self._notify_connection_callbacks(True)
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
            self._notify_connection_callbacks(False)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker, return code: {rc}")
        self._notify_connection_callbacks(False)
        
        if self.should_reconnect and rc != 0:
            logger.info("Will attempt to reconnect...")
            self._start_reconnect_thread()
    
    def _on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        logger.debug(f"Message published, message ID: {mid}")
    
    def _start_reconnect_thread(self):
        """Start background reconnection thread"""
        if self.reconnect_thread is None or not self.reconnect_thread.is_alive():
            self.reconnect_thread = Thread(target=self._reconnect_loop, daemon=True)
            self.reconnect_thread.start()
    
    def _reconnect_loop(self):
        """Background reconnection loop"""
        retry_count = 0
        max_retries = 10
        base_delay = 5
        
        while self.should_reconnect and not self.connected and retry_count < max_retries:
            retry_count += 1
            delay = min(base_delay * retry_count, 60)
            logger.info(f"Reconnection attempt {retry_count}/{max_retries} in {delay}s...")
            time.sleep(delay)
            
            try:
                self.client.reconnect()
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
        
        if retry_count >= max_retries:
            logger.error("Max reconnection attempts reached")
    
    def add_connection_callback(self, callback: Callable[[bool], None]):
        """Add callback to be notified of connection status changes"""
        self.connection_callbacks.append(callback)
    
    def _notify_connection_callbacks(self, connected: bool):
        """Notify all registered callbacks of connection status"""
        for callback in self.connection_callbacks:
            try:
                callback(connected)
            except Exception as e:
                logger.error(f"Error in connection callback: {e}")
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, self.keepalive)
            self.client.loop_start()
            
            # Wait a bit for connection
            time.sleep(2)
            return self.connected
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.should_reconnect = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def publish_key_event(self, device_name: str, pressed_key: str) -> bool:
        """Publish key event to MQTT broker"""
        if not self.connected:
            logger.warning("Cannot publish - not connected to MQTT broker")
            return False
        
        try:
            payload = {
                "device_name": device_name,
                "pressed_key": pressed_key
            }
            
            payload_json = json.dumps(payload)
            
            with self.lock:
                result = self.client.publish(
                    self.topic,
                    payload_json,
                    qos=self.qos,
                    retain=self.retain
                )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published: {payload_json}")
                return True
            else:
                logger.error(f"Failed to publish message, return code: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def test_connection(self) -> dict:
        """Test MQTT connection"""
        result = {
            "success": False,
            "message": "",
            "connected": self.connected
        }
        
        if not self.connected:
            # Try to connect
            try:
                test_client = mqtt.Client(client_id="mqtt-remapper-test", clean_session=True)
                if self.username and self.password:
                    test_client.username_pw_set(self.username, self.password)
                
                test_client.connect(self.broker, self.port, 10)
                test_client.loop_start()
                time.sleep(2)
                
                if test_client.is_connected():
                    result["success"] = True
                    result["message"] = "Connection test successful"
                else:
                    result["message"] = "Failed to connect"
                
                test_client.loop_stop()
                test_client.disconnect()
            except Exception as e:
                result["message"] = f"Connection test failed: {str(e)}"
        else:
            result["success"] = True
            result["message"] = "Already connected"
        
        return result
    
    def update_config(self, broker: str, port: int, username: str, password: str,
                     topic: str, keepalive: int = 60, qos: int = 0, retain: bool = False):
        """Update MQTT configuration and reconnect"""
        logger.info("Updating MQTT configuration...")
        
        # Disconnect current connection
        self.disconnect()
        
        # Update configuration
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.keepalive = keepalive
        self.qos = qos
        self.retain = retain
        
        # Set up new client
        self._setup_client()
        
        # Reconnect
        self.should_reconnect = True
        return self.connect()
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connected
    
    def get_status(self) -> dict:
        """Get current connection status"""
        return {
            "connected": self.connected,
            "broker": self.broker,
            "port": self.port,
            "topic": self.topic
        }
