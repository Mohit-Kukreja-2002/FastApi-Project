import redis
import os
from dotenv import load_dotenv
from redis.exceptions import RedisError
load_dotenv()

def get_redis_client():
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        print("Redis connected")
        return redis.from_url(redis_url, decode_responses=False)
    raise RedisError("Redis connection failed")

redis_client = get_redis_client()

