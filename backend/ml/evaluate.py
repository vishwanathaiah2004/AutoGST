"""
AutoGST Pro — ML Model Evaluation
Run after training to see detailed accuracy metrics.

Usage:
  cd backend
  venv\Scripts\activate
  python ml/evaluate.py
"""
import os, sys, pickle
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
MODELS_DIR = Path(__file__).parent / "models"

def evaluate():
    print("\n=== AutoGST Pro — Model Evaluation ===\n")

    # ── Classifier tests ──────────────────────────────────────────────────────
    clf_path = MODELS_DIR / "expense_classifier.pkl"
    if not clf_path.exists():
        print("❌ Classifier not found. Run: python ml/train.py first")
        return

    with open(clf_path, "rb") as f:
        clf = pickle.load(f)

    print("EXPENSE CLASSIFIER")
    print("-" * 40)
    tests = [
        ("monthly office rent payment hyderabad",  "Rent & Utilities"),
        ("aws ec2 server hosting invoice",          "Software & Tools"),
        ("employee salary payroll february",        "Salaries & Payroll"),
        ("indigo flight ticket mumbai bangalore",   "Travel & Transport"),
        ("facebook google ads digital marketing",   "Marketing"),
        ("printer paper stationery purchase",       "Office Supplies"),
        ("macbook pro m3 laptop purchase",          "Equipment"),
        ("ca audit fees annual compliance",         "Professional Services"),
        ("hdfc bank loan emi repayment",            "Banking & Finance"),
        ("team lunch client dinner meeting",        "Meals & Entertainment"),
        ("software project invoice payment received", "Sales Revenue"),
        ("raw material electronic component purchase", "Inventory & Raw Materials"),
        ("business consulting advisory services",   "Consulting Income"),
        ("product sale goods delivery invoice",     "Product Sales"),
    ]

    correct = 0
    for desc, expected in tests:
        pred = clf.predict([desc])[0]
        proba = max(clf.predict_proba([desc])[0])
        status = "✓" if pred == expected else "✗"
        if pred == expected: correct += 1
        print(f"  {status} '{desc[:40]}'")
        print(f"    Expected: {expected}")
        if pred != expected:
            print(f"    Got:      {pred} ({proba*100:.0f}% confidence)")
        else:
            print(f"    Correct ({proba*100:.0f}% confidence)")

    acc = correct / len(tests)
    print(f"\nTest accuracy: {correct}/{len(tests)} = {acc*100:.0f}%")

    if acc < 0.7:
        print("\n⚠ Accuracy below 70%. Add more training data to training_data.csv")
        print("  Aim for 100+ examples per category.")
    elif acc < 0.85:
        print("\n💡 Good start. More training data will improve accuracy further.")
    else:
        print("\n✅ Great accuracy! Model is production ready.")

    # ── Anomaly detector tests ────────────────────────────────────────────────
    ano_path = MODELS_DIR / "anomaly_detector.pkl"
    if not ano_path.exists():
        print("\n❌ Anomaly detector not found.")
        return

    with open(ano_path, "rb") as f:
        ano = pickle.load(f)

    print("\n\nANOMALY DETECTOR")
    print("-" * 40)
    amounts_to_test = [
        (1000,    "should be normal   "),
        (5000,    "should be normal   "),
        (25000,   "should be normal   "),
        (80000,   "should be normal   "),
        (150000,  "should be normal   "),
        (500000,  "might be anomaly   "),
        (1000000, "likely anomaly     "),
        (5000000, "definite anomaly   "),
        (50,      "very low - anomaly "),
        (200,     "very low - anomaly "),
    ]
    for amount, note in amounts_to_test:
        score = ano.decision_function([[amount]])[0]
        pred  = ano.predict([[amount]])[0]
        flag  = "🚨 ANOMALY" if pred == -1 else "  normal  "
        print(f"  ₹{amount:>10,.0f}  {note}  {flag}  (score: {score:.3f})")

    print("\n=== Evaluation complete ===")


if __name__ == "__main__":
    evaluate()


