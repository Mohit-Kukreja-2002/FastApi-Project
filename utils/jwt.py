from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from utils.redis_client import redis_client
import json

load_dotenv()

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN")
ACTIVATION_SECRET = os.getenv("ACTIVATION_SECRET")

ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE", "300"))  # 5 minutes in seconds
REFRESH_TOKEN_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE", "259200"))  # 3 days in seconds

def create_access_token(user_id: str) -> str:
    payload = {"id": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm="HS256")

def create_refresh_token(user_id: str) -> str:
    payload = {"id": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(days=3)}
    return jwt.encode(payload, REFRESH_TOKEN_SECRET, algorithm="HS256")

def create_activation_token(user: dict, activation_code: str) -> str:
    payload = {
        "user": user,
        "activationCode": activation_code,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    return jwt.encode(payload, ACTIVATION_SECRET, algorithm="HS256")

def verify_token(token: str, secret: str) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except JWTError:
        raise JWTError("Invalid token")

def get_access_token_options():
    return {
        "max_age": ACCESS_TOKEN_EXPIRE * 60,
        "httponly": True,
        "samesite": "lax",
    }

def get_refresh_token_options():
    return {
        "max_age": REFRESH_TOKEN_EXPIRE * 24 * 60 * 60,
        "httponly": True,
        "samesite": "lax",
    }

def send_token(user: dict, response):
    """Set tokens in cookies and return response"""
    user_id = str(user["_id"])
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    # Upload session to redis
    redis_client.set(user_id, json.dumps(user, default=str))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user
    }

