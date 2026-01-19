from utils.redis_client import redis_client
from utils.db import database
import json

async def get_user_by_id(user_id: str):
    from bson import ObjectId
    user_json = redis_client.get(user_id)
    if user_json:
        if isinstance(user_json, bytes):
            user_json = user_json.decode('utf-8')
        return json.loads(user_json)
    
    user = await database.users.find_one({"_id": ObjectId(user_id)})
    if user:
        user["_id"] = str(user["_id"])
        redis_client.set(user_id, json.dumps(user, default=str))
        return user
    return None

async def get_all_users():
    users = await database.users.find().sort("createdAt", -1).to_list(length=None)
    for user in users:
        user["_id"] = str(user["_id"])
    return users

async def update_user_role(user_id: str, role: str):
    from bson import ObjectId
    result = await database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role}}
    )
    if result.modified_count:
        user = await database.users.find_one({"_id": ObjectId(user_id)})
        user["_id"] = str(user["_id"])
        redis_client.set(user_id, json.dumps(user, default=str))
        return user
    return None

