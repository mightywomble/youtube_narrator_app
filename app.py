import os
import sys
from flask import Flask, send_from_directory, session
from dotenv import load_dotenv

# --- FIX for ModuleNotFoundError when running via python app.py ---
# Add the project root directory to sys.path so Python can find 'routes', 'services', etc.
# This assumes app.py is in the project's root directory.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- END FIX ---

# Load environment variables from .env file (for development)
load_dotenv()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration from config.py
    app.config.from_object('config')
    
    # Load sensitive configuration from instance/config.py (local, not committed to git)
    # This file should contain actual API keys, database URLs, etc.
    try:
        app.config.from_pyfile('config.py', silent=True)
    except FileNotFoundError:
        print("instance/config.py not found. Ensure sensitive API keys are set via environment variables or create this file.")

    # Configure session (important for storing temporary script data, file paths)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_that_should_be_randomized') # MUST be a strong, random key in production
    app.config['SESSION_TYPE'] = 'filesystem' # Stores sessions on the filesystem
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from routes.main_routes import main_bp
    from routes.settings_routes import settings_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(settings_bp)

    @app.route('/static/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        """Serve files from the uploads directory."""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app

if __name__ == '__main__':
    app = create_app()
    # Changed host from default '127.0.0.1' to '0.0.0.0' to bind to all interfaces
    app.run(debug=True, host='0.0.0.0', port=5005) 
