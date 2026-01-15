# Zigbee2MQTT Proxy

A lightweight HTTP API proxy for Zigbee2MQTT that connects to the MQTT broker and exposes device statistics in a format compatible with Homepage dashboard widgets.

## Features

- Health check endpoint
- Statistics endpoint returning device counts and network health
- MQTT-based real-time data collection
- Lightweight Flask-based API
- Docker container ready

## Environment Variables

- `MQTT_SERVER` - MQTT broker server address (default: `192.168.1.88`)
- `MQTT_PORT` - MQTT broker port (default: `1883`)
- `MQTT_USER` - MQTT username (default: `mqtt`)
- `MQTT_PASSWORD` - MQTT password (default: `mqtt`)
- `MQTT_BASE_TOPIC` - Zigbee2MQTT base topic (default: `zigbee2mqtt`)
- `CACHE_TIMEOUT` - Cache duration in seconds (default: `300` / 5 minutes)

## Finding Your MQTT Configuration

The MQTT settings are in your Zigbee2MQTT `configuration.yaml`:

```yaml
mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://192.168.1.88:1883
  user: mqtt
  password: mqtt
```

## Endpoints

### GET /health
Returns `OK` with status 200 if the service is running and connected to MQTT.

### GET /stats
Returns Zigbee2MQTT statistics in JSON format:

```json
{
    "total_devices": 18,
    "online_devices": 16,
    "offline_devices": 2,
    "battery_low": 0,
    "router_devices": 2,
    "end_devices": 16,
    "coordinator_version": "1.35.0",
    "permit_join": false
}
```

Where:
- `total_devices`: Total number of Zigbee devices (excluding coordinator)
- `online_devices`: Number of devices that are currently available
- `offline_devices`: Number of devices not responding
- `battery_low`: Number of battery-powered devices with low battery (placeholder - requires device state data)
- `router_devices`: Number of router/repeater devices
- `end_devices`: Number of end devices (sensors, switches, etc.)
- `coordinator_version`: Zigbee2MQTT version
- `permit_join`: Whether the network is accepting new devices

## Docker Usage

```bash
docker run -d \
  --name zigbee2mqtt-proxy \
  -p 6337:5000 \
  -e MQTT_SERVER=192.168.1.88 \
  -e MQTT_PORT=1883 \
  -e MQTT_USER=mqtt \
  -e MQTT_PASSWORD=mqtt \
  -e MQTT_BASE_TOPIC=zigbee2mqtt \
  ghcr.io/lioncitygaming/zigbee2mqtt-proxy:latest
```

## Docker Compose

```yaml
services:
  zigbee2mqtt-proxy:
    image: ghcr.io/lioncitygaming/zigbee2mqtt-proxy:latest
    container_name: zigbee2mqtt-proxy
    ports:
      - "6337:5000"
    environment:
      - MQTT_SERVER=192.168.1.88
      - MQTT_PORT=1883
      - MQTT_USER=mqtt
      - MQTT_PASSWORD=mqtt
      - MQTT_BASE_TOPIC=zigbee2mqtt
    restart: unless-stopped
```

## Homepage Widget Configuration

Add this to your Homepage `services.yaml`:

```yaml
- Zigbee2MQTT:
    icon: zigbee2mqtt.png
    href: http://192.168.1.88:6336
    description: Zigbee Network
    widget:
        type: customapi
        url: http://192.168.1.88:6337/stats
        refreshInterval: 300000  # 5 minutes
        mappings:
            - field: total_devices
              label: Devices
              format: number
            - field: online_devices
              label: Online
              format: number
            - field: router_devices
              label: Routers
              format: number
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
export MQTT_SERVER=192.168.1.88
export MQTT_USER=mqtt
export MQTT_PASSWORD=mqtt
python app.py
```

## Notes

- Requires access to the same MQTT broker that Zigbee2MQTT uses
- The API is read-only and does not modify any Zigbee2MQTT settings
- Connects to MQTT on startup and maintains a persistent connection
- Battery level detection requires additional device state monitoring (future enhancement)

## License

MIT
