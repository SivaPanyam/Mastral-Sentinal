import sys
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mastra_user:password@localhost:5432/mastra_sentinel")

def check_db_connection(retries=5, delay=5):
    engine = create_engine(DATABASE_URL)
    for i in range(retries):
        try:
            with engine.connect() as conn:
                print("Database connection successful!")
                return True
        except OperationalError:
            print(f"Database not ready. Retrying in {delay} seconds... ({i+1}/{retries})")
            time.sleep(delay)
    print("Could not connect to the database. Exiting.")
    sys.exit(1)

if __name__ == "__main__":
    check_db_connection()
