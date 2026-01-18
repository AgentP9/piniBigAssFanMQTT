"""
MQTT Client for publishing Haiku fan states and subscribing to control commands
"""
import paho.mqtt.client as mqtt
import json
import logging
from typing import Dict, Any, Optional, Callable

from mqtt_utils import raw_to_percentage_speed, raw_to_percentage_light

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """MQTT client for publishing fan states and subscribing to control commands."""
    
    def __init__(self, broker_host: str, broker_port: int = 1883, base_topic: str = "haiku_fan", 
                 username: Optional[str] = None, password: Optional[str] = None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.base_topic = base_topic
        self.username = username
        self.password = password
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.command_callbacks: Dict[str, Callable] = {}  # Callbacks for command topics
        
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set username and password if provided
            if self.username:
                self.client.username_pw_set(self.username, self.password)
                logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port} with authentication")
            else:
                logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port} without authentication")
            
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.connected = True
            logger.info("Successfully connected to MQTT broker")
            # Subscribe to command topics after successful connection
            self._subscribe_to_commands()
        else:
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker with code: {rc}")
    
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def publish_state(self, topic_suffix: str, value: Any, retain: bool = True) -> bool:
        """Publish a state value to MQTT."""
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            topic = f"{self.base_topic}/{topic_suffix}"
            payload = json.dumps(value) if not isinstance(value, str) else value
            result = self.client.publish(topic, payload, qos=1, retain=retain)
            result.wait_for_publish()
            logger.debug(f"Published to {topic}: {payload}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to MQTT: {e}")
            return False
    
    def publish_all_states(self, states: Dict[str, Any]) -> bool:
        """Publish all fan states to MQTT.
        
        Publishes values in both raw and percentage formats:
        - speed: Published as percentage (0-100) for dimmer compatibility
        - speed_raw: Published as raw value (0-7) for direct control
        - light_level: Published as percentage (0-100) for dimmer compatibility
        - light_level_raw: Published as raw value (0-16) for direct control
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            # Publish states, converting numeric values to percentages for dimmer compatibility
            for key, value in states.items():
                if value is not None:
                    if key == "speed":
                        # Publish as percentage for dimmer compatibility
                        speed_pct = raw_to_percentage_speed(value)
                        self.publish_state("speed", speed_pct)
                        # Also publish raw value for direct access
                        self.publish_state("speed_raw", value)
                    elif key == "light_level":
                        # Publish as percentage for dimmer compatibility
                        light_level_pct = raw_to_percentage_light(value)
                        self.publish_state("light_level", light_level_pct)
                        # Also publish raw value for direct access
                        self.publish_state("light_level_raw", value)
                    else:
                        # Publish other values as-is
                        self.publish_state(key, value)
            
            # Also publish all states as a single JSON message
            self.publish_state("state", states)
            return True
        except Exception as e:
            logger.error(f"Failed to publish states: {e}")
            return False
    
    def register_command_callback(self, command: str, callback: Callable[[str], None]):
        """Register a callback for a specific command topic.
        
        Args:
            command: Command name (e.g., 'power', 'speed', 'light_power', 'light_level')
            callback: Function to call when command is received. Takes the payload as argument.
        """
        self.command_callbacks[command] = callback
        logger.info(f"Registered callback for command: {command}")
    
    def _subscribe_to_commands(self):
        """Subscribe to all command topics."""
        if not self.connected or not self.client:
            logger.warning("Cannot subscribe - not connected to MQTT broker")
            return
        
        # Subscribe to command topics with /set suffix
        command_topics = [
            f"{self.base_topic}/power/set",
            f"{self.base_topic}/speed/set",
            f"{self.base_topic}/light_power/set",
            f"{self.base_topic}/light_level/set",
        ]
        
        for topic in command_topics:
            self.client.subscribe(topic, qos=1)
            logger.info(f"Subscribed to command topic: {topic}")
    
    def _on_message(self, client, userdata, msg):
        """Callback when a message is received on a subscribed topic."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8').strip()
            logger.info(f"Received MQTT message on {topic}: {payload}")
            
            # Extract command from topic (e.g., "haiku_fan/power/set" -> "power")
            if topic.startswith(f"{self.base_topic}/") and topic.endswith("/set"):
                command = topic[len(f"{self.base_topic}/"):-len("/set")]
                
                # Call the registered callback for this command
                if command in self.command_callbacks:
                    self.command_callbacks[command](payload)
                else:
                    logger.warning(f"No callback registered for command: {command}")
            else:
                logger.warning(f"Received message on unexpected topic: {topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
