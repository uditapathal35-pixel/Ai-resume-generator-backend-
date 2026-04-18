from flask import Blueprint, request, jsonify
from .models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({"error": "User exists"}), 400

    new_user = User(email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Signup successful"})


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and user.password == password:
        return jsonify({"message": "Login successful"})

    return jsonify({"error": "Invalid credentials"}), 401