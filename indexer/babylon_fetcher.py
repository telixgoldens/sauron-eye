import sys
import asyncio
import httpx
import json
from datetime import datetime

# Fix for imports to find the database module
sys.path.append('.')

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database.schema import Base, Transaction
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class BabylonIndexer:
    def __init__(self):
        self.BASE_URL = os.getenv("BABYLON_API_URL", "https://babylon-testnet-api.nodes.guru")
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL not found in .env")
            
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    async def fetch_latest_block(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.BASE_URL}/cosmos/base/tendermint/v1beta1/blocks/latest", timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                return int(data['block']['header']['height'])
            except Exception as e:
                print(f"⚠️ Error fetching latest block: {e}")
                return None

    async def fetch_txs(self, height):
        async with httpx.AsyncClient() as client:
            try:
                # Fetch both the Transaction Data (txs) and the Response Data (tx_responses)
                resp = await client.get(f"{self.BASE_URL}/cosmos/tx/v1beta1/txs?events=tx.height={height}", timeout=10.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                print(f"⚠️ Error fetching txs for block {height}: {e}")
                return None

    def extract_sender(self, tx_body):
        """Helper to find the address depending on the message type"""
        try:
            messages = tx_body.get('body', {}).get('messages', [])
            if not messages:
                return "unknown"
            
            msg = messages[0]
            # Check common Cosmos keys
            if 'sender' in msg: return msg['sender']
            if 'from_address' in msg: return msg['from_address']
            if 'delegator_address' in msg: return msg['delegator_address']
            
            # Check Babylon specific keys
            if 'staker_address' in msg: return msg['staker_address']
            if 'signer' in msg: return msg['signer']
            
            return "unknown"
        except Exception:
            return "unknown"

    async def run(self):
        latest_height = await self.fetch_latest_block()
        if not latest_height:
            return

        print(f"🏁 Latest Height: {latest_height}")
        print("📡 Scanning for transactions...")

        session = self.Session()
        
        # Scan 100 blocks back
        for h in range(latest_height, latest_height - 100, -1):
            print(f"Processing Block {h}...", end="\r")
            
            data = await self.fetch_txs(h)
            
            if data and 'tx_responses' in data and len(data['tx_responses']) > 0:
                # Get the parallel lists
                responses = data.get('tx_responses', [])
                tx_bodies = data.get('txs', [])
                
                print(f"\n⚡ Found {len(responses)} Transactions in Block {h}")

                # Loop through them safely
                for i, resp in enumerate(responses):
                    try:
                        tx_hash = resp.get('txhash')
                        timestamp_str = resp.get('timestamp', datetime.now().isoformat())
                        
                        # Try to get the body if it exists at the same index
                        sender = "unknown"
                        if i < len(tx_bodies):
                            sender = self.extract_sender(tx_bodies[i])

                        # Create DB Object
                        new_tx = Transaction(
                            tx_hash=tx_hash,
                            height=h,
                            sender=sender,
                            amount=0, # Parsing amount is complex, defaulting to 0 for now
                            timestamp=datetime.now() # Using current time as fallback
                        )
                        
                        # Save to DB safely
                        try:
                            session.merge(new_tx) # merge handles duplicates automatically
                            session.commit()
                            print(f"   ✅ Saved: {tx_hash[:10]}... | Sender: {sender[:10]}...")
                        except Exception as db_err:
                            session.rollback()
                            print(f"   ❌ DB Error: {db_err}")

                    except Exception as e:
                        print(f"   ⚠️ Parsing Error: {e}")
                        continue
            
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    indexer = BabylonIndexer()
    try:
        asyncio.run(indexer.run())
    except KeyboardInterrupt:
        print("\nStopped by user.")