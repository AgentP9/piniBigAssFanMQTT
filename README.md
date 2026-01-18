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

### Installing as a PWA

After accessing the web interface, you can install it as a Progressive Web App on your mobile device:

- **iPhone/iPad**: Open in Safari, tap Share → Add to Home Screen
- **Android**: Open in Chrome, tap Menu → Install app
- **Desktop**: Look for the install icon in your browser's address bar

For detailed PWA installation instructions, see [PWA.md](PWA.md).

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

## API Endpoints

### Health Check
- `GET /health` - Check service health and connection status

### Fan State
- `GET /api/fan/state` - Get all fan states

### Fan Control
- `GET /api/fan/power` - Get fan power state
- `POST /api/fan/power` - Set fan power (body: `{"state": "ON|OFF"}`)
- `GET /api/fan/speed` - Get fan speed
- `POST /api/fan/speed` - Set fan speed (body: `{"speed": 0-7}`)

### Light Control
- `GET /api/light/power` - Get light power state
- `POST /api/light/power` - Set light power (body: `{"state": "ON|OFF"}`)
- `GET /api/light/level` - Get light brightness level
- `POST /api/light/level` - Set light level (body: `{"level": 0-16}`)

## MQTT Topics

### Status Topics (Published by the service)

The service publishes fan states to the following MQTT topics:

- `haiku_fan/name` - Fan name
- `haiku_fan/power` - Fan power state (ON/OFF)
- `haiku_fan/speed` - Fan speed as percentage (0-100) - for dimmer compatibility
- `haiku_fan/speed_raw` - Fan speed raw value (0-7)
- `haiku_fan/light_power` - Light power state (ON/OFF)
- `haiku_fan/light_level` - Light brightness as percentage (0-100) - for dimmer compatibility
- `haiku_fan/light_level_raw` - Light brightness raw value (0-16)
- `haiku_fan/state` - All states as JSON

**Note**: The `speed` and `light_level` topics publish percentage values (0-100) for compatibility with home automation platforms like OpenHAB and Home Assistant that use dimmers. If you need raw values, use the `_raw` suffixed topics.

### Command Topics (Subscribed by the service)

You can control the fan by publishing messages to these command topics:

- `haiku_fan/power/set` - Set fan power (payload: `ON` or `OFF`)
- `haiku_fan/speed/set` - Set fan speed (payload: `0` to `7` for raw, or `0` to `100` for percentage)
- `haiku_fan/light_power/set` - Set light power (payload: `ON` or `OFF`)
- `haiku_fan/light_level/set` - Set light brightness (payload: `0` to `16` for raw, or `0` to `100` for percentage)

**Note**: The `speed/set` and `light_level/set` topics accept both raw values and percentage values. Values > 7 for speed or > 16 for light level are automatically interpreted as percentages and converted to the appropriate raw value. This allows seamless integration with OpenHAB dimmers and similar controllers.

#### Examples

Turn fan on:
```bash
mosquitto_pub -h localhost -t "haiku_fan/power/set" -m "ON"
```

Set fan speed to 5 (raw value):
```bash
mosquitto_pub -h localhost -t "haiku_fan/speed/set" -m "5"
```

Set fan speed to 50% (percentage):
```bash
mosquitto_pub -h localhost -t "haiku_fan/speed/set" -m "50"
```

Turn light on:
```bash
mosquitto_pub -h localhost -t "haiku_fan/light_power/set" -m "ON"
```

Set light brightness to 10 (raw value):
```bash
mosquitto_pub -h localhost -t "haiku_fan/light_level/set" -m "10"
```

Set light brightness to 75% (percentage):
```bash
mosquitto_pub -h localhost -t "haiku_fan/light_level/set" -m "75"
```

### OpenHAB Integration

For OpenHAB, configure your items with dimmers that send percentage values:

**things:**
```
Type switch : mqtt_bigassfan_power     "BigAssFan Power"       [ stateTopic="haiku_fan/power", commandTopic="haiku_fan/power/set" ]
Type dimmer : mqtt_bigassfan_speed     "BigAssFan Speed"       [ stateTopic="haiku_fan/speed", commandTopic="haiku_fan/speed/set" ]
Type switch : mqtt_bigassfan_lightpwr  "BigAssFan Light Power" [ stateTopic="haiku_fan/light_power", commandTopic="haiku_fan/light_power/set" ]
Type dimmer : mqtt_bigassfan_light     "BigAssFan Light Level" [ stateTopic="haiku_fan/light_level", commandTopic="haiku_fan/light_level/set" ]
```

**items:**
```
Switch BigAssFan_Power       "BigAssFan Power"       { channel="mqtt:topic:oha21b14:mqtt_bigassfan_power" }
Dimmer BigAssFan_Speed       "BigAssFan Speed"       { channel="mqtt:topic:oha21b14:mqtt_bigassfan_speed" }
Switch BigAssFan_LightPower  "BigAssFan Light Power" { channel="mqtt:topic:oha21b14:mqtt_bigassfan_lightpwr" }
Dimmer BigAssFan_Light       "BigAssFan Light"       { channel="mqtt:topic:oha21b14:mqtt_bigassfan_light" }
```

The service automatically converts between percentage values (0-100) from OpenHAB dimmers and the raw values (0-7 for speed, 0-16 for light) required by the fan.

## SenseMe Protocol

This project uses the SenseMe protocol for communicating with Haiku fans. The protocol is documented at:
https://bruce.pennypacker.org/2015/07/17/hacking-bigass-fans-with-senseme/

## Ports

- `1919`: Web interface and nginx reverse proxy
- `8000`: Backend API (internal to Docker network)
- `1883`: MQTT broker
- `9001`: MQTT websocket (optional)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
