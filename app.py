from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from supabase import create_client, Client
import os

app = Flask(__name__)
CORS(app)

# Supabase config
SUPABASE_URL = "https://nbxfieyuphlserxjylja.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ieGZpZXl1cGhsc2VyeGp5bGphIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMwOTQ3NTcsImV4cCI6MjA2ODY3MDc1N30.kvR709TEs-Ixp48DWhow4539qHrax6YCnu2DF3a0DQ8"  # You can keep it for now
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

AUTHORIZED_DEVICES = {"esp32_1", "esp32_2", "esp32_alpha"}

@app.route('/')
def home():
    return "Timer API is running!"

@app.route('/set_timer', methods=['POST'])
def set_timer():
    data = request.get_json()
    device_id = data.get('device_id')
    target_time = data.get('target_time')  # ISO 8601 timestamp string

    if not device_id or not target_time:
        return jsonify({"error": "Missing device_id or target_time"}), 400

    # Check Supabase if device is authorized
    result = supabase.table("authorized_devices").select("device_id").eq("device_id", device_id).execute()
    if not result.data:
        return jsonify({"error": "Unauthorized device ID"}), 403

    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # Insert or update timer
    timer_check = supabase.table("timers").select("*").eq("device_id", device_id).execute()

    if timer_check.data:
        supabase.table("timers").update({
            "target_time": target_time,
            "status": "pending",
            "set_time": now
        }).eq("device_id", device_id).execute()
    else:
        supabase.table("timers").insert({
            "device_id": device_id,
            "target_time": target_time,
            "status": "pending",
            "set_time": now
        }).execute()

    return jsonify({"status": "Timer set"}), 200

@app.route('/get_timer', methods=['GET'])
def get_timer():
    device_id = request.args.get('device_id')

    if not device_id:
        return jsonify({"error": "Missing device_id"}), 400
    if device_id not in AUTHORIZED_DEVICES:
        return jsonify({"error": "Unauthorized device ID"}), 403

    result = supabase.table("timers").select("*").eq("device_id", device_id).execute()
    timer = result.data[0] if result.data else None

    if not timer or timer['status'] != "pending":
        return jsonify({"target_time": None}), 200

    # Mark as used
    supabase.table("timers").update({"status": "used"}).eq("device_id", device_id).execute()

    return jsonify({"target_time": timer['target_time']}), 200

if __name__ == '__main__':
    app.run()
