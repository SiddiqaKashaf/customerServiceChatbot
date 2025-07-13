"""
Warning suppression configuration for TechCorp Solutions RAG Chatbot
This module centralizes warning suppression to keep the console clean.
"""

import warnings
import logging

def suppress_warnings():
    """Suppress common warnings that clutter the console"""
    
    # Suppress Flask development server warnings
    warnings.filterwarnings("ignore", message=".*development server.*")
    warnings.filterwarnings("ignore", message=".*This is a development server.*")
    
    # Suppress transformers FutureWarnings
    warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
    warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")
    
    # Suppress other common warnings
    warnings.filterwarnings("ignore", message=".*unclosed file.*")
    warnings.filterwarnings("ignore", message=".*unclosed socket.*")
    
    # Suppress logging warnings for cleaner output
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("requests").setLevel(logging.ERROR)

def configure_logging():
    """Configure logging to reduce noise"""
    
    # Set up basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from specific loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING) 