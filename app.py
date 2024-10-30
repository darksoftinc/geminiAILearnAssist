import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
import google.generativeai as genai
import notifications

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure Gemini AI
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
app.config['GENAI_MODEL'] = genai.GenerativeModel('gemini-pro')

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Initialize SocketIO
notifications.init_app(app)

# Register blueprints
with app.app_context():
    from auth import auth_bp
    from curriculum import curriculum_bp
    from quiz import quiz_bp
    from dashboard import dashboard_bp
    from google_auth import google_auth
    from analytics import analytics_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(curriculum_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(google_auth, url_prefix='/')
    
    # Import models and create tables
    import models
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
