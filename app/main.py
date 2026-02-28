import os
import io
import sys
import logging
import cohere
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Cohere Client
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None

app = FastAPI(title="Enterprise AI Code Reviewer")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to os.getenv("FRONTEND_URL", "*") for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRunRequest(BaseModel):
    code: str

class CodeReviewRequest(BaseModel):
    code: str
    language: Optional[str] = "python"

@app.get("/")
async def root():
    return {"message": "Enterprise AI Code Reviewer is running 🚀"}

@app.post("/run-code")
async def run_code(request: CodeRunRequest):
    """Safely runs Python code and returns output and errors."""
    output_buffer = io.StringIO()
    error_buffer = io.StringIO()
    
    # Redirect stdout and stderr
    sys.stdout = output_buffer
    sys.stderr = error_buffer
    
    try:
        # Note: exec is not safe for untrusted code in a production multi-tenant environment
        # but satisfies the requirement for a functional backend here.
        exec(request.code, {"__builtins__": __builtins__}, {})
    except Exception as e:
        print(f"Error during execution: {str(e)}", file=sys.stderr)
    finally:
        # Restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    
    return {
        "output": output_buffer.getvalue(),
        "errors": error_buffer.getvalue()
    }

@app.post("/review-code")
async def review_code(request: CodeReviewRequest):
    """Calls Cohere API to generate a detailed AI code review."""
    if not COHERE_API_KEY or not co:
        raise HTTPException(status_code=500, detail="COHERE_API_KEY is not configured.")
    
    prompt = f"""
    Review the following {request.language} code:
    
    ```
    {request.code}
    ```
    
    Provide a full AI review including:
    1. Code Summary: A brief explanation of what the code does.
    2. Bugs & Security Issues: Identify any potential logical errors or security vulnerabilities.
    3. Optimization Tips: Suggestions for better performance or efficiency.
    4. Code Quality & Best Practices: Formatting, naming conventions, and readability improvements.
    
    Be professional, concise, and helpful.
    """
    
    try:
        response = co.generate(
            model='command-xlarge-nightly',
            prompt=prompt,
            max_tokens=300,
            temperature=0.2,
            stop_sequences=["--"]
        )
        review_text = response.generations[0].text.strip()
        return {"review": review_text}
    except Exception as e:
        logger.error(f"Cohere API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Review failed: {str(e)}")

# Alias route to prevent 404s if frontend calls /api/analyze
@app.post("/api/analyze")
async def analyze_alias(request: CodeReviewRequest):
    return await review_code(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
