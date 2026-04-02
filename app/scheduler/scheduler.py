from apscheduler.schedulers.background import BackgroundScheduler
from app.database.db import SessionLocal
from app.database.models import PosterRequest
from app.workers.posting_worker import post_to_instagram_job
from app.ml.timing_model import predict_best_time, train_model
from app.utils.logger import get_logger
from datetime import datetime, timedelta
import asyncio

logger = get_logger(__name__)

def check_and_post_job():
    """Job that checks for 'image_ready' posters ready for post_time."""
    logger.info("Scheduler: Checking for pending posts...")
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        # 1. Auto-assign best posting time for ready posts with NO scheduled_time
        unscheduled_posters = db.query(PosterRequest).filter(
            PosterRequest.status.in_(["image_ready", "Generated"]),
            PosterRequest.post_time.is_(None)
        ).all()

        for poster in unscheduled_posters:
            best_hour = predict_best_time()
            # Assign for today or tomorrow depending on current hour
            target_time = now.replace(hour=best_hour, minute=0, second=0, microsecond=0)
            if target_time < now:
                target_time += timedelta(days=1)
            
            poster.post_time = target_time
            logger.info(f"Auto-assigned best posting time {target_time} for request {poster.id}")
        
        db.commit()

        # 2. Fetch posts that are ready to be posted right now
        ready_posters = db.query(PosterRequest).filter(
            PosterRequest.status.in_(["image_ready", "Generated"]),
            PosterRequest.post_time <= now
        ).all()

        if not ready_posters:
            logger.info("Scheduler: No posts due at this time.")
            return

        for poster in ready_posters:
            logger.info(f"Scheduler: Triggering auto-post for request {poster.id} (Scheduled for {poster.post_time})")
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(post_to_instagram_job(poster.id))
                loop.close()
            except Exception as inner_e:
                logger.error(f"Scheduler: Failed to trigger job for {poster.id}: {inner_e}")
                
    except Exception as e:
        logger.error(f"Scheduler: Main job failed: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Check every 5 minutes for posting
    scheduler.add_job(check_and_post_job, 'interval', minutes=5)
    
    # Add daily retraining job at midnight
    scheduler.add_job(train_model, 'cron', hour=0, minute=0)
    
    scheduler.start()
    logger.info("APScheduler started (with ML retraining job).")
