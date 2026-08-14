import logging
import pickle
import os
import numpy as np
from typing import Tuple, List, Optional
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from models.models import Transaction, TransactionType

logger = logging.getLogger("autogst.ml")

MODEL_DIR = "ml/models"
CLASSIFIER_PATH = os.path.join(MODEL_DIR, "expense_classifier.pkl")
ANOMALY_MODEL_PATH = os.path.join(MODEL_DIR, "anomaly_detector.pkl")

os.makedirs(MODEL_DIR, exist_ok=True) 

# ─── Training Data ───────────────────────────────────────────────────────────

TRAINING_DATA = [
    ("office rent payment", "Rent & Utilities"),
    ("electricity bill", "Rent & Utilities"),
    ("internet broadband bill", "Rent & Utilities"),
    ("water bill payment", "Rent & Utilities"),
    ("software subscription saas", "Software & Tools"),
    ("aws cloud services", "Software & Tools"),
    ("google workspace license", "Software & Tools"),
    ("antivirus renewal", "Software & Tools"),
    ("salary payroll payment", "Salaries & Payroll"),
    ("employee wages", "Salaries & Payroll"),
    ("contractor payment freelance", "Salaries & Payroll"),
    ("fuel petrol diesel", "Travel & Transport"),
    ("cab uber ola ride", "Travel & Transport"),
    ("flight ticket airfare", "Travel & Transport"),
    ("train ticket rail", "Travel & Transport"),
    ("hotel accommodation stay", "Travel & Transport"),
    ("stationery paper pen", "Office Supplies"),
    ("printer ink toner", "Office Supplies"),
    ("office furniture desk chair", "Office Supplies"),
    ("marketing advertising google ads", "Marketing"),
    ("facebook instagram campaign", "Marketing"),
    ("brochure printing design", "Marketing"),
    ("laptop computer hardware", "Equipment"),
    ("mobile phone purchase", "Equipment"),
    ("projector equipment", "Equipment"),
    ("food lunch dinner meal", "Meals & Entertainment"),
    ("restaurant client dinner", "Meals & Entertainment"),
    ("team outing event", "Meals & Entertainment"),
    ("tax gst filing fee", "Professional Services"),
    ("audit accounting fee", "Professional Services"),
    ("legal consultant lawyer", "Professional Services"),
    ("bank charges interest", "Banking & Finance"),
    ("loan emi repayment", "Banking & Finance"),
    ("insurance premium policy", "Banking & Finance"),
    ("product sales revenue", "Sales Revenue"),
    ("service income consulting", "Sales Revenue"),
    ("invoice payment received", "Sales Revenue"),
    ("raw material purchase", "Inventory & Raw Materials"),
    ("goods stock inventory", "Inventory & Raw Materials"),
    ("packaging material supply", "Inventory & Raw Materials"),
]

TRAINING_TEXTS = [t[0] for t in TRAINING_DATA]
TRAINING_LABELS = [t[1] for t in TRAINING_DATA]


# ─── Classifier ──────────────────────────────────────────────────────────────

def _load_or_train_classifier() -> Pipeline:
    """Load classifier from disk or train a fresh one."""
    if os.path.exists(CLASSIFIER_PATH):
        try:
            with open(CLASSIFIER_PATH, "rb") as f:
                model = pickle.load(f)
            logger.info("Loaded expense classifier from disk")
            return model
        except Exception as e:
            logger.warning("Failed to load classifier: %s. Retraining...", str(e))

    logger.info("Training expense classifier...")
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
        ("clf", MultinomialNB(alpha=0.1)),
    ])
    pipeline.fit(TRAINING_TEXTS, TRAINING_LABELS)

    try:
        with open(CLASSIFIER_PATH, "wb") as f:
            pickle.dump(pipeline, f)
        logger.info("Classifier saved to %s", CLASSIFIER_PATH)
    except Exception as e:
        logger.warning("Could not save classifier: %s", str(e))

    return pipeline


_classifier: Optional[Pipeline] = None


def get_classifier() -> Pipeline:
    global _classifier
    if _classifier is None:
        _classifier = _load_or_train_classifier()
    return _classifier


def classify_expense(description: str, amount: float) -> Tuple[str, float]:
    """Classify a transaction description into a category."""
    try:
        clf = get_classifier()
        proba = clf.predict_proba([description])[0]
        best_idx = np.argmax(proba)
        category = str(clf.classes_[best_idx])
        confidence = float(proba[best_idx])
        logger.debug("Classified '%s' → '%s' (conf=%.2f)", description, category, confidence)
        return category, confidence
    except Exception as e:
        logger.error("ML classification error: %s", str(e))
        return "Uncategorized", 0.0


# ─── Anomaly Detection ───────────────────────────────────────────────────────

def detect_anomaly(
    db: Session,
    user_id: int,
    amount: float,
    transaction_type: TransactionType,
    contamination: float = 0.1,
) -> Tuple[bool, float]:
    """Detect if a transaction amount is anomalous for this user."""
    try:
        # Fetch user's historical amounts
        historical = (
            db.query(Transaction.amount)
            .filter(
                Transaction.user_id == user_id,
                Transaction.transaction_type == transaction_type,
            )
            .limit(500)
            .all()
        )

        amounts = [float(r.amount) for r in historical]

        if len(amounts) < 10:
            # Not enough data
            return False, 0.0

        amounts_arr = np.array(amounts).reshape(-1, 1)
        model = IsolationForest(contamination=contamination, random_state=42)
        model.fit(amounts_arr)

        score = model.decision_function([[amount]])[0]
        prediction = model.predict([[amount]])[0]  # -1 = anomaly, 1 = normal

        is_anomaly = bool(prediction == -1)
        # Normalize score to 0-1 range (higher = more anomalous)
        anomaly_score = float(max(0.0, min(1.0, (-score + 0.5))))

        logger.debug(
            "Anomaly detection: amount=%.2f is_anomaly=%s score=%.3f",
            amount, is_anomaly, anomaly_score
        )
        return is_anomaly, float(round(anomaly_score, 3))

    except Exception as e:
        logger.error("Anomaly detection error: %s", str(e))
        return False, 0.0


# ─── Batch Re-classification ─────────────────────────────────────────────────

def batch_classify_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """Re-classify a list of transactions in bulk."""
    clf = get_classifier()
    for txn in transactions:
        try:
            proba = clf.predict_proba([txn.description])[0]
            best_idx = np.argmax(proba)
            txn.ml_category = str(clf.classes_[best_idx])
            txn.ml_confidence = float(proba[best_idx])
        except Exception as e:
            logger.warning("Batch classify failed for txn %d: %s", txn.id, str(e))
    return transactions