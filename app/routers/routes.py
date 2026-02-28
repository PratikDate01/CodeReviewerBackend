import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import CodeReviewRequest, CodeReviewResponse
from app.services.aggregator import ReviewAggregator

logger = logging.getLogger(__name__)
router = APIRouter()
aggregator = ReviewAggregator()

@router.post("/analyze", response_model=CodeReviewResponse)
async def analyze_code(request: CodeReviewRequest) -> CodeReviewResponse:
    """
    Main analysis endpoint for Enterprise AI Code Quality Platform.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    try:
        logger.info(f"Analyzing code in {request.mode} mode")
        response = aggregator.perform_review(request.code, request.mode)
        return response
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Basic health check for the API.
    """
    return {"status": "healthy", "service": "AI Code Reviewer"}
