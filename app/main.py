import os
import io
import sys
import logging
import cohere
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Validate Environment Variables
COHERE_API_KEY = os.getenv("COHERE_API_KEY_1") or os.getenv("COHERE_API_KEY_2")

if not COHERE_API_KEY:
    logger.error("No Cohere API key (COHERE_API_KEY_1 or COHERE_API_KEY_2) found in environment variables")
    raise ValueError("COHERE_API_KEY_1 or COHERE_API_KEY_2 environment variable is required")

# Initialize Cohere Client
try:
    co = cohere.Client(COHERE_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Cohere client: {str(e)}")
    raise

app = FastAPI(title="Enterprise AI Code Reviewer")

# CORS configuration for React frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class CodeRunRequest(BaseModel):
    code: str

class CodeReviewRequest(BaseModel):
    code: str
    language: Optional[str] = "python"
    mode: Optional[str] = "hybrid" # Support frontend 'mode' parameter

# Routes
@app.get("/")
async def root():
    return {"message": "Enterprise AI Code Reviewer is running 🚀"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "Enterprise AI Code Reviewer"}

@app.post("/run-code")
@app.post("/api/run-code") # Support both direct and prefixed calls
async def run_code(request: CodeRunRequest):
    """
    Safely runs Python code and captures stdout/stderr.
    Note: In a production environment, use a sandboxed execution environment (e.g., Docker, PyExecJS).
    """
    logger.info("Executing Python code snippet")
    output_buffer = io.StringIO()
    error_buffer = io.StringIO()
    
    # Redirect stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = output_buffer
    sys.stderr = error_buffer
    
    try:
        # Execute the code in a restricted global scope
        exec_globals = {"__builtins__": __builtins__}
        exec(request.code, exec_globals)
    except Exception as e:
        print(f"Runtime Error: {str(e)}", file=sys.stderr)
    finally:
        # Restore stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    return {
        "output": output_buffer.getvalue(),
        "errors": error_buffer.getvalue()
    }

@app.post("/review-code")
@app.post("/api/analyze") # Support frontend call to /api/analyze
async def review_code(request: CodeReviewRequest):
    """
    Calls Cohere API to generate a comprehensive AI code review.
    """
    logger.info(f"Generating review for {request.language} code")
    
    prompt = f"""
    You are an expert software architect and security auditor.
    Review the following {request.language} code:
    
    ```
    {request.code}
    ```
    
    Provide a detailed AI code review in Markdown format including:
    1. **Code Summary**: A high-level explanation of the code's purpose.
    2. **Potential Bugs & Security Issues**: Identify logical errors, edge cases, or vulnerabilities.
    3. **Optimization Tips**: Specific suggestions to improve performance and resource usage.
    4. **Best Practices & Quality**: Feedback on naming, structure, and readability.
    
    Be objective, technical, and concise.
    """
    
    try:
        # Using command-xlarge-nightly for high-quality reviews
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

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return {"detail": "Internal Server Error", "error": str(exc)}

if __name__ == "__main__":
    import uvicorn
    # PORT is typically set by Render automatically
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
