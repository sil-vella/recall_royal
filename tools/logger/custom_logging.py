import logging
import os
import json
import functools
import inspect
import types
import re
import sys
import traceback
from enum import Enum
from typing import Dict, Any, Optional
from utils.config.config import Config  # Import global config

# Error codes and messages for standardized error handling
class ErrorCode(Enum):
    # Authentication Errors (1xx)
    INVALID_CREDENTIALS = (100, "Invalid credentials")
    TOKEN_EXPIRED = (101, "Authentication expired")
    TOKEN_INVALID = (102, "Invalid authentication token")
    TOKEN_MISSING = (103, "Authentication required")
    
    # Authorization Errors (2xx)
    UNAUTHORIZED = (200, "Unauthorized access")
    INSUFFICIENT_PERMISSIONS = (201, "Insufficient permissions")
    
    # Input Validation Errors (3xx)
    INVALID_INPUT = (300, "Invalid input provided")
    MISSING_REQUIRED_FIELD = (301, "Required field missing")
    INVALID_FORMAT = (302, "Invalid format")
    
    # Resource Errors (4xx)
    RESOURCE_NOT_FOUND = (400, "Resource not found")
    RESOURCE_EXISTS = (401, "Resource already exists")
    RESOURCE_CONFLICT = (402, "Resource conflict")
    
    # Database Errors (5xx)
    DB_ERROR = (500, "Database error")
    DB_CONNECTION_ERROR = (501, "Database connection error")
    DB_QUERY_ERROR = (502, "Database query error")
    
    # Server Errors (9xx)
    INTERNAL_ERROR = (900, "Internal server error")
    SERVICE_UNAVAILABLE = (901, "Service temporarily unavailable")
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

class ErrorResponse:
    def __init__(self, 
                 error_code: ErrorCode,
                 detail: Optional[str] = None,
                 http_status: int = None):
        self.error_code = error_code
        self.detail = detail
        # Map error code ranges to HTTP status codes
        if http_status is None:
            if 100 <= error_code.code < 200:
                self.http_status = 401
            elif 200 <= error_code.code < 300:
                self.http_status = 403
            elif 300 <= error_code.code < 400:
                self.http_status = 400
            elif 400 <= error_code.code < 500:
                self.http_status = 404
            elif 500 <= error_code.code < 600:
                self.http_status = 503
            else:
                self.http_status = 500
        else:
            self.http_status = http_status

    def to_dict(self) -> Dict[str, Any]:
        response = {
            "error": {
                "code": self.error_code.code,
                "message": self.error_code.message
            }
        }
        if self.detail and Config.DEBUG:  # Only include details in debug mode
            response["error"]["detail"] = self.detail
        return response

# ✅ Check the config's global logging flag first
if not Config.LOGGING_ENABLED:
    CUSTOM_LOGGING_ENABLED = False
    GAMEPLAY_LOGGING_ENABLED = False
    FUNCTION_LOGGING_ENABLED = False
else:
    # ✅ Individual logging toggles (these still work, but only if ENABLE_LOGGER=True)
    CUSTOM_LOGGING_ENABLED = True
    GAMEPLAY_LOGGING_ENABLED = True
    FUNCTION_LOGGING_ENABLED = True

def custom_serializer(obj):
    if isinstance(obj, (set, tuple)):
        return list(obj)
    return str(obj)

class CustomFormatter(logging.Formatter):
    def __init__(self):
        super().__init__("[%(asctime)s] - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)", "%Y-%m-%d %H:%M:%S")

    def format(self, record):
        if not isinstance(record.msg, str):
            record.msg = json.dumps(record.msg, default=custom_serializer, indent=4)
        else:
            try:
                obj = json.loads(record.msg)
                record.msg = json.dumps(obj, indent=4)
            except ValueError:
                pass
        return super(CustomFormatter, self).format(record)

class SimpleFormatter(logging.Formatter):
    def __init__(self):
        super().__init__("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")

# ✅ Define loggers **only if ENABLE_LOGGER is True**
if Config.LOGGING_ENABLED:
    # Logger for custom_log
    custom_log_file_name = 'server.log'
    custom_log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), custom_log_file_name)
    custom_logger = logging.getLogger('custom_log')
    custom_logger.setLevel(logging.DEBUG)
    custom_handler = logging.FileHandler(custom_log_file_path, 'w')
    custom_handler.setFormatter(CustomFormatter())
    custom_logger.addHandler(custom_handler)

    # Logger for game_play_log
    game_play_log_file_name = 'game_play.log'
    game_play_log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), game_play_log_file_name)
    game_play_logger = logging.getLogger('game_play_log')
    game_play_logger.setLevel(logging.DEBUG)
    game_play_handler = logging.FileHandler(game_play_log_file_path, 'w')
    game_play_handler.setFormatter(SimpleFormatter())
    game_play_logger.addHandler(game_play_handler)

    # Logger for function_log
    function_log_file_name = 'function.log'
    function_log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), function_log_file_name)
    function_logger = logging.getLogger('function_log')
    function_logger.setLevel(logging.DEBUG)
    function_handler = logging.FileHandler(function_log_file_path, 'w')
    function_handler.setFormatter(SimpleFormatter())
    function_logger.addHandler(function_handler)
else:
    # ✅ If logging is disabled, replace loggers with dummy functions
    custom_logger = None
    game_play_logger = None
    function_logger = None

def sanitize_log_message(message):
    """Ensures UTF-8 encoding and removes non-ASCII characters if necessary."""
    if not isinstance(message, str):
        message = json.dumps(message, default=custom_serializer, indent=4)
    
    try:
        message = message.encode('utf-8').decode('utf-8')
    except UnicodeEncodeError:
        message = message.encode('ascii', 'ignore').decode('ascii')

    message = re.sub(r'[^\x00-\x7F]+', '', message)

    return message

# ✅ Log functions respect ENABLE_LOGGER and individual flags
def custom_log(message):
    if Config.LOGGING_ENABLED and CUSTOM_LOGGING_ENABLED and custom_logger:
        message = sanitize_log_message(message)
        custom_logger.debug(message)

def game_play_log(message, action=None):
    if Config.LOGGING_ENABLED and GAMEPLAY_LOGGING_ENABLED and game_play_logger:
        message = sanitize_log_message(message)
        game_play_logger.debug(message)

def function_log(message):
    if Config.LOGGING_ENABLED and FUNCTION_LOGGING_ENABLED and function_logger:
        message = sanitize_log_message(message)
        function_logger.debug(message)

def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if Config.LOGGING_ENABLED and FUNCTION_LOGGING_ENABLED:
            custom_log(f"Wrapping function {func.__name__} with logging")
            custom_log(f"Function logging enabled: {FUNCTION_LOGGING_ENABLED}")
            if not getattr(func, "_logging_in_progress", False):
                setattr(func, "_logging_in_progress", True)
                arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
                try:
                    arg_list = ', '.join(f'{name}={value}' for name, value in zip(arg_names, args))
                except AttributeError as e:
                    custom_log(f"Error while logging arguments for {func.__name__}: {e}")
                    arg_list = 'Error logging arguments'

                function_log(f"Entering {func.__name__} with args: {arg_list}")
                custom_log(f"Entered {func.__name__}")

                initial_locals = {k: v for k, v in locals().items() if k != 'initial_locals'}
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    custom_log(f"Error while executing {func.__name__}: {e}")
                    raise
                final_locals = {k: v for k, v in locals().items() if k != 'final_locals'}

                changed_vars = {var: final_locals[var] for var in final_locals if var in initial_locals and final_locals[var] != initial_locals[var]}
                for var, val in changed_vars.items():
                    function_log(f"Variable {var} changed to {val}")

                function_log(f"Exiting {func.__name__} with result: {result}\n")
                custom_log(f"Exiting {func.__name__}")
                setattr(func, "_logging_in_progress", False)
            else:
                result = func(*args, **kwargs)
            return result
        else:
            return func(*args, **kwargs)
    wrapper._is_logged = True
    return wrapper

def add_logging_to_plugin(plugin, exclude_instances=None, exclude_packages=None):
    if Config.LOGGING_ENABLED:
        custom_log(f"Adding logging to plugin: {plugin.__name__}")
    exclude_functions = {log_function_call, add_logging_to_plugin, custom_log, game_play_log, function_log}
    if exclude_instances is None:
        exclude_instances = []
    if exclude_packages is None:
        exclude_packages = []

    for name, obj in inspect.getmembers(plugin):
        if isinstance(obj, types.FunctionType) and not hasattr(obj, '_is_logged'):
            if obj not in exclude_functions and name != "__init__":
                if not any(obj.__plugin__.startswith(package) for package in exclude_packages):
                    if Config.LOGGING_ENABLED:
                        custom_log(f"Adding logging to function: {name} in plugin: {plugin.__name__}")
                    setattr(plugin, name, log_function_call(obj))
                    if Config.LOGGING_ENABLED:
                        custom_log(f"Function {name} is now decorated.")
        elif isinstance(obj, type):  # Check if obj is a class
            if Config.LOGGING_ENABLED:
                custom_log(f"Class {name} found in plugin: {plugin.__name__}")
            for cls_name, cls_member in inspect.getmembers(obj):
                if isinstance(cls_member, types.FunctionType) and not hasattr(cls_member, '_is_logged'):
                    if cls_member not in exclude_functions and cls_name != "__init__":
                        if not any(cls_member.__plugin__.startswith(package) for package in exclude_packages):
                            if Config.LOGGING_ENABLED:
                                custom_log(f"Adding logging to method: {cls_name} in class {name}")
                            setattr(obj, cls_name, log_function_call(cls_member))
                            if Config.LOGGING_ENABLED:
                                custom_log(f"Method {cls_name} in class {name} is now decorated.")
        elif any(isinstance(obj, cls) for cls in exclude_instances):
            if Config.LOGGING_ENABLED:
                custom_log(f"Skipping logging for excluded instance: {name}")

def log_error(error_code: ErrorCode, detail: str = None, exc_info: Exception = None) -> ErrorResponse:
    """
    Log an error and return a standardized error response.
    
    Args:
        error_code: The ErrorCode enum value
        detail: Additional error details (only logged, not sent to client unless in debug mode)
        exc_info: Exception object if available
    
    Returns:
        ErrorResponse object with standardized error format
    """
    if Config.LOGGING_ENABLED and custom_logger:
        error_msg = f"Error {error_code.code}: {error_code.message}"
        if detail:
            error_msg += f" - Details: {detail}"
        if exc_info:
            error_msg += f"\nException: {str(exc_info)}"
            if hasattr(exc_info, '__traceback__'):
                error_msg += f"\nTraceback: {''.join(traceback.format_tb(exc_info.__traceback__))}"
        
        custom_logger.error(error_msg)
    
    return ErrorResponse(error_code, detail)

def get_logger(name):
    """Get a logger instance for the given name."""
    logger = logging.getLogger(name)
    if not logger.handlers:  # Only add handler if it doesn't already have one
        handler = logging.StreamHandler()
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO if not Config.DEBUG else logging.DEBUG)
    return logger
