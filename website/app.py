from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 🔹 Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 🔹 User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

# 🔹 Resume Model
class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)


# 🔹 Create database
with app.app_context():
    db.create_all()


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

    new_user = User(email=email, password=password)
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

    if user and user.password == password:
        return jsonify({"message": "Login successful"})

    return jsonify({"error": "Invalid credentials"}), 401


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