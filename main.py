from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from utils.db import connect_db, close_db
from utils.error_handler import ErrorHandler
from middleware.error import error_middleware
from routers import user, fundraiser, contact, payment
import os
from dotenv import load_dotenv
import cloudinary

load_dotenv()

# Configure cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("CLOUD_API_KEY"),
    api_secret=os.getenv("CLOUD_SECRET_KEY")
)

# Create FastAPI app
app = FastAPI()

# CORS middleware - must be added first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Error handling middleware
@app.middleware("http")
async def error_handler_middleware(request: Request, call_next):
    return await error_middleware(request, call_next)

# Include routers
app.include_router(user.router)
app.include_router(fundraiser.router)
app.include_router(contact.router)
app.include_router(payment.router)

# Test endpoint
@app.get("/test")
async def test():
    return {
        "success": "true",
        "message": "Api is working"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    await connect_db()
    print(f"Server is running on port {os.getenv('PORT', '8000')}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


# 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": f"Route {request.url.path} Not Found"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
