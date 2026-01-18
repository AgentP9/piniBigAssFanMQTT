"""
FastAPI Backend for Haiku Fan MQTT Bridge
"""
import os
import logging
import threading
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from senseme_client import SenseMeClient
from mqtt_client import MQTTPublisher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom filter to exclude health check and state polling endpoints from access logs
class EndpointFilter(logging.Filter):
    """Filter out access logs for specific endpoints to reduce log spam."""
    def filter(self, record: logging.LogRecord) -> bool:
        # Exclude /api/health and /api/fan/state from access logs
        return not any(endpoint in record.getMessage() for endpoint in ["/api/health", "/api/fan/state"])

# Apply filter to uvicorn access logger
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

# Configuration from environment variables
FAN_IP = os.getenv("FAN_IP", "192.168.1.100")
FAN_NAME = os.getenv("FAN_NAME", "")  # Optional: Fan name, will be discovered if not set
MQTT_BROKER = os.getenv("MQTT_BROKER", "")  # Empty string means MQTT disabled
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")  # Optional: MQTT username
MQTT_PASS = os.getenv("MQTT_PASS", "")  # Optional: MQTT password
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))

# Global instances
senseme_client: Optional[SenseMeClient] = None
mqtt_publisher: Optional[MQTTPublisher] = None
fan_states: Dict[str, Any] = {}
fan_states_lock = threading.Lock()  # Lock for thread-safe access to fan_states
polling_thread: Optional[threading.Thread] = None
polling_active = False


def poll_fan_states():
    """Background task to poll fan states and publish to MQTT."""
    global fan_states
    
    logger.info("Starting fan state polling thread")
    while polling_active:
        try:
            if senseme_client:
                new_states = senseme_client.get_all_states()
                
                # Thread-safe update of fan_states
                with fan_states_lock:
                    fan_states = new_states
                
                if mqtt_publisher and mqtt_publisher.connected:
                    mqtt_publisher.publish_all_states(new_states)
                
                logger.info(f"Polled fan states: {new_states}")
        except Exception as e:
            logger.error(f"Error polling fan states: {e}")
        
        time.sleep(POLL_INTERVAL)
    
    logger.info("Stopped fan state polling thread")


def update_state_and_publish(state_key: str, get_state_func):
    """Helper function to update cached state and publish to MQTT after a command.
    
    Args:
        state_key: Key in fan_states dict (e.g., 'power', 'speed')
        get_state_func: Function to call to get the current state from the fan
    """
    try:
        # Allow fan time to process the command
        time.sleep(1)
        
        # Get the current state from the fan
        state_value = get_state_func()
        
        # Only update and publish if we got a valid value
        if state_value is not None:
            # Update cached state (thread-safe)
            with fan_states_lock:
                fan_states[state_key] = state_value
            
            # Publish to MQTT
            if mqtt_publisher and mqtt_publisher.connected:
                mqtt_publisher.publish_state(state_key, state_value)
            
            return state_value
        else:
            logger.warning(f"Failed to get {state_key} state after command")
            return None
    except Exception as e:
        logger.error(f"Error updating {state_key} state: {e}")
        return None


def handle_mqtt_fan_power(payload: str):
    """Handle MQTT command for fan power.
    
    Args:
        payload: MQTT message payload. Expected values: "ON" or "OFF" (case-insensitive)
    
    On success, updates the cached fan state and publishes the new state to MQTT status topic.
    Logs warnings for invalid payloads and errors if the command fails.
    """
    try:
        payload_upper = payload.upper()
        if payload_upper in ["ON", "OFF"]:
            logger.info(f"MQTT command: Set fan power to {payload_upper}")
            if senseme_client:
                success = senseme_client.set_fan_power(payload_upper)
                if success:
                    state = update_state_and_publish("power", senseme_client.get_fan_power)
                    if state:
                        logger.info(f"Fan power set to {state} via MQTT")
                    else:
                        logger.error("Failed to read fan power state after setting via MQTT")
                else:
                    logger.error(f"Failed to set fan power to {payload_upper} via MQTT - command returned False")
            else:
                logger.error("SenseMe client not initialized")
        else:
            logger.warning(f"Invalid fan power value from MQTT: {payload}")
    except Exception as e:
        logger.error(f"Error handling MQTT fan power command: {e}", exc_info=True)


def handle_mqtt_fan_speed(payload: str):
    """Handle MQTT command for fan speed.
    
    Args:
        payload: MQTT message payload. Expected values: "0" to "7" as string
    
    On success, updates the cached fan state and publishes the new state to MQTT status topic.
    Logs warnings for out-of-range values or invalid formats, and errors if the command fails.
    """
    try:
        speed = int(payload)
        if 0 <= speed <= 7:
            logger.info(f"MQTT command: Set fan speed to {speed}")
            if senseme_client:
                success = senseme_client.set_fan_speed(speed)
                if success:
                    state = update_state_and_publish("speed", senseme_client.get_fan_speed)
                    if state is not None:
                        logger.info(f"Fan speed set to {state} via MQTT")
                    else:
                        logger.error("Failed to read fan speed state after setting via MQTT")
                else:
                    logger.error(f"Failed to set fan speed to {speed} via MQTT - command returned False")
            else:
                logger.error("SenseMe client not initialized")
        else:
            logger.warning(f"Invalid fan speed value from MQTT: {payload} (must be 0-7)")
    except ValueError:
        logger.warning(f"Invalid fan speed format from MQTT: {payload}")
    except Exception as e:
        logger.error(f"Error handling MQTT fan speed command: {e}", exc_info=True)


def handle_mqtt_light_power(payload: str):
    """Handle MQTT command for light power.
    
    Args:
        payload: MQTT message payload. Expected values: "ON" or "OFF" (case-insensitive)
    
    On success, updates the cached light state and publishes the new state to MQTT status topic.
    Also publishes the light_level since power changes affect the level (ON=2, OFF=0).
    Logs warnings for invalid payloads and errors if the command fails.
    """
    try:
        payload_upper = payload.upper()
        if payload_upper in ["ON", "OFF"]:
            logger.info(f"MQTT command: Set light power to {payload_upper}")
            if senseme_client:
                success = senseme_client.set_light_power(payload_upper)
                if success:
                    # Update and publish light power state
                    power_state = update_state_and_publish("light_power", senseme_client.get_light_power)
                    # Also update and publish light level since it changes with power
                    level_state = update_state_and_publish("light_level", senseme_client.get_light_level)
                    if power_state:
                        logger.info(f"Light power set to {power_state} via MQTT (level: {level_state})")
                    else:
                        logger.error("Failed to read light power state after setting via MQTT")
                else:
                    logger.error(f"Failed to set light power to {payload_upper} via MQTT - command returned False")
            else:
                logger.error("SenseMe client not initialized")
        else:
            logger.warning(f"Invalid light power value from MQTT: {payload}")
    except Exception as e:
        logger.error(f"Error handling MQTT light power command: {e}", exc_info=True)


def handle_mqtt_light_level(payload: str):
    """Handle MQTT command for light level.
    
    Args:
        payload: MQTT message payload. Expected values: "0" to "16" as string
    
    On success, updates the cached light state and publishes the new state to MQTT status topic.
    Logs warnings for out-of-range values or invalid formats, and errors if the command fails.
    """
    try:
        level = int(payload)
        if 0 <= level <= 16:
            logger.info(f"MQTT command: Set light level to {level}")
            if senseme_client:
                success = senseme_client.set_light_level(level)
                if success:
                    state = update_state_and_publish("light_level", senseme_client.get_light_level)
                    if state is not None:
                        logger.info(f"Light level set to {state} via MQTT")
                    else:
                        logger.error("Failed to read light level state after setting via MQTT")
                else:
                    logger.error(f"Failed to set light level to {level} via MQTT - command returned False")
            else:
                logger.error("SenseMe client not initialized")
        else:
            logger.warning(f"Invalid light level value from MQTT: {payload} (must be 0-16)")
    except ValueError:
        logger.warning(f"Invalid light level format from MQTT: {payload}")
    except Exception as e:
        logger.error(f"Error handling MQTT light level command: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global senseme_client, mqtt_publisher, polling_thread, polling_active
    
    # Startup
    logger.info("Starting Haiku Fan MQTT Bridge")
    logger.info(f"Fan IP: {FAN_IP}")
    if FAN_NAME:
        logger.info(f"Fan Name: {FAN_NAME}")
    
    # Initialize SenseMe client
    senseme_client = SenseMeClient(FAN_IP, fan_name=FAN_NAME if FAN_NAME else None)
    if not senseme_client.connect():
        logger.warning("Failed to connect to fan on startup")
    
    # Initialize MQTT publisher only if broker is configured
    if MQTT_BROKER:
        logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        if MQTT_USER:
            logger.info("MQTT Authentication: Enabled")
        else:
            logger.info("MQTT Authentication: Disabled")
        mqtt_publisher = MQTTPublisher(MQTT_BROKER, MQTT_PORT, username=MQTT_USER or None, password=MQTT_PASS or None)
        mqtt_publisher.connect()
        
        # Register MQTT command callbacks
        mqtt_publisher.register_command_callback('power', handle_mqtt_fan_power)
        mqtt_publisher.register_command_callback('speed', handle_mqtt_fan_speed)
        mqtt_publisher.register_command_callback('light_power', handle_mqtt_light_power)
        mqtt_publisher.register_command_callback('light_level', handle_mqtt_light_level)
        logger.info("Registered MQTT command callbacks")
    else:
        logger.info("MQTT Broker not configured - MQTT publishing disabled")
        mqtt_publisher = None
    
    # Start polling thread
    polling_active = True
    polling_thread = threading.Thread(target=poll_fan_states, daemon=True)
    polling_thread.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Haiku Fan MQTT Bridge")
    polling_active = False
    if polling_thread:
        polling_thread.join(timeout=5)
    
    if senseme_client:
        senseme_client.disconnect()
    
    if mqtt_publisher:
        mqtt_publisher.disconnect()


# Create FastAPI app with custom docs URLs
app = FastAPI(
    title="Haiku Fan MQTT Bridge",
    description="REST API and MQTT bridge for BigAssFan Haiku fans",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class PowerRequest(BaseModel):
    state: str = Field(..., pattern="^(ON|OFF)$", description="Power state: ON or OFF")


class SpeedRequest(BaseModel):
    speed: int = Field(..., ge=0, le=7, description="Fan speed from 0 to 7")


class LightPowerRequest(BaseModel):
    state: str = Field(..., pattern="^(ON|OFF)$", description="Light power: ON or OFF")


class LightLevelRequest(BaseModel):
    level: int = Field(..., ge=0, le=16, description="Light brightness level from 0 to 16")


# API Routes
@app.get("/", tags=["General"])
async def root():
    """
    Root endpoint - Service information.
    
    Returns basic information about the service including name, version, and status.
    """
    return {
        "service": "Haiku Fan MQTT Bridge",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health", tags=["General"])
async def health():
    """
    Health check endpoint.
    
    Check the health status of the service including:
    - Overall service status
    - Fan connection status (connected/disconnected)
    - MQTT broker connection status (if configured)
    
    Returns:
        dict: Health status with connection states
    """
    return {
        "status": "healthy",
        "fan_connected": senseme_client.connected if senseme_client else False,
        "mqtt_connected": mqtt_publisher.connected if mqtt_publisher else False
    }


@app.get("/api/fan/state", tags=["Fan"])
async def get_fan_state():
    """
    Get complete fan state.
    
    Returns all current fan states including:
    - name: Fan name
    - power: Fan power state (ON/OFF)
    - speed: Fan speed (0-7, where 0=OFF)
    - light_power: Light power state (ON/OFF)
    - light_level: Light brightness level (0-16)
    
    Returns:
        dict: Complete fan state
        
    Raises:
        HTTPException: 503 if fan states are not yet available
    """
    with fan_states_lock:
        if not fan_states:
            raise HTTPException(status_code=503, detail="Fan states not yet available")
        return fan_states.copy()  # Return a copy to avoid concurrent modification


@app.get("/api/fan/power", tags=["Fan"])
async def get_fan_power():
    """
    Get fan power state.
    
    Returns the current power state of the fan (ON or OFF).
    
    Returns:
        dict: {"power": "ON"|"OFF"}
        
    Raises:
        HTTPException: 503 if unable to get fan power state
    """
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    power = senseme_client.get_fan_power()
    if power is None:
        raise HTTPException(status_code=503, detail="Failed to get fan power state")
    
    return {"power": power}


@app.post("/api/fan/power", tags=["Fan"])
async def set_fan_power(request: PowerRequest):
    """
    Set fan power state.
    
    Turn the fan ON or OFF.
    
    Args:
        request: PowerRequest with state field ("ON" or "OFF")
        
    Returns:
        dict: {"success": true, "power": "ON"|"OFF"}
        
    Raises:
        HTTPException: 503 if SenseMe client not initialized
        HTTPException: 500 if failed to set fan power
    """
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    if senseme_client.set_fan_power(request.state):
        # Update state immediately
        time.sleep(1)
        power = senseme_client.get_fan_power()
        
        # Update cached fan_states immediately for responsive UI (thread-safe)
        with fan_states_lock:
            fan_states["power"] = power
        
        if mqtt_publisher and mqtt_publisher.connected:
            mqtt_publisher.publish_state("power", power)
        return {"success": True, "power": request.state}
    else:
        raise HTTPException(status_code=500, detail="Failed to set fan power")


@app.get("/api/fan/speed", tags=["Fan"])
async def get_fan_speed():
    """
    Get fan speed.
    
    Returns the current fan speed (0-7, where 0 means fan is OFF).
    
    Returns:
        dict: {"speed": 0-7}
        
    Raises:
        HTTPException: 503 if unable to get fan speed
    """
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    speed = senseme_client.get_fan_speed()
    if speed is None:
        raise HTTPException(status_code=503, detail="Failed to get fan speed")
    
    return {"speed": speed}


@app.post("/api/fan/speed", tags=["Fan"])
async def set_fan_speed(request: SpeedRequest):
    """
    Set fan speed.
    
    Set the fan speed to a value between 0 and 7.
    Note: Setting speed to 0 turns the fan OFF.
    
    Args:
        request: SpeedRequest with speed field (0-7)
        
    Returns:
        dict: {"success": true, "speed": 0-7}
        
    Raises:
        HTTPException: 503 if SenseMe client not initialized
        HTTPException: 500 if failed to set fan speed
    """
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    if senseme_client.set_fan_speed(request.speed):
        # Update state immediately
        time.sleep(1)
        speed = senseme_client.get_fan_speed()
        
        # Update cached fan_states immediately for responsive UI (thread-safe)
        with fan_states_lock:
            fan_states["speed"] = speed
        
        if mqtt_publisher and mqtt_publisher.connected:
            mqtt_publisher.publish_state("speed", speed)
        return {"success": True, "speed": request.speed}
    else:
        raise HTTPException(status_code=500, detail="Failed to set fan speed")


@app.get("/api/light/power", tags=["Light"])
async def get_light_power():
    """
    Get light power state.
    
    Returns the current power state of the light (ON or OFF).
    
    Returns:
        dict: {"power": "ON"|"OFF"}
        
    Raises:
        HTTPException: 503 if unable to get light power state
    """
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    power = senseme_client.get_light_power()
    if power is None:
        raise HTTPException(status_code=503, detail="Failed to get light power state")
    
    return {"power": power}


@app.post("/api/light/power", tags=["Light"])
async def set_light_power(request: LightPowerRequest):
    """
    Set light power state.
    
    Turn the light ON or OFF.
    - When turning ON: Light is set to level 2 (default brightness)
    - When turning OFF: Light level is set to 0
    
    Both light_power and light_level states are published to MQTT when changed.
    
    Args:
        request: LightPowerRequest with state field ("ON" or "OFF")
        
    Returns:
        dict: {"success": true, "power": "ON"|"OFF"}
        
    Raises:
        HTTPException: 503 if SenseMe client not initialized
        HTTPException: 500 if failed to set light power
    """
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    if senseme_client.set_light_power(request.state):
        # Update state immediately
        time.sleep(1)
        power = senseme_client.get_light_power()
        level = senseme_client.get_light_level()
        
        # Update cached fan_states immediately for responsive UI (thread-safe)
        with fan_states_lock:
            fan_states["light_power"] = power
            fan_states["light_level"] = level
        
        if mqtt_publisher and mqtt_publisher.connected:
            mqtt_publisher.publish_state("light_power", power)
            mqtt_publisher.publish_state("light_level", level)
        return {"success": True, "power": request.state}
    else:
        raise HTTPException(status_code=500, detail="Failed to set light power")


@app.get("/api/light/level", tags=["Light"])
async def get_light_level():
    """
    Get light brightness level.
    
    Returns the current brightness level of the light (0-16).
    
    Returns:
        dict: {"level": 0-16}
        
    Raises:
        HTTPException: 503 if unable to get light level
    """
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    level = senseme_client.get_light_level()
    if level is None:
        raise HTTPException(status_code=503, detail="Failed to get light level")
    
    return {"level": level}


@app.post("/api/light/level", tags=["Light"])
async def set_light_level(request: LightLevelRequest):
    """
    Set light brightness level.
    
    Set the light brightness to a value between 0 and 16.
    Note: Setting level to 0 turns the light OFF.
    
    Args:
        request: LightLevelRequest with level field (0-16)
        
    Returns:
        dict: {"success": true, "level": 0-16}
        
    Raises:
        HTTPException: 503 if SenseMe client not initialized
        HTTPException: 500 if failed to set light level
    """
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    if senseme_client.set_light_level(request.level):
        # Update state immediately
        time.sleep(1)
        level = senseme_client.get_light_level()
        
        # Update cached fan_states immediately for responsive UI (thread-safe)
        with fan_states_lock:
            fan_states["light_level"] = level
        
        if mqtt_publisher and mqtt_publisher.connected:
            mqtt_publisher.publish_state("light_level", level)
        return {"success": True, "level": request.level}
    else:
        raise HTTPException(status_code=500, detail="Failed to set light level")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
