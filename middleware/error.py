from fastapi import Request, status
from fastapi.responses import JSONResponse
from utils.error_handler import ErrorHandler
from pymongo.errors import DuplicateKeyError
from jose import JWTError
import os

base_url = os.getenv("BASE_URL", "http://localhost:3000")
def add_cors_headers(response: JSONResponse, origin: str = base_url) -> JSONResponse:
    """Add CORS headers to response"""
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

async def error_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        # Add CORS headers if not already present
        if "Access-Control-Allow-Origin" not in response.headers:
            origin = request.headers.get("origin", base_url)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    except ErrorHandler as err:
        origin = request.headers.get("origin", base_url)
        response = JSONResponse(
            status_code=err.status_code,
            content={
                "success": False,
                "message": err.message
            }
        )
        return add_cors_headers(response, origin)
    except DuplicateKeyError as err:
        origin = request.headers.get("origin", base_url)
        response = JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "Duplicate key entered"
            }
        )
        return add_cors_headers(response, origin)
    except JWTError as err:
        origin = request.headers.get("origin", base_url)
        response = JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "JSON web token is invalid, try again"
            }
        )
        return add_cors_headers(response, origin)
    except Exception as err:
        origin = request.headers.get("origin", base_url)
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": str(err)
            }
        )
        return add_cors_headers(response, origin)

