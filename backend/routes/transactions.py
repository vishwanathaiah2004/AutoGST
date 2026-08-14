import logging
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from config.database import get_db
from models.models import User, TransactionType
from models.schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionListResponse, SuccessResponse
)
from services.auth_service import get_current_user
from services.transaction_service import (
    create_transaction, get_transactions, get_transaction_by_id,
    update_transaction, delete_transaction
)

logger = logging.getLogger("autogst.routes.transactions")
router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
def create(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Create transaction: user=%d", current_user.id)
    return create_transaction(db, current_user, data)


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_transactions(
        db, current_user.id, page, size,
        transaction_type, start_date, end_date, search, is_anomaly
    )


@router.get("/{txn_id}", response_model=TransactionResponse)
def get_one(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_transaction_by_id(db, txn_id, current_user.id)


@router.put("/{txn_id}", response_model=TransactionResponse)
def update(
    txn_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_transaction(db, txn_id, current_user.id, data)


@router.delete("/{txn_id}", response_model=SuccessResponse)
def delete(
    txn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_transaction(db, txn_id, current_user.id)
    return SuccessResponse(message="Transaction deleted successfully")