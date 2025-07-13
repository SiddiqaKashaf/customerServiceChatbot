import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import and configure warning suppression
from src.config.warnings_config import suppress_warnings, configure_logging

# Suppress warnings and configure logging
suppress_warnings()
configure_logging()

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.routes.chat import chat_bp
import logging

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not SECRET_KEY:
    logging.getLogger(__name__).error('FLASK_SECRET_KEY environment variable not set!')
    raise RuntimeError('FLASK_SECRET_KEY environment variable not set!')
app.config['SECRET_KEY'] = SECRET_KEY

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/api')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    # Only enable debug mode if explicitly set in environment
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    if debug_mode:
        # Configure extra directories to watch only project files, not entire environment
        extra_dirs = [
            os.path.join(os.path.dirname(__file__)),  # src directory
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'company_documents'),  # company_documents
        ]
        extra_files = []
        for extra_dir in extra_dirs:
            if os.path.exists(extra_dir):
                for dirname, dirs, files in os.walk(extra_dir):
                    for filename in files:
                        filename = os.path.join(dirname, filename)
                        if filename.endswith(('.py', '.html', '.js', '.css', '.json', '.md')):
                            extra_files.append(filename)
        
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=True,
            extra_files=extra_files,
            use_reloader = False
        )
    else:
        app.run(host='0.0.0.0', port=5000, debug=False)
