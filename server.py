import os
from flask import Flask, request, send_file

app = Flask(__name__)
SCRIPT_FILE = "script.lua"

# Secret key for secure uploads (set this in Render environment variables)
UPLOAD_KEY = os.environ.get("UPLOAD_KEY", "changeme")

# Serve the Lua script
@app.route("/script.lua", methods=["GET"])
def get_script():
    if os.path.exists(SCRIPT_FILE):
        return send_file(SCRIPT_FILE, mimetype="text/plain")
    return "No script uploaded yet.", 404

# Upload a new Lua script (secure)
@app.route("/upload", methods=["POST"])
def upload_script():
    # Authorization check
    key = request.headers.get("Authorization")
    if key != UPLOAD_KEY:
        return "Unauthorized", 401

    if "file" not in request.files:
        return "No file uploaded.", 400

    file = request.files["file"]
    if file.filename == "":
        return "Empty filename.", 400

    file.save(SCRIPT_FILE)
    return "Script uploaded successfully!"

# This is only used if running locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
