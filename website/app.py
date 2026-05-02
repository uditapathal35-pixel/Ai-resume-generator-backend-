import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ]
        }
    },
)

# 🔹 Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-secret-change-me-in-production')

_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
_TOKEN_SALT = 'user-auth-token'
_TOKEN_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

db = SQLAlchemy(app)

# 🔹 User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(256))  # hashed passwords are longer

# 🔹 Resume Model
class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)


def _build_resume_content(data):
    name = data.get('name', '')
    title = data.get('title', '')
    email = data.get('email', '')
    phone = data.get('phone', '')
    location = data.get('location', '')
    linkedin = data.get('linkedin', '')
    summary = data.get('summary', '')
    skills = data.get('skills', '')
    education = data.get('education', '')
    experience = data.get('experience', '')

    return f"""
    ===== RESUME =====

    Name: {name}
    Title: {title}
    Email: {email}
    Phone: {phone}
    Location: {location}
    LinkedIn: {linkedin}
    Summary: {summary}

    Skills:
    {skills}

    Education:
    {education}

    Experience:
    {experience}

    ==================
    """


def _extract_title(content):
    if not content:
        return "Untitled Resume"

    for line in content.splitlines():
        cleaned = line.strip()
        if cleaned.lower().startswith("name:"):
            value = cleaned.split(":", 1)[1].strip()
            return value if value else "Untitled Resume"

    return "Untitled Resume"


def _serialize_resume(resume):
    return {
        "id": resume.id,
        "title": _extract_title(resume.content),
        "content": resume.content,
    }


# 🔹 Create database
with app.app_context():
    db.create_all()


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

    resume = _build_resume_content(data)
    # ✅ SAVE TO DATABASE
    new_resume = Resume(content=resume)
    db.session.add(new_resume)
    db.session.commit()

    return jsonify({"resume": resume, "resumeId": new_resume.id})

@app.route('/resumes')
def get_resumes():
    resumes = Resume.query.all()

    return jsonify({"resumes": [_serialize_resume(r) for r in resumes]})


@app.route('/resumes/<int:resume_id>', methods=['GET'])
def get_resume(resume_id):
    resume = db.session.get(Resume, resume_id)
    if not resume:
        return jsonify({"error": "Resume not found"}), 404

    return jsonify({"resume": _serialize_resume(resume)})


@app.route('/resumes/<int:resume_id>', methods=['PUT'])
def update_resume(resume_id):
    resume = db.session.get(Resume, resume_id)
    if not resume:
        return jsonify({"error": "Resume not found"}), 404

    data = request.get_json() or {}

    if isinstance(data.get('content'), str) and data.get('content').strip():
        resume.content = data.get('content').strip()
    else:
        resume.content = _build_resume_content(data)

    db.session.commit()
    return jsonify({"message": "Resume updated", "resume": _serialize_resume(resume)})


@app.route('/resumes/<int:resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    resume = db.session.get(Resume, resume_id)
    if not resume:
        return jsonify({"error": "Resume not found"}), 404

    db.session.delete(resume)
    db.session.commit()
    return jsonify({"message": "Resume deleted", "id": resume_id})


# 🔹 RUN SERVER
if __name__ == "__main__":
    app.run(debug=True)