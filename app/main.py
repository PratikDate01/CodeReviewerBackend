import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import routes
from app.config import settings
from app.models.database import engine, Base

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Advanced AI Code Reviewer Platform",
    description="Enterprise-grade code quality and security analysis platform",
    version="2.0.0",
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
app.include_router(routes.router, prefix="/api", tags=["analysis"])

frontend_build_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(frontend_build_path):
    logger.info("Mounting built frontend from dist folder")
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")
elif os.path.exists(frontend_path):
    logger.info("Mounting frontend from source folder")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Enterprise AI Code Reviewer starting...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization warning: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Platform shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
