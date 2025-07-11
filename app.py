from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🔒 Whitelist of allowed device IDs
AUTHORIZED_DEVICES = {"esp32_1", "esp32_2", "esp32_alpha"}

# Store timers by device ID
device_timers = {}

@app.route('/')
def home():
    return "Timer API is running!"

# POST /set_timer - from website
@app.route('/set_timer', methods=['POST'])
def set_timer():
    data = request.get_json()
    device_id = data.get('device_id')
    seconds = data.get('seconds')

    if not device_id or seconds is None:
        return jsonify({"error": "Missing data"}), 400

    # 🔒 Check if device_id is allowed
    if device_id not in AUTHORIZED_DEVICES:
        return jsonify({"error": "Unauthorized device ID"}), 403

    # Save timer
    device_timers[device_id] = {
        "seconds": seconds,
        "status": "pending"
    }

    return jsonify({"status": "Timer set"}), 200

# GET /get_timer - from ESP32
@app.route('/get_timer', methods=['GET'])
def get_timer():
    device_id = request.args.get('device_id')

    if not device_id:
        return jsonify({"error": "Missing device_id"}), 400

    # 🔒 Check if device_id is allowed
    if device_id not in AUTHORIZED_DEVICES:
        return jsonify({"error": "Unauthorized device ID"}), 403

    timer = device_timers.get(device_id)

    if not timer or timer['status'] != "pending":
        return jsonify({"seconds": None}), 200  # No timer set

    # Mark it used so ESP32 doesn't repeat
    timer['status'] = "used"
    return jsonify({"seconds": timer["seconds"]}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)