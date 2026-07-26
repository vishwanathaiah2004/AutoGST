# AutoGST Pro + SmartTax AI..

A production-ready full-stack GST management and tax calculation platform for Indian businesses.

## Tech Stack
- **Frontend**: Next.js 15 (App Router) + Tailwind CSS + TypeScript
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL
- **Auth**: JWT (python-jose + bcrypt)
- **OCR**: Tesseract + pytesseract
- **AI**: Google Gemini 1.5 Flash (fallback parser)
- **ML**: scikit-learn (expense classification + anomaly detection)
- **Reports**: ReportLab (PDF) + openpyxl (Excel)

---

## Features

| Feature | Status |
|---|---|
| JWT Authentication (Signup/Login) | ✅ |
| Transactions CRUD | ✅ |
| GST Engine (CGST/SGST/IGST/IGST/exempt) | ✅ |
| Dashboard with Charts | ✅ |
| File Upload + OCR (Tesseract) | ✅ |
| Regex Invoice Parsing | ✅ |
| Gemini AI Fallback Parsing | ✅ |
| GSTR-1 & GSTR-3B Simulation | ✅ |
| PDF & Excel Export | ✅ |
| Alerts System (GST deadlines, anomalies) | ✅ |
| ML Expense Classification | ✅ |
| ML Anomaly Detection | ✅ |
| Individual Tax Calculator (Old+New Regime) | ✅ |
| Global Exception Handler | ✅ |
| Structured Logging | ✅ |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Tesseract OCR

---

## Step 1: Install Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install tesseract-ocr -y
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
Add to PATH after installation.

**Verify:**
```bash
tesseract --version
```

---

## Step 2: Setup PostgreSQL

```bash
# Create database
psql -U postgres
CREATE DATABASE autogst_pro;
\q
```

---

## Step 3: Backend Setup

```bash
cd backend

# Copy env file
cp .env.example .env

# Edit .env with your values:
# DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/autogst_pro
# JWT_SECRET_KEY=your-super-secret-key-min-32-chars
# GEMINI_API_KEY=your-gemini-api-key (optional, for AI fallback)

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create DB tables and seed sample data
python utils/seed.py

# Run backend
python main.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

---

## Step 4: Frontend Setup

```bash
cd frontend

# Copy env (already set for local)
cp .env.local.example .env.local  # or just use .env.local as-is

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend runs at: http://localhost:3000

---

## Step 5: Login

Use the seeded demo account:
- **Email**: demo@autogst.pro
- **Password**: Demo@1234

---

## Project Structure

```
autogst-pro/
├── backend/
│   ├── main.py                 # FastAPI app entrypoint
│   ├── requirements.txt
│   ├── schema.sql              # Manual SQL schema reference
│   ├── .env.example
│   ├── config/
│   │   ├── settings.py         # Pydantic settings
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   └── logging_config.py   # Rotating file logger
│   ├── models/
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── routes/
│   │   ├── auth.py             # /auth/register, /auth/login, /auth/me
│   │   ├── transactions.py     # CRUD /transactions
│   │   ├── gst.py              # /gst/calculate, /gst/rates
│   │   ├── upload.py           # /upload (OCR)
│   │   ├── reports.py          # /reports/gstr (PDF+Excel)
│   │   ├── tax.py              # /tax/calculate
│   │   └── dashboard.py        # /dashboard, /alerts
│   ├── services/
│   │   ├── auth_service.py     # JWT, bcrypt, user auth
│   │   ├── transaction_service.py  # CRUD + dashboard stats
│   │   ├── gst_service.py      # GST engine + GSTR aggregations
│   │   ├── ocr_service.py      # Tesseract + Regex + Gemini
│   │   ├── ml_service.py       # Expense classifier + anomaly detection
│   │   ├── report_service.py   # PDF + Excel generation
│   │   ├── tax_service.py      # Income tax calculator
│   │   └── alert_service.py    # Alert CRUD + deadline alerts
│   ├── utils/
│   │   ├── exceptions.py       # Global exception handlers
│   │   └── seed.py             # DB seed script
│   ├── ml/models/              # Saved ML model files (auto-created)
│   ├── logs/                   # Log files (auto-created)
│   └── uploads/                # Uploaded files (auto-created)
│
└── frontend/
    ├── app/
    │   ├── layout.tsx           # Root layout with providers
    │   ├── page.tsx             # Redirect to dashboard/login
    │   ├── globals.css
    │   ├── login/page.tsx
    │   ├── register/page.tsx
    │   ├── dashboard/page.tsx   # Charts + stats
    │   ├── transactions/page.tsx  # CRUD table with filters
    │   ├── upload/page.tsx      # Drag & drop OCR
    │   ├── reports/page.tsx     # GSTR report + PDF/Excel download
    │   ├── tax-assistant/page.tsx  # Tax calculator
    │   └── alerts/page.tsx
    ├── components/
    │   ├── layout/Sidebar.tsx
    │   └── ui/StatCard.tsx
    ├── lib/
    │   ├── api.ts               # Axios client + all API functions
    │   └── auth.tsx             # Auth context + hook
    └── ...config files
```

---

## API Reference (Sample Requests)

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","full_name":"Test User","password":"Test@1234"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@autogst.pro","password":"Demo@1234"}'
```

### Create Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Software services","amount":100000,"transaction_type":"income","transaction_date":"2024-11-01","gst_type":"CGST","gst_rate":18}'
```

### Calculate GST
```bash
curl -X POST http://localhost:8000/api/v1/gst/calculate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":100000,"gst_rate":18,"gst_type":"CGST","is_inclusive":false}'
```

### Calculate Income Tax
```bash
curl -X POST http://localhost:8000/api/v1/tax/calculate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"regime":"new","gross_income":1200000,"salary_income":1200000,"assessment_year":"2024-25"}'
```

### Upload Invoice for OCR
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/invoice.jpg"
```

### Get GSTR-1 Report
```bash
curl "http://localhost:8000/api/v1/reports/gstr?report_type=GSTR-1&month=11&year=2024" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Response Format

All errors follow this structure:
```json
{
  "success": false,
  "message": "Human-readable error message",
  "error_code": "VALIDATION_ERROR",
  "details": "Optional technical details"
}
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `tesseract not found` | Tesseract not installed | Install Tesseract and ensure it's in PATH |
| `could not connect to database` | PostgreSQL not running | Start PostgreSQL service |
| `401 Unauthorized` | Invalid/expired token | Re-login to get new token |
| `422 Unprocessable Entity` | Invalid request body | Check request schema |
| `ModuleNotFoundError` | Missing Python package | Run `pip install -r requirements.txt` |
| `CORS error in browser` | Frontend origin not allowed | Add `http://localhost:3000` to `CORS_ORIGINS` in `.env` |

---

## Gemini API Key (Optional)

To enable Gemini AI fallback parsing for OCR:
1. Go to https://makersuite.google.com/app/apikey
2. Create an API key
3. Add to `backend/.env`: `GEMINI_API_KEY=your-key`

Without this, the system still uses Tesseract + regex parsing.

---

## Testing

Run backend health check:
```bash
curl http://localhost:8000/health
```

Run seed:
```bash
cd backend && python utils/seed.py
```

View API docs (Swagger UI): http://localhost:8000/docs
