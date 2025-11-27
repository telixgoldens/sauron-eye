import sys
import random
import secrets
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.schema import Transaction, Base
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL not found in .env")
    sys.exit(1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

print(" Initializing Cluster Generator...")

HUB_ADDRESS = "bbn1_MASTER_MIND_999999999999999999999"

BOT_ARMY = [f"bbn1_bot_wallet_{i}_{secrets.token_hex(4)}" for i in range(20)]

NOW = datetime.now()

try:
    print(" Clearing old data...")
    session.execute(text("TRUNCATE TABLE transactions"))
    session.commit()

    print(f"Weaving a cluster of {len(BOT_ARMY)} bots around {HUB_ADDRESS}...")

    for i, bot in enumerate(BOT_ARMY):
        tx = Transaction(
            tx_hash=f"TX_FUNDING_{i}_{secrets.token_hex(4)}",
            height=60000 + i,
            sender=HUB_ADDRESS, 
            amount=random.randint(1000, 5000), 
            timestamp=NOW - timedelta(minutes=60) + timedelta(seconds=i*10)
        )
        session.add(tx)

    tx_count = 0
    for i, bot in enumerate(BOT_ARMY):
        for j in range(random.randint(3, 5)):
            tx = Transaction(
                tx_hash=f"TX_BOT_ACT_{i}_{j}",
                height=60050 + tx_count,
                sender=bot, 
                amount=random.randint(10, 50), 
                timestamp=NOW - timedelta(minutes=30) + timedelta(minutes=j)
            )
            session.add(tx)
            tx_count += 1

   
    print(" Adding background noise...")
    for i in range(50):
        session.add(Transaction(
            tx_hash=secrets.token_hex(16),
            height=random.randint(59000, 60000),
            sender=f"bbn1_civilian_{secrets.token_hex(4)}",
            amount=random.randint(1, 100),
            timestamp=NOW - timedelta(minutes=random.randint(0, 120))
        ))

    session.commit()
    print("DATA INJECTION COMPLETE.")
    print("-" * 40)
    print(f"TARGET FOR INSPECTOR: {HUB_ADDRESS}")
    print("-" * 40)

except Exception as e:
    session.rollback()
    print(f"Error: {e}")
finally:
    session.close()