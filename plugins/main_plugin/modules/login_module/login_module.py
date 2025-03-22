import bcrypt
import hashlib
from flask import request, jsonify
from tools.logger.custom_logging import custom_log
from core.managers.module_manager import ModuleManager
import jwt
import yaml
import os
import time
from datetime import datetime, timedelta
from ..base_module import SecureBaseModule

class LoginModule(SecureBaseModule):
    def __init__(self, app_manager=None):
        """Initialize the LoginModule."""
        super().__init__(app_manager)
        self.connection_api_module = self.get_connection_api_module()

        if not self.connection_api_module:
            raise RuntimeError("LoginModule: Failed to retrieve ConnectionModule from ModuleManager.")
    
        self._create_users_table()

        custom_log("✅ LoginModule initialized.")

    def get_connection_api_module(self):
        """Retrieve ConnectionModule from ModuleManager."""
        module_manager = self.app_manager.module_manager if self.app_manager else ModuleManager()
        connection_api_module = module_manager.get_module("connection_api_module")

        if not connection_api_module:
            custom_log("❌ ConnectionModule not found in ModuleManager.")
        
        return connection_api_module

    def _create_users_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.connection_api_module.execute_query(query)

    def register_routes(self):
        """Register authentication routes."""
        if not self.app:
            raise RuntimeError("Flask app is not available yet.")

        self.app.add_url_rule('/register', 'register', self.register_user, methods=['POST'])
        self.app.add_url_rule('/login', 'login', self.login_user, methods=['POST'])
        self.app.add_url_rule('/delete-user', 'delete_user', self.delete_user_request, methods=['POST'])
        self.app.add_url_rule('/secure', 'secure', self.secure_endpoint, methods=['GET'])

        custom_log("🌐 LoginModule: Authentication routes registered successfully.")

    def delete_user_request(self):
        """API Endpoint to delete a user and their data."""
        @self.require_auth
        def protected_delete():
            try:
                data = request.get_json()
                user_id = data.get("user_id")

                if not user_id:
                    return jsonify({"error": "User ID is required"}), 400

                # ✅ Call the proper delete method
                response, status_code = self.delete_user_data(user_id)
                return jsonify(response), status_code

            except Exception as e:
                custom_log(f"❌ Error in delete-user API: {e}")
                return jsonify({"error": "Server error"}), 500
        
        return protected_delete()

    def hash_password(self, password):
        """Hash the password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def check_password(self, password, hashed_password):
        """Check if a given password matches the stored hash."""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def _save_guessed_names(self, user_id, guessed_names):
        """Stores guessed names per category & level."""
        try:
            insert_query = """
            INSERT INTO guessed_names (user_id, category, level, guessed_name) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, category, level, guessed_name) 
            DO NOTHING;
            """

            for category, levels in guessed_names.items():
                for level_str, names in levels.items():
                    level = int(level_str.replace("level_", ""))  # Convert "level_1" -> 1

                    for name in names:
                        self.connection_api_module.execute_query(insert_query, (user_id, category, level, name))

            custom_log(f"✅ Guessed names saved for user {user_id}: {guessed_names}")

        except Exception as e:
            custom_log(f"❌ Error saving guessed names: {e}")

    def _get_category_progress(self, user_id):
        """Fetches category-based levels & points."""
        query = """
        SELECT category, level, points FROM user_category_progress WHERE user_id = %s;
        """
        result = self.connection_api_module.fetch_from_db(query, (user_id,), as_dict=True)

        return {row["category"]: {"level": row["level"], "points": row["points"]} for row in result} if result else {}

    def _save_category_progress(self, user_id, category_progress):
        """Saves user points & levels per category."""
        try:
            for category, progress in category_progress.items():
                points = progress.get("points", 0)
                level = int(progress.get("level", 1))  # Ensure level is an integer

                insert_query = """
                INSERT INTO user_category_progress (user_id, category, level, points)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, category, level) 
                DO UPDATE SET points = EXCLUDED.points, level = EXCLUDED.level, updated_at = CURRENT_TIMESTAMP;
                """

                self.connection_api_module.execute_query(insert_query, (user_id, category, level, points))

            custom_log(f"✅ Category progress saved for user {user_id}: {category_progress}")

        except Exception as e:
            custom_log(f"❌ Error saving category progress: {e}")

    def _get_guessed_names(self, user_id):
        """Retrieves guessed names grouped by category & level."""
        try:
            query = """
            SELECT category, level, guessed_name 
            FROM guessed_names WHERE user_id = %s;
            """
            results = self.connection_api_module.fetch_from_db(query, (user_id,), as_dict=True)

            guessed_names = {}

            for row in results:
                category = row["category"]
                level = f"level_{row['level']}"  # ✅ Convert 1 -> "level_1"
                name = row["guessed_name"]

                if category not in guessed_names:
                    guessed_names[category] = {}

                if level not in guessed_names[category]:
                    guessed_names[category][level] = []

                guessed_names[category][level].append(name)

            custom_log(f"📜 Retrieved guessed names for user {user_id}: {guessed_names}")
            return guessed_names

        except Exception as e:
            custom_log(f"❌ Error fetching guessed names: {e}")
            return {}

    def delete_user_data(self, user_id):
        """Delete all data associated with a user before removing them from the database."""
        try:
            if not self.connection_api_module:
                return {"error": "Database connection is unavailable"}, 500

            # ✅ Delete guessed names
            custom_log(f"🗑️ Deleting guessed names for User ID {user_id}...")
            self.connection_api_module.execute_query("DELETE FROM guessed_names WHERE user_id = %s", (user_id,))

            # ✅ Delete user progress
            custom_log(f"🗑️ Deleting category progress for User ID {user_id}...")
            self.connection_api_module.execute_query("DELETE FROM user_category_progress WHERE user_id = %s", (user_id,))

            # ✅ Finally, delete the user
            custom_log(f"🗑️ Deleting User ID {user_id} from users table...")
            self.connection_api_module.execute_query("DELETE FROM users WHERE id = %s", (user_id,))

            custom_log(f"✅ Successfully deleted all data for User ID {user_id}.")
            return {"message": f"User ID {user_id} and all associated data deleted successfully"}, 200

        except Exception as e:
            custom_log(f"❌ Error deleting user data: {e}")
            return {"error": f"Failed to delete user data: {str(e)}"}, 500

    def register_user(self):
        """Handles user registration."""
        try:
            custom_log("🟢 Registering user: Processing request...")

            data = request.get_json()
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            if not username or not email or not password:
                custom_log("⚠️ Missing required fields in registration request.")
                return jsonify({"error": "Missing required fields"}), 400

            # ✅ Check if email already exists
            query = "SELECT id FROM users WHERE email = %s;"
            existing_user = self.connection_api_module.fetch_from_db(query, (email,))
            if existing_user:
                custom_log(f"⚠️ Registration failed: Email '{email}' already exists.")
                return jsonify({"error": "Email is already registered"}), 400

            # ✅ Insert new user
            hashed_password = self.hash_password(password)
            insert_user_query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id;"
            user_result = self.connection_api_module.execute_query(insert_user_query, (username, email, hashed_password))

            if not user_result:
                custom_log("❌ Insert failed: No ID returned from insert statement.")
                return jsonify({"error": "User registration failed."}), 500

            custom_log(f"✅ User '{username}' registered successfully with ID {user_result[0][0]}.")
            return jsonify({
                "message": "User registered successfully",
                "user_id": user_result[0][0]
            }), 200

        except Exception as e:
            custom_log(f"❌ Error registering user: {e}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    def login_user(self):
        """Handles user login."""
        try:
            custom_log("🟢 Login attempt received...")

            data = request.get_json()
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                custom_log("⚠️ Login failed: Missing email or password.")
                return jsonify({"error": "Missing email or password"}), 400

            query = "SELECT id, username, password FROM users WHERE email = %s;"
            user = self.connection_api_module.fetch_from_db(query, (email,), as_dict=True)

            if not user:
                custom_log(f"⚠️ Login failed: Email '{email}' not found.")
                return jsonify({"error": "Invalid credentials"}), 401

            user = user[0]  # Get first row since fetch_from_db returns a list
            
            if not self.check_password(password, user["password"]):
                custom_log(f"⚠️ Login failed: Invalid password for email '{email}'.")
                return jsonify({"error": "Invalid credentials"}), 401

            # Generate JWT token using SecureBaseModule's method
            payload = {
                "user_id": user["id"],
                "username": user["username"],
                "exp": datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
            }
            token = self.get_jwt_token(payload)

            custom_log(f"✅ User '{user['username']}' logged in successfully.")
            return jsonify({
                "message": "Login successful",
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"]
                }
            }), 200

        except Exception as e:
            custom_log(f"❌ Error during login: {e}")
            return jsonify({"error": "Server error"}), 500

    def secure_endpoint(self):
        """Test endpoint that requires JWT authentication."""
        @self.require_auth
        def protected():
            return jsonify({
                "message": "You have accessed a secure endpoint",
                "status": "success"
            }), 200
        return protected()