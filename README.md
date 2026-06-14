# 🤖 CodeReviewer Backend

A FastAPI-based Python backend for AI-powered code review and analysis service with Cohere AI integration, comprehensive code quality metrics, and security analysis.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Code Analysis](#code-analysis)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- **AI-Powered Code Review** - Uses Cohere API for intelligent code analysis
- **Code Quality Metrics** - Pylint, Radon for complexity analysis
- **Security Analysis** - Bandit for security vulnerability detection
- **Code Style Check** - Pycodestyle for PEP8 compliance
- **Performance Analysis** - Code metrics and optimization suggestions
- **Fast API** - High-performance async Python framework
- **Database Support** - SQLAlchemy with Alembic migrations
- **Caching** - Redis integration for performance
- **Email Notifications** - Async email support
- **RESTful API** - Clean, well-documented endpoints

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.8+ | Language |
| FastAPI | ^0.104.1 | Web framework |
| Uvicorn | ^0.24.0 | ASGI server |
| Cohere | ^5.0.0 | AI code review |
| SQLAlchemy | ^2.0.0 | ORM |
| Pydantic | ^2.5.0 | Data validation |
| Redis | ^5.0.0 | Caching |
| Pylint | ^3.0.0 | Code analysis |
| Bandit | ^1.7.5 | Security analysis |

## 📦 Prerequisites

- **Python** (3.8 or higher) - [Download](https://www.python.org/downloads/)
- **pip** (Python package manager)
- **Redis** - [Download](https://redis.io/download)
- **Cohere API Key** - [Get here](https://cohere.com/)
- **Git** - [Download](https://git-scm.com/)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PratikDate01/CodeReviewerBackend.git
   cd CodeReviewerBackend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Activate on Windows:
   venv\Scripts\activate
   # Activate on macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment configuration**
   ```bash
   cp .env.example .env
   ```

5. **Configure environment variables** (see [Configuration](#configuration))

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

## 🚀 Getting Started

### Development Mode

Start the development server:

```bash
uvicorn main:app --reload
```

API runs at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api
```

### Authentication
Include Bearer token in Authorization header:

```
Authorization: Bearer <token>
```

### Code Review Endpoints

```python
# Submit code for review
POST /review
{
  "code": "python code string",
  "language": "python",
  "focus": ["security", "performance", "style"]
}

# Get review result
GET /review/{review_id}

# List reviews
GET /reviews?limit=50&offset=0

# Delete review
DELETE /review/{review_id}
```

### Response Example

```json
{
  "id": "review-123",
  "status": "completed",
  "code_quality": {
    "score": 8.5,
    "issues": [
      {
        "type": "security",
        "severity": "high",
        "message": "Potential SQL injection",
        "line": 45,
        "suggestion": "Use parameterized queries"
      }
    ]
  },
  "metrics": {
    "complexity": 3.2,
    "maintainability_index": 85,
    "lines_of_code": 150
  },
  "suggestions": [
    "Consider breaking down function into smaller parts",
    "Add type hints for better code clarity"
  ],
  "ai_review": "Well-structured code with good error handling..."
}
```

### File Upload for Review

```python
# Submit file for review
POST /review/upload
Content-Type: multipart/form-data
{
  "file": <binary>,
  "language": "python"
}
```

## 🔍 Code Analysis Features

### Security Analysis (Bandit)
- SQL injection detection
- Hardcoded passwords/credentials
- Insecure cryptography
- Shell injection risks
- XXE vulnerabilities

### Performance Analysis (Radon)
- Cyclomatic complexity
- Maintainability index
- Raw metrics
- Halstead metrics

### Code Quality
- PEP8 compliance
- Naming conventions
- Documentation completeness
- Code duplication

## 🔐 Environment Variables

```env
# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:password@localhost/codereviewer
DATABASE_ECHO=False

# Redis
REDIS_URL=redis://localhost:6379/0

# Cohere AI
COHERE_API_KEY=your_cohere_api_key
COHERE_MODEL=command

# JWT
JWT_SECRET=your_super_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Email (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@codereviewer.com

# Logging
LOG_LEVEL=INFO
```

## 📊 Database Schema

### Reviews Table
```python
class Review(Base):
    __tablename__ = "reviews"
    
    id: int
    user_id: int
    code: str
    language: str
    status: str  # pending, processing, completed
    quality_score: float
    complexity: float
    issues_count: int
    ai_feedback: str
    created_at: datetime
    updated_at: datetime
```

### Analysis Results Table
```python
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id: int
    review_id: int
    issue_type: str  # security, performance, style
    severity: str  # low, medium, high, critical
    message: str
    line_number: int
    suggestion: str
    created_at: datetime
```

## 🚀 Deployment

### Deploy to Render

1. **Connect GitHub repository to Render**
2. **Set environment variables**
3. **Build command**: `pip install -r requirements.txt && alembic upgrade head`
4. **Start command**: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4`

### Deploy with Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN alembic upgrade head

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

## 📄 License

Licensed under ISC License.

## 🆘 Support

- **Issues** - [GitHub Issues](https://github.com/PratikDate01/CodeReviewerBackend/issues)
- **Documentation** - Check docs folder

## 🔗 Related Projects

- [CodeReviewer Frontend](https://github.com/PratikDate01/CodeReviewer)

---

Made with ❤️ by the CodeReviewer Team
