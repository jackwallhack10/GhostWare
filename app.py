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
        "hwid": None  # locks to first HWID
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

@app.route("/key_action", methods=["POST"])
def key_action():
    data = request.get_json()
    key = data.get("key")
    action = data.get("action")
    value = data.get("value")

    if key not in keys_data:
        return jsonify({"status":"error","message":"Key not found"}),404

    key_info = keys_data[key]

    if action == "add_time":
        try:
            minutes = int(value)
            key_info["expires"] = (datetime.fromisoformat(key_info["expires"]) + timedelta(minutes=minutes)).isoformat()
        except:
            return jsonify({"status":"error","message":"Invalid value"}),400
    elif action == "reset_hwid":
        key_info["hwid"] = None
    elif action == "delete":
        del keys_data[key]
        save_keys()
        return jsonify({"status":"success","deleted":key})

    save_keys()
    return jsonify({"status":"success", "key": key})

# ------------------- Web Interface -------------------

@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>Executor Key Management</title>
    <style>
    body { font-family: Arial; padding: 20px; }
    table { border-collapse: collapse; width: 80%; }
    th, td { border: 1px solid black; padding: 8px; text-align: center; }
    button { padding: 5px 10px; margin: 2px; }
    </style>
    <script>
    function keyAction(key, action){
        if(action === 'add_time'){
            var minutes = prompt('Enter number of minutes to add:');
            if(!minutes) return;
        } else { var minutes = null; }

        fetch('/key_action', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({key:key, action:action, value:minutes})
        }).then(res=>location.reload())
    }
    </script>
    </head>
    <body>
    <h1>Executor Key Management</h1>
    <h2>Existing Keys</h2>
    <table>
    <tr><th>Key</th><th>Status</th><th>Expires</th><th>HWID</th><th>Actions</th></tr>
    """
    for key, info in keys_data.items():
        status = "Paused" if info["paused"] else "Active"
        hwid = info["hwid"] or "None"
        expire = info["expires"]
        html += f"""
        <tr>
        <td>{key}</td>
        <td>{status}</td>
        <td>{expire}</td>
        <td>{hwid}</td>
        <td>
        <button onclick="keyAction('{key}','add_time')">Add Time</button>
        <button onclick="keyAction('{key}','reset_hwid')">Reset HWID</button>
        <button onclick="keyAction('{key}','delete')">Delete</button>
        </td>
        </tr>
        """

    html += "</table><h2>Generate New Key</h2>"
    html += """
    <form method='post' action='/generate_key_form'>
    Duration (minutes): <input name='duration' type='number' value='60'/>
    <button type='submit'>Generate</button>
    </form>
    </body>
    </html>
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
