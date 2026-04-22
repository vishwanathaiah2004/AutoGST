from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, JSON, Numeric, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from config.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"
    accountant = "accountant"


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class GSTType(str, enum.Enum):
    CGST = "CGST"
    SGST = "SGST"
    IGST = "IGST"
    UTGST = "UTGST"
    exempt = "exempt"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


# ─── User ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    gstin = Column(String(15), nullable=True)
    pan = Column(String(10), nullable=True)
    business_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    uploaded_files = relationship("UploadedFile", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    tax_calculations = relationship("TaxCalculation", back_populates="user", cascade="all, delete-orphan")


# ─── Category ────────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    gst_rate = Column(Numeric(5, 2), default=0.0)
    hsn_sac_code = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="category")


# ─── Transaction ─────────────────────────────────────────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    transaction_date = Column(Date, nullable=False)

    # GST fields
    gst_type = Column(Enum(GSTType), default=GSTType.CGST)
    gst_rate = Column(Numeric(5, 2), default=0.0)
    cgst_amount = Column(Numeric(15, 2), default=0.0)
    sgst_amount = Column(Numeric(15, 2), default=0.0)
    igst_amount = Column(Numeric(15, 2), default=0.0)
    total_gst = Column(Numeric(15, 2), default=0.0)
    taxable_amount = Column(Numeric(15, 2), default=0.0)
    total_amount = Column(Numeric(15, 2), default=0.0)

    # Vendor/Customer
    party_name = Column(String(255), nullable=True)
    party_gstin = Column(String(15), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    hsn_sac_code = Column(String(20), nullable=True)

    # ML fields
    ml_category = Column(String(100), nullable=True)
    ml_confidence = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)

    # Source
    source = Column(String(50), default="manual")  # manual, ocr, import
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    uploaded_file = relationship("UploadedFile", back_populates="transactions")


# ─── Uploaded File ───────────────────────────────────────────────────────────

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)

    # OCR result
    ocr_text = Column(Text, nullable=True)
    ocr_status = Column(String(50), default="pending")  # pending, success, failed
    ocr_confidence = Column(Float, nullable=True)
    parsed_data = Column(JSON, nullable=True)
    parsing_method = Column(String(50), nullable=True)  # regex, gemini, manual

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="uploaded_files")
    transactions = relationship("Transaction", back_populates="uploaded_file")


# ─── Alert ───────────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.info)
    category = Column(String(100), nullable=True)  # gst, anomaly, deadline, system
    is_read = Column(Boolean, default=False)
    related_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    alert_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="alerts")


# ─── GST Return ──────────────────────────────────────────────────────────────

class GSTReturn(Base):
    __tablename__ = "gst_returns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    return_type = Column(String(20), nullable=False)  # GSTR-1, GSTR-3B
    period_month = Column(Integer, nullable=False)
    period_year = Column(Integer, nullable=False)

    # Aggregates
    total_taxable_value = Column(Numeric(15, 2), default=0.0)
    total_cgst = Column(Numeric(15, 2), default=0.0)
    total_sgst = Column(Numeric(15, 2), default=0.0)
    total_igst = Column(Numeric(15, 2), default=0.0)
    total_tax = Column(Numeric(15, 2), default=0.0)
    net_gst_liability = Column(Numeric(15, 2), default=0.0)
    input_tax_credit = Column(Numeric(15, 2), default=0.0)

    status = Column(String(50), default="draft")  # draft, filed, revised
    report_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")


# ─── Tax Calculation ─────────────────────────────────────────────────────────

class TaxCalculation(Base):
    __tablename__ = "tax_calculations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_year = Column(String(10), nullable=False)
    regime = Column(String(20), nullable=False)  # old, new

    # Income breakdown
    gross_income = Column(Numeric(15, 2), default=0.0)
    salary_income = Column(Numeric(15, 2), default=0.0)
    business_income = Column(Numeric(15, 2), default=0.0)
    other_income = Column(Numeric(15, 2), default=0.0)

    # Deductions
    standard_deduction = Column(Numeric(15, 2), default=0.0)
    section_80c = Column(Numeric(15, 2), default=0.0)
    section_80d = Column(Numeric(15, 2), default=0.0)
    section_80g = Column(Numeric(15, 2), default=0.0)
    hra_exemption = Column(Numeric(15, 2), default=0.0)
    total_deductions = Column(Numeric(15, 2), default=0.0)

    # Result
    taxable_income = Column(Numeric(15, 2), default=0.0)
    income_tax = Column(Numeric(15, 2), default=0.0)
    surcharge = Column(Numeric(15, 2), default=0.0)
    cess = Column(Numeric(15, 2), default=0.0)
    total_tax_liability = Column(Numeric(15, 2), default=0.0)
    effective_tax_rate = Column(Float, default=0.0)

    calculation_details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="tax_calculations")
