import os
import redis
from redis.connection import ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError
from tools.logger.custom_logging import get_logger

logger = get_logger(__name__)

class RedisManager:
    _instance = None
    _pool = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.host = os.getenv('REDIS_HOST', 'recall_redis')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self._initialize_pool()

    def _initialize_pool(self):
        if self._pool is None:
            try:
                self._pool = ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=0,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    max_connections=10
                )
                logger.info(f"Redis connection pool initialized with host={self.host}, port={self.port}")
            except Exception as e:
                logger.error(f"Failed to initialize Redis connection pool: {str(e)}")
                raise

    def get_client(self):
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
        if self._pool:
            self._pool.disconnect()
            logger.info("Redis connection pool closed") 