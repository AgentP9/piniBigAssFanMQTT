# piniBigAssFanMQTT

Offering a MQTT-Bridge to older Haiku fans by BigAssFan

## Overview

This project provides a REST API and MQTT bridge for BigAssFan Haiku fans using the SenseMe protocol. It allows you to control your fan through a web interface, REST API, or MQTT messages.

## Features

- **REST API**: FastAPI-based REST API for fan control
- **MQTT Integration** (Optional): Publishes fan states to MQTT broker when configured
- **Progressive Web App (PWA)**: Install on mobile devices (iPhone, Android) for native app-like experience
- **Web Interface**: Simple web UI for controlling the fan (accessible on port 1919)
- **Docker Support**: Easy deployment with Docker Compose
- **Environment Configuration**: Configure via environment variables (Portainer compatible)

## Fan Controls

- Fan power (ON/OFF)
- Fan speed (0-7)
- Light power (ON/OFF)
- Light brightness level (0-16)

## Architecture

- **Backend**: Python FastAPI application that communicates with the Haiku fan using the SenseMe protocol
- **Frontend**: Single-page HTML/JavaScript application
- **MQTT Broker** (Optional): Eclipse Mosquitto for MQTT messaging - can be disabled by not setting MQTT_BROKER
- **Nginx**: Reverse proxy serving frontend and routing API requests

## Quick Start

### Using Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/AgentP9/piniBigAssFanMQTT.git
   cd piniBigAssFanMQTT
   ```

2. Copy the environment file and configure your fan IP:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and set your fan's IP address:
   ```
   FAN_IP=192.168.1.100  # Replace with your fan's IP
   MQTT_BROKER=mosquitto  # Or leave empty to disable MQTT
   ```

4. Start the services:
   ```bash
   docker-compose up -d
   ```

5. Access the web interface at: `http://localhost:1919`

6. Access the API documentation (Swagger UI) at: `http://localhost:1919/docs`

### Installing as a PWA

After accessing the web interface, you can install it as a Progressive Web App on your mobile device:

- **iPhone/iPad**: Open in Safari, tap Share → Add to Home Screen
- **Android**: Open in Chrome, tap Menu → Install app
- **Desktop**: Look for the install icon in your browser's address bar

The app works offline and provides a native-like experience on mobile devices with fullscreen mode, custom icons, and fast loading from cached assets.

### Running Without MQTT

To run the system without MQTT integration:

1. Set `MQTT_BROKER` to an empty string in your `.env` file:
   ```
   FAN_IP=192.168.1.100
   MQTT_BROKER=
   ```

2. The backend will start without MQTT publishing, and you can use the REST API and web interface normally.

3. If using Docker Compose, you can also comment out the `mosquitto` service if not needed.

### Manual Setup

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the backend directory:
   ```bash
   cp .env.example .env
   ```

3. Configure your fan IP and MQTT broker in `.env`

4. Run the backend:
   ```bash
   python main.py
   ```

5. Serve the frontend using any web server on port 1919

## Environment Variables

Configure these variables in your `.env` file or through Portainer:

- `FAN_IP`: IP address of your Haiku fan (default: 192.168.1.100)
- `FAN_NAME`: Fan name (optional - leave empty to auto-discover; example: "Master Bedroom")
- `MQTT_BROKER`: MQTT broker hostname (optional - leave empty to disable MQTT; default: mosquitto)
- `MQTT_PORT`: MQTT broker port (default: 1883)
- `MQTT_USER`: MQTT username for authentication (optional - leave empty for no authentication)
- `MQTT_PASS`: MQTT password for authentication (optional - leave empty for no authentication)
- `POLL_INTERVAL`: How often to poll fan state in seconds (default: 30)

**Note**: If `MQTT_BROKER` is not set or is empty, the system will operate without MQTT publishing. The REST API and web interface will continue to function normally.

## API Documentation

### Interactive API Documentation (Swagger UI)

Access the interactive API documentation at: **`http://localhost:1919/api/docs`**

The Swagger UI provides:
- Complete list of all API endpoints
- Request/response schemas
- Try-it-out functionality to test API calls directly from your browser
- Detailed parameter descriptions and validation rules

Alternative documentation formats:
- **ReDoc**: `http://localhost:1919/api/redoc` - Alternative API documentation interface
- **OpenAPI JSON**: `http://localhost:1919/api/openapi.json` - Raw OpenAPI specification

### API Endpoints Summary

#### Health Check
- `GET /api/health` - Check service health and connection status

#### Fan State
- `GET /api/fan/state` - Get all fan states (name, power, speed, light_power, light_level)

#### Fan Control
- `GET /api/fan/power` - Get fan power state
- `POST /api/fan/power` - Set fan power (body: `{"state": "ON|OFF"}`)
- `GET /api/fan/speed` - Get fan speed
- `POST /api/fan/speed` - Set fan speed (body: `{"speed": 0-7}`)

#### Light Control
- `GET /api/light/power` - Get light power state
- `POST /api/light/power` - Set light power (body: `{"state": "ON|OFF"}`)
- `GET /api/light/level` - Get light brightness level
- `POST /api/light/level` - Set light level (body: `{"level": 0-16}`)

**Note**: For detailed request/response examples and to test the API interactively, use the Swagger UI at `/docs`

## MQTT Topics

### Status Topics (Published by the service)

The service publishes fan states to the following MQTT topics:

- `haiku_fan/name` - Fan name
- `haiku_fan/power` - Fan power state (ON/OFF)
- `haiku_fan/speed` - Fan speed (0-7)
- `haiku_fan/light_power` - Light power state (ON/OFF)
- `haiku_fan/light_level` - Light brightness level (0-16)
- `haiku_fan/state` - All states as JSON

### Command Topics (Subscribed by the service)

You can control the fan by publishing messages to these command topics:

- `haiku_fan/power/set` - Set fan power (payload: `ON` or `OFF`)
- `haiku_fan/speed/set` - Set fan speed (payload: `0` to `7`)
- `haiku_fan/light_power/set` - Set light power (payload: `ON` or `OFF`)
- `haiku_fan/light_level/set` - Set light brightness (payload: `0` to `16`)

#### Examples

Turn fan on:
```bash
mosquitto_pub -h localhost -t "haiku_fan/power/set" -m "ON"
```

Set fan speed to 5:
```bash
mosquitto_pub -h localhost -t "haiku_fan/speed/set" -m "5"
```

Turn light on:
```bash
mosquitto_pub -h localhost -t "haiku_fan/light_power/set" -m "ON"
```

Set light brightness to 10:
```bash
mosquitto_pub -h localhost -t "haiku_fan/light_level/set" -m "10"
```

## SenseMe Protocol

This project uses the SenseMe protocol for communicating with Haiku fans. The protocol is documented at:
https://bruce.pennypacker.org/2015/07/17/hacking-bigass-fans-with-senseme/

## Ports

- `1919`: Web interface and nginx reverse proxy
- `8000`: Backend API (internal to Docker network)
- `1883`: MQTT broker
- `9001`: MQTT websocket (optional)

## Testing

### Without a Physical Fan

You can test the application structure without a physical fan:

```bash
# Set a dummy fan IP
echo "FAN_IP=192.168.1.100" > .env
echo "MQTT_BROKER=mosquitto" >> .env

# Start services
docker-compose up -d

# Check service health
curl http://localhost:8000/health
# Response: {"status":"healthy","fan_connected":false,"mqtt_connected":true}
```

### With a Physical Fan

1. Find your fan's IP address (check your router's DHCP client list)

2. Configure environment:
   ```bash
   echo "FAN_IP=<your-fan-ip>" > .env
   echo "MQTT_BROKER=mosquitto" >> .env
   ```

3. Start services and verify connection:
   ```bash
   docker-compose up -d
   curl http://localhost:8000/health
   # Should show fan_connected: true
   ```

4. Test API endpoints:
   ```bash
   # Get fan state
   curl http://localhost:8000/api/fan/state
   
   # Turn fan on
   curl -X POST http://localhost:8000/api/fan/power \
     -H "Content-Type: application/json" \
     -d '{"state":"ON"}'
   ```

5. Test MQTT:
   ```bash
   # Subscribe to status updates
   mosquitto_sub -h localhost -t "haiku_fan/#" -v
   
   # Send commands
   mosquitto_pub -h localhost -t "haiku_fan/power/set" -m "ON"
   ```

## Troubleshooting

### Fan Won't Connect

**Symptom**: `fan_connected: false` in health check

**Solutions**:
- Verify the fan IP address is correct in `.env`
- Ensure the fan is on the same network or reachable from Docker
- Check that port 31415 (UDP) is not blocked by firewalls
- Verify the fan supports the SenseMe protocol (older Haiku models)

### MQTT Commands Not Working

**Symptom**: Fan doesn't respond to MQTT `/set` commands

**Solutions**:
- Check backend logs: `docker-compose logs backend`
- Verify MQTT topics match exactly (case-sensitive)
- Ensure values are in correct range:
  - Fan speed: 0-7 (not 0-100)
  - Light level: 0-16 (not 0-100)
- For OpenHAB integration, see [OPENHAB_CONFIG.md](OPENHAB_CONFIG.md)

### Web Interface Not Loading

**Symptom**: Cannot access http://localhost:1919

**Solutions**:
- Check frontend container is running: `docker-compose ps frontend`
- Check nginx logs: `docker-compose logs frontend`
- Verify port 1919 is not in use by another service

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mosquitto
```

## Advanced Deployment

For deploying with Portainer, see [PORTAINER.md](PORTAINER.md) for a comprehensive guide including:
- Git repository deployment
- Environment variable configuration
- Network considerations
- Updating and monitoring

For OpenHAB integration with proper value ranges and configuration, see [OPENHAB_CONFIG.md](OPENHAB_CONFIG.md).

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
