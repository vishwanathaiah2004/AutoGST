from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Any, Dict
from datetime import date, datetime
from decimal import Decimal
from models.models import UserRole, TransactionType, GSTType, AlertSeverity


# ─── Auth / User ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    gstin: Optional[str] = Field(None, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    business_name: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    gstin: Optional[str]
    pan: Optional[str]
    business_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# ─── Category ────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type: TransactionType
    gst_rate: Decimal = Field(default=0.0, ge=0, le=100)
    hsn_sac_code: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: TransactionType
    gst_rate: Decimal
    hsn_sac_code: Optional[str]
    description: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# ─── Transaction ─────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0)
    transaction_type: TransactionType
    transaction_date: date
    category_id: Optional[int] = None
    gst_type: GSTType = GSTType.CGST
    gst_rate: Decimal = Field(default=0.0, ge=0, le=100)
    party_name: Optional[str] = None
    party_gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    hsn_sac_code: Optional[str] = None
    notes: Optional[str] = None

    @validator("gst_rate")
    def validate_gst_rate(cls, v):
        valid_rates = [0, 0.25, 3, 5, 12, 18, 28]
        if round(float(v), 2) not in valid_rates:
            raise ValueError(f"GST rate must be one of {valid_rates}")
        return v


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_type: Optional[TransactionType] = None
    transaction_date: Optional[date] = None
    category_id: Optional[int] = None
    gst_type: Optional[GSTType] = None
    gst_rate: Optional[Decimal] = None
    party_name: Optional[str] = None
    party_gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    description: str
    amount: Decimal
    transaction_type: TransactionType
    transaction_date: date
    gst_type: GSTType
    gst_rate: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_gst: Decimal
    taxable_amount: Decimal
    total_amount: Decimal
    party_name: Optional[str]
    party_gstin: Optional[str]
    invoice_number: Optional[str]
    hsn_sac_code: Optional[str]
    ml_category: Optional[str]
    ml_confidence: Optional[float]
    is_anomaly: bool
    anomaly_score: Optional[float]
    source: str
    notes: Optional[str]
    created_at: datetime
    category: Optional[CategoryResponse]

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int
    pages: int


# ─── GST ─────────────────────────────────────────────────────────────────────

class GSTCalculationRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Base taxable amount")
    gst_rate: Decimal = Field(..., ge=0, le=28)
    gst_type: GSTType
    is_inclusive: bool = False


class GSTCalculationResponse(BaseModel):
    taxable_amount: Decimal
    gst_rate: Decimal
    cgst_rate: Optional[Decimal]
    sgst_rate: Optional[Decimal]
    igst_rate: Optional[Decimal]
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_gst: Decimal
    total_amount: Decimal
    gst_type: GSTType


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    total_gst_collected: Decimal
    total_gst_paid: Decimal
    net_gst_liability: Decimal
    transaction_count: int
    anomaly_count: int
    pending_alerts: int
    monthly_summary: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]


# ─── OCR / File ──────────────────────────────────────────────────────────────

class OCRResponse(BaseModel):
    file_id: int
    filename: str
    ocr_text: Optional[str]
    ocr_status: str
    parsed_data: Optional[Dict[str, Any]]
    parsing_method: Optional[str]
    confidence: Optional[float]


# ─── Reports ─────────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    report_type: str = Field(..., description="GSTR-1 or GSTR-3B")
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    format: str = Field(default="json", description="json, pdf, or excel")


class GSTRSummary(BaseModel):
    period: str
    total_taxable_value: Decimal
    total_cgst: Decimal
    total_sgst: Decimal
    total_igst: Decimal
    total_tax: Decimal
    net_gst_liability: Decimal
    input_tax_credit: Decimal
    transactions: List[TransactionResponse]


# ─── Tax Calculator ──────────────────────────────────────────────────────────

class TaxCalculationRequest(BaseModel):
    assessment_year: str = Field(default="2024-25")
    regime: str = Field(..., description="old or new")
    gross_income: Decimal = Field(..., ge=0)
    salary_income: Decimal = Field(default=0, ge=0)
    business_income: Decimal = Field(default=0, ge=0)
    other_income: Decimal = Field(default=0, ge=0)
    # Deductions (old regime only)
    section_80c: Decimal = Field(default=0, ge=0, le=150000)
    section_80d: Decimal = Field(default=0, ge=0)
    section_80g: Decimal = Field(default=0, ge=0)
    hra_exemption: Decimal = Field(default=0, ge=0)

    @validator("regime")
    def validate_regime(cls, v):
        if v not in ["old", "new"]:
            raise ValueError("Regime must be 'old' or 'new'")
        return v


class TaxCalculationResponse(BaseModel):
    assessment_year: str
    regime: str
    gross_income: Decimal
    total_deductions: Decimal
    taxable_income: Decimal
    income_tax: Decimal
    surcharge: Decimal
    cess: Decimal
    total_tax_liability: Decimal
    effective_tax_rate: float
    slab_breakdown: List[Dict[str, Any]]
    comparison: Optional[Dict[str, Any]]


# ─── Alert ───────────────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: int
    title: str
    message: str
    severity: AlertSeverity
    category: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Standard API Responses ──────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str
    details: Optional[str] = None
