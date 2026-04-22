"""
Gemini-powered AI assistant service.
Answers questions about GST, Indian tax law, and business finance.
"""
import logging
from typing import List, Dict, Any
from fastapi import HTTPException

from config.settings import settings

logger = logging.getLogger("autogst.ai_assistant")

SYSTEM_PROMPT = """You are AutoGST AI, an expert assistant specializing in:
- Indian GST (Goods and Services Tax) rules, rates, and compliance
- Indian income tax (old and new regime), deductions, and filing
- Business accounting, invoicing, and financial management
- GSTR-1, GSTR-3B, GSTR-9 filing guidance
- HSN/SAC codes, input tax credit (ITC), and reverse charge mechanism

Guidelines:
- Give accurate, concise answers relevant to Indian tax law
- When quoting rates or rules, cite the relevant section (e.g., Section 80C, CGST Act)
- Always clarify if rules change based on taxpayer type (individual/business/composition)
- For complex legal matters, recommend consulting a CA or tax professional
- Format responses clearly using bullet points and amounts in INR
- Current assessment year context: FY 2024-25 (AY 2025-26)
- Do NOT answer questions unrelated to tax, finance, or accounting
"""


async def chat_with_ai(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    user_context: Dict[str, Any] = None,
) -> str:
    """Send a message to Gemini and return the response."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI Assistant is not configured. Please set GEMINI_API_KEY in your .env file.",
        )

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )

        # Build context string from user profile
        context_str = ""
        if user_context:
            context_str = f"\n\nUser context: Business: {user_context.get('business_name', 'N/A')}, GSTIN: {user_context.get('gstin', 'Not registered')}, Regime preference: unknown\n\n"

        # Build Gemini chat history
        history = []
        for msg in conversation_history[:-1]:  # exclude last (current) message
            history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]],
            })

        chat = model.start_chat(history=history)
        full_message = context_str + user_message if context_str else user_message
        response = chat.send_message(full_message)

        logger.info(
            "AI chat response generated: %d input chars → %d output chars",
            len(user_message), len(response.text)
        )
        return response.text

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Gemini chat error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"AI service error: {str(e)}",
        )


SUGGESTED_QUESTIONS = [
    "What are the GST rates for software services?",
    "How do I claim input tax credit (ITC)?",
    "What is the difference between GSTR-1 and GSTR-3B?",
    "Which tax regime is better for a salary of ₹12 lakhs?",
    "What deductions can I claim under Section 80C?",
    "What is the due date for GST filing?",
    "How is reverse charge mechanism applied?",
    "What is the GST rate on restaurant services?",
    "Can I get ITC on capital goods purchase?",
    "What is the penalty for late GST filing?",
]
