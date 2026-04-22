import logging
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import get_db
from models.models import User
from services.auth_service import get_current_user
from services.ai_service import chat_with_ai, SUGGESTED_QUESTIONS

logger = logging.getLogger("autogst.routes.ai")
router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    suggested_questions: List[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to the AI tax assistant."""
    logger.info("AI chat: user=%d message_len=%d", current_user.id, len(request.message))

    user_context = {
        "business_name": current_user.business_name,
        "gstin": current_user.gstin,
        "full_name": current_user.full_name,
    }

    history = [{"role": m.role, "content": m.content} for m in request.history]

    reply = await chat_with_ai(
        user_message=request.message,
        conversation_history=history,
        user_context=user_context,
    )

    return ChatResponse(
        reply=reply,
        suggested_questions=SUGGESTED_QUESTIONS[:4],
    )


@router.get("/suggestions")
def get_suggestions(current_user: User = Depends(get_current_user)):
    """Return suggested questions for the AI assistant."""
    return {"questions": SUGGESTED_QUESTIONS}
