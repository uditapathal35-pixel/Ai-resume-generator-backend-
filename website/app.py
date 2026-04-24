import os
from flask import Flask, request, jsonify
from website.models import db
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3001", "http://127.0.0.1:3001"]}})

# 🔹 Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-secret-change-me-in-production')
db.init_app(app)

_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
_TOKEN_SALT = 'user-auth-token'
_TOKEN_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

@app.route('/')
def index():
    return jsonify({
        "message": "AI Resume Generator Backend is running",
        "endpoints": [
            "/test",
            "/signup",
            "/login",
            "/generate-resume",
            "/resumes"
        ]
    })


# 🔹 TEST ROUTE
@app.route('/test')
def test():
    return jsonify({"message": "Backend working"})


# 🔹 SIGNUP
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data"}), 400

    email = data.get('email')
    password = data.get('password')

    # check if user exists
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"error": "User already exists"}), 400

    hashed = generate_password_hash(password)
    new_user = User(email=email, password=hashed)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Signup successful"})


# 🔹 LOGIN
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data"}), 400

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        token = _serializer.dumps(user.id, salt=_TOKEN_SALT)
        return jsonify({"message": "Login successful", "token": token, "email": user.email})

    return jsonify({"error": "Invalid credentials"}), 401


# 🔹 ME (verify token, return current user)
@app.route('/me', methods=['GET'])
def me():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.removeprefix('Bearer ').strip()

    if not token:
        return jsonify({"error": "No token provided"}), 401

    try:
        user_id = _serializer.loads(token, salt=_TOKEN_SALT, max_age=_TOKEN_MAX_AGE)
    except SignatureExpired:
        return jsonify({"error": "Session expired, please sign in again"}), 401
    except BadSignature:
        return jsonify({"error": "Invalid token"}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    return jsonify({"email": user.email, "id": user.id})


# 🔹 RESUME GENERATOR
@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data"}), 400

    name = data.get('name')
    skills = data.get('skills')
    education = data.get('education')
    experience = data.get('experience')

    resume = f"""
    ===== RESUME =====

    Name: {name}

    Skills:
    {skills}

    Education:
    {education}

    Experience:
    {experience}

    ==================
    """
    # ✅ SAVE TO DATABASE
    new_resume = Resume(content=resume)
    db.session.add(new_resume)
    db.session.commit()

    return jsonify({"resume": resume})

@app.route('/resumes')
def get_resumes():
    resumes = Resume.query.all()

    output = []
    for r in resumes:
        output.append(r.content)

    return jsonify({"resumes": output})


# 🔹 RUN SERVER
if __name__ == "__main__":
    app.run(debug=True)
