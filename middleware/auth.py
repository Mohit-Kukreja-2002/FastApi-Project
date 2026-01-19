from fastapi import HTTPException, Cookie, status, Depends
from jose import jwt, JWTError
from utils.jwt import ACCESS_TOKEN_SECRET, verify_token
from utils.redis_client import redis_client
from utils.error_handler import ErrorHandler
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timezone


load_dotenv()

def is_authenticated(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please login to access this resource"
        )
    
    try:
        decoded = verify_token(access_token, ACCESS_TOKEN_SECRET)
        
        # Check if token is expired
        exp = decoded.get("exp")
        if exp and exp <= datetime.now(timezone.utc).timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        user_id = decoded.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_json = redis_client.get(user_id)
        if isinstance(user_json, bytes):
            user_json = user_json.decode('utf-8')
        elif user_json is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please login to access this resource"
            )
        
        user = json.loads(user_json)
        return user
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

def authorize_roles(*roles):
    def role_checker(user: dict = None):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authenticated"
            )
        user_role = user.get("role", "")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role: {user_role} is not allowed to access this resource"
            )
        return user
    return role_checker

