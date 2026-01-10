"""
SenseMe Protocol Client for Haiku fans by BigAssFan
Based on: https://bruce.pennypacker.org/2015/07/17/hacking-bigass-fans-with-senseme/
"""
import socket
import threading
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SenseMeClient:
    """Client for communicating with BigAssFan Haiku fans using the SenseMe protocol."""
    
    def __init__(self, fan_ip: str, port: int = 31415):
        self.fan_ip = fan_ip
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self._lock = threading.Lock()
        
    def connect(self) -> bool:
        """Establish connection to the fan."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.fan_ip, self.port))
            self.connected = True
            logger.info(f"Connected to fan at {self.fan_ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to fan: {e}")
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
    
    def send_command(self, command: str) -> Optional[str]:
        """Send a command to the fan and return the response."""
        with self._lock:
            if not self.connected:
                if not self.connect():
                    return None
            
            try:
                # Commands should be formatted as per SenseMe protocol
                full_command = f"<{command}>"
                self.socket.sendall(full_command.encode('utf-8'))
                
                # Receive response
                response = self.socket.recv(1024).decode('utf-8').strip()
                return response
            except Exception as e:
                logger.error(f"Error sending command '{command}': {e}")
                self.disconnect()
                return None
    
    def get_fan_name(self) -> Optional[str]:
        """Get the fan name."""
        response = self.send_command("Device;Name;GET")
        if response:
            # Parse response format: (Device;Name;VALUE;fan_name)
            parts = response.strip("()").split(";")
            if len(parts) >= 4:
                return parts[3]
        return None
    
    def get_fan_power(self) -> Optional[str]:
        """Get the fan power state (ON/OFF)."""
        response = self.send_command("Device;Power;GET")
        if response:
            parts = response.strip("()").split(";")
            if len(parts) >= 4:
                return parts[3]
        return None
    
    def set_fan_power(self, state: str) -> bool:
        """Set the fan power state (ON/OFF)."""
        response = self.send_command(f"Device;Power;SET;{state}")
        return response is not None
    
    def get_fan_speed(self) -> Optional[int]:
        """Get the fan speed (0-7)."""
        response = self.send_command("Device;Speed;GET")
        if response:
            parts = response.strip("()").split(";")
            if len(parts) >= 4:
                try:
                    return int(parts[3])
                except ValueError:
                    pass
        return None
    
    def set_fan_speed(self, speed: int) -> bool:
        """Set the fan speed (0-7)."""
        if not 0 <= speed <= 7:
            logger.error(f"Invalid speed {speed}. Must be between 0 and 7.")
            return False
        response = self.send_command(f"Device;Speed;SET;{speed}")
        return response is not None
    
    def get_fan_whoosh(self) -> Optional[str]:
        """Get the whoosh mode state (ON/OFF)."""
        response = self.send_command("Device;Whoosh;GET")
        if response:
            parts = response.strip("()").split(";")
            if len(parts) >= 4:
                return parts[3]
        return None
    
    def set_fan_whoosh(self, state: str) -> bool:
        """Set the whoosh mode state (ON/OFF)."""
        response = self.send_command(f"Device;Whoosh;SET;{state}")
        return response is not None
    
    def get_light_power(self) -> Optional[str]:
        """Get the light power state (ON/OFF)."""
        response = self.send_command("Device;Light;Power;GET")
        if response:
            parts = response.strip("()").split(";")
            if len(parts) >= 5:
                return parts[4]
        return None
    
    def set_light_power(self, state: str) -> bool:
        """Set the light power state (ON/OFF)."""
        response = self.send_command(f"Device;Light;Power;SET;{state}")
        return response is not None
    
    def get_light_level(self) -> Optional[int]:
        """Get the light brightness level (0-16)."""
        response = self.send_command("Device;Light;Level;GET")
        if response:
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
        response = self.send_command(f"Device;Light;Level;SET;{level}")
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
