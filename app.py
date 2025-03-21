import eventlet
eventlet.monkey_patch()  # ✅ Required for eventlet to work properly with WebSockets

from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO
import sys
import os
from core.managers.app_manager import AppManager
from plugins.main_plugin.main_plugin_main import MainPlugin
from tools.logger.custom_logging import custom_log
from utils.secret_manager import get_secrets


sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# ✅ Initialize Flask
app = Flask(__name__)

# Load secrets
secrets = get_secrets()
app.config['SECRET_KEY'] = secrets['APP_SECRET_KEY']
app.config['JWT_SECRET_KEY'] = secrets['JWT_SECRET_KEY']
app.config['ENCRYPTION_KEY'] = secrets['ENCRYPTION_KEY']

# ✅ Enable Cross-Origin Resource Sharing (CORS) with credentials support
CORS(app, supports_credentials=True)

# ✅ Initialize WebSockets BEFORE loading plugins
socketio = SocketIO(
    app,
    cors_allowed_origins="*",  # Allow all origins (adjust as needed)
    async_mode="eventlet",
    logger=True,
    engineio_logger=True
)

# ✅ Initialize AppManager
app_manager = AppManager()
app_manager.initialize(app)

# ✅ Initialize `MainPlugin`
main_plugin = MainPlugin()
main_plugin.initialize(app_manager)

# ✅ Set CSP headers to explicitly allow WebSockets
@app.after_request
def add_csp_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' ws://127.0.0.1:5000 ws://localhost:5000 wss://fmif.reignofplay.com; "
        "connect-src 'self' ws://127.0.0.1:5000 ws://localhost:5000 wss://fmif.reignofplay.com;"
    )
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# ✅ Attach WebSocket events
@socketio.on("connect")
def handle_connect():
    custom_log(f"✅ WebSocket Client Connected: {request.sid}")


@socketio.on("disconnect")
def handle_disconnect():
    custom_log("❌ WebSocket Client Disconnected.")

@socketio.on("message")
def handle_message(msg):
    custom_log(f"📩 Received WebSocket Message: {msg}")
    socketio.emit("message", f"Echo: {msg}")  # Echo response

# ✅ Start Flask & WebSockets together on PORT 5000
if __name__ == "__main__":
    custom_log("🚀 Starting Flask & WebSocket Server on port 5000...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
