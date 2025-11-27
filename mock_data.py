import sys
import random
import secrets
from datetime import datetime, timedelta
from sqlalchemy import create_engine
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

print("🏭 Starting Synthetic Data Generator...")

WHALES = [
    "bbn1w5c290t8305848205830158205820582058201", 
    "bbn1x9999999999999999999999999999999999999",
    "bbn100000000000000000000000000000000000000", 
]

def random_address():
    return f"bbn1{secrets.token_hex(19)}"

START_HEIGHT = 350000
NOW = datetime.now()

count = 0
try:
    for i in range(1000):
        time_offset = random.randint(0, 60 * 24 * 7) 
        tx_time = NOW - timedelta(minutes=time_offset)
        
        if random.random() < 0.10:
            sender = random.choice(WHALES)
            amount = random.randint(100, 5000) 
        else:
            sender = random_address()
            amount = random.randint(1, 50) 

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
    print(f"Successfully injected {count} synthetic transactions into the DB!")
    print("You are now ready to build the Dashboard.")

except Exception as e:
    session.rollback()
    print(f"Error: {e}")
finally:
    session.close()