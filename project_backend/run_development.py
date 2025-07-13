#!/usr/bin/env python3
"""
Development server script for TechCorp Solutions RAG Chatbot
This script runs the Flask server with optimized debug mode.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variable to enable debug mode
os.environ['FLASK_DEBUG'] = 'true'

# Import and configure warning suppression
from src.config.warnings_config import suppress_warnings, configure_logging

# Suppress warnings and configure logging
suppress_warnings()
configure_logging()

from src.main import app

if __name__ == '__main__':
    print("Starting TechCorp Solutions RAG Chatbot Server (Development Mode)")
    print("Debug mode enabled with optimized file watching")
    print("Server will be available at:")
    print("  - http://127.0.0.1:5000")
    print("  - http://localhost:5000")
    print("  - http://[your-ip]:5000")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    # The main.py will handle the optimized debug configuration
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True
    ) 