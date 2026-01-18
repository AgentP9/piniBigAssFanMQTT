# Testing Guide

## Prerequisites for Testing

Since this application requires a physical Haiku fan by BigAssFan, testing the full functionality requires:

1. A Haiku fan connected to your network
2. Knowledge of the fan's IP address
3. An MQTT broker (provided by docker-compose)

## Testing Without a Physical Fan

If you don't have a physical fan, you can still test the application structure:

### 1. Start the Services

```bash
# Set a dummy fan IP in .env
echo "FAN_IP=192.168.1.100" > .env
echo "MQTT_BROKER=mosquitto" >> .env
echo "MQTT_PORT=1883" >> .env

# Start services
docker compose up -d
```

### 2. Check Service Health

```bash
# Check if services are running
docker compose ps

# Check backend logs
docker compose logs backend

# Check frontend logs
docker compose logs frontend

# Check MQTT broker logs
docker compose logs mosquitto
```

### 3. Test API Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response (fan will be disconnected without a real fan):
# {"status":"healthy","fan_connected":false,"mqtt_connected":true}
```

### 4. Access Web Interface

Open your browser and navigate to: http://localhost:1919

You should see the fan control interface, though it won't be able to connect to a fan without the correct IP.

## Testing With a Physical Fan

### 1. Find Your Fan's IP Address

Check your router's DHCP client list or use network scanning tools to find devices on port 31415.

### 2. Configure Environment

```bash
# Create .env file with your fan's IP
echo "FAN_IP=<your-fan-ip>" > .env
echo "MQTT_BROKER=mosquitto" >> .env
echo "MQTT_PORT=1883" >> .env
echo "POLL_INTERVAL=30" >> .env
```

### 3. Start Services

```bash
docker compose up -d
```

### 4. Verify Fan Connection

```bash
# Check health endpoint
curl http://localhost:8000/health

# Should show fan_connected: true
```

### 5. Test API Endpoints

```bash
# Get current fan state
curl http://localhost:8000/api/fan/state

# Get fan power
curl http://localhost:8000/api/fan/power

# Set fan power ON
curl -X POST http://localhost:8000/api/fan/power \
  -H "Content-Type: application/json" \
  -d '{"state":"ON"}'

# Set fan speed to 3
curl -X POST http://localhost:8000/api/fan/speed \
  -H "Content-Type: application/json" \
  -d '{"speed":3}'

# Turn on light
curl -X POST http://localhost:8000/api/light/power \
  -H "Content-Type: application/json" \
  -d '{"state":"ON"}'

# Set light level to 10
curl -X POST http://localhost:8000/api/light/level \
  -H "Content-Type: application/json" \
  -d '{"level":10}'
```

### 6. Test MQTT Publishing

```bash
# Subscribe to MQTT topics (in a separate terminal)
docker compose exec mosquitto mosquitto_sub -t "haiku_fan/#" -v

# Or use an external MQTT client
mosquitto_sub -h localhost -t "haiku_fan/#" -v
```

You should see fan states being published every 30 seconds (or whatever POLL_INTERVAL is set to).

### 7. Test MQTT Subscription (Control via MQTT)

```bash
# Turn fan ON via MQTT
docker compose exec mosquitto mosquitto_pub -t "haiku_fan/power/set" -m "ON"

# Turn fan OFF via MQTT
docker compose exec mosquitto mosquitto_pub -t "haiku_fan/power/set" -m "OFF"

# Set fan speed via MQTT (0-7)
docker compose exec mosquitto mosquitto_pub -t "haiku_fan/speed/set" -m "5"

# Turn light ON via MQTT
docker compose exec mosquitto mosquitto_pub -t "haiku_fan/light_power/set" -m "ON"

# Set light brightness via MQTT (0-16)
docker compose exec mosquitto mosquitto_pub -t "haiku_fan/light_level/set" -m "10"

# Or use external MQTT client
mosquitto_pub -h localhost -t "haiku_fan/power/set" -m "ON"
mosquitto_pub -h localhost -t "haiku_fan/speed/set" -m "3"
```

After sending these commands, you should see:
1. The fan/light state change immediately
2. Updated status published back to status topics (e.g., `haiku_fan/power`)
3. Log messages in the backend confirming the MQTT command was received and processed

### 8. Test Web Interface

1. Open http://localhost:1919 in your browser
2. Verify that connection status shows "Connected"
3. Test all controls:
   - Fan power on/off
   - Fan speed slider
   - Light power on/off
   - Light brightness slider
4. Verify that MQTT commands also update the web interface:
   - Send an MQTT command (e.g., turn fan on via MQTT)
   - Check that the web interface reflects the change after the next poll interval

## Troubleshooting

### Fan Won't Connect

**Symptom**: `fan_connected: false` in health check

**Solutions**:
1. Verify the fan IP address is correct
2. Ensure the fan is on the same network or reachable from Docker
3. Check that port 31415 is open and not blocked by firewalls
4. Verify the fan supports the SenseMe protocol (older Haiku models)

### MQTT Not Publishing

**Symptom**: No messages in MQTT broker

**Solutions**:
1. Check MQTT broker is running: `docker compose ps mosquitto`
2. Check backend logs: `docker compose logs backend`
3. Verify MQTT_BROKER environment variable is set correctly

### Web Interface Not Loading

**Symptom**: Cannot access http://localhost:1919

**Solutions**:
1. Check frontend container is running: `docker compose ps frontend`
2. Check nginx logs: `docker compose logs frontend`
3. Verify port 1919 is not in use by another service

### API Returns 503 Errors

**Symptom**: API endpoints return "Service Unavailable"

**Solutions**:
1. Check if backend can connect to the fan
2. Review backend logs: `docker compose logs backend`
3. Ensure the fan IP is correct and the fan is powered on

## Manual Testing Checklist

- [ ] Health endpoint returns correct status
- [ ] Can retrieve fan state
- [ ] Can turn fan on/off via API
- [ ] Can change fan speed (0-7) via API
- [ ] Can turn light on/off via API
- [ ] Can change light brightness (0-16) via API
- [ ] MQTT status messages are published
- [ ] Can turn fan on/off via MQTT
- [ ] Can change fan speed (0-7) via MQTT
- [ ] Can turn light on/off via MQTT
- [ ] Can change light brightness (0-16) via MQTT
- [ ] Web interface loads successfully
- [ ] Web interface shows connection status correctly
- [ ] All web interface controls work
- [ ] MQTT commands update web interface state

## Performance Testing

Test the application under load:

```bash
# Install Apache Bench (if needed)
apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test get state endpoint
ab -n 1000 -c 10 http://localhost:8000/api/fan/state
```

## Security Considerations

- The current implementation has no authentication
- MQTT broker allows anonymous connections
- Consider adding authentication for production use
- Use HTTPS/TLS in production environments

## Logs

View logs for debugging:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mosquitto
```
