from fastapi import APIRouter
from utils.db import database
from utils.error_handler import ErrorHandler
from models.contact import ContactCreate

router = APIRouter(prefix="/api/v1", tags=["contact"])

@router.post("/contact")
async def contact_controller(request: ContactCreate):
    try:
        data = request.model_dump()
        await database.contacts.insert_one(data)
        return {"success": True}
    except Exception as error:
        raise ErrorHandler(str(error), 400)

