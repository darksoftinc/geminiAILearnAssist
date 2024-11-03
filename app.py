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

# Uygulama oluştur
app = Flask(__name__)

# Uygulama yapılandırması
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Configure database URL with proper handling of postgres:// vs postgresql://
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace("postgres://", "postgresql://")

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Gemini AI yapılandırması
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
app.config['GENAI_MODEL'] = genai.GenerativeModel('gemini-pro')

# Eklentileri başlat
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# SocketIO başlat
notifications.init_app(app)

# Blueprint'leri kaydet
with app.app_context():
    from auth import auth_bp
    from curriculum import curriculum_bp
    from quiz import quiz_bp
    from dashboard import dashboard_bp
    from google_auth import google_auth
    from analytics import analytics_bp
    from student import student_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(curriculum_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(google_auth, url_prefix='/')
    
    # Modelleri içe aktar ve tablolar yoksa oluştur
    import models
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
