from flask import Flask, request, jsonify, send_from_directory
import os
import requests
from werkzeug.utils import secure_filename
import time
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
USER_UPLOADS_FOLDER = 'useruploads'
GENERATED_FOLDER = 'generated'
CREDENTIALS_FILE = 'database/credentials.json'

# Ensure all directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(USER_UPLOADS_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs('database', exist_ok=True)

# Create the credentials file if it doesn't exist
if not os.path.exists(CREDENTIALS_FILE):
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump([], f)

# ------------------ Register Endpoint ------------------
@app.route('/register', methods=['POST'])
def register_api():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({"message": "Missing fields"}), 400

    # Load existing credentials
    with open(CREDENTIALS_FILE, 'r') as f:
        users = json.load(f)

    # Check if email already exists
    for user in users:
        if user['email'] == email:
            return jsonify({"message": "User already exists"}), 409

    # Add new user
    users.append({
        "name": name,
        "email": email,
        "password": password
    })

    # Save updated credentials
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

    return jsonify({"message": "User registered successfully"}), 201

# ------------------ Login Endpoint ------------------
@app.route('/login', methods=['GET'])  # Keep route as /register for now
def login_api():
    email = request.args.get('email')
    password = request.args.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    # Load existing credentials
    with open(CREDENTIALS_FILE, 'r') as f:
        users = json.load(f)

    for user in users:
        if user['email'] == email and user['password'] == password:
            return jsonify({"success": True, "message": "Login successful"}), 200

    return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route('/save-avatar', methods=['POST'])
def save_avatar():
    data = request.get_json()
    avatar_url = data.get('avatar_url')
    if not avatar_url:
        return jsonify({"message": "Avatar URL missing"}), 400

    response = requests.get(avatar_url)
    if response.status_code == 200:
        filename = os.path.join(UPLOAD_FOLDER, os.path.basename(avatar_url))
        with open(filename, 'wb') as f:
            f.write(response.content)
        return jsonify({"message": "Avatar saved", "file": filename}), 200
    else:
        return jsonify({"message": "Failed to download avatar"}), 500

@app.route('/gernator', methods=['POST'])
def avatar_generator():
    if 'avatar' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return jsonify({"message": "Avatar uploaded successfully", "filename": filepath}), 201

# ------------------ New Upload Endpoint ------------------

@app.route('/useruploads', methods=['POST'])
def handle_user_uploads():
    if 'files' not in request.files:
        return jsonify({"error": "No files part"}), 400

    files = request.files.getlist('files')
    if len(files) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    uploaded_files = []
    for file in files:
        filename = secure_filename(f"{int(time.time())}-{file.filename}") 
        filepath = os.path.join(USER_UPLOADS_FOLDER, filename)
        file.save(filepath)

        uploaded_files.append({
            "filename": filename,
            "path": filepath,
            "url": f"/useruploads/{filename}"
        })

    return jsonify({"status": "success", "uploaded": len(uploaded_files), "files": uploaded_files}), 200

# Serve uploaded files statically (just like Express)
@app.route('/useruploads/<path:filename>', methods=['GET'])
def serve_user_uploads(filename):
    return send_from_directory(USER_UPLOADS_FOLDER, filename)

# ------------------ Image Listing from Uploads ------------------

@app.route('/images', methods=['GET'])
def list_images_by_category():
    categorized = {}
    base_url = request.host_url.rstrip('/') + "/uploads"

    for category in os.listdir(UPLOAD_FOLDER):
        category_path = os.path.join(UPLOAD_FOLDER, category)
        if os.path.isdir(category_path):
            images = []
            for file in os.listdir(category_path):
                images.append({
                    "filename": file,
                    "url": f"{base_url}/{category}/{file}"
                })
            categorized[category] = images

    return jsonify(categorized)

# Serve uploaded images from /uploads
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ------------------ Entry Point ------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)