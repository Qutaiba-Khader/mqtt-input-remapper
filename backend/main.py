"""
Main FastAPI Application
Web API for MQTT Input Remapper
"""
import logging
import os
import json
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# Import application modules
from backend.config import config
from backend.logger import log_manager
from backend.mqtt_client import MQTTClient
from backend.device_manager import DeviceManager
from backend.bluetooth_manager import BluetoothManager
from backend.input_capture import InputCapture

# Initialize logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="MQTT Input Remapper", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
mqtt_client = None
device_manager = None
bluetooth_manager = None
input_capture = None
websocket_connections = []


# Pydantic models for API requests
class MQTTConfig(BaseModel):
    broker: str
    port: int
    username: str
    password: str
    topic: str
    keepalive: Optional[int] = 60
    qos: Optional[int] = 0
    retain: Optional[bool] = False


class DeviceConfig(BaseModel):
    device_id: str
    enabled: bool


class MappingsUpdate(BaseModel):
    device_id: str
    mappings: Dict[str, str]


class IgnoredKeysUpdate(BaseModel):
    device_id: str
    ignored_keys: List[str]


class MasterToggle(BaseModel):
    enabled: bool


class BluetoothCommand(BaseModel):
    address: str
    action: str  # pair, unpair, connect, disconnect, trust, untrust
    value: Optional[str] = None


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application components"""
    global mqtt_client, device_manager, bluetooth_manager, input_capture
    
    logger.info("Starting MQTT Input Remapper...")
    
    # Initialize device manager
    device_manager = DeviceManager()
    
    # Initialize Bluetooth manager
    bluetooth_manager = BluetoothManager()
    
    # Initialize MQTT client
    mqtt_config = config.get_mqtt_config()
    mqtt_client = MQTTClient(
        broker=mqtt_config['broker'],
        port=mqtt_config['port'],
        username=mqtt_config['username'],
        password=mqtt_config['password'],
        topic=mqtt_config['topic'],
        keepalive=mqtt_config.get('keepalive', 60),
        qos=mqtt_config.get('qos', 0),
        retain=mqtt_config.get('retain', False)
    )
    
    # Connect to MQTT broker
    mqtt_client.connect()
    
    # Initialize input capture
    input_capture = InputCapture(device_manager, mqtt_client, config)
    
    # Start capturing from configured devices
    input_capture.start_all_configured_devices()
    
    logger.info("MQTT Input Remapper started successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MQTT Input Remapper...")
    
    if input_capture:
        input_capture.stop_all_captures()
    
    if mqtt_client:
        mqtt_client.disconnect()
    
    logger.info("Shutdown complete")


# API Routes

@app.get("/api/status")
async def get_status():
    """Get system status"""
    mqtt_status = mqtt_client.get_status() if mqtt_client else {"connected": False}
    active_captures = input_capture.get_active_captures() if input_capture else []
    
    return {
        "service_running": True,
        "mqtt_connected": mqtt_status.get('connected', False),
        "mqtt_broker": mqtt_status.get('broker', 'N/A'),
        "active_devices": len(active_captures),
        "master_enabled": config.is_master_enabled(),
        "bluetooth_available": bluetooth_manager.is_available() if bluetooth_manager else False,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/devices")
async def get_devices():
    """Get all devices"""
    if not device_manager:
        raise HTTPException(status_code=500, detail="Device manager not initialized")
    
    # Refresh device list
    all_devices = device_manager.refresh_devices()
    
    # Get remapped devices configuration
    remapped_devices = config.config['devices']['remapped_devices']
    
    # Enrich device info with configuration
    for device in all_devices.values():
        device_id = device['device_id']
        if device_id in remapped_devices:
            device['remapped'] = True
            device['enabled'] = remapped_devices[device_id].get('enabled', False)
            device['capturing'] = input_capture.is_capturing(device_id)
        else:
            device['remapped'] = False
            device['enabled'] = False
            device['capturing'] = False
    
    return {
        "devices": list(all_devices.values()),
        "count": len(all_devices)
    }


@app.post("/api/devices/add")
async def add_device(device_config: DeviceConfig):
    """Add device to remapped collection"""
    device_id = device_config.device_id
    
    # Get device info
    device_info = device_manager.get_device_by_id(device_id)
    if not device_info:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Add to configuration
    config.add_device(device_id, {
        'name': device_info['name'],
        'path': device_info['path'],
        'enabled': device_config.enabled
    })
    
    # Start capture if enabled
    if device_config.enabled and config.is_master_enabled():
        input_capture.start_capture(device_id)
    
    logger.info(f"Added device to remapped collection: {device_info['name']}")
    
    return {"success": True, "message": "Device added to remapped collection"}


@app.post("/api/devices/remove")
async def remove_device(device_config: DeviceConfig):
    """Remove device from remapped collection"""
    device_id = device_config.device_id
    
    # Stop capture if active
    if input_capture.is_capturing(device_id):
        input_capture.stop_capture(device_id)
    
    # Remove from configuration
    config.remove_device(device_id)
    
    logger.info(f"Removed device from remapped collection: {device_id}")
    
    return {"success": True, "message": "Device removed from remapped collection"}


@app.post("/api/devices/toggle")
async def toggle_device(device_config: DeviceConfig):
    """Enable or disable a device"""
    device_id = device_config.device_id
    enabled = device_config.enabled
    
    # Update configuration
    device_cfg = config.get_device_config(device_id)
    if not device_cfg:
        raise HTTPException(status_code=404, detail="Device not in remapped collection")
    
    device_cfg['enabled'] = enabled
    config.set(f'devices.remapped_devices.{device_id}', device_cfg)
    
    # Start or stop capture
    if enabled and config.is_master_enabled():
        input_capture.start_capture(device_id)
    else:
        if input_capture.is_capturing(device_id):
            input_capture.stop_capture(device_id)
    
    logger.info(f"Device {device_id} {'enabled' if enabled else 'disabled'}")
    
    return {"success": True, "enabled": enabled}


@app.get("/api/devices/{device_id}/keys")
async def get_device_keys(device_id: str):
    """Get all keys for a device"""
    device_info = device_manager.get_device_by_id(device_id)
    if not device_info:
        raise HTTPException(status_code=404, detail="Device not found")
    
    keys = device_manager.get_device_keys(device_info['path'])
    
    return {
        "device_id": device_id,
        "device_name": device_info['name'],
        "keys": keys
    }


@app.get("/api/mappings/{device_id}")
async def get_mappings(device_id: str):
    """Get key mappings for a device"""
    mappings = config.get_mappings(device_id)
    ignored_keys = config.get_ignored_keys(device_id)
    
    return {
        "device_id": device_id,
        "mappings": mappings,
        "ignored_keys": ignored_keys
    }


@app.post("/api/mappings/update")
async def update_mappings(update: MappingsUpdate):
    """Update key mappings for a device"""
    device_id = update.device_id
    
    # Update configuration
    config.set_mappings(device_id, update.mappings)
    
    # Update active capture if running
    if input_capture.is_capturing(device_id):
        input_capture.update_device_mappings(device_id)
    
    logger.info(f"Updated mappings for device {device_id}")
    
    return {"success": True, "message": "Mappings updated"}


@app.post("/api/mappings/ignored")
async def update_ignored_keys(update: IgnoredKeysUpdate):
    """Update ignored keys for a device"""
    device_id = update.device_id
    
    # Update configuration
    config.set_ignored_keys(device_id, update.ignored_keys)
    
    # Update active capture if running
    if input_capture.is_capturing(device_id):
        input_capture.update_device_ignored_keys(device_id)
    
    logger.info(f"Updated ignored keys for device {device_id}")
    
    return {"success": True, "message": "Ignored keys updated"}


@app.get("/api/mqtt/config")
async def get_mqtt_config():
    """Get MQTT configuration"""
    mqtt_config = config.get_mqtt_config()
    # Don't send password in plain text
    mqtt_config['password'] = '********' if mqtt_config['password'] else ''
    return mqtt_config


@app.post("/api/mqtt/config")
async def update_mqtt_config(mqtt_config_update: MQTTConfig):
    """Update MQTT configuration"""
    # Update configuration
    config.set_mqtt_config(mqtt_config_update.dict())
    
    # Update MQTT client
    mqtt_client.update_config(
        broker=mqtt_config_update.broker,
        port=mqtt_config_update.port,
        username=mqtt_config_update.username,
        password=mqtt_config_update.password,
        topic=mqtt_config_update.topic,
        keepalive=mqtt_config_update.keepalive,
        qos=mqtt_config_update.qos,
        retain=mqtt_config_update.retain
    )
    
    logger.info("MQTT configuration updated")
    
    return {"success": True, "message": "MQTT configuration updated"}


@app.post("/api/mqtt/test")
async def test_mqtt_connection():
    """Test MQTT connection"""
    result = mqtt_client.test_connection()
    return result


@app.get("/api/master")
async def get_master_status():
    """Get master enable status"""
    return {"enabled": config.is_master_enabled()}


@app.post("/api/master/toggle")
async def toggle_master(toggle: MasterToggle):
    """Toggle master enable/disable"""
    enabled = toggle.enabled
    config.set_master_enabled(enabled)
    
    logger.info(f"Master remapping {'enabled' if enabled else 'disabled'}")
    
    return {"success": True, "enabled": enabled}


@app.get("/api/bluetooth/devices")
async def get_bluetooth_devices(scan: bool = False):
    """Get Bluetooth devices"""
    if not bluetooth_manager.is_available():
        return {"available": False, "devices": [], "message": "Bluetooth not available"}
    
    devices = bluetooth_manager.get_devices(scan_first=scan)
    
    return {
        "available": True,
        "devices": devices,
        "count": len(devices)
    }


@app.post("/api/bluetooth/scan")
async def scan_bluetooth():
    """Start Bluetooth scan"""
    if not bluetooth_manager.is_available():
        raise HTTPException(status_code=400, detail="Bluetooth not available")
    
    success = bluetooth_manager.start_scan(timeout=10)
    
    return {"success": success, "message": "Bluetooth scan started"}


@app.post("/api/bluetooth/command")
async def bluetooth_command(command: BluetoothCommand):
    """Execute Bluetooth command"""
    if not bluetooth_manager.is_available():
        raise HTTPException(status_code=400, detail="Bluetooth not available")
    
    address = command.address
    action = command.action
    
    if action == "pair":
        success = bluetooth_manager.pair_device(address)
    elif action == "unpair":
        success = bluetooth_manager.unpair_device(address)
    elif action == "connect":
        success = bluetooth_manager.connect_device(address)
    elif action == "disconnect":
        success = bluetooth_manager.disconnect_device(address)
    elif action == "trust":
        success = bluetooth_manager.trust_device(address, True)
    elif action == "untrust":
        success = bluetooth_manager.trust_device(address, False)
    elif action == "rename":
        if command.value:
            success = bluetooth_manager.set_alias(address, command.value)
        else:
            raise HTTPException(status_code=400, detail="Alias value required")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    
    return {"success": success, "action": action, "address": address}


@app.get("/api/logs")
async def get_logs(level: Optional[str] = None, limit: int = 100):
    """Get system logs"""
    logs = log_manager.get_logs(level=level, limit=limit)
    return {"logs": logs, "count": len(logs)}


@app.post("/api/logs/clear")
async def clear_logs():
    """Clear log buffer"""
    log_manager.clear_logs()
    return {"success": True, "message": "Logs cleared"}


@app.get("/api/config/export")
async def export_config():
    """Export configuration"""
    config_json = config.export_config()
    return JSONResponse(content=json.loads(config_json))


@app.post("/api/config/import")
async def import_config(file: UploadFile = File(...)):
    """Import configuration"""
    try:
        content = await file.read()
        config_json = content.decode('utf-8')
        
        success = config.import_config(config_json)
        
        if success:
            # Restart captures with new configuration
            input_capture.stop_all_captures()
            input_capture.start_all_configured_devices()
            
            return {"success": True, "message": "Configuration imported successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to import configuration")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error importing configuration: {str(e)}")


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time logs"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Send recent logs every second
            await asyncio.sleep(1)
            logs = log_manager.get_logs(limit=10)
            await websocket.send_json({"logs": logs})
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


# Serve frontend
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/")
async def index():
    """Serve index page"""
    return FileResponse("frontend/index.html")


@app.get("/{page}")
async def serve_page(page: str):
    """Serve other HTML pages"""
    file_path = f"frontend/{page}"
    if os.path.exists(file_path) and page.endswith('.html'):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Page not found")


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration
    web_port = config.get('service.web_port', 8080)
    bind_address = config.get('service.bind_address', '0.0.0.0')
    
    logger.info(f"Starting web server on {bind_address}:{web_port}")
    
    uvicorn.run(app, host=bind_address, port=web_port, log_level="info")
