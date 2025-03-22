"""
Redis Manager Module

This module provides a singleton Redis connection manager for the application.
It handles connection pooling, retries, and provides a unified interface for Redis operations.
"""

import os
import redis
from redis.connection import ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError
from tools.logger.custom_logging import get_logger

logger = get_logger(__name__)

class RedisManager:
    """
    A singleton Redis connection manager that handles connection pooling and provides
    a unified interface for Redis operations across the application.
    
    Attributes:
        _instance (RedisManager): Singleton instance of the manager
        _pool (ConnectionPool): Redis connection pool
        host (str): Redis host address
        port (int): Redis port number
        max_connections (int): Maximum number of connections in the pool
        socket_timeout (int): Socket timeout in seconds
        socket_connect_timeout (int): Connection timeout in seconds
    """
    
    _instance = None
    _pool = None

    @classmethod
    def get_instance(cls):
        """
        Get or create the singleton instance of RedisManager.
        
        Returns:
            RedisManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the Redis manager with configuration from environment variables."""
        self.host = os.getenv('REDIS_HOST', 'recall_redis')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', 10))
        self.socket_timeout = int(os.getenv('REDIS_SOCKET_TIMEOUT', 5))
        self.socket_connect_timeout = int(os.getenv('REDIS_CONNECT_TIMEOUT', 5))
        self._initialize_pool()

    def _initialize_pool(self):
        """
        Initialize the Redis connection pool with configured parameters.
        
        Raises:
            Exception: If pool initialization fails
        """
        if self._pool is None:
            try:
                self._pool = ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=0,
                    decode_responses=True,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_connect_timeout,
                    retry_on_timeout=True,
                    max_connections=self.max_connections
                )
                logger.info(
                    f"Redis connection pool initialized with "
                    f"host={self.host}, port={self.port}, "
                    f"max_connections={self.max_connections}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Redis connection pool: {str(e)}")
                raise

    def get_client(self):
        """
        Get a Redis client from the connection pool.
        
        Returns:
            redis.Redis: A Redis client instance
            
        Raises:
            RuntimeError: If connection fails
        """
        try:
            client = redis.Redis(connection_pool=self._pool)
            # Test the connection
            client.ping()
            return client
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error: {str(e)}")
            raise RuntimeError("Redis connection error") from e
        except Exception as e:
            logger.error(f"Unexpected Redis error: {str(e)}")
            raise

    def close(self):
        """Close the Redis connection pool and clean up resources."""
        if self._pool:
            self._pool.disconnect()
            logger.info("Redis connection pool closed")
            
    def __del__(self):
        """Ensure connection pool is closed when the manager is destroyed."""
        self.close() 