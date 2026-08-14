import logging
from decimal import Decimal
from typing import Optional, List
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, text
from fastapi import HTTPException, status

from models.models import Transaction, User, Category, TransactionType
from models.schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionListResponse
)
from services.gst_service import calculate_gst
from services.ml_service import classify_expense, detect_anomaly
from services.alert_service import create_alert

logger = logging.getLogger("autogst.transactions")


def create_transaction(db: Session, user: User, data: TransactionCreate) -> Transaction:
    """Create a new transaction with GST calculation and ML classification."""
    try:
        # Calculate GST
        gst_result = calculate_gst(data.amount, data.gst_rate, data.gst_type)

        txn = Transaction(
            user_id=user.id,
            category_id=data.category_id,
            description=data.description,
            amount=data.amount,
            transaction_type=data.transaction_type,
            transaction_date=data.transaction_date,
            gst_type=data.gst_type,
            gst_rate=data.gst_rate,
            cgst_amount=gst_result["cgst_amount"],
            sgst_amount=gst_result["sgst_amount"],
            igst_amount=gst_result["igst_amount"],
            total_gst=gst_result["total_gst"],
            taxable_amount=gst_result["taxable_amount"],
            total_amount=gst_result["total_amount"],
            party_name=data.party_name,
            party_gstin=data.party_gstin,
            invoice_number=data.invoice_number,
            hsn_sac_code=data.hsn_sac_code,
            notes=data.notes,
            source="manual",
        )

        # ML: expense classification
        try:
            ml_cat, confidence = classify_expense(data.description, float(data.amount))
            txn.ml_category = str(ml_cat) if ml_cat is not None else None
            txn.ml_confidence = float(confidence) if confidence is not None else None
        except Exception as ml_err:
            logger.warning("ML classification failed for transaction: %s", str(ml_err))

        # ML: anomaly detection
        try:
            is_anomaly, anomaly_score = detect_anomaly(
                db, user.id, float(data.amount), data.transaction_type
            )
            txn.is_anomaly = bool(is_anomaly)
            txn.anomaly_score = float(anomaly_score) if anomaly_score is not None else None

            if is_anomaly:
                create_alert(
                    db=db,
                    user_id=user.id,
                    title="Anomalous Transaction Detected",
                    message=f"Transaction '{data.description}' of ₹{data.amount} may be anomalous (score: {anomaly_score:.2f})",
                    severity="warning",
                    category="anomaly",
                )
        except Exception as ml_err:
            logger.warning("Anomaly detection failed: %s", str(ml_err))

        db.add(txn)
        db.commit()
        db.refresh(txn)
        logger.info("Transaction created: id=%d user=%d amount=%.2f", txn.id, user.id, float(data.amount))
        return txn

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Create transaction failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}",
        )


def get_transactions(
    db: Session,
    user_id: int,
    page: int = 1,
    size: int = 20,
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
) -> TransactionListResponse:
    """Get paginated, filtered transactions."""
    try:
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if search:
            query = query.filter(
                Transaction.description.ilike(f"%{search}%") |
                Transaction.party_name.ilike(f"%{search}%") |
                Transaction.invoice_number.ilike(f"%{search}%")
            )
        if is_anomaly is not None:
            query = query.filter(Transaction.is_anomaly == is_anomaly)

        total = query.count()
        items = (
            query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        pages = (total + size - 1) // size

        return TransactionListResponse(
            items=[TransactionResponse.model_validate(t) for t in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
    except Exception as e:
        logger.error("Get transactions error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")


def get_transaction_by_id(db: Session, txn_id: int, user_id: int) -> Transaction:
    txn = db.query(Transaction).filter(
        Transaction.id == txn_id, Transaction.user_id == user_id
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


def update_transaction(
    db: Session, txn_id: int, user_id: int, data: TransactionUpdate
) -> Transaction:
    """Update transaction and recalculate GST if needed."""
    try:
        txn = get_transaction_by_id(db, txn_id, user_id)
        update_data = data.model_dump(exclude_unset=True)

        # Recalculate GST if amount or rate changed
        amount = Decimal(str(update_data.get("amount", txn.amount)))
        gst_rate = Decimal(str(update_data.get("gst_rate", txn.gst_rate)))
        gst_type = update_data.get("gst_type", txn.gst_type)

        if "amount" in update_data or "gst_rate" in update_data or "gst_type" in update_data:
            gst_result = calculate_gst(amount, gst_rate, gst_type)
            txn.cgst_amount = gst_result["cgst_amount"]
            txn.sgst_amount = gst_result["sgst_amount"]
            txn.igst_amount = gst_result["igst_amount"]
            txn.total_gst = gst_result["total_gst"]
            txn.taxable_amount = gst_result["taxable_amount"]
            txn.total_amount = gst_result["total_amount"]

        for field, value in update_data.items():
            if field not in ("cgst_amount", "sgst_amount", "igst_amount", "total_gst", "taxable_amount", "total_amount"):
                setattr(txn, field, value)

        db.commit()
        db.refresh(txn)
        logger.info("Transaction updated: id=%d", txn_id)
        return txn
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Update transaction failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to update transaction")


def delete_transaction(db: Session, txn_id: int, user_id: int) -> bool:
    try:
        txn = get_transaction_by_id(db, txn_id, user_id)
        db.delete(txn)
        db.commit()
        logger.info("Transaction deleted: id=%d", txn_id)
        return True
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Delete transaction failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete transaction")


def get_dashboard_stats(db: Session, user_id: int) -> dict:
    """Aggregate dashboard statistics."""
    try:
        stats = db.query(
            func.sum(case(
                (Transaction.transaction_type == TransactionType.income, Transaction.amount),
                else_=0
            )).label("total_income"),
            func.sum(case(
                (Transaction.transaction_type == TransactionType.expense, Transaction.amount),
                else_=0
            )).label("total_expense"),
            func.sum(case(
                (Transaction.transaction_type == TransactionType.income, Transaction.total_gst),
                else_=0
            )).label("gst_collected"),
            func.sum(case(
                (Transaction.transaction_type == TransactionType.expense, Transaction.total_gst),
                else_=0
            )).label("gst_paid"),
            func.count(Transaction.id).label("txn_count"),
            func.sum(case(
                (Transaction.is_anomaly == True, 1),
                else_=0
            )).label("anomaly_count"),
        ).filter(Transaction.user_id == user_id).first()

        total_income = Decimal(str(stats.total_income or 0))
        total_expense = Decimal(str(stats.total_expense or 0))
        gst_collected = Decimal(str(stats.gst_collected or 0))
        gst_paid = Decimal(str(stats.gst_paid or 0))

        # Monthly summary (last 6 months)
        monthly = db.execute(text("""
            SELECT
                DATE_TRUNC('month', transaction_date) AS month,
                SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) AS income,
                SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) AS expense,
                SUM(total_gst) AS total_gst
            FROM transactions
            WHERE user_id = :uid
            GROUP BY DATE_TRUNC('month', transaction_date)
            ORDER BY month DESC
            LIMIT 6
        """), {"uid": user_id}).fetchall()

        # Top categories
        top_cats = db.execute(text("""
            SELECT
                COALESCE(c.name, t.ml_category, 'Uncategorized') AS category,
                SUM(t.amount) AS total,
                COUNT(*) AS count
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = :uid
            GROUP BY COALESCE(c.name, t.ml_category, 'Uncategorized')
            ORDER BY total DESC
            LIMIT 5
        """), {"uid": user_id}).fetchall()

        from models.models import Alert
        pending_alerts = db.query(Alert).filter(
            Alert.user_id == user_id, Alert.is_read == False
        ).count()

        return {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "net_balance": float(total_income - total_expense),
            "total_gst_collected": float(gst_collected),
            "total_gst_paid": float(gst_paid),
            "net_gst_liability": float(gst_collected - gst_paid),
            "transaction_count": stats.txn_count or 0,
            "anomaly_count": stats.anomaly_count or 0,
            "pending_alerts": pending_alerts,
            "monthly_summary": [
                {
                    "month": str(r.month)[:7],
                    "income": float(r.income or 0),
                    "expense": float(r.expense or 0),
                    "gst": float(r.total_gst or 0),
                }
                for r in monthly
            ],
            "top_categories": [
                {"category": r.category, "total": float(r.total), "count": r.count}
                for r in top_cats
            ],
        }
    except Exception as e:
        logger.error("Dashboard stats error: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to compute dashboard stats")