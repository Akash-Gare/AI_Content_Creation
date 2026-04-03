import os
import sys

# Ensure virtual environment site-packages are in the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
VENV_PATH = os.path.join(ROOT_DIR, "aiccenv", "Lib", "site-packages")
if VENV_PATH not in sys.path:
    sys.path.append(VENV_PATH)

from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

from app.database.db import get_db, SessionLocal, Base, engine
from app.database import models
from app.workers.content_worker import generate_content_job
from app.workers.image_worker import generate_image_job
from app.workers.posting_worker import post_to_instagram_job
from app.scheduler.scheduler import start_scheduler
from app.utils.logger import get_logger
from app.utils.auth import verify_password, get_password_hash


from fastapi.middleware.cors import CORSMiddleware

logger = get_logger(__name__)
app = FastAPI(title="AI Poster System")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files using absolute paths to root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

app.mount("/frontend", StaticFiles(directory=os.path.join(ROOT_DIR, "frontend")), name="frontend")
app.mount("/images", StaticFiles(directory=os.path.join(ROOT_DIR, "images")), name="images")

# Start worker/scheduler on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Poster System...")
    
    # Initialize DB (Move inside startup to prevent module-level hang)
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    try:
        start_scheduler()
        logger.info("Scheduler started successfully.")
    except Exception as e:
        logger.error(f"Scheduler failed to start: {e}")
        
    logger.info("AI Poster System is ready!")

class PosterCreate(BaseModel):
    topic: str
    style: str
    post_time: datetime

class UserRegister(BaseModel):
    full_name: str
    email: str
    password: str

@app.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == data.email).first()
    if existing_user:
        return {"error": "Email already registered"}
    
    hashed_password = get_password_hash(data.password)
    
    new_user = models.User(
        email=data.email,
        hashed_password=hashed_password,
        full_name=data.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Registration successful"}

class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        return {"error": "Invalid email or password"}
    
    if not verify_password(data.password, user.hashed_password):
        return {"error": "Invalid email or password"}
    
    return {
        "message": "Login successful",
        "user": {
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.post("/request-poster")
async def request_poster(data: PosterCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Store in DB
    new_request = models.PosterRequest(
        topic=data.topic,
        style=data.style,
        post_time=data.post_time,
        status="Pending"
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    # 2. Trigger worker chain in background
    background_tasks.add_task(process_full_chain, new_request.id)

    return {"message": "Request queued", "request_id": new_request.id}

async def process_full_chain(request_id: int):
    """Orchestrates content then image generation."""
    # Run content job (Sync)
    generate_content_job(request_id)
    
    # Run image job (Async)
    await generate_image_job(request_id)

@app.get("/status/{request_id}")
def get_status(request_id: int, db: Session = Depends(get_db)):
    request = db.query(models.PosterRequest).filter(models.PosterRequest.id == request_id).first()
    if not request:
        return {"error": "Not found"}
    return {
        "id": request.id,
        "status": request.status,
        "title": request.title,
        "post_time": request.post_time,
        "image_url": request.image_url
    }

@app.post("/post-to-instagram/{request_id}")
async def trigger_instagram_post(request_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    request = db.query(models.PosterRequest).filter(models.PosterRequest.id == request_id).first()
    if not request:
        return {"error": "Request not found"}
    
    if request.status != "Generated":
        return {"error": f"Request status is {request.status}, must be 'Generated' to post."}

    background_tasks.add_task(post_to_instagram_job, request_id)
    return {"message": "Posting task queued", "request_id": request_id}

@app.get("/calendar")
def get_calendar(db: Session = Depends(get_db)):
    """Returns a list of all posts sorted by post_time."""
    requests = db.query(models.PosterRequest).order_by(models.PosterRequest.post_time.asc()).all()
    
    calendar = []
    for r in requests:
        calendar.append({
            "id": r.id,
            "topic": r.topic,
            "status": r.status,
            "post_time": r.post_time,
            "image_ready": bool(r.image_url),
            "image_url": r.image_url
        })
    
    return {
        "current_time_utc": datetime.utcnow(),
        "total_requests": len(calendar),
        "schedule": calendar
    }

class UpdateTime(BaseModel):
    new_post_time: datetime

@app.patch("/update-post-time/{request_id}")
def update_post_time(request_id: int, data: UpdateTime, db: Session = Depends(get_db)):
    request = db.query(models.PosterRequest).filter(models.PosterRequest.id == request_id).first()
    if not request:
        return {"error": "Not found"}
    
    request.post_time = data.new_post_time
    db.commit()
    
    return {"message": "Schedule updated", "request_id": request_id, "new_time": request.post_time}