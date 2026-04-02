from app.database.db import SessionLocal
from app.database import models
from app.utils.auth import get_password_hash

def seed_user():
    db = SessionLocal()
    try:
        # Check if user already exists
        user = db.query(models.User).filter(models.User.email == "admin@aiposter.com").first()
        if user:
            print("Admin user already exists.")
            return

        # Create admin user
        admin_user = models.User(
            email="admin@aiposter.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User"
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error seeding user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_user()
