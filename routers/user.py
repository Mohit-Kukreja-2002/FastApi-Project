from fastapi import APIRouter, HTTPException, Cookie, Response, status, Depends
from pydantic import EmailStr, BaseModel, Field
from passlib.context import CryptContext
from bson import ObjectId
from utils.jwt import create_activation_token, verify_token, send_token, create_access_token, create_refresh_token, get_access_token_options, get_refresh_token_options
from utils.error_handler import ErrorHandler
from utils.redis_client import redis_client
from utils.send_mail import send_mail
from models.user import UserCreate, UserLogin, UserResponse, UserUpdate, SocialAuth
from services.user_service import get_user_by_id
from middleware.auth import is_authenticated
import cloudinary
import cloudinary.uploader
import json
from datetime import datetime, timezone
import random
from utils.db import get_database

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/v1", tags=["user"])

class RegistrationRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)

class ActivationRequest(BaseModel):
    activation_token: str
    activation_code: str

class GetUserRequest(BaseModel):
    email: EmailStr

class GetUserPicRequest(BaseModel):
    email: EmailStr

class UpdateFundArrayRequest(BaseModel):
    id: str

@router.post("/registration")
async def registration_user(request: RegistrationRequest, database=Depends(get_database)):
    print('Im here')
    try:
        existing_user = await database.users.find_one({"email": request.email})
        print('existing_user', existing_user)
        if existing_user:
            raise ErrorHandler("Email already exists", 400)
        
        user_data = {
            "name": request.name,
            "email": request.email,
            "password": request.password
        }
        print('user_data', user_data)
        
        activation_code = str(random.randint(1000, 9999))
        activation_token = create_activation_token(user_data, activation_code)
        print('activation_token', activation_token)
        data = {
            "user": {"name": user_data["name"]},
            "activationCode": activation_code
        }
        
        try:
            await send_mail(
                email=user_data["email"],
                subject="Account Activation Mail",
                template="activation-mail.ejs",
                data=data
            )
            return {
                "success": True,
                "message": f"Please check your email: {user_data['email']} to activate your account",
                "activationToken": activation_token
            }
        except Exception as error:
            raise ErrorHandler(str(error), 400)
    except ErrorHandler:
        raise
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/activate-user")
async def activate_user(request: ActivationRequest, database=Depends(get_database)):
    try:
        from utils.jwt import ACTIVATION_SECRET
        decoded = verify_token(request.activation_token, ACTIVATION_SECRET)
        
        if decoded.get("activationCode") != request.activation_code:
            raise ErrorHandler("Invalid activation code", 400)
        
        user_data = decoded.get("user")
        name = user_data.get("name")
        email = user_data.get("email")
        password = user_data.get("password")
        
        existing_user = await database.users.find_one({"email": email})
        if existing_user:
            raise ErrorHandler(f"{email} already exists", 400)
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create user
        user_doc = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "amountDonated": 0,
            "donationsArray": [],
            "createdFunds": [],
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
        
        result = await database.users.insert_one(user_doc)
        user_doc["_id"] = str(result.inserted_id)
        
        return {"success": True}
    except ErrorHandler:
        raise
    except Exception as err:
        raise ErrorHandler(str(err), 400)

@router.post("/login")
async def login_user(request: UserLogin, response: Response, database=Depends(get_database)):
    try:
        if not request.email or not request.password:
            raise ErrorHandler("Please enter email and password", 400)
        
        user_doc = await database.users.find_one({"email": request.email})
        if not user_doc:
            raise ErrorHandler("Invalid email or password", 400)
        
        if not user_doc.get("password"):
            raise ErrorHandler("Invalid email or password", 400)
        
        if not pwd_context.verify(request.password.strip(), user_doc["password"]):
            raise ErrorHandler("Incorrect Password", 400)
        
        user_doc["_id"] = str(user_doc["_id"])
        # Remove password from response
        user_doc.pop("password", None)
        token_data = await send_token(user_doc, response)
        
        # Set cookies
        access_token_options = get_access_token_options()
        refresh_token_options = get_refresh_token_options()
        
        response.set_cookie(
            key="access_token",
            value=token_data["access_token"],
            **access_token_options
        )
        response.set_cookie(
            key="refresh_token",
            value=token_data["refresh_token"],
            **refresh_token_options
        )
        
        return {
            "success": True,
            "user": token_data["user"],
            "accessToken": token_data["access_token"]
        }
    except ErrorHandler:
        raise
    except Exception as err:
        raise ErrorHandler(str(err), 400)

@router.get("/logout")
async def logout_user(user: dict = Depends(is_authenticated), response: Response = None):
    try:
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        user_id = user.get("_id", "")
        redis_client.delete(user_id)
        return {
            "success": True,
            "message": "Logged out successfully"
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.get("/refresh")
async def update_access_token(refresh_token: str = Cookie(None)):
    try:
        if not refresh_token:
            raise ErrorHandler("Could not refresh token", 400)
        
        from utils.jwt import REFRESH_TOKEN_SECRET
        decoded = verify_token(refresh_token, REFRESH_TOKEN_SECRET)
        
        user_id = decoded.get("id")
        session = redis_client.get(user_id)
        
        if session is None:
            raise ErrorHandler("Please login for access this resources!", 400)
        
        if isinstance(session, bytes):
            session = session.decode('utf-8')
        
        user = json.loads(session)
        
        access_token = create_access_token(user_id)
        refresh_token_new = create_refresh_token(user_id)
        
        redis_client.set(user_id, json.dumps(user, default=str), ex=604800)  # 7 days
        
        # Set cookies
        access_token_options = get_access_token_options()
        refresh_token_options = get_refresh_token_options()
        
        from fastapi.responses import JSONResponse
        
        response_obj = JSONResponse(
            content={
                "status": "success",
                "accessToken": access_token
            }
        )
        
        response_obj.set_cookie(
            key="access_token",
            value=access_token,
            **access_token_options
        )
        response_obj.set_cookie(
            key="refresh_token",
            value=refresh_token_new,
            **refresh_token_options
        )
        
        return response_obj
    except ErrorHandler:
        raise
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.get("/me")
async def get_user_info(user: dict = Depends(is_authenticated)):
    try:
        user_id = user.get("_id")
        user_data = await get_user_by_id(user_id)
        if not user_data:
            raise ErrorHandler("User not found", 404)
        
        return {
            "success": True,
            "user": user_data
        }
    except ErrorHandler:
        raise
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/socialAuth")
async def social_auth(request: SocialAuth, response: Response, database=Depends(get_database)):
    try:
        user = await database.users.find_one({"email": request.email})
        if not user:
            new_user = {
                "email": request.email,
                "name": request.name,
                "avatar": {"url": request.avatar} if request.avatar else None,
                "amountDonated": 0,
                "donationsArray": [],
                "createdFunds": [],
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            }
            result = await database.users.insert_one(new_user)
            new_user["_id"] = str(result.inserted_id)
            token_data = await send_token(new_user, response)
        else:
            user["_id"] = str(user["_id"])
            token_data = await send_token(user, response)
        
        # Set cookies
        access_token_options = get_access_token_options()
        refresh_token_options = get_refresh_token_options()
        
        response.set_cookie(
            key="access_token",
            value=token_data["access_token"],
            **access_token_options
        )
        response.set_cookie(
            key="refresh_token",
            value=token_data["refresh_token"],
            **refresh_token_options
        )
        
        return {
            "success": True,
            "user": token_data["user"],
            "accessToken": token_data["access_token"]
        }
    except ErrorHandler:
        raise
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.put("/update-user-info")
async def update_user_info(request: UserUpdate, user: dict = Depends(is_authenticated), database=Depends(get_database)):
    try:
        user_id = user.get("_id")
        update_data = {}
        
        if request.name:
            update_data["name"] = request.name
        
        if update_data:
            await database.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            updated_user = await database.users.find_one({"_id": ObjectId(user_id)})
            updated_user["_id"] = str(updated_user["_id"])
            redis_client.set(user_id, json.dumps(updated_user, default=str))
        
        return {"success": True}
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.put("/update-user-avatar")
async def update_profile_picture(request: UserUpdate, user: dict = Depends(is_authenticated), database=Depends(get_database)):
    try:
        user_id = user.get("_id")
        user_data = await database.users.find_one({"_id": ObjectId(user_id)})
        
        if request.avatar and user_data:
            if user_data.get("avatar", {}).get("public_id"):
                # Delete old image
                cloudinary.uploader.destroy(user_data["avatar"]["public_id"])
            
            # Upload new image
            result = cloudinary.uploader.upload(
                request.avatar,
                folder="avatars",
                width=150
            )
            
            update_data = {
                "avatar": {
                    "public_id": result["public_id"],
                    "url": result["secure_url"]
                }
            }
            
            await database.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            updated_user = await database.users.find_one({"_id": ObjectId(user_id)})
            updated_user["_id"] = str(updated_user["_id"])
            redis_client.set(user_id, json.dumps(updated_user, default=str))
        
        return {"success": True}
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.put("/update-user-fundArray")
async def update_user_fund_id_array(request: UpdateFundArrayRequest, user: dict = Depends(is_authenticated), database=Depends(get_database)):
    try:
        user_id = user.get("_id")
        user_data = await database.users.find_one({"_id": ObjectId(user_id)})
        
        if request.id not in user_data.get("createdFunds", []):
            await database.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"createdFunds": request.id}}
            )
        
        updated_user = await database.users.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"])
        redis_client.set(user_id, json.dumps(updated_user, default=str))
        
        return {"success": True}
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/getUser")
async def get_user(request: GetUserRequest, database=Depends(get_database)):
    try:
        user = await database.users.find_one({"email": request.email})
        if user:
            user["_id"] = str(user["_id"])
            return {
                "success": True,
                "user": user
            }
        else:
            return {
                "success": False,
                "error": "not found"
            }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/get-user-pic")
async def get_user_pic(request: GetUserPicRequest, database=Depends(get_database)):
    try:
        user = await database.users.find_one({"email": request.email})
        if user:
            user_pic = user.get("avatar", {}).get("url") if user.get("avatar") else None
            return {
                "success": True,
                "userPic": user_pic
            }
        else:
            return {
                "success": False,
                "userPic": None
            }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

