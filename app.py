from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, storage
import traceback
import uuid

app = Flask(__name__)
CORS(app)


cred = credentials.Certificate(r"/Users/syed/Desktop/ARTEMIS-AI/artemis-ai-c9143-firebase-adminsdk-fbsvc-84bc5c0417.json")
firebase_admin.initialize_app(cred)


db = firestore.client() #Initialized database as a firebase, firestore database
bucket = storage.bucket()  # Get Firebase Storage bucket

# APP REGISTER
@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"error": "Missing fields"}), 400

        users_ref = db.collection("users")

        # Check if username or email already exists
        existing_users = users_ref.where("username", "==", username).stream()
        existing_emails = users_ref.where("email", "==", email).stream()

        if any(existing_users):
            return jsonify({"error": "Username already exists"}), 400
        if any(existing_emails):
            return jsonify({"error": "Email already registered"}), 400

        # Save user in Firestore
        users_ref.add({
            "username": username,
            "email": email,
            "password": password 
        })

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#APP LOGIN

@app.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Query Firestore for the user by email
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).stream()

        user_data = None
        for user in query:
            user_data = user.to_dict()
            user_id = user.id  # Get Firestore document ID
            break

        if not user_data:
            return jsonify({"error": "User not found"}), 404

        # 🔥 Check the password
        if user_data.get("password") != password:
            return jsonify({"error": "Invalid credentials"}), 401

        return jsonify({
            "message": "Login successful",
            "user_id": user_id,  
            "username": user_data.get("username"),
            "email": user_data.get("email")
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/delete', methods=['DELETE'])
def delete_user():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({"error": "Email is required"}), 400

        users_ref = db.collection("users")
        query = users_ref.where("email", "==", email).stream()

        user_found = False
        for doc in query:
            users_ref.document(doc.id).delete()
            user_found = True
            break

        if not user_found:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/update', methods=['PUT'])
def update_user():
    try:
        data = request.get_json()
        email = data.get('email')
        field = data.get('field')  # 'username', 'email', or 'password'
        new_value = data.get('newValue')

        if not email or not field or not new_value:
            return jsonify({"error": "Missing required fields"}), 400

        users_ref = db.collection("users")
        query = users_ref.where("email", "==", email).stream()

        user_id = None
        for doc in query:
            user_id = doc.id
            break

        if not user_id:
            return jsonify({"error": "User not found"}), 404

        # 🔥 Update the requested field 🔥
        users_ref.document(user_id).update({field: new_value})

        return jsonify({"message": f"{field.capitalize()} updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_images():
    try:
        if 'images' not in request.files or 'email' not in request.form:
            return jsonify({"error": "Missing images or email"}), 400

        user_email = request.form['email']
        files = request.files.getlist('images')  # Get multiple files

        uploaded_urls = []

        for file in files:
            filename = str(uuid.uuid4()) + "-" + file.filename
            blob = bucket.blob(f"uploads/{filename}")
            blob.upload_from_file(file)
            blob.make_public()
            uploaded_urls.append(blob.public_url)

        # Update Firestore: Add images to the user's `uploaded_images` array
        user_ref = db.collection("users").document(user_email)
        user_ref.set({"uploaded_images": firestore.ArrayUnion(uploaded_urls)}, merge=True)

        return jsonify({"message": "Images uploaded successfully", "uploaded_images": uploaded_urls}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['POST'])
def save_downloaded_image():
    try:
        data = request.get_json()
        if "email" not in data or "image_url" not in data:
            return jsonify({"error": "Missing email or image URL"}), 400

        user_email = data["email"]
        image_url = data["image_url"]

        # Update Firestore: Add image URL to the user's `downloaded_images` array
        user_ref = db.collection("users").document(user_email)
        user_ref.set({"downloaded_images": firestore.ArrayUnion([image_url])}, merge=True)

        return jsonify({"message": "Image saved to downloads", "downloaded_images": [image_url]}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        return jsonify({"error": str(e)}), 500

token = os.getenv("HUGGINGFACE_TOKEN")    
API_KEY = token
URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def generate_image(prompt):
    """Send a request to the Hugging Face API to generate an image based on the prompt."""
    payload = {"inputs": prompt}
    response = requests.post(URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        output_path = os.path.join("static", "output.png")
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path
    else:
        return None

@app.route("/")
def home():
    """Serve the frontend HTML."""
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    """API endpoint to generate an image from a text prompt."""
    data = request.get_json()  # Use get_json() to properly parse JSON data
    prompt = data.get("prompt")

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    image_path = generate_image(prompt)

    if image_path:
        return jsonify({"image_url": "/static/output.png"})
    else:
        return jsonify({"error": "Failed to generate image"}), 500


@app.route('/static/images/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

IMAGE_SAVE_PATH = r"/Users/syed/Desktop/ARTEMIS-AI/static/images"
os.makedirs(IMAGE_SAVE_PATH, exist_ok=True)

@app.route('/save_image', methods=['POST'])
def save_image():
    try:
        data = request.json
        user_id = data.get("user_id")
        image_data = data.get("image")  # Base64 encoded image string
        image_name = data.get("image_name", "image.png")
        
        if not user_id or not image_data:
            return jsonify({"error": "Missing user_id or image data"}), 400
        
        # Decode and save the image locally
        image_path = os.path.join(IMAGE_SAVE_PATH, f"{user_id}_{image_name}")
        with open(image_path, "wb") as img_file:
            img_file.write(base64.b64decode(image_data))
        
        # Store image path in Firestore under the user's collection
        user_ref = db.collection("users").document(user_id)
        user_images_ref = user_ref.collection("images")
        user_images_ref.add({"image_path": image_path})
        
        return jsonify({"message": "Image saved successfully", "image_path": image_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
