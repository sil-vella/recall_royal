from typing import Optional
from flask import Flask, request, jsonify
from functools import wraps
from tools.logger.custom_logging import custom_log, log_error, ErrorCode

class BaseModule:
    """Base module for all plugin modules"""
    def __init__(self, app_manager=None):
        self.app = None
        self.app_manager = app_manager
        if app_manager:
            self.init_app(app_manager)
    
    def init_app(self, app_manager):
        """Initialize the module with an AppManager instance"""
        self.app_manager = app_manager
        self.app = app_manager.flask_app if app_manager else None

class SecureBaseModule(BaseModule):
    """Base module for modules requiring security features"""
    def __init__(self, app_manager=None):
        self.secret_key = None
        self.jwt_key = None
        self.encryption_key = None
        super().__init__(app_manager)
    
    def init_app(self, app_manager):
        """Initialize the module with security features"""
        super().init_app(app_manager)
        if not self.app:
            return
            
        # Load secrets from app config
        self.secret_key = self.app.config.get('SECRET_KEY')
        self.jwt_key = self.app.config.get('JWT_SECRET_KEY')
        self.encryption_key = self.app.config.get('ENCRYPTION_KEY')
        
    def get_jwt_token(self, payload: dict) -> str:
        """Generate a JWT token"""
        import jwt
        if not self.jwt_key:
            error_response = log_error(ErrorCode.INTERNAL_ERROR, "JWT key not configured")
            raise ValueError(error_response.to_dict()["error"]["message"])
        return jwt.encode(
            payload=payload,
            key=self.jwt_key,
            algorithm='HS256'
        )
    
    def verify_jwt_token(self, token: str) -> dict:
        """Verify and decode a JWT token"""
        import jwt
        if not self.jwt_key:
            error_response = log_error(ErrorCode.INTERNAL_ERROR, "JWT key not configured")
            raise ValueError(error_response.to_dict()["error"]["message"])
        try:
            return jwt.decode(
                jwt=token,
                key=self.jwt_key,
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            error_response = log_error(ErrorCode.TOKEN_EXPIRED, "Token has expired")
            raise ValueError(error_response.to_dict()["error"]["message"])
        except jwt.InvalidTokenError:
            error_response = log_error(ErrorCode.TOKEN_INVALID, "Invalid token format or signature")
            raise ValueError(error_response.to_dict()["error"]["message"])

    def require_auth(self, f):
        """Decorator to protect routes with JWT authentication."""
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                error_response = log_error(ErrorCode.TOKEN_MISSING, "No token provided in Authorization header")
                return jsonify(error_response.to_dict()), error_response.http_status
                
            token = auth_header.split(' ')[1]
            try:
                user_data = self.verify_jwt_token(token)
                return f(*args, **kwargs)
            except ValueError as e:
                error_response = log_error(ErrorCode.TOKEN_INVALID, str(e))
                return jsonify(error_response.to_dict()), error_response.http_status
        return decorated 