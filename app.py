import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

# Load configuration values from environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    
    # Configure absolute paths for asset upload directories
    app.config['UPLOAD_FOLDER_PROMO'] = os.path.join(app.static_folder, 'uploads', 'tours')
    app.config['UPLOAD_FOLDER_REPORTS'] = os.path.join(app.static_folder, 'uploads', 'reports')
    
    # Ensure physical storage destinations exist safely on system boot
    os.makedirs(app.config['UPLOAD_FOLDER_PROMO'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_REPORTS'], exist_ok=True)

    # Initialize Flask-Login lifecycle management
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    from dao.users_dao import get_user_by_id
    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    # Core blueprint registration interfaces
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.guides import guides_bp
    from routes.participants import participants_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(guides_bp, url_prefix='/guide')
    app.register_blueprint(participants_bp, url_prefix='/participant')

    return app

if __name__ == '__main__':
    app = create_app()
    # Debug active locally; automatically handled clean on production servers
    app.run(debug=True, port=5000)