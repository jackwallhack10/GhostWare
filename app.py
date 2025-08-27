from flask import Flask, request, jsonify, render_template_string
import json
import os

app = Flask(__name__)
data_file = "hwids.json"

# Load existing HWID data from file
if os.path.exists(data_file):
    with open(data_file, "r") as f:
        hwid_data = json.load(f)
else:
    hwid_data = {}

# Endpoint to receive HWID from executor
@app.route("/hwid", methods=["POST"])
def receive_hwid():
    content = request.get_json()
    hwid = content.get("hwid")
    if hwid:
        # Increment execution count for this HWID
        hwid_data[hwid] = hwid_data.get(hwid, 0) + 1
        # Save updated data to file
        with open(data_file, "w") as f:
            json.dump(hwid_data, f)
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "No HWID provided"}), 400

# Web page to display all HWIDs and counts
@app.route("/")
def index():
    html = "<h1>Executor HWID Usage</h1><ul>"
    for hwid, count in hwid_data.items():
        html += f"<li>{hwid} - {count} executions</li>"
    html += "</ul>"
    return render_template_string(html)

# Optional test endpoint
@app.route("/hello")
def hello():
    return jsonify({"message": "Hello Roblox!"})

if __name__ == "__main__":
    # Render requires running on host 0.0.0.0
    app.run(host="0.0.0.0", port=10000)
