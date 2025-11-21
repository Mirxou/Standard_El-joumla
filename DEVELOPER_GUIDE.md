# Developer Guide - دليل المطورين

## 🚀 Quick Start للمطورين

### المتطلبات
- Python 3.13+
- Docker & Docker Compose (اختياري)
- VS Code (موصى به)
- Git

### الإعداد السريع

#### 1. Clone المشروع
```bash
git clone https://github.com/your-org/logical-version-erp.git
cd logical-version-erp
```

#### 2. إعداد البيئة الافتراضية
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. تثبيت Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

#### 4. تشغيل النظام
```bash
# تشغيل واجهة Qt
python main.py

# تشغيل API Server
uvicorn src.api.app:app --reload --port 8000
```

---

## 🏗️ بنية المشروع

```
logical-version-erp/
├── src/                          # Source code
│   ├── api/                      # FastAPI application
│   │   ├── app.py               # Main API app
│   │   ├── routes/              # API endpoints
│   │   └── middleware/          # Auth, CORS, etc.
│   │
│   ├── core/                     # Core business logic
│   │   ├── database_manager.py
│   │   ├── inventory_manager.py
│   │   ├── sales_manager.py
│   │   └── purchase_manager.py
│   │
│   ├── services/                 # Business services
│   │   ├── ai_service.py
│   │   ├── loyalty_service.py
│   │   ├── einvoice_service.py
│   │   └── marketing_service.py
│   │
│   ├── security/                 # Security features
│   │   ├── mfa_service.py
│   │   └── audit_service.py
│   │
│   └── ui/                       # Qt GUI
│       ├── main_window.py
│       └── dialogs/
│
├── tests/                        # Unit & integration tests
│   ├── test_ai_features.py      # AI tests (26 tests)
│   ├── test_comprehensive.py    # Integration tests (8 tests)
│   ├── test_sales_api.py        # Sales API tests
│   └── test_*.py                # Other test files
│
├── .github/workflows/            # CI/CD pipelines
├── .devcontainer/               # Dev container config
├── docs/                        # Documentation
│
├── requirements.txt             # Production dependencies
├── requirements-test.txt        # Test dependencies
├── pytest.ini                   # Pytest configuration
├── Dockerfile                   # Production container
├── docker-compose.yml           # Multi-container setup
└── README.md                    # Main README
```

---

## 🧪 Testing

### تشغيل جميع الاختبارات
```bash
# All tests
pytest -v

# Specific test files
pytest test_ai_features.py -v
pytest test_comprehensive.py -v
pytest tests/test_sales_api.py -v

# With coverage
pytest --cov=src --cov-report=html

# Performance tests
python test_performance.py
```

### التوقعات
- ✅ **42/42 tests** يجب أن تمر بنجاح
- ⏱️ **< 5 seconds** لجميع الاختبارات
- 📊 **> 80% code coverage**

---

## 🔧 Development Workflow

### 1. إنشاء Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. الكتابة والاختبار
```python
# Write code in src/
# Write tests in tests/

# Run tests frequently
pytest test_your_new_feature.py -v
```

### 3. Code Quality Checks
```bash
# Linting
ruff check .

# Formatting
black src/ tests/

# Type checking
mypy src/
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: Add new feature"
```

### 5. Push & Create PR
```bash
git push origin feature/your-feature-name
# Create Pull Request on GitHub
```

---

## 📚 API Development

### إضافة Endpoint جديد

#### 1. إنشاء Route Function
```python
# src/api/routes/your_module.py
from fastapi import APIRouter, Depends
from src.api.auth import get_current_user

router = APIRouter(prefix="/your-module", tags=["your-module"])

@router.get("/items")
async def get_items(
    page: int = 1,
    user: dict = Depends(get_current_user)
):
    """Get list of items"""
    # Your logic here
    return {"items": [], "total": 0}
```

#### 2. تسجيل Router في App
```python
# src/api/app.py
from src.api.routes import your_module

app.include_router(your_module.router)
```

#### 3. إضافة Tests
```python
# tests/test_your_module.py
def test_get_items(client, auth_headers):
    response = client.get("/your-module/items", headers=auth_headers)
    assert response.status_code == 200
```

#### 4. تحديث Documentation
```bash
python generate_api_docs.py
# Updates openapi.json, API_DOCS.md, postman_collection.json
```

---

## 🐳 Docker Development

### Build & Run Locally
```bash
# Build image
docker build -t logical-version:dev .

# Run container
docker run -p 8000:8000 logical-version:dev

# Using Docker Compose
docker-compose up --build
```

### VS Code Dev Container
```bash
# 1. Install "Dev Containers" extension
# 2. Press F1 → "Dev Containers: Reopen in Container"
# 3. Container will build and start automatically
```

---

## 🔍 Debugging

### VS Code Debug Configuration
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.api.app:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true
    },
    {
      "name": "Python: Qt GUI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal"
    }
  ]
}
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Use in code
logger.info("Processing order #123")
logger.error("Failed to process payment", exc_info=True)
```

---

## 🚀 Performance Best Practices

### Database
- ✅ Use transactions for multi-step operations
- ✅ Add indexes on frequently queried columns
- ✅ Use `executemany()` for bulk inserts
- ❌ Avoid N+1 queries
- ❌ Don't fetch all rows without limit

### API
- ✅ Implement pagination (`page`, `page_size`)
- ✅ Use async/await for I/O operations
- ✅ Cache frequently accessed data
- ❌ Don't return full objects when partial will do
- ❌ Avoid blocking operations in async functions

### Frontend
- ✅ Lazy load data tables
- ✅ Use virtual scrolling for large lists
- ✅ Debounce search inputs
- ❌ Don't reload entire tables on single row change

---

## 🔒 Security Guidelines

### Authentication
```python
# Always verify user permissions
from src.api.auth import require_role

@router.delete("/products/{id}")
async def delete_product(
    id: int,
    user: dict = Depends(require_role("admin"))
):
    # Only admins can delete
    pass
```

### Input Validation
```python
from pydantic import BaseModel, Field, validator

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    
    @validator('price')
    def validate_price(cls, v):
        if v > 1000000:
            raise ValueError('Price too high')
        return v
```

### SQL Injection Prevention
```python
# ✅ Good - parameterized query
cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))

# ❌ Bad - string formatting
cursor.execute(f"SELECT * FROM products WHERE id = {product_id}")
```

---

## 📊 Monitoring & Analytics

### Application Metrics
```python
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total API requests')
response_time = Histogram('api_response_seconds', 'API response time')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_count.inc()
    with response_time.time():
        response = await call_next(request)
    return response
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "database": "connected",
  "version": "3.5.2"
}
```

---

## 🌐 Internationalization (i18n)

### إضافة ترجمات جديدة
```python
# src/i18n/translations.py
TRANSLATIONS = {
    "ar": {
        "welcome": "مرحباً",
        "logout": "تسجيل خروج"
    },
    "en": {
        "welcome": "Welcome",
        "logout": "Logout"
    }
}

# Usage
from src.i18n import translate
print(translate("welcome", lang="ar"))  # "مرحباً"
```

---

## 🤝 Contributing

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
feat(sales): Add bulk order discount calculation

- Calculate discounts based on quantity tiers
- Apply customer loyalty tier multipliers
- Update unit tests

Closes #123
```

---

## 📞 Support & Resources

### Documentation
- 📖 [API Reference](API_REFERENCE.md)
- 🐳 [Docker Deployment](DOCKER_DEPLOYMENT.md)
- 📊 [Database Schema](DATABASE_SCHEMA_INFO.md)
- 🔒 [Security Guide](SECURITY_I18N_QUICK_REFERENCE.md)

### Tools
- **Postman Collection**: Import `postman_collection.json`
- **VS Code REST Client**: Use `api_samples.http`
- **OpenAPI Spec**: `openapi.json` (import into Swagger Editor)

### Commands Cheat Sheet
```bash
# Development
python main.py                              # Run Qt GUI
uvicorn src.api.app:app --reload           # Run API server
pytest -v                                   # Run tests
python test_performance.py                  # Performance tests

# Code Quality
ruff check .                                # Lint
black src/ tests/                           # Format
mypy src/                                   # Type check

# Docker
docker-compose up --build                   # Build & run
docker-compose logs -f api                  # View logs
docker-compose down                         # Stop containers

# Documentation
python generate_api_docs.py                 # Generate API docs

# Database
python check_db_tables.py                   # Verify schema
```

---

## ⚡ Pro Tips

1. **VS Code Extensions**: Install Python, Ruff, Docker, REST Client
2. **Use Dev Container**: Consistent environment, no local setup
3. **Hot Reload**: `--reload` flag for instant code updates
4. **Test Driven**: Write tests first, then implementation
5. **API Testing**: Use REST Client extension in VS Code
6. **Performance**: Run `test_performance.py` before major releases
7. **Git Hooks**: Use pre-commit hooks for linting
8. **Database Backup**: Regular backups before schema changes

---

**Happy Coding! 🚀**

For questions or issues, please open a GitHub issue or contact the development team.
