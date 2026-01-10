"""
MQTT Client for publishing Haiku fan states
"""
import paho.mqtt.client as mqtt
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MQTTPublisher:
    """MQTT client for publishing fan states."""
    
    def __init__(self, broker_host: str, broker_port: int = 1883, base_topic: str = "haiku_fan"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.base_topic = base_topic
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.connected = True
            logger.info("Successfully connected to MQTT broker")
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
        """Publish all fan states to MQTT."""
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            # Publish individual states
            for key, value in states.items():
                if value is not None:
                    self.publish_state(key, value)
            
            # Also publish all states as a single JSON message
            self.publish_state("state", states)
            return True
        except Exception as e:
            logger.error(f"Failed to publish states: {e}")
            return False
