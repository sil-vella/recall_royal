from flask_socketio import SocketIO
from plugins.main_plugin.modules.connection_api_module.connection_api_module import ConnectionApiModule
from plugins.main_plugin.modules.login_module.login_module import LoginModule

class MainPlugin:
    def initialize(self, app_manager):
        """
        Initialize the MainPlugin with AppManager.
        :param app_manager: AppManager - The main application manager.
        """
        print("Initializing MainPlugin...")

        try:
            # Store app_manager reference
            self.app_manager = app_manager

            # Ensure ConnectionMySqlModule is registered FIRST
            if not app_manager.module_manager.get_module("connection_api_module"):
                app_manager.module_manager.register_module(
                    "connection_api_module",
                    ConnectionApiModule,
                    app_manager=app_manager
                )

            # Retrieve API module
            connection_api_module = app_manager.module_manager.get_module("connection_api_module")
            if not connection_api_module:
                raise Exception("ConnectionMySqlModule is not registered in ModuleManager.")

            connection_api_module.initialize(app_manager.flask_app)

            # Ensure LoginModule is registered LAST
            if not app_manager.module_manager.get_module("login_module"):
                print("Registering LoginModule...")
                app_manager.module_manager.register_module(
                    "login_module",
                    LoginModule,
                    app_manager=app_manager
                )

            login_module = app_manager.module_manager.get_module("login_module")
            if login_module:
                login_module.register_routes()

            print("✅ MainPlugin initialized successfully.")

            # Register the `/` route with the correct view function
            connection_api_module.register_route("/", self.home, methods=["GET"])
            print("✅ Route '/' registered successfully.")
        except Exception as e:
            print(f"❌ Error initializing MainPlugin: {e}")
            raise

    def home(self):
        """Handle the root route."""
        return "Il-recall app / route."
