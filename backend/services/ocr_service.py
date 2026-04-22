import logging
import re
import os
import uuid
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from PIL import Image
import pytesseract

from config.settings import settings
from models.models import UploadedFile, User

logger = logging.getLogger("autogst.ocr")

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# ─── File Upload ─────────────────────────────────────────────────────────────

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff", "application/pdf"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


async def save_upload(file: UploadFile, user_id: int) -> Tuple[str, str, int]:
    """Save uploaded file to disk and return (path, unique_name, size)."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB")

    ext = Path(file.filename).suffix.lower()
    unique_name = f"{user_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info("File saved: %s (%d bytes)", file_path, len(content))
    return file_path, unique_name, len(content)


# ─── OCR Extraction ──────────────────────────────────────────────────────────

def extract_text_tesseract(image_path: str) -> Tuple[str, float]:
    """Extract text from image using Tesseract OCR."""
    try:
        img = Image.open(image_path)

        # Preprocess: convert to grayscale for better OCR
        if img.mode != "L":
            img = img.convert("L")

        # Tesseract config for invoice-like documents
        config = "--oem 3 --psm 6 -l eng"
        data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)

        # Compute average confidence
        confidences = [int(c) for c in data["conf"] if str(c) != "-1" and int(c) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        text = pytesseract.image_to_string(img, config=config)
        logger.info(
            "Tesseract OCR complete: %d chars, confidence=%.1f%%",
            len(text), avg_confidence
        )
        return text.strip(), avg_confidence / 100
    except Exception as e:
        logger.error("Tesseract OCR failed: %s", str(e))
        raise


# ─── Regex Parser ────────────────────────────────────────────────────────────

def parse_invoice_regex(text: str) -> Dict[str, Any]:
    """Extract invoice fields using regex patterns."""
    result = {}

    # Total amount patterns
    amount_patterns = [
        r"(?:total|grand total|amount|net payable|payable)[:\s]+(?:rs\.?|₹|inr)?\s*([0-9,]+\.?\d{0,2})",
        r"(?:rs\.?|₹|inr)\s*([0-9,]+\.?\d{0,2})\s*(?:only|/-)?",
        r"([0-9,]+\.\d{2})\s*(?:total|amount)",
    ]
    for pat in amount_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                result["amount"] = float(amount_str)
                break
            except ValueError:
                pass

    # GSTIN pattern
    gstin_match = re.search(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text)
    if gstin_match:
        result["gstin"] = gstin_match.group(1)

    # GST amounts
    gst_patterns = {
        "cgst": r"cgst[:\s]+(?:rs\.?|₹)?\s*([0-9,]+\.?\d{0,2})",
        "sgst": r"sgst[:\s]+(?:rs\.?|₹)?\s*([0-9,]+\.?\d{0,2})",
        "igst": r"igst[:\s]+(?:rs\.?|₹)?\s*([0-9,]+\.?\d{0,2})",
    }
    for key, pat in gst_patterns.items():
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            try:
                result[key] = float(match.group(1).replace(",", ""))
            except ValueError:
                pass

    # Invoice number
    inv_match = re.search(
        r"(?:invoice|inv|bill)\s*(?:no\.?|#|number)?\s*[:\s]*([A-Z0-9\-/]+)",
        text, re.IGNORECASE
    )
    if inv_match:
        result["invoice_number"] = inv_match.group(1).strip()

    # Date
    date_patterns = [
        r"(?:date|dt)[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})",
        r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
    ]
    for pat in date_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            result["date"] = match.group(1)
            break

    # Vendor name (first non-empty line often)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        result["vendor_name"] = lines[0][:100]

    # HSN/SAC code
    hsn_match = re.search(r"(?:hsn|sac)[:\s]*([0-9]{4,8})", text, re.IGNORECASE)
    if hsn_match:
        result["hsn_sac_code"] = hsn_match.group(1)

    logger.debug("Regex parsing extracted: %s", list(result.keys()))
    return result


# ─── Gemini Fallback ─────────────────────────────────────────────────────────

async def parse_invoice_gemini(text: str) -> Optional[Dict[str, Any]]:
    """Use Google Gemini to parse invoice text when regex fails."""
    try:
        import google.generativeai as genai
        from config.settings import settings

        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured")
            return None

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
You are an invoice parser. Extract structured data from the following invoice/receipt text.
Return ONLY valid JSON with these fields (use null if not found):
{{
  "vendor_name": string,
  "invoice_number": string,
  "date": "YYYY-MM-DD",
  "amount": number,
  "taxable_amount": number,
  "cgst": number,
  "sgst": number,
  "igst": number,
  "total_gst": number,
  "gstin": string,
  "hsn_sac_code": string,
  "description": string
}}

Invoice text:
{text[:3000]}
"""
        response = model.generate_content(prompt)
        import json

        raw = response.text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw)

        parsed = json.loads(raw)
        logger.info("Gemini successfully parsed invoice data")
        return parsed

    except Exception as e:
        logger.error("Gemini parsing failed: %s", str(e))
        return None


# ─── Main OCR Pipeline ───────────────────────────────────────────────────────

async def process_uploaded_file(
    db: Session,
    file: UploadFile,
    user: User,
) -> UploadedFile:
    """Full pipeline: save → OCR → parse (regex → Gemini fallback) → DB."""
    file_path, unique_name, file_size = await save_upload(file, user.id)

    db_file = UploadedFile(
        user_id=user.id,
        filename=unique_name,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        content_type=file.content_type,
        ocr_status="processing",
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    try:
        # Step 1: OCR
        ocr_text, confidence = extract_text_tesseract(file_path)
        db_file.ocr_text = ocr_text
        db_file.ocr_confidence = confidence
        db_file.ocr_status = "success"

        # Step 2: Regex parsing
        parsed = parse_invoice_regex(ocr_text)
        parsing_method = "regex"

        # Step 3: Gemini fallback if regex found less than 3 fields
        if len(parsed) < 3:
            logger.info("Regex yielded few fields, trying Gemini fallback...")
            gemini_parsed = await parse_invoice_gemini(ocr_text)
            if gemini_parsed:
                parsed = {k: v for k, v in gemini_parsed.items() if v is not None}
                parsing_method = "gemini"

        db_file.parsed_data = parsed
        db_file.parsing_method = parsing_method

    except Exception as e:
        logger.error("OCR pipeline failed for file %s: %s", file.filename, str(e))
        db_file.ocr_status = "failed"

    db.commit()
    db.refresh(db_file)
    return db_file
