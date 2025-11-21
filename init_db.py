# init_db.py
import os
from dotenv import load_dotenv
from database.schema import init_db

load_dotenv()
db_url = os.getenv("DATABASE_URL")
print(f"Connecting to: {db_url}")
init_db(db_url)
print("Database tables created successfully!")