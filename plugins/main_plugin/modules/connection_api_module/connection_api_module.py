import os
import psycopg2
import psycopg2.extras
import psycopg2.pool
import jwt
from cryptography.fernet import Fernet
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from tools.logger.custom_logging import custom_log, log_error, ErrorCode, get_logger
from utils.config.config import Config  # Import global config
from ..base_module import SecureBaseModule
import time
from utils.redis.redis_manager import RedisManager

logger = get_logger(__name__)

class ConnectionApiModule(SecureBaseModule):
    """Handles database connection pooling, Redis caching, and API security."""
    
    db_pool = None
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # Ensure this is securely stored
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

    def __init__(self, app_manager=None):
        """Initialize the module with a database connection pool, Redis caching, and Flask-Limiter."""
        if not app_manager or not app_manager.flask_app:
            error_response = log_error(ErrorCode.INTERNAL_ERROR, "AppManager is not initialized or Flask app is missing")
            raise RuntimeError(error_response.to_dict()["error"]["message"])

        self.app = app_manager.flask_app
        self.app_manager = app_manager
        
        # Initialize SecureBaseModule after validating app_manager
        super().__init__(app_manager)

        # Initialize PostgreSQL connection pool
        if not ConnectionApiModule.db_pool:
            ssl_mode = "require" if Config.USE_SSL else "disable"
            db_name = os.getenv("POSTGRES_DB", "recall_db")  # Use recall_db as default

            try:
                ConnectionApiModule.db_pool = psycopg2.pool.SimpleConnectionPool(
                    Config.DB_POOL_MIN_CONN,
                    Config.DB_POOL_MAX_CONN,
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASSWORD"),
                    host=os.getenv("DB_HOST", "127.0.0.1"),
                    port=os.getenv("DB_PORT", "5432"),
                    database=db_name,
                    sslmode=ssl_mode  # Dynamically set SSL mode
                )
                custom_log(f"🔌 Database connection initialized with SSL mode: {ssl_mode}, Pool size: {Config.DB_POOL_MIN_CONN}-{Config.DB_POOL_MAX_CONN}")
            except psycopg2.Error as e:
                error_response = log_error(ErrorCode.DB_CONNECTION_ERROR, f"Failed to initialize database connection pool", e)
                raise RuntimeError(error_response.to_dict()["error"]["message"])

        # Initialize Redis client for caching
        self.redis_client = Redis.from_url(Config.RATE_LIMIT_STORAGE_URL, decode_responses=True)
        self.redis_manager = RedisManager.get_instance()

    def initialize(self, flask_app):
        """Initialize the module with additional setup after registration."""
        if not flask_app:
            error_response = log_error(ErrorCode.INTERNAL_ERROR, "ConnectionApiModule requires a valid Flask app instance")
            raise RuntimeError(error_response.to_dict()["error"]["message"])
            
        # Use Redis for Flask-Limiter (Rate limiting)
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
        
        custom_log("✅ ConnectionApiModule successfully initialized with Flask app.")

    def health_check(self):
        """Health check endpoint that verifies Redis connection"""
        try:
            redis_client = self.redis_manager.get_client()
            redis_client.ping()
            return jsonify({
                "status": "healthy",
                "redis": "connected"
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                "status": "unhealthy",
                "redis": "disconnected",
                "error": str(e)
            }), 500

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
                error_response = log_error(ErrorCode.DB_CONNECTION_ERROR, "Failed to retrieve database connection from pool")
                raise RuntimeError(error_response.to_dict()["error"]["message"])
            return connection
        except Exception as e:
            error_response = log_error(ErrorCode.DB_CONNECTION_ERROR, "Database connection retrieval error", e)
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
            
            # Check if the query contains RETURNING clause
            result = None
            if "RETURNING" in query.upper():
                result = cursor.fetchall()
                custom_log("✅ Query executed successfully with returned data")
            else:
                custom_log("✅ Query executed successfully")
            
            connection.commit()
            cursor.close()
            return result
        except psycopg2.Error as e:
            error_response = log_error(ErrorCode.DB_QUERY_ERROR, "Error executing query", e)
            connection.rollback()
            return None
        finally:
            self.release_connection(connection)

    def fetch_from_db(self, query, params=None, as_dict=False):
        connection = self.get_connection()
        if not connection:
            error_response = log_error(ErrorCode.DB_CONNECTION_ERROR, "Failed to get database connection")
            return None
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor if as_dict else None)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in result] if as_dict else result
        except psycopg2.Error as e:
            error_response = log_error(ErrorCode.DB_QUERY_ERROR, "Database error in SELECT", e)
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
            view_func = self.require_auth(view_func)  # Using SecureBaseModule's require_auth

        self.app.add_url_rule(path, endpoint=endpoint, view_func=view_func, methods=methods)
        custom_log(f"🌐 Route registered: {path} [{', '.join(methods)}] as '{endpoint}'")
        
    def test_route(self):
        """Test route that uses Redis for basic operations"""
        try:
            redis_client = self.redis_manager.get_client()
            redis_client.incr('test_counter')
            count = redis_client.get('test_counter')
            return jsonify({
                "message": "Test route working",
                "counter": count
            }), 200
        except Exception as e:
            logger.error(f"Test route failed: {str(e)}")
            return jsonify({
                "error": "Test route failed",
                "details": str(e)
            }), 500

    def dispose(self):
        """Dispose of database connections and cleanup resources."""
        custom_log("🔄 Disposing ConnectionModule...")
        if ConnectionApiModule.db_pool:
            ConnectionApiModule.db_pool.closeall()
            custom_log("🔌 Database connection pool closed.")

    def secure_test_route(self):
        """Test endpoint that requires JWT authentication"""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            error_response = log_error(ErrorCode.TOKEN_MISSING, "No token provided in Authorization header")
            return jsonify(error_response.to_dict()), error_response.http_status
            
        token = auth_header.split(' ')[1]
        try:
            # Using SecureBaseModule's verify_jwt_token method
            user_data = self.verify_jwt_token(token)
            return jsonify({
                "message": "Secure endpoint accessed successfully",
                "user_data": user_data
            })
        except ValueError as e:
            error_response = log_error(ErrorCode.TOKEN_INVALID, str(e))
            return jsonify(error_response.to_dict()), error_response.http_status