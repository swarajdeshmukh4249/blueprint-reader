"""
Error Handler Middleware
Ensures all API responses follow the standard error response shape
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Union
import uuid
from config import ERROR_VERBOSITY, DEBUG
from utils.errors import BlueprintIQError


async def blueprintiq_error_handler(request: Request, exc: BlueprintIQError) -> JSONResponse:
    """
    Handle BlueprintIQ custom exceptions
    
    Returns standard error response shape
    """
    error_response = exc.to_dict()
    
    # Add request context in debug mode
    if DEBUG and ERROR_VERBOSITY == "verbose":
        error_response["debug"] = {
            "path": str(request.url),
            "method": request.method
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI validation errors
    
    Converts to standard error response shape
    """
    errors = exc.errors()
    
    # Get the first error for the main message
    first_error = errors[0] if errors else {}
    
    field = None
    if "loc" in first_error and len(first_error["loc"]) > 0:
        # Get the field name (last item in loc)
        field = str(first_error["loc"][-1])
    
    error_response = {
        "error": True,
        "error_code": "VALIDATION_ERROR",
        "message": first_error.get("msg", "Validation failed"),
        "field": field,
        "details": {
            "errors": errors if DEBUG and ERROR_VERBOSITY == "verbose" else [first_error]
        },
        "request_id": str(uuid.uuid4())
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions
    
    Converts to standard error response shape
    """
    error_response = {
        "error": True,
        "error_code": "HTTP_ERROR",
        "message": exc.detail,
        "field": None,
        "details": {
            "status_code": exc.status_code
        } if DEBUG and ERROR_VERBOSITY == "verbose" else None,
        "request_id": str(uuid.uuid4())
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other exceptions
    
    Converts to standard error response shape
    """
    error_response = {
        "error": True,
        "error_code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred" if not DEBUG else str(exc),
        "field": None,
        "details": {
            "exception_type": type(exc).__name__
        } if DEBUG and ERROR_VERBOSITY == "verbose" else None,
        "request_id": str(uuid.uuid4())
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def setup_error_handlers(app):
    """
    Register all error handlers with the FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    from utils.errors import BlueprintIQError
    
    app.add_exception_handler(BlueprintIQError, blueprintiq_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_error_handler)
