from fastapi import APIRouter, HTTPException, Depends
from utils.db import get_database
from utils.error_handler import ErrorHandler
from utils.redis_client import redis_client
from models.fundraiser import FundraiserCreate, FundraiserResponse, FundraiserUpdate, FundraiserByType, FundraiserBySearch
from services.fundraiser_service import create_fundraiser, get_single_fundraiser, fundraiser_by_type, fundraiser_by_search, COLLECTION_NAME, serialize_document
from middleware.auth import is_authenticated
import cloudinary
import cloudinary.uploader
from bson import ObjectId
import json
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["fundraiser"])

class FundraiserDataRequest(BaseModel):
    data: dict

class AddImageRequest(BaseModel):
    avatar: str

class DeleteImageRequest(BaseModel):
    public_id: str

class UpdateAmountRequest(BaseModel):
    amount: int

@router.post("/createFundraiser")
async def create_fundraiser_request(request: FundraiserDataRequest, user: dict = Depends(is_authenticated)):
    try:
        # Validate data through Pydantic model to apply defaults
        from models.fundraiser import FundraiserCreate
        fundraiser_model = FundraiserCreate(**request.data)
        data = fundraiser_model.model_dump()
        
        fundraise = await create_fundraiser(data)
        return {
            "success": True,
            "fundraise": fundraise
        }
    except ErrorHandler:
        raise
    except Exception as err:
        raise ErrorHandler(str(err), 400)

@router.put("/edit-fund/{id}")
async def edit_fundraiser(id: str, request: dict, user: dict = Depends(is_authenticated)):
    try:
        database = get_database()
        data = request
        cover_img = data.get("coverImg")
        
        fundraiser_data = await database[COLLECTION_NAME].find_one({"_id": ObjectId(id)})
        if not fundraiser_data:
            raise ErrorHandler("Fundraiser not found", 404)
        
        if cover_img and not cover_img.startswith("https"):
            # Delete old image
            if fundraiser_data.get("coverImg", {}).get("public_id"):
                cloudinary.uploader.destroy(fundraiser_data["coverImg"]["public_id"])
            
            # Upload new image
            result = cloudinary.uploader.upload(
                cover_img,
                folder="fundraisers"
            )
            
            data["coverImg"] = {
                "public_id": result["public_id"],
                "url": result["secure_url"]
            }
        elif cover_img and cover_img.startswith("https"):
            data["coverImg"] = {
                "public_id": fundraiser_data.get("coverImg", {}).get("public_id"),
                "url": fundraiser_data.get("coverImg", {}).get("url")
            }
        
        # Update the updatedAt timestamp
        from datetime import datetime, timezone
        data["updatedAt"] = datetime.now(timezone.utc)
        
        await database[COLLECTION_NAME].update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        
        fund = await database[COLLECTION_NAME].find_one({"_id": ObjectId(id)})
        serialized_fund = serialize_document(fund)
        redis_client.set(id, json.dumps(serialized_fund, default=str))
        
        return {
            "success": True,
            "fund": serialized_fund
        }
    except ErrorHandler:
        raise
    except Exception as error:
        raise ErrorHandler(str(error), 500)

@router.put("/update-fund-amount/{id}")
async def update_fundraiser_amount(id: str, request: UpdateAmountRequest):
    try:
        database = get_database()
        fundraiser = await database[COLLECTION_NAME].find_one({"_id": ObjectId(id)})
        if not fundraiser:
            raise HTTPException(status_code=404, detail="Fundraiser Not Found")
        
        if request.amount:
            new_amount_raised = fundraiser.get("amountRaised", 0) + request.amount
            new_number_of_donators = fundraiser.get("numberOfDonators", 0) + 1
            
            await database[COLLECTION_NAME].update_one(
                {"_id": ObjectId(id)},
                {"$set": {
                    "amountRaised": new_amount_raised,
                    "numberOfDonators": new_number_of_donators
                }}
            )
        
        updated_fundraiser = await database[COLLECTION_NAME].find_one({"_id": ObjectId(id)})
        serialized = serialize_document(updated_fundraiser)
        
        return {
            "success": True,
            "updatedFundraiser": serialized
        }
    except HTTPException:
        raise
    except Exception as error:
        raise ErrorHandler(str(error), 500)

@router.get("/getAllFunds")
async def get_all_fundraisers():
    try:
        database = get_database()
        fundraisers = await database[COLLECTION_NAME].find().sort("createdAt", -1).to_list(length=None)
        serialized = [serialize_document(fund) for fund in fundraisers]
        return {
            "success": True,
            "fundraisers": serialized
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.get("/getAllFundsByUrgency")
async def get_all_fundraisers_by_urgency():
    try:
        database = get_database()
        fundraisers = await database[COLLECTION_NAME].find({"verified": True}).sort("endDateToRaise", 1).to_list(length=None)
        serialized = [serialize_document(fund) for fund in fundraisers]
        return {
            "success": True,
            "fundraisers": serialized
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.get("/get-fund/{id}")
async def get_single_fundraiser_route(id: str):
    try:
        fundraiser = await get_single_fundraiser(id)
        return {
            "success": True,
            "fundraiser": fundraiser
        }
    except ErrorHandler:
        raise
    except Exception as error:
        raise ErrorHandler(str(error), 500)

@router.get("/getUserCreatedFunds")
async def get_fundraisers_by_user(user: dict = Depends(is_authenticated)):
    try:
        database = get_database()
        donation_array = user.get("createdFunds", [])
        res_array = []
        
        for fund_id in donation_array:
            fundraiser_data = await database[COLLECTION_NAME].find_one({"_id": ObjectId(fund_id)})
            if fundraiser_data:
                res_array.append(serialize_document(fundraiser_data))
        
        return {
            "success": True,
            "resArray": res_array
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.get("/getUserDonatedFunds")
async def get_donated_funds_by_user(user: dict = Depends(is_authenticated)):
    try:
        database = get_database()
        donation_array = user.get("donationsArray", [])
        res_array = []
        
        for fund in donation_array:
            fundraiser_data = await database[COLLECTION_NAME].find_one({"_id": ObjectId(fund["fundraiser"])})
            if fundraiser_data:
                serialized = serialize_document(fundraiser_data)
                res_array.append({
                    "title": serialized.get("fundraiserTitle"),
                    "id": serialized["_id"],
                    "coverImg": serialized.get("coverImg"),
                    "amount": fund.get("amount"),
                    "date": fund.get("date")
                })
        
        return {
            "success": True,
            "resArray": res_array
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/addBenefitterImg")
async def add_benefitter_img(request: AddImageRequest):
    try:
        result = cloudinary.uploader.upload(
            request.avatar,
            folder="benefitter",
            width=150
        )
        
        ans = {
            "public_id": result["public_id"],
            "url": result["secure_url"]
        }
        
        return {
            "success": True,
            "ans": ans
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/deleteBenefitterImg")
async def delete_benefitter_img(request: DeleteImageRequest):
    try:
        cloudinary.uploader.destroy(request.public_id)
        return {"success": True}
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/addCoverImg")
async def add_cover_img(request: AddImageRequest):
    try:
        result = cloudinary.uploader.upload(
            request.avatar,
            folder="coverImg",
            width=150
        )
        
        ans = {
            "public_id": result["public_id"],
            "url": result["secure_url"]
        }
        
        return {
            "success": True,
            "ans": ans
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/deleteCoverImg")
async def delete_cover_img(request: DeleteImageRequest):
    try:
        cloudinary.uploader.destroy(request.public_id)
        return {"success": True}
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/fundraiserByType")
async def fundraiser_by_type_route(request: FundraiserByType):
    try:
        # Extract type from nested structure: {"type": {"type": "medical"}}
        type_value = request.type.type
        fundraisers = await fundraiser_by_type(type_value)
        return {
            "success": True,
            "fundraisers": fundraisers
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

@router.post("/fundraiserBySearch")
async def fundraiser_by_search_route(request: FundraiserBySearch):
    try:
        # Extract search from nested structure: {"search": {"search": "term"}}
        search_term = request.search.search
        fundraisers = await fundraiser_by_search(search_term)
        return {
            "success": True,
            "fundraisers": fundraisers
        }
    except Exception as error:
        raise ErrorHandler(str(error), 400)

