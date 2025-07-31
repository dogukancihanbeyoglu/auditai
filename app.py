import os
import logging
from datetime import datetime

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging for production
log_level = logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO
logging.basicConfig(level=log_level)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "audit-ai-secret-key-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///auditai.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'Lütfen giriş yapın.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Avoid circular imports by deferring blueprint registration
def register_blueprints():
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.audit_areas import audit_areas_bp
    from routes.data_sources import data_sources_bp
    from routes.rules import rules_bp
    from routes.alarms import alarms_bp
    from routes.admin import admin
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(audit_areas_bp, url_prefix='/audit-areas')
    app.register_blueprint(data_sources_bp, url_prefix='/data-sources')
    app.register_blueprint(rules_bp, url_prefix='/rules')
    app.register_blueprint(alarms_bp, url_prefix='/alarms')
    app.register_blueprint(admin, url_prefix='/admin')

# Context processor for global variables
@app.context_processor
def inject_globals():
    return {
        'current_user': current_user,
        'now': datetime.now()
    }

# Main route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')
    return render_template('index.html')

# Register blueprints and create tables in proper order
register_blueprints()

with app.app_context():
    # Import models to ensure tables are created
    import models
    
    # Create all tables
    db.create_all()
    
    # Create default admin user if not exists
    from models import User, Role
    from werkzeug.security import generate_password_hash
    
    # Create default roles
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role()
        admin_role.name = 'admin'
        admin_role.description = 'Sistem Yöneticisi'
        db.session.add(admin_role)
    
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role()
        user_role.name = 'user'
        user_role.description = 'Standart Kullanıcı'
        db.session.add(user_role)
    
    auditor_role = Role.query.filter_by(name='auditor').first()
    if not auditor_role:
        auditor_role = Role()
        auditor_role.name = 'auditor'
        auditor_role.description = 'Denetçi'
        db.session.add(auditor_role)
    
    # Create default admin user
    admin_user = User.query.filter_by(email='admin@auditai.com').first()
    if not admin_user:
        admin_user = User()
        admin_user.username = 'admin'
        admin_user.email = 'admin@auditai.com'
        admin_user.password_hash = generate_password_hash('admin123')
        admin_user.role_id = admin_role.id
        admin_user.active = True
        admin_user.created_at = datetime.now()
        db.session.add(admin_user)
    else:
        # Update existing admin user's role if needed
        if not admin_user.role_id:
            admin_user.role_id = admin_role.id
            admin_user.active = True
    
    db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
