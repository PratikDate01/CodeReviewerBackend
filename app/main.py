import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

from app.config import settings
from app.routers.routes import router as api_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise AI Code Reviewer",
    debug=settings.debug
)

# CORS configuration: secure specific origins when credentials are enabled
allowed_origins = [
    os.getenv("FRONTEND_URL", "https://devpilot-ai.vercel.app"),
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Size Limit Middleware (Max 1MB)
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        if int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request Entity Too Large"}
            )
    return await call_next(request)

# Custom Exception Handlers to Prevent Info Leakage
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    # Only leak raw exception message in debug mode
    error_msg = str(exc) if settings.debug else "An unexpected error occurred."
    return JSONResponse(
        status_code=500,
        content={"detail": error_msg}
    )

# Include API Router
app.include_router(api_router, prefix="/api")

# Disabled Execution Endpoints
@app.post("/run-code")
@app.post("/api/run-code")
async def run_code():
    """
    Disabled for security reasons (vulnerability remediation).
    """
    raise HTTPException(
        status_code=403,
        detail="Code execution is disabled for security reasons."
    )

# Root Endpoint
@app.get("/")
async def root():
    return {"message": "Enterprise AI Code Reviewer is running 🚀"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
