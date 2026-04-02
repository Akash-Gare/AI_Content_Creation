from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database.db import Base

class PosterRequest(Base):
    __tablename__ = "poster_requests"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    style = Column(String, nullable=False)
    post_time = Column(DateTime, nullable=False)
    status = Column(String, default="Pending") # Pending, Generating, image_ready, Posted, Failed
    
    # Performance Metrics
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)

    # LLM Generated Content
    title = Column(String, nullable=True)
    caption = Column(Text, nullable=True)
    call_to_action = Column(String, nullable=True)
    hashtags = Column(Text, nullable=True)
    image_prompt = Column(Text, nullable=True)
    design_instructions = Column(Text, nullable=True)
    
    # Final Output
    image_url = Column(String, nullable=True)
    last_error = Column(Text, nullable=True)
    

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)