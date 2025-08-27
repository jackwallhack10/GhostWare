from flask import Flask, request, jsonify, render_template_string
import json
import os
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
key_file = "keys.json"

# Load existing keys
if os.path.exists(key_file):
    with open(key_file, "r") as f:
        keys_data = json.load(f)
else:
    keys_data = {}

def save_keys():
    with open(key_file, "w") as f:
        json.dump(keys_data, f, indent=4)

def generate_key(duration_minutes=60):
    key = secrets.token_urlsafe(16)
    expire_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
    keys_data[key] = {
        "expires": expire_time.isoformat(),
        "paused": False,
        "hwid": None  # will lock to first HWID
    }
    save_keys()
    return key

# ------------------- API Endpoints -------------------

@app.route("/validate_key", methods=["POST"])
def validate_key():
    content = request.get_json() or {}
    key = content.get("key")
    hwid = content.get("hwid")
    if not key or key not in keys_data:
        return jsonify({"valid": False, "reason": "Key not found"}), 400
    
    key_info = keys_data[key]
    
    if key_info["paused"]:
        return jsonify({"valid": False, "reason": "Key paused"}), 400
    if datetime.utcnow() > datetime.fromisoformat(key_info["expires"]):
        return jsonify({"valid": False, "reason": "Key expired"}), 400
    
    # HWID lock check
    if key_info["hwid"] is None:
        key_info["hwid"] = hwid  # first use locks it
        save_keys()
    elif key_info["hwid"] != hwid:
        return jsonify({"valid": False, "reason": "HWID locked"}), 403
    
    return jsonify({"valid": True})

# Pause/unpause key
@app.route("/key/<key>/pause", methods=["POST"])
def pause_key(key):
    if key not in keys_data:
        return jsonify({"status": "error", "message": "Key not found"}), 404
    keys_data[key]["paused"] = True
    save_keys()
    return jsonify({"status": "success", "key": key, "paused": True})

@app.route("/key/<key>/unpause", methods=["POST"])
def unpause_key(key):
    if key not in keys_data:
        return jsonify({"status": "error", "message": "Key not found"}), 404
    keys_data[key]["paused"] = False
    save_keys()
    return jsonify({"status": "success", "key": key, "paused": False})

# Delete key
@app.route("/key/<key>/delete", methods=["POST"])
def delete_key(key):
    if key not in keys_data:
        return jsonify({"status": "error", "message": "Key not found"}), 404
    del keys_data[key]
    save_keys()
    return jsonify({"status": "success", "deleted": key})

# Reset HWID
@app.route("/key/<key>/reset_hwid", methods=["POST"])
def reset_hwid(key):
    if key not in keys_data:
        return jsonify({"status": "error", "message": "Key not found"}), 404
    keys_data[key]["hwid"] = None
    save_keys()
    return jsonify({"status": "success", "key": key, "hwid": None})

# ------------------- Web Interface -------------------

@app.route("/")
def index():
    html = "<h1>Executor Key Management</h1>"
    html += "<h2>Existing Keys</h2><ul>"
    for key, info in keys_data.items():
        status = "Paused" if info["paused"] else "Active"
        hwid = info["hwid"] or "None"
        expire = info["expires"]
        html += f"<li>{key} - {status} - Expires: {expire} - HWID: {hwid}</li>"
    html += "</ul>"
    html += """
    <h2>Generate New Key</h2>
    <form method='post' action='/generate_key_form'>
    Duration (minutes): <input name='duration' type='number' value='60'/>
    <button type='submit'>Generate</button>
    </form>
    """
    return render_template_string(html)

@app.route("/generate_key_form", methods=["POST"])
def generate_key_form():
    duration = int(request.form.get("duration", 60))
    key = generate_key(duration)
    return f"New key generated: {key} - Duration: {duration} minutes<br><a href='/'>Back</a>"

# Optional test endpoint
@app.route("/hello")
def hello():
    return jsonify({"message": "Hello Roblox!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
