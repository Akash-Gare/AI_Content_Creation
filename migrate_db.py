from sqlalchemy import text
from app.database.db import engine
from app.database.models import Base

def update_schema():
    print("Updating database schema...")
    try:
        with engine.connect() as conn:
            # Check if columns exist and add if missing
            columns_to_add = {
                'last_error': 'TEXT',
                'likes': 'INTEGER DEFAULT 0',
                'views': 'INTEGER DEFAULT 0',
                'posted_at': 'TIMESTAMP'
            }
            
            for col, col_type in columns_to_add.items():
                result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='poster_requests' AND column_name='{col}'"))
                if not result.fetchone():
                    print(f"Adding column '{col}' to 'poster_requests'...")
                    conn.execute(text(f"ALTER TABLE poster_requests ADD COLUMN {col} {col_type}"))
                    conn.commit()
                    print(f"Column '{col}' added successfully.")
                else:
                    print(f"Column '{col}' already exists.")
    except Exception as e:
        print(f"Error updating schema: {e}")

if __name__ == "__main__":
    update_schema()
