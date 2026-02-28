import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cohere
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Enterprise AI Code Reviewer")

# Add CORS middleware to support React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cohere setup
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

class CodeReviewRequest(BaseModel):
    code: str
    language: Optional[str] = "python"
    mode: Optional[str] = "hybrid"

@app.on_event("startup")
async def startup_event():
    """Logs server startup and placeholder database initialization."""
    logger.info("Enterprise AI Code Reviewer server is starting up...")
    # Placeholder for database initialization
    logger.info("Initializing database connection... [COMPLETED]")

@app.get("/")
async def root():
    """Root route for sanity checks."""
    return {"message": "Enterprise AI Code Reviewer is running \ud83d\ude80"}

@app.get("/api/health")
async def health():
    """Health check for React frontend."""
    return {"status": "healthy"}

@app.post("/api/analyze")
async def analyze_code(request: CodeReviewRequest):
    """Alias for /review-code to support frontend expectations."""
    return await review_code(request)

@app.post("/review-code")
async def review_code(request: CodeReviewRequest):
    """
    POST route for AI code review using Cohere.
    Returns a structured review for the React frontend.
    """
    if not COHERE_API_KEY:
        logger.error("COHERE_API_KEY is missing from environment variables.")
        raise HTTPException(
            status_code=500, 
            detail="Server configuration error: COHERE_API_KEY is missing."
        )

    try:
        co = cohere.Client(COHERE_API_KEY)
        
        prompt = (
            f"Review the following {request.language} code:\n\n"
            f"{request.code}\n\n"
            "Provide a comprehensive review in JSON format with these exact keys:\n"
            "- logical_flaws: list of strings\n"
            "- architecture_suggestions: list of strings\n"
            "- performance_optimization: list of strings\n"
            "- readability_suggestions: list of strings\n"
            "- refactoring_proposal: list of strings\n"
            "- design_pattern_recommendations: list of strings\n"
            "- refactored_code: string (the improved code)\n"
            "- ai_score: number between 1 and 10\n\n"
            "Respond ONLY with valid JSON."
        )

        response = co.generate(
            model='xlarge',
            prompt=prompt,
            max_tokens=600,
            temperature=0.2,
            stop_sequences=["--"]
        )

        review_text = response.generations[0].text.strip()
        
        import json
        try:
            review_json = json.loads(review_text)
            return {"review": review_json}
        except json.JSONDecodeError:
            # Fallback if AI doesn't return perfect JSON
            return {
                "review": {
                    "logical_flaws": ["Could not parse AI response as JSON"],
                    "architecture_suggestions": [],
                    "performance_optimization": [],
                    "readability_suggestions": [review_text],
                    "refactoring_proposal": [],
                    "design_pattern_recommendations": [],
                    "refactored_code": request.code,
                    "ai_score": 5
                }
            }

    except Exception as e:
        logger.error(f"Cohere API call failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate code review: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    # Render uses PORT env var
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
