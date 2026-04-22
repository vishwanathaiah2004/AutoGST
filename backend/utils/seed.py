"""
Seed the database with sample categories, a demo user, and sample transactions.
Run: python utils/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from decimal import Decimal
import random
from config.database import SessionLocal, engine, Base
from models.models import User, Category, Transaction, TransactionType, GSTType
from services.auth_service import hash_password
from services.gst_service import calculate_gst

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ── Categories ──────────────────────────────────────────
        categories_data = [
            ("Sales Revenue", TransactionType.income, 18, "9999"),
            ("Consulting Income", TransactionType.income, 18, "9983"),
            ("Product Sales", TransactionType.income, 12, "8471"),
            ("Office Rent", TransactionType.expense, 18, "9972"),
            ("Software & Tools", TransactionType.expense, 18, "8523"),
            ("Salaries & Payroll", TransactionType.expense, 0, None),
            ("Travel & Transport", TransactionType.expense, 5, "9964"),
            ("Marketing", TransactionType.expense, 18, "9983"),
            ("Office Supplies", TransactionType.expense, 12, "4820"),
            ("Professional Services", TransactionType.expense, 18, "9982"),
            ("Banking & Finance", TransactionType.expense, 18, "9971"),
            ("Meals & Entertainment", TransactionType.expense, 5, "9963"),
            ("Equipment", TransactionType.expense, 18, "8471"),
            ("Inventory & Raw Materials", TransactionType.expense, 12, "3926"),
        ]

        categories = {}
        for name, txn_type, gst_rate, hsn in categories_data:
            existing = db.query(Category).filter(Category.name == name).first()
            if not existing:
                cat = Category(name=name, type=txn_type, gst_rate=Decimal(str(gst_rate)), hsn_sac_code=hsn)
                db.add(cat)
                db.flush()
                categories[name] = cat
            else:
                categories[name] = existing

        db.commit()
        logger.info("✓ Categories seeded: %d", len(categories))

        # ── Demo User ────────────────────────────────────────────
        demo_email = "demo@autogst.pro"
        user = db.query(User).filter(User.email == demo_email).first()
        if not user:
            user = User(
                email=demo_email,
                full_name="Rahul Sharma",
                hashed_password=hash_password("Demo@1234"),
                gstin="27AAPFU0939F1ZV",
                pan="AAPFU0939F",
                business_name="TechVentures India Pvt Ltd",
                phone="+91-9876543210",
                role="user",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("✓ Demo user created: %s (password: Demo@1234)", demo_email)
        else:
            logger.info("✓ Demo user already exists")

        # ── Sample Transactions ──────────────────────────────────
        existing_count = db.query(Transaction).filter(Transaction.user_id == user.id).count()
        if existing_count > 0:
            logger.info("✓ Transactions already seeded (%d found)", existing_count)
            return

        today = date.today()
        transactions_data = [
            # Income
            ("Software development services", 150000, TransactionType.income, GSTType.CGST, 18, "TechCorp Solutions", "27AAACP1234F1Z5", "INV-2024-001", categories["Consulting Income"]),
            ("Annual SaaS license fee", 50000, TransactionType.income, GSTType.CGST, 18, "StartupXYZ", "29AABCS1234G1Z8", "INV-2024-002", categories["Sales Revenue"]),
            ("Product sale - Laptops (5 units)", 300000, TransactionType.income, GSTType.IGST, 12, "MegaMart Delhi", "07AAACM1234H1Z7", "INV-2024-003", categories["Product Sales"]),
            ("Consulting - digital transformation", 80000, TransactionType.income, GSTType.CGST, 18, "Finance Corp Ltd", "27AABCF1234J1Z1", "INV-2024-004", categories["Consulting Income"]),
            ("Website redesign project", 45000, TransactionType.income, GSTType.CGST, 18, "RetailBrand Pvt", None, "INV-2024-005", categories["Consulting Income"]),
            ("Mobile app development", 200000, TransactionType.income, GSTType.IGST, 18, "Startup Bangalore", "29AABCS5678K1Z2", "INV-2024-006", categories["Consulting Income"]),
            ("Training & workshops", 25000, TransactionType.income, GSTType.CGST, 18, "HR Solutions", None, "INV-2024-007", categories["Sales Revenue"]),

            # Expenses
            ("Monthly office rent - Andheri", 35000, TransactionType.expense, GSTType.CGST, 18, "Property Owners", "27AADCP1234L1Z3", None, categories["Office Rent"]),
            ("AWS cloud hosting - monthly", 15000, TransactionType.expense, GSTType.IGST, 18, "Amazon Web Services", None, "AWS-INV-10234", categories["Software & Tools"]),
            ("Employee salaries - October", 180000, TransactionType.expense, GSTType.exempt, 0, None, None, None, categories["Salaries & Payroll"]),
            ("Google Workspace annual plan", 8000, TransactionType.expense, GSTType.IGST, 18, "Google India", None, "GOOG-INV-5678", categories["Software & Tools"]),
            ("Facebook advertising campaign", 20000, TransactionType.expense, GSTType.IGST, 18, "Meta Platforms", None, "META-INV-9012", categories["Marketing"]),
            ("Business travel - Mumbai to Delhi flight", 12000, TransactionType.expense, GSTType.CGST, 5, "IndiGo Airlines", None, "6E-INV-3456", categories["Travel & Transport"]),
            ("CA audit fees - annual", 25000, TransactionType.expense, GSTType.CGST, 18, "A&B Associates", "27AABCA5678M1Z4", "CA-INV-001", categories["Professional Services"]),
            ("Office stationery and supplies", 5000, TransactionType.expense, GSTType.CGST, 12, "Office Depot", None, None, categories["Office Supplies"]),
            ("Client lunch meeting", 3500, TransactionType.expense, GSTType.CGST, 5, "The Oberoi Mumbai", None, None, categories["Meals & Entertainment"]),
            ("MacBook Pro - developer workstation", 180000, TransactionType.expense, GSTType.CGST, 18, "Apple India", None, "APL-INV-7890", categories["Equipment"]),
            ("Bank loan EMI repayment", 22000, TransactionType.expense, GSTType.exempt, 0, "HDFC Bank", None, None, categories["Banking & Finance"]),
            ("Raw material purchase - electronic components", 85000, TransactionType.expense, GSTType.CGST, 12, "Rajshree Electronics", "27AAACR1234N1Z5", "RE-INV-2345", categories["Inventory & Raw Materials"]),
            ("SEO and content marketing services", 18000, TransactionType.expense, GSTType.CGST, 18, "Digital Growth Agency", None, "DGA-INV-001", categories["Marketing"]),
        ]

        days_back = 90
        for i, (desc, amount, txn_type, gst_type, gst_rate, party, gstin, inv_no, category) in enumerate(transactions_data):
            days_ago = random.randint(0, days_back)
            txn_date = today - timedelta(days=days_ago)
            amt = Decimal(str(amount))
            rate = Decimal(str(gst_rate))

            gst_result = calculate_gst(amt, rate, gst_type)

            txn = Transaction(
                user_id=user.id,
                category_id=category.id,
                description=desc,
                amount=amt,
                transaction_type=txn_type,
                transaction_date=txn_date,
                gst_type=gst_type,
                gst_rate=rate,
                cgst_amount=gst_result["cgst_amount"],
                sgst_amount=gst_result["sgst_amount"],
                igst_amount=gst_result["igst_amount"],
                total_gst=gst_result["total_gst"],
                taxable_amount=gst_result["taxable_amount"],
                total_amount=gst_result["total_amount"],
                party_name=party,
                party_gstin=gstin,
                invoice_number=inv_no,
                source="manual",
                is_anomaly=False,
            )
            db.add(txn)

        db.commit()
        logger.info("✓ Sample transactions seeded: %d", len(transactions_data))
        logger.info("\n========================================")
        logger.info("SEED COMPLETE!")
        logger.info("  Demo login: demo@autogst.pro")
        logger.info("  Password:   Demo@1234")
        logger.info("========================================\n")

    except Exception as e:
        db.rollback()
        logger.error("Seed failed: %s", str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
