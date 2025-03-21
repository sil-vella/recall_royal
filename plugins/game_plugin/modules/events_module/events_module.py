from tools.logger.custom_logging import custom_log
from core.managers.module_manager import ModuleManager

class GamesEventsModule:
    def __init__(self, app_manager=None):
        """Initialize GamesEventsModule and register event handlers."""
        self.app_manager = app_manager
        self.module_manager = self.app_manager.module_manager if self.app_manager else ModuleManager()
        self.websocket_module = self.module_manager.get_module("connection_websockets_module")

        if not self.websocket_module:
            raise RuntimeError("GamesEventsModule: Failed to retrieve WebSocket module from ModuleManager.")

        self.register_websocket_events()
        custom_log("✅ GamesEventsModule initialized.")

    def register_websocket_events(self):
        """Registers WebSocket events to handle game joining."""
        if not self.websocket_module:
            custom_log("⚠️ WebSocket module not available, skipping event registration.")
            return

        @self.websocket_module.socketio.on("join")
        def handle_join_game(data):
            """Handles players joining a game via WebSocket."""
            try:
                game_id = data.get("game_id")
                player = data.get("host")  # Renamed `host` to `player`

                if not game_id or not player:
                    custom_log("⚠️ Invalid game join request.")
                    self.websocket_module.socketio.emit("game_join_failed", {"error": "Invalid data"})
                    return

                custom_log(f"🎮 Player '{player}' joined Game: {game_id}")

                # Send acknowledgment back to the joining player
                self.websocket_module.socketio.emit("game_joined", {
                    "status": "success",
                    "game_id": game_id,
                    "player": player,
                    "message": "Successfully joined the game."
                })

            except Exception as e:
                custom_log(f"❌ Error handling game join: {str(e)}")
                self.websocket_module.socketio.emit("game_join_failed", {"error": "Internal server error"})
