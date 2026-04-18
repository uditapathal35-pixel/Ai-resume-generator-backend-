from flask import Flask
from .models import db

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .auth import auth
    from .resume import resume

    app.register_blueprint(auth)
    app.register_blueprint(resume)

    with app.app_context():
        db.create_all()

    return app