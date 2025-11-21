import sys
import random
import secrets
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.schema import Transaction, Base
from dotenv import load_dotenv
import os

# Load Database
load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ Error: DATABASE_URL not found in .env")
    sys.exit(1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

print("🏭 Starting Synthetic Data Generator...")

# 1. Define some "Persona" Wallets
WHALES = [
    "bbn1w5c290t8305848205830158205820582058201", # Big Whale
    "bbn1x9999999999999999999999999999999999999", # Exchange Wallet
    "bbn100000000000000000000000000000000000000", # Foundation
]

# 2. Helper to generate random addresses
def random_address():
    return f"bbn1{secrets.token_hex(19)}"

# 3. Generate 1,000 Transactions over the last 7 days
START_HEIGHT = 350000
NOW = datetime.now()

count = 0
try:
    for i in range(1000):
        # Randomize time (spread over last 7 days)
        time_offset = random.randint(0, 60 * 24 * 7) # Minutes
        tx_time = NOW - timedelta(minutes=time_offset)
        
        # Decide Sender (10% chance it's a Whale)
        if random.random() < 0.10:
            sender = random.choice(WHALES)
            amount = random.randint(100, 5000) # Big amount
        else:
            sender = random_address()
            amount = random.randint(1, 50) # Small amount

        # Create Tx
        tx = Transaction(
            tx_hash=secrets.token_hex(32).upper(),
            height=START_HEIGHT + i,
            sender=sender,
            amount=amount,
            timestamp=tx_time
        )
        session.add(tx)
        count += 1
        
    session.commit()
    print(f"✅ Successfully injected {count} synthetic transactions into the DB!")
    print("🚀 You are now ready to build the Dashboard.")

except Exception as e:
    session.rollback()
    print(f"❌ Error: {e}")
finally:
    session.close()