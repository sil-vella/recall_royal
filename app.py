import eventlet
# Configure eventlet before other imports
eventlet.monkey_patch(socket=True)

import os
from flask import Flask
from flask_cors import CORS
from core.plugin_manager import PluginManager
from core.services_manager import ServicesManager
from core.app_manager import AppManager
from tools.logger.custom_logging import get_logger, setup_logging
from utils.config.config import Config

logger = get_logger(__name__)

def create_app():
    setup_logging()
    logger.info("Initializing Flask application...")
    
    app = Flask(__name__)
    CORS(app)
    
    # Load configuration
    config = Config()
    app.config.from_object(config)
    
    # Initialize managers
    plugin_manager = PluginManager()
    services_manager = ServicesManager()
    app_manager = AppManager(app, plugin_manager, services_manager)
    
    # Initialize the application
    app_manager.init_app()
    
    logger.info("Flask application initialized successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port)
