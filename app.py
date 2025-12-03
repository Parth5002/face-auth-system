from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import cv2
import numpy as np
import os
import face_recognition
from flask_migrate import Migrate
from models import db, FDUser, FDLoginHistory
import json

# Flask App Initialization
app = Flask(__name__)
CORS(app)  

# --- CONFIGURATION SECTION ---
def get_db_uri():
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            
        params = config.get('params', {})
        server = params.get('server')
        database = params.get('database_name')
        username = params.get('username')
        password = params.get('password')

        if not all([server, database, username, password]):
            print("❌ ERROR: Missing fields in config.json")
            return None

        # Return PostgreSQL Connection String
        return f"postgresql://{username}:{password}@{server}/{database}"
    except Exception as e:
        print(f"❌ ERROR loading config.json: {e}")
        return None

# 1. Load Config
db_uri = get_db_uri()
if not db_uri:
    print("❌ CRITICAL: Could not load database config. Exiting.")
    exit(1)

# 2. Configure App
print(f"--> Connecting to PostgreSQL...")
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. Initialize Database
db.init_app(app)
Migrate(app, db)

# 4. Create Tables (If they don't exist)
with app.app_context():
    try:
        db.create_all()
        print("✅ PostgreSQL Database connected and tables ready!")
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")

# -----------------------------

# Face Detection and Storage Setup
image_folder = os.path.join(app.static_folder, 'images')
if not os.path.exists(app.static_folder):
    os.makedirs(app.static_folder)
os.makedirs(image_folder, exist_ok=True)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')

        if not name or not email:
            return jsonify({"error": "Name and email are required"}), 400

        # Check existing user
        if FDUser.query.filter((FDUser.username == name) | (FDUser.email == email)).first():
            return jsonify({"error": "User with this username or email already exists"}), 400

        # Capture and encode face
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
             return jsonify({"error": "Webcam not accessible"}), 500
        
        # Read a few frames to let camera adjust
        for _ in range(5):
            cap.read()
            
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return jsonify({"error": "Failed to capture image. Try again."}), 500

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings) != 1:
            return jsonify({"error": "Ensure exactly one face is visible."}), 400

        new_face_encoding = face_encodings[0]
        
        # Check against all existing faces
        all_users = FDUser.query.all()
        for user in all_users:
            if user.face_encoding:
                try:
                    existing_encoding = np.fromstring(user.face_encoding, sep=",")
                    # Compare faces
                    matches = face_recognition.compare_faces([existing_encoding], new_face_encoding)
                    if matches[0]:
                        return jsonify({"error": "Face already registered with another account"}), 400
                except:
                    continue

        # Save new user
        face_encoding_str = ",".join(map(str, new_face_encoding))
        new_user = FDUser(username=name, email=email, face_encoding=face_encoding_str)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": f"User {name} registered successfully!"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to register user: {e}"}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        print("--> Starting Login Process...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
             return jsonify({"error": "Webcam not accessible"}), 500
        
        # Warmup camera
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return jsonify({"error": "Failed to capture image."}), 500

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings_list = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings_list) != 1:
            print("--> Error: No face or multiple faces detected.")
            return jsonify({"error": "Ensure exactly one face is visible."}), 400

        login_encoding = face_encodings_list[0]
        users = FDUser.query.all()

        print(f"--> Comparing against {len(users)} registered users...")

        best_match_score = 1.0 # Lower is better
        matched_user = None

        for user in users:
            if user.face_encoding:
                try:
                    stored_encoding = np.fromstring(user.face_encoding, sep=",")
                    
                    # Calculate the "Distance" (Difference)
                    # 0.0 = Exact Match
                    # 1.0 = Completely Different
                    face_dist = face_recognition.face_distance([stored_encoding], login_encoding)[0]
                    
                    print(f"Checking {user.username}: Difference Score = {face_dist}")

                    # CHANGE TOLERANCE HERE (Standard is 0.6)
                    if face_dist < 0.55: 
                        if face_dist < best_match_score:
                            best_match_score = face_dist
                            matched_user = user
                except Exception as e:
                    print(f"Error processing user {user.username}: {e}")
                    continue

        if matched_user:
            # Log success
            print(f"--> MATCH FOUND: {matched_user.username}")
            login_history = FDLoginHistory(user_id=matched_user.id, success=True)
            db.session.add(login_history)
            db.session.commit()

            return jsonify({
                "message": "Login successful!",
                "user_id": matched_user.id,
                "username": matched_user.username,
                "score": str(best_match_score)
            })

        print("--> NO MATCH FOUND.")
        return jsonify({"error": "Face not recognized. Please register first."}), 401

    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)