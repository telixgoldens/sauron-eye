import random
import secrets
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text  # <-- Added 'text' import
from sqlalchemy.orm import sessionmaker
from database.schema import Transaction, Base
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ Error: DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# --- THE SUSPECT ---
SUSPECT_ADDR = "bbn1badguy9999999999999999999999999999999"
LAUNDER_A = "bbn1launderA..............................."

print("🕵️ Planting evidence in the database...")

try:
    # --- FIX IS HERE: Wrapped in text() ---
    session.execute(text("TRUNCATE TABLE transactions"))
    session.commit()

    # 2. Create 'Fan Out' Pattern (Suspect -> Many Mules)
    # Suspect sends money to 10 different people in 5 minutes
    base_time = datetime.now() - timedelta(hours=2)

    for i in range(12):
        tx = Transaction(
            tx_hash=f"TX_FANOUT_{i}",
            height=50000 + i,
            sender=SUSPECT_ADDR,
            amount=5000, # 5000 BBN each
            timestamp=base_time + timedelta(minutes=i)
        )
        session.add(tx)

    # 3. Create 'Wash Trading' Pattern 
    # Cycle 1
    session.add(Transaction(tx_hash="TX_WASH_1", height=50100, sender=SUSPECT_ADDR, amount=10000, timestamp=base_time + timedelta(hours=1)))
    session.add(Transaction(tx_hash="TX_WASH_2", height=50101, sender=LAUNDER_A, amount=10000, timestamp=base_time + timedelta(hours=1, minutes=5)))

    # 4. Add Noise (Normal Users)
    for i in range(50):
        session.add(Transaction(
            tx_hash=secrets.token_hex(16),
            height=random.randint(40000, 49000),
            sender=f"bbn1user{secrets.token_hex(4)}",
            amount=random.randint(1, 100),
            timestamp=base_time - timedelta(minutes=random.randint(0, 1000))
        ))

    session.commit()
    print(f"✅ CRIME SCENE GENERATED.")
    print(f"🎯 Target Suspect Address: {SUSPECT_ADDR}")

except Exception as e:
    session.rollback()
    print(f"❌ Error: {e}")
finally:
    session.close()