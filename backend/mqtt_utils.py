"""
Utility functions for converting between percentage and raw values for MQTT interface.
"""


def percentage_to_raw_speed(percentage: int) -> int:
    """Convert percentage (0-100) to raw fan speed (0-7).
    
    Uses integer arithmetic to avoid floating-point precision issues.
    
    Args:
        percentage: Speed as percentage (0-100)
        
    Returns:
        Raw speed value (0-7)
    """
    return (percentage * 7 + 50) // 100


def percentage_to_raw_light(percentage: int) -> int:
    """Convert percentage (0-100) to raw light level (0-16).
    
    Uses integer arithmetic to avoid floating-point precision issues.
    
    Args:
        percentage: Light level as percentage (0-100)
        
    Returns:
        Raw light level (0-16)
    """
    return (percentage * 16 + 50) // 100


def raw_to_percentage_speed(raw_speed: int) -> int:
    """Convert raw fan speed (0-7) to percentage (0-100).
    
    Uses integer arithmetic to avoid floating-point precision issues.
    
    Args:
        raw_speed: Raw speed value (0-7)
        
    Returns:
        Speed as percentage (0-100)
    """
    return (raw_speed * 100 + 3) // 7


def raw_to_percentage_light(raw_level: int) -> int:
    """Convert raw light level (0-16) to percentage (0-100).
    
    Uses integer arithmetic to avoid floating-point precision issues.
    
    Args:
        raw_level: Raw light level (0-16)
        
    Returns:
        Light level as percentage (0-100)
    """
    return (raw_level * 100 + 8) // 16
