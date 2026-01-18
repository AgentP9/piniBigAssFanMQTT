# Troubleshooting Guide

## MQTT Commands Not Reacting

If the fan occasionally doesn't respond to MQTT `/set` commands, check the following:

### 1. Check Logs

The system now provides detailed logging. Look for these messages:

**Successful command:**
```
INFO - MQTT command: Set fan power to ON
INFO - Fan power set to ON via MQTT
```

**Failed command with retries:**
```
WARNING - Command timeout (attempt 1/3): FAN;PWR;ON
WARNING - Command timeout (attempt 2/3): FAN;PWR;ON
ERROR - Command failed after 3 attempts: FAN;PWR;ON
```

**Network issues:**
```
ERROR - Error sending command 'FAN;PWR;ON' (attempt 1/3): [Errno 113] No route to host
```

### 2. Network Connectivity

The fan communicates via UDP on port 31415. Ensure:
- Fan IP address is correct in `.env` file
- Network allows UDP traffic to the fan
- No firewall blocking port 31415
- Fan and MQTT bridge are on the same network segment

### 3. Fan Discovery

Check if the fan name is discovered correctly:
```
INFO - Discovered fan name: Master Bedroom
```

If you see:
```
WARNING - Could not discover fan name, will use empty name in commands
```

Set `FAN_NAME` explicitly in your `.env` file.

### 4. MQTT Broker Connection

Verify MQTT broker connectivity:
```bash
mosquitto_sub -h <mqtt-broker> -t "haiku_fan/#" -v
```

You should see status messages when the fan state changes.

### 5. Command Retry Behavior

Commands automatically retry up to 3 times with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: After 0.5 seconds
- Attempt 3: After 1.0 seconds

If all 3 attempts fail, check network connectivity and fan power.

### 6. Testing Commands

Test directly with mosquitto_pub:

```bash
# Fan power
mosquitto_pub -h <broker> -t "haiku_fan/power/set" -m "ON"

# Fan speed (0-7)
mosquitto_pub -h <broker> -t "haiku_fan/speed/set" -m "3"

# Light power
mosquitto_pub -h <broker> -t "haiku_fan/light_power/set" -m "ON"

# Light level (0-16)
mosquitto_pub -h <broker> -t "haiku_fan/light_level/set" -m "8"
```

### 7. Validation Errors

Commands are validated before being sent:

**Out of range:**
```
WARNING - Invalid fan speed value from MQTT: 10 (must be 0-7)
```

**Invalid format:**
```
WARNING - Invalid fan speed format from MQTT: abc
```

**Invalid power state:**
```
WARNING - Invalid fan power value from MQTT: TOGGLE
```

### 8. Common Issues

**Issue: Commands work in REST API but not via MQTT**
- Check MQTT broker is running and accessible
- Verify topics match exactly (case-sensitive)
- Check MQTT authentication if enabled

**Issue: Some commands work, others don't**
- Check validation logs for out-of-range values
- Verify OpenHAB is sending correct value ranges
- See `OPENHAB_CONFIG.md` for proper configuration

**Issue: Commands work intermittently**
- Network instability - check WiFi signal strength
- Fan may be busy processing previous command
- Retry logic should handle this automatically now

**Issue: Frontend shows different state than MQTT**
- Frontend polls every 5 seconds
- Wait up to 5 seconds for UI to update
- Check `/api/fan/state` endpoint directly

### 9. Debug Mode

To enable debug logging, set in your environment:
```bash
LOG_LEVEL=DEBUG
```

This will show all UDP communication with the fan:
```
DEBUG - Sending command (attempt 1/3): <Master Bedroom;FAN;PWR;ON>
DEBUG - Received response: (Master Bedroom;FAN;PWR;ON)
```

### 10. Getting Help

When reporting issues, include:
1. Exact MQTT topic and payload sent
2. Relevant log entries (with timestamps)
3. OpenHAB configuration (things and items)
4. Network setup (same subnet? firewall?)
5. Fan model and firmware version (if known)
