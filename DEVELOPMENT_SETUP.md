# Development Team Setup Guide

## Custom Dependencies

This project uses **one** custom Python package not available on standard PyPI:

### 1. emergentintegrations

This is Emergent's integration library for LLM access (OpenAI, Anthropic, Google).

**Installation:**
```bash
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

**Full requirements install:**
```bash
pip install -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

---

### 2. ContentAnalyze (NOT an external package)

`ContentAnalyze` is **NOT** an external package - it's a Pydantic model defined in the codebase:

**Location:** `/app/backend/models/schemas.py` (line 126)

```python
class ContentAnalyze(BaseModel):
    content: str
    user_id: str
    language: str = "en"
    profile_id: Optional[str] = None
    platform_context: Optional[Dict[str, Any]] = None
```

This is imported from the local models module:
```python
from models.schemas import ContentAnalyze
# or
from models import ContentAnalyze
```

---

## Complete Setup Steps

### Step 1: Clone the repository
```bash
git clone <your-repo-url>
cd <repo-name>
```

### Step 2: Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

### Step 3: Install dependencies with custom index
```bash
cd backend
pip install -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

### Step 4: Set environment variables
```bash
# Create .env file in /backend
cp .env.example .env  # if exists, or create manually

# Required variables:
MONGO_URL=mongodb://localhost:27017
DB_NAME=contentry

# For LLM features (get from Emergent dashboard):
EMERGENT_API_KEY=your_emergent_key

# For Google Vision/Video (optional):
GOOGLE_VISION_API_KEY=your_key
GOOGLE_CREDENTIALS_BASE64=your_base64_credentials
```

### Step 5: Import database (optional)
```bash
cd database_export
python import_database.py
```

### Step 6: Run the backend
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Step 7: Run the frontend
```bash
cd frontend
yarn install
yarn dev
```

---

## Troubleshooting

### "Could not find emergentintegrations"
Make sure to use the `--extra-index-url` flag:
```bash
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

### "ImportError: cannot import name 'ContentAnalyze'"
This is a local model, not a package. Ensure you're running from the `/backend` directory so Python can find the `models` module.

### "ModuleNotFoundError: No module named 'models'"
Add the backend directory to your Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

---

## Package Sources

| Package | Source |
|---------|--------|
| emergentintegrations | `https://d33sy5i8bnduwe.cloudfront.net/simple/` |
| All other packages | PyPI (standard) |
| ContentAnalyze | Local model (`/backend/models/schemas.py`) |
