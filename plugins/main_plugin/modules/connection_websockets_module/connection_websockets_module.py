from threading import Thread
import os
import sys
from flask import Flask, jsonify
from flask_socketio import SocketIO
from tools.logger.custom_logging import custom_log
import threading

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

class ConnectionWebsocketsModule:
    def __init__(self, app_manager, socketio):
        """Use the existing Flask-SocketIO instance instead of creating a new one."""
        if not app_manager or not app_manager.flask_app:
            raise RuntimeError("❌ AppManager is not initialized or Flask app is missing.")

        self.app = app_manager.flask_app
        self.app_manager = app_manager
        self.socketio = socketio  # ✅ Use the existing instance

        # ✅ Register WebSocket events
        self.register_events()


    def register_events(self):
        """Register core WebSocket event handlers."""
        
        @self.socketio.on("connect")
        def handle_connect():
            custom_log("🔗 Client connected via WebSocket")
            self.socketio.emit("connected", {"message": "Connected to WebSocket!"})


        @self.socketio.on("disconnect")
        def handle_disconnect():
            custom_log("❌ Client disconnected")

        @self.socketio.on("message")
        def handle_message(data):
            custom_log(f"📩 Received WebSocket message: {data}")
            self.socketio.emit("message", {"message": f"Echo: {data}"})


    def health_check(self):
        """Health check endpoint for WebSocket service."""
        return jsonify({"status": "healthy", "message": "WebSocket server is running."}), 200

    def register_plugin_event(self, event_name, handler):
        """
        Allow plugins to register custom WebSocket events.
        """
        if event_name in self.plugin_events:
            custom_log(f"⚠️ Event '{event_name}' is already registered. Overwriting.")

        self.plugin_events[event_name] = handler
        self.socketio.on(event_name, handler)
        custom_log(f"✅ Registered WebSocket event: {event_name}")

    def run(self):
        """Start the WebSocket server on the same port as Flask (5000)."""
        custom_log("🚀 Starting WebSocket server on port 5000...")
        self.socketio.run(self.app, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)

