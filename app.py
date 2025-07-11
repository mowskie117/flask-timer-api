from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from supabase import create_client, Client
import os

app = Flask(__name__)
CORS(app)

# 🔐 Replace with your Supabase values
SUPABASE_URL = "https://rdwucvlksaqsajawyhrf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJkd3Vjdmxrc2Fxc2FqYXd5aHJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIyNTIyNDAsImV4cCI6MjA2NzgyODI0MH0.t-oQb-8u0pOGy9V6L4seNcuG52z8UwJ3d2IZhkkWCUI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

AUTHORIZED_DEVICES = {"esp32_1", "esp32_2", "esp32_alpha"}

@app.route('/')
def home():
    return "Timer API is running!"

@app.route('/set_timer', methods=['POST'])
def set_timer():
    data = request.get_json()
    device_id = data.get('device_id')
    seconds = data.get('seconds')

    if not device_id or seconds is None:
        return jsonify({"error": "Missing data"}), 400

    # 🔐 Check Supabase for valid device
    result = supabase.table("authorized_devices").select("device_id").eq("device_id", device_id).execute()
    if not result.data:
        return jsonify({"error": "Unauthorized device ID"}), 403

    now = datetime.utcnow().isoformat()

    # Set or update timer in timers table
    timer_check = supabase.table("timers").select("device_id").eq("device_id", device_id).execute()

    if timer_check.data:
        supabase.table("timers").update({
            "seconds": seconds,
            "status": "pending",
            "set_time": now
        }).eq("device_id", device_id).execute()
    else:
        supabase.table("timers").insert({
            "device_id": device_id,
            "seconds": seconds,
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
        return jsonify({"seconds": None}), 200

    # Mark as used
    supabase.table("timers").update({"status": "used"}).eq("device_id", device_id).execute()

    return jsonify({"seconds": timer['seconds']}), 200

if __name__ == '__main__':
    app.run()
