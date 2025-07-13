#!/usr/bin/env python3
"""
Production server script for TechCorp Solutions RAG Chatbot
This script runs the Flask server without debug mode to avoid frequent restarts.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import and configure warning suppression
from src.config.warnings_config import suppress_warnings, configure_logging

# Suppress warnings and configure logging
suppress_warnings()
configure_logging()

from src.main import app

if __name__ == '__main__':
    print("Starting TechCorp Solutions RAG Chatbot Server (Production Mode)")
    print("Server will be available at:")
    print("  - http://127.0.0.1:5000")
    print("  - http://localhost:5000")
    print("  - http://[your-ip]:5000")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run in production mode (no debug, no auto-reload)
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=False,
        threaded=True
    ) 