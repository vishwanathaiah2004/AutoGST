"""
AutoGST Pro — ML Training Script
Run this once to train and save both ML models:
  1. Expense Classifier  (TF-IDF + Naive Bayes)
  2. Anomaly Detector    (Isolation Forest)

Usage:
  cd backend
  venv\Scripts\activate         (Windows)
  source venv/bin/activate      (Mac/Linux)
  python ml/train.py
"""

import os, sys, pickle, logging
import numpy as np
import pandas as pd
from pathlib import Path

# ── make imports work from backend/ root ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("train")

DATA_DIR   = Path(__file__).parent / "data"
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFIER_PATH = MODELS_DIR / "expense_classifier.pkl"
ANOMALY_PATH    = MODELS_DIR / "anomaly_detector.pkl"

# ─── 14 Categories (must match what the app expects) ─────────────────────────
CATEGORIES = [
    "Rent & Utilities",
    "Software & Tools",
    "Salaries & Payroll",
    "Travel & Transport",
    "Marketing",
    "Office Supplies",
    "Equipment",
    "Professional Services",
    "Banking & Finance",
    "Meals & Entertainment",
    "Sales Revenue",
    "Inventory & Raw Materials",
    "Consulting Income",
    "Product Sales",
]

# ─── Built-in training data (used when no CSV is found) ──────────────────────
BUILTIN_DATA = [
    # Rent & Utilities
    ("office rent payment monthly", "Rent & Utilities"),
    ("electricity bill payment", "Rent & Utilities"),
    ("internet broadband bill", "Rent & Utilities"),
    ("water bill monthly", "Rent & Utilities"),
    ("office space lease", "Rent & Utilities"),
    ("building maintenance charge", "Rent & Utilities"),
    ("gas bill utility", "Rent & Utilities"),
    ("coworking space rent", "Rent & Utilities"),
    ("commercial property rent", "Rent & Utilities"),
    ("power bill electricity", "Rent & Utilities"),

    # Software & Tools
    ("aws cloud hosting monthly", "Software & Tools"),
    ("google workspace license", "Software & Tools"),
    ("software subscription saas", "Software & Tools"),
    ("antivirus renewal annual", "Software & Tools"),
    ("microsoft office 365", "Software & Tools"),
    ("slack premium subscription", "Software & Tools"),
    ("figma design tool", "Software & Tools"),
    ("github enterprise license", "Software & Tools"),
    ("zoom video conferencing", "Software & Tools"),
    ("notion team plan", "Software & Tools"),
    ("digitalocean server hosting", "Software & Tools"),
    ("adobe creative cloud", "Software & Tools"),

    # Salaries & Payroll
    ("employee salary payment", "Salaries & Payroll"),
    ("payroll monthly wages", "Salaries & Payroll"),
    ("contractor payment freelance", "Salaries & Payroll"),
    ("staff salary disbursement", "Salaries & Payroll"),
    ("bonus payment employee", "Salaries & Payroll"),
    ("consultant fees payment", "Salaries & Payroll"),
    ("worker wages weekly", "Salaries & Payroll"),
    ("hr payroll processing", "Salaries & Payroll"),

    # Travel & Transport
    ("flight ticket airfare booking", "Travel & Transport"),
    ("uber cab ride office", "Travel & Transport"),
    ("train ticket rail journey", "Travel & Transport"),
    ("hotel accommodation stay", "Travel & Transport"),
    ("petrol fuel diesel vehicle", "Travel & Transport"),
    ("ola cab client visit", "Travel & Transport"),
    ("airport taxi fare", "Travel & Transport"),
    ("business travel reimbursement", "Travel & Transport"),
    ("metro card recharge", "Travel & Transport"),
    ("parking fees office", "Travel & Transport"),

    # Marketing
    ("google ads campaign advertising", "Marketing"),
    ("facebook instagram ads marketing", "Marketing"),
    ("seo content writing", "Marketing"),
    ("brochure printing design", "Marketing"),
    ("marketing agency retainer", "Marketing"),
    ("email campaign mailchimp", "Marketing"),
    ("influencer marketing payment", "Marketing"),
    ("trade show exhibition fee", "Marketing"),
    ("linkedin premium ads", "Marketing"),
    ("youtube advertising campaign", "Marketing"),

    # Office Supplies
    ("stationery paper pen notebook", "Office Supplies"),
    ("printer ink toner cartridge", "Office Supplies"),
    ("office furniture desk chair", "Office Supplies"),
    ("whiteboard markers pens", "Office Supplies"),
    ("filing cabinet folders", "Office Supplies"),
    ("coffee tea pantry supplies", "Office Supplies"),
    ("cleaning supplies office", "Office Supplies"),
    ("tissue paper tissue boxes", "Office Supplies"),

    # Equipment
    ("laptop computer purchase", "Equipment"),
    ("macbook pro developer", "Equipment"),
    ("mobile phone iphone", "Equipment"),
    ("projector conference room", "Equipment"),
    ("printer scanner purchase", "Equipment"),
    ("server hardware rack", "Equipment"),
    ("external hard drive storage", "Equipment"),
    ("keyboard mouse peripherals", "Equipment"),
    ("camera equipment photography", "Equipment"),
    ("generator power backup", "Equipment"),

    # Professional Services
    ("ca audit fees annual", "Professional Services"),
    ("legal consultant lawyer fees", "Professional Services"),
    ("accounting bookkeeping service", "Professional Services"),
    ("tax filing gst return", "Professional Services"),
    ("compliance consultant charges", "Professional Services"),
    ("notary legal document charges", "Professional Services"),
    ("trademark registration fees", "Professional Services"),
    ("hr consulting services", "Professional Services"),

    # Banking & Finance
    ("bank loan emi repayment", "Banking & Finance"),
    ("credit card interest charge", "Banking & Finance"),
    ("insurance premium policy", "Banking & Finance"),
    ("bank charges processing fee", "Banking & Finance"),
    ("fd fixed deposit investment", "Banking & Finance"),
    ("overdraft interest bank", "Banking & Finance"),
    ("wire transfer fee bank", "Banking & Finance"),
    ("cheque book charges bank", "Banking & Finance"),

    # Meals & Entertainment
    ("client lunch dinner restaurant", "Meals & Entertainment"),
    ("team outing event", "Meals & Entertainment"),
    ("office party celebration", "Meals & Entertainment"),
    ("conference catering food", "Meals & Entertainment"),
    ("swiggy zomato food order", "Meals & Entertainment"),
    ("coffee meeting client", "Meals & Entertainment"),
    ("team dinner celebration", "Meals & Entertainment"),

    # Sales Revenue
    ("invoice payment received client", "Sales Revenue"),
    ("product sale revenue", "Sales Revenue"),
    ("service charge bill raised", "Sales Revenue"),
    ("online sales ecommerce", "Sales Revenue"),
    ("subscription revenue saas", "Sales Revenue"),
    ("project delivery payment", "Sales Revenue"),
    ("annual maintenance contract", "Sales Revenue"),
    ("licensing fee income", "Sales Revenue"),

    # Inventory & Raw Materials
    ("raw material purchase supplier", "Inventory & Raw Materials"),
    ("goods stock inventory", "Inventory & Raw Materials"),
    ("packaging material boxes", "Inventory & Raw Materials"),
    ("component spare part", "Inventory & Raw Materials"),
    ("wholesale purchase bulk", "Inventory & Raw Materials"),
    ("warehouse storage goods", "Inventory & Raw Materials"),
    ("manufacturing material supply", "Inventory & Raw Materials"),

    # Consulting Income
    ("consulting project income", "Consulting Income"),
    ("advisory fees received", "Consulting Income"),
    ("technical consulting charges", "Consulting Income"),
    ("strategy consulting payment", "Consulting Income"),
    ("business consulting revenue", "Consulting Income"),
    ("freelance consulting work", "Consulting Income"),

    # Product Sales
    ("product delivery sale invoice", "Product Sales"),
    ("goods sold customer", "Product Sales"),
    ("hardware sale b2b", "Product Sales"),
    ("retail product revenue", "Product Sales"),
    ("export sale shipment", "Product Sales"),
    ("marketplace sale amazon flipkart", "Product Sales"),
]


# ─── STEP 1: Load Training Data ───────────────────────────────────────────────

def load_training_data():
    """Load from CSV if exists, otherwise use built-in data."""
    csv_path = DATA_DIR / "training_data.csv"

    if csv_path.exists():
        log.info(f"Loading from {csv_path}...")
        df = pd.read_csv(csv_path)

        # Flexible column detection
        desc_col = next((c for c in df.columns if "desc" in c.lower() or "text" in c.lower() or "name" in c.lower()), None)
        cat_col  = next((c for c in df.columns if "cat" in c.lower() or "label" in c.lower() or "class" in c.lower()), None)

        if not desc_col or not cat_col:
            log.warning(f"Could not find description/category columns in CSV. Columns found: {list(df.columns)}")
            log.warning("Expected columns named 'description' and 'category'. Using built-in data.")
            return _builtin_df()

        df = df[[desc_col, cat_col]].rename(columns={desc_col: "description", cat_col: "category"})
        df = df.dropna()
        df["description"] = df["description"].astype(str).str.strip()
        df["category"]    = df["category"].astype(str).str.strip()
        df = df[df["description"].str.len() > 2]
        log.info(f"Loaded {len(df)} rows from CSV with {df['category'].nunique()} categories")
        return df
    else:
        log.info("No training_data.csv found — using built-in training data.")
        log.info(f"Tip: Put your CSV at {csv_path} for better accuracy.")
        return _builtin_df()


def _builtin_df():
    df = pd.DataFrame(BUILTIN_DATA, columns=["description", "category"])
    log.info(f"Using {len(df)} built-in training examples across {df['category'].nunique()} categories")
    return df


# ─── STEP 2: Train Expense Classifier ────────────────────────────────────────

def train_classifier(df: pd.DataFrame):
    log.info("\n--- Training Expense Classifier ---")

    X = df["description"].tolist()
    y = df["category"].tolist()

    # Show category distribution
    log.info("Category distribution:")
    for cat, count in df["category"].value_counts().items():
        bar = "█" * min(count, 40)
        log.info(f"  {cat[:30]:<30} {bar} ({count})")

    # Split for evaluation
    if len(X) >= 20:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None)
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    # Build pipeline: TF-IDF → Naive Bayes
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 3),      # unigrams, bigrams, trigrams
            max_features=10000,
            sublinear_tf=True,       # apply log normalization
            min_df=1,
            analyzer="word",
        )),
        ("clf", MultinomialNB(alpha=0.1)),
    ])

    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    log.info(f"\nAccuracy on test set: {acc*100:.1f}%")

    if len(set(y_test)) > 1:
        log.info("\nPer-category report:")
        log.info(classification_report(y_test, y_pred))

    # Test with sample predictions
    samples = [
        "office rent paid",
        "aws server bill",
        "employee salary march",
        "google ads facebook campaign",
        "laptop purchase apple",
    ]
    log.info("Sample predictions:")
    for s in samples:
        pred = pipeline.predict([s])[0]
        prob = max(pipeline.predict_proba([s])[0])
        log.info(f"  '{s}' → {pred} ({prob*100:.0f}%)")

    # Save
    with open(CLASSIFIER_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    log.info(f"\n✓ Classifier saved to {CLASSIFIER_PATH}")
    return pipeline


# ─── STEP 3: Train Anomaly Detector ──────────────────────────────────────────

def train_anomaly_detector():
    log.info("\n--- Training Anomaly Detector ---")

    csv_path = DATA_DIR / "amounts_data.csv"

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        amount_col = next((c for c in df.columns if "amount" in c.lower() or "value" in c.lower() or "price" in c.lower()), df.columns[0])
        amounts = df[amount_col].dropna().values.astype(float)
        log.info(f"Loaded {len(amounts)} amount records from {csv_path}")
    else:
        log.info("No amounts_data.csv found — generating synthetic training amounts.")
        # Realistic Indian business transaction amounts
        rng = np.random.default_rng(42)
        amounts = np.concatenate([
            rng.normal(5000,  2000,  200),   # small expenses
            rng.normal(25000, 8000,  300),   # medium transactions
            rng.normal(80000, 20000, 200),   # large invoices
            rng.normal(150000,40000, 100),   # big contracts
            [2000000, 1500000, 3000000, 500, 100],  # anomalies
        ])
        amounts = np.abs(amounts)

    amounts = amounts[amounts > 0].reshape(-1, 1)
    log.info(f"Amount stats: min=₹{amounts.min():.0f} median=₹{np.median(amounts):.0f} max=₹{amounts.max():.0f}")

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,  # assume 5% of transactions are anomalous
        random_state=42,
        max_features=1,
    )
    model.fit(amounts)

    # Quick check
    test_amounts = [[5000], [25000], [80000], [2000000], [100]]
    log.info("Sample anomaly scores:")
    for a in test_amounts:
        score = model.decision_function([a])[0]
        pred  = model.predict([a])[0]
        flag  = "ANOMALY" if pred == -1 else "normal"
        log.info(f"  ₹{a[0]:>10,.0f}  score={score:.3f}  → {flag}")

    with open(ANOMALY_PATH, "wb") as f:
        pickle.dump(model, f)
    log.info(f"\n✓ Anomaly detector saved to {ANOMALY_PATH}")
    return model


# ─── STEP 4: Validate saved models load correctly ────────────────────────────

def validate_models():
    log.info("\n--- Validating saved models ---")

    with open(CLASSIFIER_PATH, "rb") as f:
        clf = pickle.load(f)
    result = clf.predict(["laptop purchase equipment"])
    log.info(f"✓ Classifier loads OK → test prediction: '{result[0]}'")

    with open(ANOMALY_PATH, "rb") as f:
        ano = pickle.load(f)
    score = ano.decision_function([[50000]])[0]
    log.info(f"✓ Anomaly detector loads OK → test score: {score:.3f}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("=" * 55)
    log.info("AutoGST Pro — ML Training")
    log.info("=" * 55)

    df = load_training_data()
    train_classifier(df)
    train_anomaly_detector()
    validate_models()

    log.info("\n" + "=" * 55)
    log.info("TRAINING COMPLETE")
    log.info(f"Models saved to: {MODELS_DIR}")
    log.info("Restart the backend to use the new models:")
    log.info("  python main.py")
    log.info("=" * 55)
