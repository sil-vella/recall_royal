import os
import psycopg2
import psycopg2.extras
import psycopg2.pool
import bcrypt
import jwt
from cryptography.fernet import Fernet
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from tools.logger.custom_logging import custom_log
from utils.config.config import Config  # Import global config
from ..base_module import SecureBaseModule
import time

class ConnectionApiModule(SecureBaseModule):
    """Handles database connection pooling, Redis caching, authentication, rate-limiting, and API security."""
    
    db_pool = None
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # Ensure this is securely stored
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())  # Used for encryption

    def __init__(self, app_manager=None):
        """Initialize the module with a database connection pool, Redis caching, and Flask-Limiter."""
        if not app_manager or not app_manager.flask_app:
            raise RuntimeError("❌ AppManager is not initialized or Flask app is missing.")

        self.app = app_manager.flask_app
        self.app_manager = app_manager
        
        # Initialize SecureBaseModule after validating app_manager
        super().__init__(app_manager)

        # ✅ Initialize PostgreSQL connection pool
        if not ConnectionApiModule.db_pool:
            ssl_mode = "require" if Config.USE_SSL else "disable"

            ConnectionApiModule.db_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,  # Min and max connections in the pool
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("DB_HOST", "127.0.0.1"),
                port=os.getenv("DB_PORT", "5432"),
                database=os.getenv("POSTGRES_DB"),
                sslmode=ssl_mode  # Dynamically set SSL mode
            )

        # ✅ Initialize Redis client for caching
        self.redis_client = Redis.from_url(Config.RATE_LIMIT_STORAGE_URL, decode_responses=True)

        custom_log(f"🔌 Database connection initialized with SSL mode: {ssl_mode}")

    def initialize(self, flask_app):
        """Initialize the module with additional setup after registration."""
        if not flask_app:
            raise RuntimeError("❌ ConnectionApiModule requires a valid Flask app instance.")
            
        # ✅ Use Redis for Flask-Limiter (Rate limiting)
        self.limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=Config.RATE_LIMIT_STORAGE_URL,
            strategy="fixed-window"
        )
        self.limiter.init_app(flask_app)  # Attach Limiter to Flask app

        # Register routes
        flask_app.add_url_rule("/health", "health_check", self.health_check)
        flask_app.add_url_rule("/test", "test_route", self.test_route, methods=['GET', 'POST'])
        
        # Add secure test endpoint
        flask_app.add_url_rule("/secure-test", "secure_test", self.secure_test_route, methods=['POST'])
        flask_app.add_url_rule("/login-test", "login_test", self.login_test_route, methods=['POST'])
        
        custom_log("✅ ConnectionApiModule successfully initialized with Flask app.")

    def init_app(self, app_manager):
        """Initialize the module with an AppManager instance."""
        super().init_app(app_manager)
        if not self.app:
            raise RuntimeError("❌ ConnectionApiModule requires a valid Flask app instance.")
            
        # ✅ Use Redis for Flask-Limiter (Rate limiting)
        self.limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=Config.RATE_LIMIT_STORAGE_URL,
            strategy="fixed-window"
        )
        self.limiter.init_app(self.app)  # Attach Limiter to Flask app

        # Register routes
        self.app.add_url_rule("/health", "health_check", self.health_check)
        self.app.add_url_rule("/test", "test_route", self.test_route, methods=['GET', 'POST'])
        
        # Add secure test endpoint
        self.app.add_url_rule("/secure-test", "secure_test", self.secure_test_route, methods=['POST'])
        self.app.add_url_rule("/login-test", "login_test", self.login_test_route, methods=['POST'])
        
        custom_log("✅ ConnectionApiModule successfully initialized with Flask app.")

    def health_check(self):
        """Health check endpoint for Flask API."""
        return jsonify({"status": "healthy", "message": "API is running."}), 200


    # ================================
    # 🚀 DATABASE CONNECTION MANAGEMENT
    # ================================

    def get_connection(self):
        """Retrieve a database connection from the pool."""
        try:
            connection = ConnectionApiModule.db_pool.getconn()
            if connection:
                custom_log("✅ Successfully retrieved database connection from pool.")
            else:
                custom_log("❌ Failed to retrieve database connection from pool.")
            return connection
        except Exception as e:
            custom_log(f"❌ Database connection retrieval error: {e}")
            return None


    def release_connection(self, connection):
        """Release a database connection back to the pool."""
        ConnectionApiModule.db_pool.putconn(connection)

    def execute_query(self, query, params=None):
        """Execute INSERT, UPDATE, DELETE queries safely with parameterized queries."""
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            connection.commit()
            cursor.close()
            custom_log("✅ Query executed successfully")
        except psycopg2.Error as e:
            custom_log(f"❌ Error executing query: {e}")
            connection.rollback()
        finally:
            self.release_connection(connection)

    def fetch_from_db(self, query, params=None, as_dict=False):
        connection = self.get_connection()
        if not connection:
            custom_log("❌ Failed to get database connection.")
            return None
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor if as_dict else None)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in result] if as_dict else result
        except psycopg2.Error as e:
            custom_log(f"❌ Database error in SELECT: {e}")
            connection.rollback()
            return None
        finally:
            self.release_connection(connection)


    # ================================
    # 🔄 REDIS CACHE MANAGEMENT
    # ================================

    def store_rate_limit_data(self, key, value, ttl=60):
        """Store rate limit data in Redis."""
        self.redis_client.setex(key, ttl, value)
        custom_log(f"✅ Rate limit data stored in Redis for key: {key}")

    def fetch_rate_limit_data(self, key):
        """Fetch rate limit data from Redis."""
        value = self.redis_client.get(key)
        custom_log(f"🔍 Retrieved rate limit data for key: {key} -> {value}")
        return value

    def clear_rate_limit_data(self, key):
        """Clear rate limit data from Redis."""
        self.redis_client.delete(key)
        custom_log(f"🗑️ Cleared rate limit data for key: {key}")

    # ================================
    # 🔑 AUTHENTICATION & SECURITY
    # ================================

    def hash_password(self, password):
        """Hash passwords securely using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def verify_password(self, password, hashed_password):
        """Verify passwords securely."""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def encrypt_data(self, data):
        """Encrypt sensitive data using Fernet."""
        cipher = Fernet(self.ENCRYPTION_KEY.encode())
        return cipher.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data."""
        cipher = Fernet(self.ENCRYPTION_KEY.encode())
        return cipher.decrypt(encrypted_data.encode()).decode()

    def generate_token(self, user_id, is_admin=False):
        """Generate a JWT token."""
        return jwt.encode({"user_id": user_id, "is_admin": is_admin}, self.SECRET_KEY, algorithm="HS256")

    def verify_token(self, token):
        """Verify a JWT token."""
        try:
            return jwt.decode(token, self.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        
    def protected_route(self, f):
        """Decorator to protect routes with JWT authentication."""
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization")
            if not token or not self.verify_token(token):
                return {"error": "Unauthorized"}, 401
            return f(*args, **kwargs)
        return wrapper

    def register_route(self, path, view_func, methods=None, endpoint=None, require_auth=False):
        """Register a Flask route with optional authentication, preventing duplicate registration."""
        if self.app is None:
            raise RuntimeError("ConnectionModule must be initialized with a Flask app before registering routes.")

        methods = methods or ["GET"]
        endpoint = endpoint or view_func.__name__

        # Check if the endpoint already exists
        existing_endpoints = {rule.endpoint for rule in self.app.url_map.iter_rules()}
        if endpoint in existing_endpoints:
            custom_log(f"⚠️ Route '{path}' already exists with endpoint '{endpoint}'. Skipping registration.")
            return  # Exit to prevent overwriting

        if require_auth:
            view_func = self.protected_route(view_func)

        self.app.add_url_rule(path, endpoint=endpoint, view_func=view_func, methods=methods)
        custom_log(f"🌐 Route registered: {path} [{', '.join(methods)}] as '{endpoint}'")

        
    def test_route(self):
        """A simple test route to verify API is working."""
        custom_log("🟢 Test route accessed successfully.")
        return jsonify({"message": "Test route working!"}), 200

    def dispose(self):
        """Dispose of database connections and cleanup resources."""
        custom_log("🔄 Disposing ConnectionModule...")
        if ConnectionApiModule.db_pool:
            ConnectionApiModule.db_pool.closeall()
            custom_log("🔌 Database connection pool closed.")

    def authenticate_request(self, token: str) -> dict:
        """Authenticate a request using JWT token"""
        return self.verify_jwt_token(token)
        
    def generate_auth_token(self, user_data: dict) -> str:
        """Generate an authentication token"""
        return self.get_jwt_token(user_data)

    # Add these new test methods
    def login_test_route(self):
        """Test endpoint to get a JWT token"""
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({"error": "Username required"}), 400
            
        # For testing, generate a token with user data
        user_data = {
            "username": data['username'],
            "role": "test_user",
            "exp": int(time.time()) + 3600  # Token expires in 1 hour
        }
        
        token = self.generate_auth_token(user_data)
        return jsonify({
            "token": token,
            "message": "Test login successful"
        })

    def secure_test_route(self):
        """Test endpoint that requires JWT authentication"""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "No token provided"}), 401
            
        token = auth_header.split(' ')[1]
        try:
            # This will use our new SecureBaseModule's verify_jwt_token method
            user_data = self.verify_jwt_token(token)
            return jsonify({
                "message": "Secure endpoint accessed successfully",
                "user_data": user_data
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 401
