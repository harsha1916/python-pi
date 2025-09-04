#!/usr/bin/env python3
"""
Startup script for the Camera Service Web Interface
"""
import os
import sys
import logging
from logging_config import setup_logging

def main():
    """Start the web application."""
    # Setup logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Camera Service Web Interface...")
    
    # Check if required directories exist
    required_dirs = ['templates', 'static', 'images']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            logger.info(f"Created directory: {dir_name}")
    
    # Import and run the web app
    try:
        from web_app import app
        logger.info("Web application initialized successfully")
        logger.info("Access the dashboard at: http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Failed to start web application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
