import os
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, send_file, render_template_string, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supersecret123")  # Any random string

SCRIPT_FILE = "script.lua"
OWNER_PASSWORD = "HRErege2342dfs352"
KEY_FILE = "keys.json"

# Load keys from file
def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    return {}

# Save keys to file
def save_keys(keys):
    with open(KEY_FILE, "w") as f:
        json.dump(keys, f, indent=4)

# Check if a key is valid
def is_key_valid(key):
    keys = load_keys()
    if key in keys:
        expire_time = datetime.fromisoformat(keys[key])
        if datetime.now() < expire_time:
            return True
    return False

# -------------------------------
# Key-protected script endpoint
# -------------------------------
@app.route("/script.lua", methods=["GET"])
def get_script():
    key = request.args.get("key")
    if not key or not is_key_valid(key):
        return "Invalid or expired key!", 403
    if os.path.exists(SCRIPT_FILE):
        return send_file(SCRIPT_FILE, mimetype="text/plain")
    return "No script uploaded yet.", 404

# -------------------------------
# Owner upload page & key management
# -------------------------------
@app.route("/", methods=["GET", "POST"])
def upload_page():
    message = None
    filename = None
    filesize = None

    if request.method == "POST" and "file" in request.files:
        password = request.form.get("password", "")
        if password != OWNER_PASSWORD:
            flash("Unauthorized: Wrong owner password!", "error")
            return redirect(url_for("upload_page"))

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(url_for("upload_page"))

        temp_path = "temp_uploaded.lua"
        file.save(temp_path)
        filename = file.filename
        filesize = os.path.getsize(temp_path)
        message = f"Uploaded '{filename}' ({filesize} bytes). Click Save to finalize."

    keys = load_keys()
    key_list = [(k, v) for k, v in keys.items()]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lua Script & Key Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            .message { color: green; }
            .error { color: red; }
            table { border-collapse: collapse; width: 70%; margin-top: 20px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            button { margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>Upload Lua Script (Owner Only)</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, msg in messages %}
              <div class="{{category}}">{{ msg }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form method="POST" enctype="multipart/form-data">
            <label>Owner Password:</label><input type="password" name="password" required><br><br>
            <input type="file" name="file" required><br><br>
            <button type="submit">Upload</button>
        </form>

        {% if message %}
            <div class="message">
                <p>{{message}}</p>
                <form method="POST" action="/save">
                    <input type="hidden" name="temp_file" value="temp_uploaded.lua">
                    <button type="submit">Save</button>
                </form>
            </div>
        {% endif %}

        <h2>Key Management</h2>
        <form method="POST" action="/generate_key">
            <label>Key Duration (minutes): </label>
            <input type="number" name="duration" min="1" required>
            <input type="hidden" name="password" value="HRErege2342dfs352">
            <button type="submit">Generate Key</button>
        </form>

        <table>
            <tr><th>Key</th><th>Expires At</th><th>Actions</th></tr>
            {% for key, expire in key_list %}
            <tr>
                <td>{{key}}</td>
                <td>{{expire}}</td>
                <td>
                    <form style="display:inline;" method="POST" action="/delete_key">
                        <input type="hidden" name="key" value="{{key}}">
                        <input type="hidden" name="password" value="HRErege2342dfs352">
                        <button type="submit">Delete</button>
                    </form>
                    <form style="display:inline;" method="POST" action="/extend_key">
                        <input type="hidden" name="key" value="{{key}}">
                        <input type="hidden" name="password" value="HRErege2342dfs352">
                        <input type="number" name="extra_minutes" placeholder="Minutes" required>
                        <button type="submit">Extend</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, message=message, key_list=key_list)

# -------------------------------
# Save uploaded Lua script
# -------------------------------
@app.route("/save", methods=["POST"])
def save_file():
    temp_file = request.form.get("temp_file")
    if not temp_file or not os.path.exists(temp_file):
        flash("No uploaded file to save.", "error")
        return redirect(url_for("upload_page"))
    os.replace(temp_file, SCRIPT_FILE)
    flash("Script saved successfully!", "success")
    return redirect(url_for("upload_page"))

# -------------------------------
# Generate a new key
# -------------------------------
@app.route("/generate_key", methods=["POST"])
def generate_key():
    password = request.form.get("password", "")
    if password != OWNER_PASSWORD:
        flash("Unauthorized!", "error")
        return redirect(url_for("upload_page"))

    try:
        duration = int(request.form.get("duration"))
    except:
        flash("Invalid duration!", "error")
        return redirect(url_for("upload_page"))

    new_key = str(uuid.uuid4()).replace("-", "")[:12]
    expire_time = datetime.now() + timedelta(minutes=duration)

    keys = load_keys()
    keys[new_key] = expire_time.isoformat()
    save_keys(keys)
    flash(f"Generated key {new_key} valid for {duration} minutes.", "success")
    return redirect(url_for("upload_page"))

# -------------------------------
# Delete a key
# -------------------------------
@app.route("/delete_key", methods=["POST"])
def delete_key():
    password = request.form.get("password", "")
    if password != OWNER_PASSWORD:
        flash("Unauthorized!", "error")
        return redirect(url_for("upload_page"))

    key = request.form.get("key")
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        flash(f"Key {key} deleted.", "success")
    return redirect(url_for("upload_page"))

# -------------------------------
# Extend key expiration
# -------------------------------
@app.route("/extend_key", methods=["POST"])
def extend_key():
    password = request.form.get("password", "")
    if password != OWNER_PASSWORD:
        flash("Unauthorized!", "error")
        return redirect(url_for("upload_page"))

    key = request.form.get("key")
    try:
        extra = int(request.form.get("extra_minutes"))
    except:
        flash("Invalid extra minutes!", "error")
        return redirect(url_for("upload_page"))

    keys = load_keys()
    if key in keys:
        expire_time = datetime.fromisoformat(keys[key])
        new_expire = expire_time + timedelta(minutes=extra)
        keys[key] = new_expire.isoformat()
        save_keys(keys)
        flash(f"Extended key {key} by {extra} minutes.", "success")
    return redirect(url_for("upload_page"))

# -------------------------------
# Run server
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
