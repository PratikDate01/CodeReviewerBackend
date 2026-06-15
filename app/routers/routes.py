import logging
import hashlib
import time
from collections import defaultdict
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.schemas import CodeReviewRequest, CodeReviewResponse
from app.models.database import get_db, ReviewRecord
from app.services.aggregator import ReviewAggregator
from app.services.cache import cache_manager

logger = logging.getLogger(__name__)
router = APIRouter()
aggregator = ReviewAggregator()

# Simple In-Memory Rate Limiter (30 requests per minute per IP)
class InMemoryRateLimiter:
    def __init__(self, requests_limit: int = 30, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        # Clean up old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window_seconds]
        if len(self.requests[client_ip]) < self.requests_limit:
            self.requests[client_ip].append(now)
            return True
        return False

rate_limiter = InMemoryRateLimiter(requests_limit=30, window_seconds=60)

async def rate_limit_check(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too Many Requests. Please try again later.")

async def handle_code_review(request: CodeReviewRequest, db: Session) -> Dict[str, Any]:
    """Helper to perform review with caching and DB persistence"""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
        
    # Generate unique hash for this code & mode
    code_hash = hashlib.sha256(f"{request.code}:{request.mode}".encode()).hexdigest()
    
    # 1. Check in-memory cache
    cached_result = cache_manager.get(request.code, request.mode)
    if cached_result and isinstance(cached_result, dict) and "scoring" in cached_result:
        logger.info("Cache hit: returned from in-memory cache")
        return cached_result
        
    # 2. Check DB cache
    try:
        db_record = db.query(ReviewRecord).filter(ReviewRecord.code_hash == code_hash).first()
        if db_record and db_record.full_result and "scoring" in db_record.full_result:
            logger.info("Cache hit: returned from database")
            # Populate in-memory cache
            cache_manager.set(request.code, request.mode, db_record.full_result)
            return db_record.full_result
        elif db_record:
            logger.info("Database record found but lacks compatibility fields. Forcing re-review.")
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        
    # 3. Cache miss: run aggregator
    logger.info(f"Cache miss: running aggregator in '{request.mode}' mode")
    response_data = await aggregator.perform_review(request.code, request.mode)
    
    # 4. Save to DB and in-memory cache
    try:
        # Check if record already exists to avoid unique constraint violations
        existing = db.query(ReviewRecord).filter(ReviewRecord.code_hash == code_hash).first()
        if existing:
            existing.full_result = response_data
            existing.final_score = response_data["final_score"]
            existing.static_score = response_data["breakdown"]["static_score"]
            existing.ai_score = response_data["breakdown"]["ai_score"]
        else:
            new_record = ReviewRecord(
                code_hash=code_hash,
                final_score=response_data["final_score"],
                static_score=response_data["breakdown"]["static_score"],
                ai_score=response_data["breakdown"]["ai_score"],
                review_mode=request.mode,
                code_snippet=request.code[:200],
                full_result=response_data
            )
            db.add(new_record)
        db.commit()
    except Exception as dbe:
        logger.error(f"Failed to save review to DB: {dbe}")
        db.rollback()
        
    cache_manager.set(request.code, request.mode, response_data)
    return response_data

@router.post("/analyze", response_model=CodeReviewResponse, dependencies=[Depends(rate_limit_check)])
async def analyze_code(request: CodeReviewRequest, db: Session = Depends(get_db)) -> CodeReviewResponse:
    """
    Main analysis endpoint called by the React frontend.
    """
    try:
        response = await handle_code_review(request, db)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal analysis failure")

@router.post("/review", response_model=CodeReviewResponse, dependencies=[Depends(rate_limit_check)])
async def review_code(request: CodeReviewRequest, db: Session = Depends(get_db)) -> CodeReviewResponse:
    """
    Review endpoint called by automated integration tests.
    """
    # Map review_mode from payload if provided (for backwards compatibility with tests)
    # The Pydantic request model might contain mode (mapped from review_mode by the user agent, 
    # but since tests send review_mode, Pydantic validation handles it if mapped correctly).
    try:
        response = await handle_code_review(request, db)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal review failure")

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check including database connection status.
    """
    db_status = "unhealthy"
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        # Fallback if text/SELECT 1 fails
        try:
            db.connection()
            db_status = "healthy"
        except Exception:
            pass
            
    return {
        "status": "healthy",
        "service": "AI Code Reviewer",
        "database": db_status,
        "version": "2.0.0"
    }
