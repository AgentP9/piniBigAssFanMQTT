"""
SenseMe Protocol Client for Haiku fans by BigAssFan
Based on: https://bruce.pennypacker.org/2015/07/17/hacking-bigass-fans-with-senseme/

The SenseMe protocol uses UDP datagrams on port 31415.
Commands are sent in the format: <FanName;COMMAND;PARAMETERS>
Responses are received in the format: (FanName;COMMAND;PARAMETERS)
"""
import socket
import threading
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SenseMeClient:
    """Client for communicating with BigAssFan Haiku fans using the SenseMe protocol."""
    
    def __init__(self, fan_ip: str, port: int = 31415, fan_name: Optional[str] = None):
        self.fan_ip = fan_ip
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self._lock = threading.Lock()
        self.fan_name: Optional[str] = fan_name  # Can be pre-configured or discovered
        
    def connect(self) -> bool:
        """Establish UDP socket for the fan."""
        try:
            # Use UDP socket instead of TCP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(5.0)
            self.connected = True
            logger.info(f"Created UDP socket for fan at {self.fan_ip}:{self.port}")
            
            # Try to get the fan name if not already provided
            if not self.fan_name:
                self.fan_name = self._discover_fan_name()
                if self.fan_name:
                    logger.info(f"Discovered fan name: {self.fan_name}")
                else:
                    logger.warning("Could not discover fan name, will use empty name in commands")
                    self.fan_name = ""
            else:
                logger.info(f"Using configured fan name: {self.fan_name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create socket for fan: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close connection to the fan."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
            finally:
                self.socket = None
                self.connected = False
    
    def _discover_fan_name(self) -> Optional[str]:
        """Discover the fan name using the ALL;DEVICE;ID;GET command."""
        try:
            # Try discovery command first
            discovery_cmd = "<ALL;DEVICE;ID;GET>"
            self.socket.sendto(discovery_cmd.encode('utf-8'), (self.fan_ip, self.port))
            
            # Wait for response
            data, addr = self.socket.recvfrom(1024)
            response = data.decode('utf-8').strip()
            logger.info(f"Discovery response: {response}")
            
            # Parse response format: (FanName;DEVICE;ID;...)
            if response.startswith('(') and response.endswith(')'):
                parts = response.strip("()").split(";")
                if len(parts) >= 1:
                    return parts[0]
        except Exception as e:
            logger.debug(f"Failed to discover fan name: {e}")
        
        return None
    
    def send_command(self, command: str) -> Optional[str]:
        """Send a command to the fan and return the response.
        
        Args:
            command: Command without fan name prefix (e.g., "FAN;PWR;GET")
        
        Returns:
            Response string or None if failed
        """
        with self._lock:
            if not self.connected:
                if not self.connect():
                    return None
            
            try:
                # Commands should be formatted as per SenseMe protocol
                # Format: <FanName;COMMAND>
                full_command = f"<{self.fan_name};{command}>"
                logger.debug(f"Sending command: {full_command}")
                
                # Send UDP datagram
                self.socket.sendto(full_command.encode('utf-8'), (self.fan_ip, self.port))
                
                # Receive response
                data, addr = self.socket.recvfrom(1024)
                response = data.decode('utf-8').strip()
                logger.debug(f"Received response: {response}")
                return response
            except Exception as e:
                logger.error(f"Error sending command '{command}': {e}")
                self.disconnect()
                return None
    
    def get_fan_name(self) -> Optional[str]:
        """Get the fan name."""
        # Return the discovered fan name
        return self.fan_name
    
    def get_fan_power(self) -> Optional[str]:
        """Get the fan power state (ON/OFF)."""
        response = self.send_command("FAN;PWR;GET;ACTUAL")
        if response:
            # Parse response format: (FanName;FAN;PWR;value)
            parts = response.strip("()").split(";")
            if len(parts) >= 4:
                return parts[3]
        return None
    
    def set_fan_power(self, state: str) -> bool:
        """Set the fan power state (ON/OFF)."""
        response = self.send_command(f"FAN;PWR;{state}")
        return response is not None
    
    def get_fan_speed(self) -> Optional[int]:
        """Get the fan speed (0-7)."""
        response = self.send_command("FAN;SPD;GET;ACTUAL")
        if response:
            # Parse response format: (FanName;FAN;SPD;ACTUAL;value)
            parts = response.strip("()").split(";")
            if len(parts) >= 5:
                try:
                    return int(parts[4])
                except ValueError:
                    pass
        return None
    
    def set_fan_speed(self, speed: int) -> bool:
        """Set the fan speed (0-7)."""
        if not 0 <= speed <= 7:
            logger.error(f"Invalid speed {speed}. Must be between 0 and 7.")
            return False
        response = self.send_command(f"FAN;SPD;SET;{speed}")
        return response is not None
    
    def get_fan_whoosh(self) -> Optional[str]:
        """Get the whoosh mode state (ON/OFF)."""
        response = self.send_command("FAN;WHOOSH;GET;ACTUAL")
        if response:
            # Parse response format: (FanName;FAN;WHOOSH;ACTUAL;value)
            parts = response.strip("()").split(";")
            if len(parts) >= 5:
                return parts[4]
        return None
    
    def set_fan_whoosh(self, state: str) -> bool:
        """Set the whoosh mode state (ON/OFF)."""
        response = self.send_command(f"FAN;WHOOSH;{state}")
        return response is not None
    
    def get_light_power(self) -> Optional[str]:
        """Get the light power state (ON/OFF)."""
        response = self.send_command("LIGHT;PWR;GET;ACTUAL")
        if response:
            # Parse response format: (FanName;LIGHT;PWR;ACTUAL;value)
            parts = response.strip("()").split(";")
            if len(parts) >= 5:
                return parts[4]
        return None
    
    def set_light_power(self, state: str) -> bool:
        """Set the light power state (ON/OFF)."""
        response = self.send_command(f"LIGHT;PWR;{state}")
        return response is not None
    
    def get_light_level(self) -> Optional[int]:
        """Get the light brightness level (0-16)."""
        response = self.send_command("LIGHT;LEVEL;GET;ACTUAL")
        if response:
            # Parse response format: (FanName;LIGHT;LEVEL;ACTUAL;value)
            parts = response.strip("()").split(";")
            if len(parts) >= 5:
                try:
                    return int(parts[4])
                except ValueError:
                    pass
        return None
    
    def set_light_level(self, level: int) -> bool:
        """Set the light brightness level (0-16)."""
        if not 0 <= level <= 16:
            logger.error(f"Invalid light level {level}. Must be between 0 and 16.")
            return False
        response = self.send_command(f"LIGHT;LEVEL;SET;{level}")
        return response is not None
    
    def get_all_states(self) -> Dict[str, Any]:
        """Get all current states of the fan."""
        states = {
            "name": self.get_fan_name(),
            "power": self.get_fan_power(),
            "speed": self.get_fan_speed(),
            "whoosh": self.get_fan_whoosh(),
            "light_power": self.get_light_power(),
            "light_level": self.get_light_level(),
        }
        return states
