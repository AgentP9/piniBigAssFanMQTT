# API Documentation

The Haiku Fan MQTT Bridge provides a RESTful API for controlling and monitoring your BigAssFan Haiku fan.

## Base URL

When running locally:
```
http://localhost:8000
```

When deployed via Docker:
```
http://<your-host>:8000
```

When accessed through the frontend:
```
http://<your-host>:1919/api
```

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### Health & Status

#### Get Health Status
```http
GET /health
```

Returns the health status and connection state of the service.

**Response**
```json
{
  "status": "healthy",
  "fan_connected": true,
  "mqtt_connected": true
}
```

#### Get Service Info
```http
GET /
```

Returns basic service information.

**Response**
```json
{
  "service": "Haiku Fan MQTT Bridge",
  "version": "1.0.0",
  "status": "running"
}
```

### Fan State

#### Get All Fan States
```http
GET /api/fan/state
```

Returns all current states of the fan.

**Response**
```json
{
  "name": "Living Room Fan",
  "power": "ON",
  "speed": 3,
  "whoosh": "OFF",
  "light_power": "ON",
  "light_level": 10
}
```

### Fan Power Control

#### Get Fan Power State
```http
GET /api/fan/power
```

**Response**
```json
{
  "power": "ON"
}
```

#### Set Fan Power State
```http
POST /api/fan/power
```

**Request Body**
```json
{
  "state": "ON"
}
```

**Parameters**
- `state` (string, required): Either "ON" or "OFF"

**Response**
```json
{
  "success": true,
  "power": "ON"
}
```

**Error Response**
```json
{
  "detail": "Failed to set fan power"
}
```

### Fan Speed Control

#### Get Fan Speed
```http
GET /api/fan/speed
```

**Response**
```json
{
  "speed": 3
}
```

#### Set Fan Speed
```http
POST /api/fan/speed
```

**Request Body**
```json
{
  "speed": 5
}
```

**Parameters**
- `speed` (integer, required): Speed level from 0 to 7

**Response**
```json
{
  "success": true,
  "speed": 5
}
```

### Whoosh Mode Control

#### Get Whoosh Mode State
```http
GET /api/fan/whoosh
```

**Response**
```json
{
  "whoosh": "OFF"
}
```

#### Set Whoosh Mode State
```http
POST /api/fan/whoosh
```

**Request Body**
```json
{
  "state": "ON"
}
```

**Parameters**
- `state` (string, required): Either "ON" or "OFF"

**Response**
```json
{
  "success": true,
  "whoosh": "ON"
}
```

### Light Power Control

#### Get Light Power State
```http
GET /api/light/power
```

**Response**
```json
{
  "power": "ON"
}
```

#### Set Light Power State
```http
POST /api/light/power
```

**Request Body**
```json
{
  "state": "ON"
}
```

**Parameters**
- `state` (string, required): Either "ON" or "OFF"

**Response**
```json
{
  "success": true,
  "power": "ON"
}
```

### Light Brightness Control

#### Get Light Brightness Level
```http
GET /api/light/level
```

**Response**
```json
{
  "level": 10
}
```

#### Set Light Brightness Level
```http
POST /api/light/level
```

**Request Body**
```json
{
  "level": 12
}
```

**Parameters**
- `level` (integer, required): Brightness level from 0 to 16

**Response**
```json
{
  "success": true,
  "level": 12
}
```

## Error Responses

All endpoints may return the following error responses:

### 503 Service Unavailable
Returned when the service cannot connect to the fan or perform the requested operation.

```json
{
  "detail": "SenseMe client not initialized"
}
```

### 500 Internal Server Error
Returned when an operation fails.

```json
{
  "detail": "Failed to set fan speed"
}
```

### 422 Validation Error
Returned when request parameters are invalid.

```json
{
  "detail": [
    {
      "loc": ["body", "speed"],
      "msg": "ensure this value is less than or equal to 7",
      "type": "value_error.number.not_le"
    }
  ]
}
```

## CORS

The API supports CORS and allows requests from any origin. This is configured in the FastAPI application:

```python
allow_origins=["*"]
```

For production deployments, consider restricting this to specific origins.

## Rate Limiting

Currently, there is no rate limiting implemented. For production use, consider adding rate limiting middleware.

## Examples

### Using cURL

#### Get fan state
```bash
curl http://localhost:8000/api/fan/state
```

#### Turn fan on
```bash
curl -X POST http://localhost:8000/api/fan/power \
  -H "Content-Type: application/json" \
  -d '{"state":"ON"}'
```

#### Set fan speed
```bash
curl -X POST http://localhost:8000/api/fan/speed \
  -H "Content-Type: application/json" \
  -d '{"speed":5}'
```

#### Turn light on
```bash
curl -X POST http://localhost:8000/api/light/power \
  -H "Content-Type: application/json" \
  -d '{"state":"ON"}'
```

#### Set light brightness
```bash
curl -X POST http://localhost:8000/api/light/level \
  -H "Content-Type: application/json" \
  -d '{"level":12}'
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Get fan state
response = requests.get(f"{BASE_URL}/api/fan/state")
print(response.json())

# Turn fan on
response = requests.post(
    f"{BASE_URL}/api/fan/power",
    json={"state": "ON"}
)
print(response.json())

# Set fan speed
response = requests.post(
    f"{BASE_URL}/api/fan/speed",
    json={"speed": 5}
)
print(response.json())
```

### Using JavaScript

```javascript
const BASE_URL = "http://localhost:8000";

// Get fan state
fetch(`${BASE_URL}/api/fan/state`)
  .then(response => response.json())
  .then(data => console.log(data));

// Turn fan on
fetch(`${BASE_URL}/api/fan/power`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ state: 'ON' })
})
  .then(response => response.json())
  .then(data => console.log(data));

// Set fan speed
fetch(`${BASE_URL}/api/fan/speed`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ speed: 5 })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## WebSocket Support

Currently, the API does not support WebSockets. For real-time updates, consider:
1. Polling the `/api/fan/state` endpoint
2. Subscribing to MQTT topics (see MQTT documentation)

## Authentication

The current implementation does not include authentication. For production use, consider implementing:
- API keys
- JWT tokens
- OAuth2

## Versioning

The current API version is 1.0.0. Future versions will maintain backward compatibility or use path-based versioning (e.g., `/v2/api/fan/state`).
