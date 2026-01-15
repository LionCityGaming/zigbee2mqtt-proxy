from flask import Flask, jsonify
import requests
import os
import logging
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zigbee2MQTT configuration from environment variables
ZIGBEE2MQTT_URL = os.environ.get('ZIGBEE2MQTT_URL', 'http://zigbee2mqtt:8080')
CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))  # 5 minutes default

# Stats cache
_stats_cache = {
    'stats': None,
    'last_fetch': 0
}

def get_zigbee2mqtt_stats():
    """Fetch statistics from Zigbee2MQTT API"""
    # Check cache first
    now = time.time()
    if (_stats_cache['stats'] and
        now - _stats_cache['last_fetch'] < CACHE_TIMEOUT):
        logger.info("Returning cached stats")
        return _stats_cache['stats']

    try:
        # Get bridge info
        info_response = requests.get(
            f'{ZIGBEE2MQTT_URL}/api/info',
            timeout=10
        )
        info_response.raise_for_status()
        info_data = info_response.json()

        # Get all devices
        devices_response = requests.get(
            f'{ZIGBEE2MQTT_URL}/api/devices',
            timeout=10
        )
        devices_response.raise_for_status()
        devices_data = devices_response.json()

        # Calculate statistics
        total_devices = len(devices_data)
        online_devices = 0
        offline_devices = 0
        battery_low = 0
        router_devices = 0
        end_devices = 0

        for device in devices_data:
            # Skip the coordinator
            if device.get('type') == 'Coordinator':
                continue

            # Check if device is online (available)
            if device.get('supported') is not False:
                # Check last_seen or availability
                last_seen = device.get('last_seen')
                if last_seen and last_seen != 'N/A':
                    online_devices += 1
                else:
                    offline_devices += 1

            # Check battery level
            battery = device.get('power_source')
            battery_level = device.get('battery')
            if battery == 'Battery' and battery_level:
                if battery_level < 20:
                    battery_low += 1

            # Count device types
            device_type = device.get('type')
            if device_type == 'Router':
                router_devices += 1
            elif device_type == 'EndDevice':
                end_devices += 1

        # Get coordinator version
        coordinator_version = info_data.get('version', 'unknown')
        permit_join = info_data.get('permit_join', False)

        result = {
            'total_devices': total_devices - 1,  # Exclude coordinator from count
            'online_devices': online_devices,
            'offline_devices': offline_devices,
            'battery_low': battery_low,
            'router_devices': router_devices,
            'end_devices': end_devices,
            'coordinator_version': coordinator_version,
            'permit_join': permit_join
        }

        # Update cache
        _stats_cache['stats'] = result
        _stats_cache['last_fetch'] = now

        logger.info(f"Fetched stats: {result}")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Zigbee2MQTT stats: {e}")
        raise

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return 'OK', 200

@app.route('/stats', methods=['GET'])
def stats():
    """Get Zigbee2MQTT statistics"""
    try:
        stats_data = get_zigbee2mqtt_stats()
        return jsonify(stats_data), 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Zigbee2MQTT stats: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
