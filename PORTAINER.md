# Portainer Deployment Guide

This guide explains how to deploy the Haiku Fan MQTT Bridge using Portainer.

## Prerequisites

- Portainer installed and running
- Access to your Portainer instance
- Knowledge of your Haiku fan's IP address

## Deployment Steps

### Method 1: Using Git Repository (Recommended)

1. **Login to Portainer**
   - Navigate to your Portainer web interface

2. **Add a New Stack**
   - Go to "Stacks" in the left menu
   - Click "Add stack"
   - Enter a name: `haiku-fan-mqtt-bridge`

3. **Configure Repository**
   - Select "Git Repository" as the build method
   - Repository URL: `https://github.com/AgentP9/piniBigAssFanMQTT`
   - Repository reference: `main` (or your preferred branch)
   - Compose path: `docker-compose.yml`

4. **Set Environment Variables**
   In the environment variables section, add:
   
   ```
   FAN_IP=192.168.1.100          # Replace with your fan's IP
   MQTT_BROKER=mosquitto
   MQTT_PORT=1883
   POLL_INTERVAL=30
   ```

5. **Deploy**
   - Click "Deploy the stack"
   - Wait for the deployment to complete

### Method 2: Using Web Editor

1. **Login to Portainer**
   - Navigate to your Portainer web interface

2. **Add a New Stack**
   - Go to "Stacks" in the left menu
   - Click "Add stack"
   - Enter a name: `haiku-fan-mqtt-bridge`

3. **Copy Docker Compose Content**
   - Select "Web editor"
   - Copy the entire content of `docker-compose.yml` from the repository

4. **Set Environment Variables**
   In the environment variables section, add:
   
   ```
   FAN_IP=192.168.1.100          # Replace with your fan's IP
   MQTT_BROKER=mosquitto
   MQTT_PORT=1883
   POLL_INTERVAL=30
   ```

5. **Deploy**
   - Click "Deploy the stack"
   - Wait for the deployment to complete

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FAN_IP` | IP address of your Haiku fan | 192.168.1.100 | Yes |
| `MQTT_BROKER` | MQTT broker hostname | mosquitto | Yes |
| `MQTT_PORT` | MQTT broker port | 1883 | No |
| `POLL_INTERVAL` | Polling interval in seconds | 30 | No |

## Post-Deployment Verification

### 1. Check Container Status

In Portainer:
- Go to "Stacks" → Select your stack
- Verify all three containers are running:
  - `haiku-fan-backend`
  - `haiku-fan-frontend`
  - `haiku-fan-mqtt`

### 2. Check Logs

For each container:
- Click on the container name
- Go to "Logs"
- Look for successful connection messages

**Expected Backend Logs:**
```
Connected to fan at 192.168.1.100:31415
Successfully connected to MQTT broker
Starting fan state polling thread
```

### 3. Access the Web Interface

- Navigate to: `http://<your-host>:1919`
- You should see the fan control interface
- Connection status should show "Connected" for both fan and MQTT

### 4. Test API

```bash
curl http://<your-host>:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "fan_connected": true,
  "mqtt_connected": true
}
```

## Updating the Stack

### To Update Configuration

1. Go to "Stacks" → Select your stack
2. Click "Editor"
3. Modify environment variables as needed
4. Click "Update the stack"

### To Update Code

If you deployed using Git repository:
1. Go to "Stacks" → Select your stack
2. Click "Pull and redeploy"
3. Portainer will pull the latest code and redeploy

If you deployed using Web editor:
1. Pull latest code from GitHub
2. Go to "Stacks" → Select your stack
3. Click "Editor"
4. Update the docker-compose.yml content
5. Click "Update the stack"

## Network Considerations

### Accessing the Fan

The backend container needs to reach your Haiku fan on the network. Consider:

- **Host Network Mode**: If the fan is on the same network as your Portainer host
  - Modify `docker-compose.yml` to use `network_mode: host` for the backend
  
- **Bridge Mode** (default): Works if Docker can route to your fan's network
  - May require additional routing configuration
  
- **Macvlan**: For complex network setups
  - Create a macvlan network in Portainer
  - Attach the backend container to it

### Port Mapping

By default, these ports are exposed:
- `1919`: Web interface (nginx)
- `8000`: Backend API (optional, can be removed if only using web interface)
- `1883`: MQTT broker

Make sure these ports are not in use by other services.

## Troubleshooting

### Fan Not Connecting

**Symptom**: Backend logs show "Failed to connect to fan"

**Solutions**:
1. Verify `FAN_IP` is correct
2. Check network connectivity from container to fan:
   ```bash
   # In Portainer, open console for backend container
   ping <FAN_IP>
   telnet <FAN_IP> 31415
   ```
3. Consider using host network mode if on same network

### MQTT Not Working

**Symptom**: No MQTT messages being published

**Solutions**:
1. Check mosquitto container is running
2. Verify `MQTT_BROKER` environment variable
3. Check mosquitto logs for errors

### Web Interface Not Accessible

**Symptom**: Cannot access port 1919

**Solutions**:
1. Verify frontend container is running
2. Check if port 1919 is mapped correctly in Portainer
3. Check nginx logs for errors

### Permission Issues

**Symptom**: Volume mount errors

**Solutions**:
1. Ensure Portainer has permissions to create volumes
2. Check volume configuration in stack settings

### Config File Mount Errors

**Symptom**: Error like "not a directory: Are you trying to mount a directory onto a file (or vice-versa)?"

**Cause**: This typically occurs with direct file bind mounts when deploying from Git repositories.

**Solution**: 
The project now uses Docker configs instead of bind mounts for the mosquitto.conf file, which resolves this issue. If you're experiencing this error:
1. Ensure you're using the latest version of docker-compose.yml
2. Check that the `configs` section is present in your stack configuration
3. Verify the mosquitto service uses `configs` instead of a volume mount for mosquitto.conf

## Advanced Configuration

### Custom MQTT Configuration

The mosquitto configuration is managed using Docker configs, which provides better compatibility with Portainer deployments.

To modify mosquitto configuration:

**Option 1: Modify in Repository (Recommended)**
1. Edit the `mosquitto.conf` file in the repository
2. Commit and push changes (or pull and redeploy if using Git repository method in Portainer)

**Option 2: Use Custom Config File**
1. In Portainer, go to your stack editor
2. Modify the `configs` section to point to your custom file:
   ```yaml
   configs:
     mosquitto_config:
       file: /path/to/your/custom/mosquitto.conf
   ```

Note: The default configuration uses Docker configs instead of volume mounts to avoid file/directory mount conflicts during deployment.

### SSL/TLS Configuration

For production deployments:
1. Set up a reverse proxy (Traefik, Nginx Proxy Manager)
2. Configure SSL certificates
3. Update environment variables to use secure connections

### Authentication

Consider adding:
- API authentication (JWT tokens)
- MQTT authentication (username/password)
- Nginx basic authentication

## Monitoring

### Using Portainer

- View real-time logs in the "Logs" tab
- Monitor resource usage in the "Stats" tab
- Set up health checks in container configuration

### Using External Tools

- Connect MQTT monitoring tools to port 1883
- Use API monitoring tools to track API health
- Set up alerts for container status changes

## Backup and Restore

### Backup

1. Export stack configuration from Portainer
2. Backup MQTT data volume:
   ```bash
   docker run --rm -v haiku-fan-mqtt-bridge_mosquitto-data:/data \
     -v /backup:/backup alpine \
     tar czf /backup/mqtt-data.tar.gz -C /data .
   ```

### Restore

1. Import stack configuration to Portainer
2. Restore MQTT data volume:
   ```bash
   docker run --rm -v haiku-fan-mqtt-bridge_mosquitto-data:/data \
     -v /backup:/backup alpine \
     tar xzf /backup/mqtt-data.tar.gz -C /data
   ```

## Support

For issues or questions:
- Check the [TESTING.md](TESTING.md) document
- Review logs in Portainer
- Open an issue on GitHub
