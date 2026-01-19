from utils.db import get_database
from utils.redis_client import redis_client
from utils.error_handler import ErrorHandler
import json
from bson import ObjectId
from datetime import datetime, timezone

# MongoDB collection name - Mongoose model 'FundraiseRequests' becomes 'fundraiserequests' collection
COLLECTION_NAME = "fundraiserequests"

def serialize_document(doc):
    """Recursively convert ObjectId and datetime objects to strings for JSON serialization"""
    if doc is None:
        return None
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    if isinstance(doc, dict):
        return {key: serialize_document(value) for key, value in doc.items()}
    if isinstance(doc, list):
        return [serialize_document(item) for item in doc]
    return doc

async def create_fundraiser(data: dict):
    database = get_database()
    # Data should already have defaults applied from Pydantic model validation
    # Add timestamps (Mongoose adds these automatically with { timestamps: true })
    now = datetime.now(timezone.utc)
    data["createdAt"] = now
    data["updatedAt"] = now
    
    # Ensure all default fields are set (in case they weren't in the schema)
    if "verified" not in data:
        data["verified"] = False
    if "amountRaised" not in data:
        data["amountRaised"] = 0
    if "numberOfDonators" not in data:
        data["numberOfDonators"] = 0
    if "donators" not in data:
        data["donators"] = []
    
    result = await database[COLLECTION_NAME].insert_one(data)
    fundraiser = await database[COLLECTION_NAME].find_one({"_id": result.inserted_id})
    return serialize_document(fundraiser)

async def get_single_fundraiser(fund_id: str):
    # Check cache first
    cached = redis_client.get(fund_id)
    if cached:
        if isinstance(cached, bytes):
            cached = cached.decode('utf-8')
        return json.loads(cached)
    
    database = get_database()
    fundraiser = await database[COLLECTION_NAME].find_one({"_id": ObjectId(fund_id)})
    if not fundraiser:
        raise ErrorHandler("Fundraiser not found", 404)
    
    serialized = serialize_document(fundraiser)
    redis_client.set(fund_id, json.dumps(serialized, default=str), ex=604800)  # 7 days
    return serialized

async def fundraiser_by_type(type: str):
    database = get_database()
    query = {"verified": True}
    if type == "non-profit":
        query["category"] = {"$in": ["education", "others"]}
    else:
        query["category"] = type
    
    fundraisers = await database[COLLECTION_NAME].find(query).sort("endDateToRaise", 1).to_list(length=None)
    return [serialize_document(fund) for fund in fundraisers]

async def fundraiser_by_search(search_term: str):
    import re
    database = get_database()
    regex_term = re.compile(f".*{search_term}.*", re.IGNORECASE)
    
    regex = '$regex'
    query = {
        "verified": True,
        "$or": [
            {"benefitterName": {regex: regex_term}},
            {"category": {regex: regex_term}},
            {"fundraiserTitle": {regex: regex_term}},
            {"benefitterAddress": {regex: regex_term}},
            {"ailment": {regex: regex_term}},
            {"createdBy": {regex: regex_term}},
            {"hospitalLocation": {regex: regex_term}},
        ]
    }
    
    fundraisers = await database[COLLECTION_NAME].find(query).sort("endDateToRaise", 1).to_list(length=None)
    return [serialize_document(fund) for fund in fundraisers]

