from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import cv2
import numpy as np
import os
import face_recognition
from flask_migrate import Migrate
from models import db, FDUser, FDLoginHistory
import json
import base64

# Flask App Initialization
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- CONFIGURATION SECTION ---
def get_db_uri():
    """Cloud-ready DB config: DATABASE_URL env var first, config.json fallback."""
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        print("--> Using Cloud Database Connection (DATABASE_URL)")
        return database_url

    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
            
        params = config.get('params', {})
        server = params.get('server')
        database = params.get('database_name')
        username = params.get('username')
        password = params.get('password')

        if not all([server, database, username, password]):
            print("❌ ERROR: Missing fields in config.json")
            return None

        print("--> Using Local config.json")
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

image_folder = os.path.join(app.static_folder, 'images')
if not os.path.exists(app.static_folder):
    os.makedirs(app.static_folder)
os.makedirs(image_folder, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    import face_recognition
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')

        if not name or not email:
            return jsonify({"error": "Name and email are required"}), 400

        if FDUser.query.filter((FDUser.username == name) | (FDUser.email == email)).first():
            return jsonify({"error": "User with this username or email already exists"}), 400

        # NEW CLOUD-READY IMAGE PROCESSING
        image_data = data.get('image')
        if not image_data:
            return jsonify({"error": "No image provided by frontend"}), 400

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings) != 1:
            return jsonify({"error": "Ensure exactly one face is visible."}), 400

        new_face_encoding = face_encodings[0]
        
        # --- FIXED DUPLICATE CHECK ---
        all_users = FDUser.query.all()
        for user in all_users:
            if user.face_encoding:
                try:
                    existing_encoding = np.fromstring(user.face_encoding, sep=",")
                    
                    # CHANGED TOLERANCE TO 0.5 (Stricter)
                    # This prevents the system from confusing two different people
                    matches = face_recognition.compare_faces([existing_encoding], new_face_encoding, tolerance=0.5)
                    
                    if matches[0]:
                        return jsonify({"error": "Face already registered with another account"}), 400
                except:
                    continue

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
    import face_recognition
    import base64
    import numpy as np
    
    try:
        print("--> Starting Login Process...")
        
        # 1. Grab the JSON payload from the React frontend
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        image_data = data.get('image')
        if not image_data:
            return jsonify({"error": "No image provided by frontend"}), 400

        # 2. Decode the Base64 image string back into an OpenCV image
        # This handles the 'data:image/jpeg;base64,' prefix if React sends it
        encoded_data = image_data.split(',')[1] if ',' in image_data else image_data
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Failed to decode image."}), 400

        # 3. Shrink the image to 25% size to prevent Render memory crashes
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # 4. Convert the shrunk image to RGB for face_recognition
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # --- The rest is your original authentication logic ---
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings_list = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings_list) != 1:
            print("--> Error: No face or multiple faces detected.")
            return jsonify({"error": "Ensure exactly one face is visible."}), 400

        login_encoding = face_encodings_list[0]
        users = FDUser.query.all()

        print(f"--> Comparing against {len(users)} registered users...")

        best_match_score = 1.0 
        matched_user = None

        for user in users:
            if user.face_encoding:
                try:
                    stored_encoding = np.fromstring(user.face_encoding, sep=",")
                    
                    face_dist = face_recognition.face_distance([stored_encoding], login_encoding)[0]
                    print(f"Checking {user.username}: Difference Score = {face_dist}")

                    # Login Tolerance (0.55) - Keeps it easy to login
                    if face_dist < 0.55: 
                        if face_dist < best_match_score:
                            best_match_score = face_dist
                            matched_user = user
                except Exception as e:
                    print(f"Error processing user {user.username}: {e}")
                    continue

        if matched_user:
            print(f"--> MATCH FOUND: {matched_user.username}")
            login_history = FDLoginHistory(user_id=matched_user.id, success=True)
            db.session.add(login_history)
            db.session.commit()

            return jsonify({
                "message": "Login successful!",
                "user_id": matched_user.id,
                "username": matched_user.username,
                "email": matched_user.email,
                "score": str(best_match_score)
            })

        print("--> NO MATCH FOUND.")
        return jsonify({"error": "Face not recognized. Please register first."}), 401

    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify
        
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=int(os.environ.get("PORT", 5000)))
