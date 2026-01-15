from flask import Flask, jsonify
import paho.mqtt.client as mqtt
import os
import logging
import json
import threading
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MQTT_SERVER = os.environ.get('MQTT_SERVER', '192.168.1.88')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USER = os.environ.get('MQTT_USER', 'mqtt')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', 'mqtt')
MQTT_BASE_TOPIC = os.environ.get('MQTT_BASE_TOPIC', 'zigbee2mqtt')
CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))  # 5 minutes default

# Data storage
_mqtt_data = {
    'bridge_info': None,
    'devices': None,
    'last_update': 0,
    'connected': False
}

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        logger.info("Connected to MQTT broker")
        _mqtt_data['connected'] = True
        # Subscribe to bridge topics
        client.subscribe(f"{MQTT_BASE_TOPIC}/bridge/info")
        client.subscribe(f"{MQTT_BASE_TOPIC}/bridge/devices")
        logger.info(f"Subscribed to {MQTT_BASE_TOPIC}/bridge/#")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")
        _mqtt_data['connected'] = False

def on_disconnect(client, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    logger.warning(f"Disconnected from MQTT broker, return code {rc}")
    _mqtt_data['connected'] = False

def on_message(client, userdata, msg):
    """Callback when a message is received"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode('utf-8'))

        if topic == f"{MQTT_BASE_TOPIC}/bridge/info":
            _mqtt_data['bridge_info'] = payload
            _mqtt_data['last_update'] = time.time()
            logger.info("Updated bridge info")
        elif topic == f"{MQTT_BASE_TOPIC}/bridge/devices":
            _mqtt_data['devices'] = payload
            _mqtt_data['last_update'] = time.time()
            logger.info(f"Updated devices list ({len(payload)} devices)")
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

def calculate_stats():
    """Calculate statistics from MQTT data"""
    if not _mqtt_data['devices'] or not _mqtt_data['bridge_info']:
        raise ValueError("No data available from Zigbee2MQTT")

    devices = _mqtt_data['devices']
    bridge_info = _mqtt_data['bridge_info']

    # Calculate statistics
    total_devices = 0
    online_devices = 0
    offline_devices = 0
    battery_low = 0
    router_devices = 0
    end_devices = 0

    for device in devices:
        # Skip the coordinator
        if device.get('type') == 'Coordinator':
            continue

        total_devices += 1

        # Check if device is online (available)
        if device.get('supported') is not False:
            # Check last_seen or availability
            if device.get('available', False):
                online_devices += 1
            else:
                offline_devices += 1
        else:
            offline_devices += 1

        # Check battery level
        power_source = device.get('power_source')
        if power_source == 'Battery':
            definition = device.get('definition', {})
            if definition:
                # Battery devices have battery percentage in exposes
                exposes = definition.get('exposes', [])
                for expose in exposes:
                    if expose.get('name') == 'battery' and expose.get('property') == 'battery':
                        # Device has battery - check if it's low
                        # We'll mark it as "battery_low" candidate
                        # Note: actual battery level is in device state, not in device list
                        # For now, we'll just count battery devices
                        pass

        # Count device types
        device_type = device.get('type')
        if device_type == 'Router':
            router_devices += 1
        elif device_type == 'EndDevice':
            end_devices += 1

    # Get coordinator version and permit_join
    coordinator_version = bridge_info.get('version', 'unknown')
    permit_join = bridge_info.get('permit_join', False)

    result = {
        'total_devices': total_devices,
        'online_devices': online_devices,
        'offline_devices': offline_devices,
        'battery_low': battery_low,  # Note: requires device state data
        'router_devices': router_devices,
        'end_devices': end_devices,
        'coordinator_version': coordinator_version,
        'permit_join': permit_join
    }

    return result

def start_mqtt_client():
    """Start MQTT client in background thread"""
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        logger.info(f"Connecting to MQTT broker at {MQTT_SERVER}:{MQTT_PORT}")
        client.connect(MQTT_SERVER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        logger.error(f"Error starting MQTT client: {e}")

# Start MQTT client in background thread
mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
mqtt_thread.start()

# Wait a bit for initial connection and data
time.sleep(2)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    if _mqtt_data['connected']:
        return 'OK', 200
    else:
        return 'MQTT not connected', 503

@app.route('/stats', methods=['GET'])
def stats():
    """Get Zigbee2MQTT statistics"""
    try:
        if not _mqtt_data['connected']:
            return jsonify({'error': 'MQTT not connected'}), 503

        stats_data = calculate_stats()
        return jsonify(stats_data), 200
    except ValueError as e:
        logger.error(f"Error calculating stats: {e}")
        return jsonify({'error': str(e)}), 503
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
