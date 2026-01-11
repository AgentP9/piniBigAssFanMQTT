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


# Create FastAPI app
app = FastAPI(
    title="Haiku Fan MQTT Bridge",
    description="REST API and MQTT bridge for BigAssFan Haiku fans",
    version="1.0.0",
    lifespan=lifespan
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
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Haiku Fan MQTT Bridge",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "fan_connected": senseme_client.connected if senseme_client else False,
        "mqtt_connected": mqtt_publisher.connected if mqtt_publisher else False
    }


@app.get("/api/fan/state")
async def get_fan_state():
    """Get current fan state."""
    with fan_states_lock:
        if not fan_states:
            raise HTTPException(status_code=503, detail="Fan states not yet available")
        return fan_states.copy()  # Return a copy to avoid concurrent modification


@app.get("/api/fan/power")
async def get_fan_power():
    """Get fan power state."""
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    power = senseme_client.get_fan_power()
    if power is None:
        raise HTTPException(status_code=503, detail="Failed to get fan power state")
    
    return {"power": power}


@app.post("/api/fan/power")
async def set_fan_power(request: PowerRequest):
    """Set fan power state."""
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


@app.get("/api/fan/speed")
async def get_fan_speed():
    """Get fan speed."""
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    speed = senseme_client.get_fan_speed()
    if speed is None:
        raise HTTPException(status_code=503, detail="Failed to get fan speed")
    
    return {"speed": speed}


@app.post("/api/fan/speed")
async def set_fan_speed(request: SpeedRequest):
    """Set fan speed."""
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


@app.get("/api/light/power")
async def get_light_power():
    """Get light power state."""
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    power = senseme_client.get_light_power()
    if power is None:
        raise HTTPException(status_code=503, detail="Failed to get light power state")
    
    return {"power": power}


@app.post("/api/light/power")
async def set_light_power(request: LightPowerRequest):
    """Set light power state."""
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    if senseme_client.set_light_power(request.state):
        # Update state immediately
        time.sleep(1)
        power = senseme_client.get_light_power()
        
        # Update cached fan_states immediately for responsive UI (thread-safe)
        with fan_states_lock:
            fan_states["light_power"] = power
        
        if mqtt_publisher and mqtt_publisher.connected:
            mqtt_publisher.publish_state("light_power", power)
        return {"success": True, "power": request.state}
    else:
        raise HTTPException(status_code=500, detail="Failed to set light power")


@app.get("/api/light/level")
async def get_light_level():
    """Get light brightness level."""
    if not senseme_client:
        raise HTTPException(status_code=503, detail="SenseMe client not initialized")
    
    level = senseme_client.get_light_level()
    if level is None:
        raise HTTPException(status_code=503, detail="Failed to get light level")
    
    return {"level": level}


@app.post("/api/light/level")
async def set_light_level(request: LightLevelRequest):
    """Set light brightness level."""
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
