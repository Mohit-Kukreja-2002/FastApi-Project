from fastapi import APIRouter, Depends
from utils.db import get_database
from utils.error_handler import ErrorHandler
from utils.redis_client import redis_client
from models.payment import PaymentCreate, PaymentIntent
from services.fundraiser_service import COLLECTION_NAME
import stripe
import os
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime, timezone
import json

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/api/v1", tags=["payment"])

@router.post("/make-payment")
async def create_payment(request: PaymentCreate, database=Depends(get_database)):
    try:
        payment_info = request.payment_info
        
        if payment_info and "id" in payment_info:
            payment_intent_id = payment_info["id"]
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status != "succeeded":
                raise ErrorHandler("Payment not authorized!", 400)
        
        user = await database.users.find_one({"email": request.email})
        fund = await database[COLLECTION_NAME].find_one({"_id": ObjectId(request.fundId)})
        
        if not user:
            user_data = {
                "email": request.email,
                "name": request.email.split("@")[0],
                "amountDonated": 0,
                "donationsArray": [],
                "createdFunds": [],
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            }
            result = await database.users.insert_one(user_data)
            user = await database.users.find_one({"_id": result.inserted_id})
        
        if not fund:
            raise ErrorHandler("Fund not found", 404)
        
        to_push = {
            "fundraiser": request.fundId,
            "amount": request.amount,
            "date": datetime.now(timezone.utc)
        }
        
        if fund.get("coverImg", {}).get("url"):
            to_push["fundraiserImg"] = fund["coverImg"]["url"]
        
        # Update user
        await database.users.update_one(
            {"_id": user["_id"]},
            {
                "$push": {"donationsArray": to_push},
                "$inc": {"amountDonated": request.amount}
            }
        )
        
        updated_user = await database.users.find_one({"_id": user["_id"]})
        updated_user["_id"] = str(updated_user["_id"])
        redis_client.set(str(updated_user["_id"]), json.dumps(updated_user, default=str), ex=604800)
        
        # Update fund
        await database[COLLECTION_NAME].update_one(
            {"_id": ObjectId(request.fundId)},
            {
                "$push": {"donators": str(user["_id"])},
                "$inc": {
                    "amountRaised": request.amount,
                    "numberOfDonators": 1
                }
            }
        )
        
        updated_fund = await database[COLLECTION_NAME].find_one({"_id": ObjectId(request.fundId)})
        updated_fund["_id"] = str(updated_fund["_id"])
        redis_client.set(request.fundId, json.dumps(updated_fund, default=str), ex=604800)
        
        return {"success": True}
    except ErrorHandler:
        raise
    except Exception as error:
        raise ErrorHandler(str(error), 500)

@router.get("/payment/stripepublishablekey")
async def send_stripe_publishable_key():
    return {
        "publishablekey": os.getenv("STRIPE_PUBLISHABLE_KEY")
    }

@router.post("/payment")
async def new_payment(request: PaymentIntent):
    try:
        my_payment = stripe.PaymentIntent.create(
            amount=int(request.amount * 100),
            currency="INR",
            description="HopeFund donation services",
            metadata={
                "company": "HopeFund"
            },
            automatic_payment_methods={
                "enabled": True
            },
            shipping={
                "name": "Mohit Kukreja",
                "address": {
                    "line1": "2179 Sector 15",
                    "postal_code": "131001",
                    "city": "Sonipat",
                    "state": "Haryana",
                    "country": "INDIA"
                }
            }
        )
        
        return {
            "success": True,
            "client_secret": my_payment.client_secret
        }
    except Exception as error:
        raise ErrorHandler(str(error), 500)

