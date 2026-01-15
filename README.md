# Zigbee2MQTT Proxy

A lightweight HTTP API proxy for Zigbee2MQTT that exposes device statistics in a format compatible with Homepage dashboard widgets.

## Features

- Health check endpoint
- Statistics endpoint returning device counts and network health
- Configurable cache timeout (default: 5 minutes)
- Lightweight Flask-based API
- Docker container ready

## Environment Variables

- `ZIGBEE2MQTT_URL` - Base URL for Zigbee2MQTT web interface (default: `http://zigbee2mqtt:8080`)
- `CACHE_TIMEOUT` - Cache duration in seconds (default: `300` / 5 minutes)

## Endpoints

### GET /health
Returns `OK` with status 200 if the service is running.

### GET /stats
Returns Zigbee2MQTT statistics in JSON format:

```json
{
    "total_devices": 45,
    "online_devices": 43,
    "offline_devices": 2,
    "battery_low": 2,
    "router_devices": 15,
    "end_devices": 30,
    "coordinator_version": "1.35.0",
    "permit_join": false
}
```

Where:
- `total_devices`: Total number of Zigbee devices (excluding coordinator)
- `online_devices`: Number of devices that have reported recently
- `offline_devices`: Number of devices not responding
- `battery_low`: Number of battery-powered devices with < 20% battery
- `router_devices`: Number of router/repeater devices
- `end_devices`: Number of end devices (sensors, switches, etc.)
- `coordinator_version`: Zigbee2MQTT version
- `permit_join`: Whether the network is accepting new devices

## Docker Usage

```bash
docker run -d \
  --name zigbee2mqtt-proxy \
  -p 5153:5000 \
  -e ZIGBEE2MQTT_URL=http://zigbee2mqtt:8080 \
  -e CACHE_TIMEOUT=300 \
  ghcr.io/lioncitygaming/zigbee2mqtt-proxy:latest
```

## Docker Compose

```yaml
services:
  zigbee2mqtt-proxy:
    image: ghcr.io/lioncitygaming/zigbee2mqtt-proxy:latest
    container_name: zigbee2mqtt-proxy
    ports:
      - "5153:5000"
    environment:
      - ZIGBEE2MQTT_URL=http://zigbee2mqtt:8080
      - CACHE_TIMEOUT=300
    restart: unless-stopped
```

## Homepage Widget Configuration

Add this to your Homepage `services.yaml`:

```yaml
- Zigbee2MQTT:
    icon: zigbee2mqtt.png
    href: http://your-server:8080
    description: Zigbee Network
    widget:
        type: customapi
        url: http://your-server:5153/stats
        refreshInterval: 300000  # 5 minutes
        mappings:
            - field: total_devices
              label: Devices
              format: number
            - field: online_devices
              label: Online
              format: number
            - field: battery_low
              label: Low Battery
              format: number
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
export ZIGBEE2MQTT_URL=http://localhost:8080
python app.py
```

## Notes

- Requires Zigbee2MQTT with the web interface enabled (frontend enabled in configuration)
- The API is read-only and does not modify any Zigbee2MQTT settings
- Statistics are cached for the configured timeout period

## License

MIT
