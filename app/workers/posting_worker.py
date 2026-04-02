from datetime import datetime
from app.posting.instagram import post_to_instagram
from app.database.db import SessionLocal
from app.database.models import PosterRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def post_to_instagram_job(request_id: int):
    """Worker job to post to Instagram. Now supports synchronous Selenium posting."""
    db = SessionLocal()
    request = None
    try:
        request = db.query(PosterRequest).filter(PosterRequest.id == request_id).first()
        if not request:
            logger.error(f"Request {request_id} not found")
            return

        image_path = request.image_url # Assuming image_url stored the local path or URL
        if not image_path:
            logger.error(f"No image path for request {request_id}")
            request.status = "Failed"
            request.last_error = "Missing image path"
            db.commit()
            return

        request.status = "Posting"
        db.commit()

        # Combine caption and hashtags
        full_caption = request.caption or ""
        if request.hashtags:
            full_caption += f"\n\n{request.hashtags}"

        # Call Instagram posting service (Selenium - synchronous)
        # We run it in a thread if needed, but since this is an async worker, 
        # let's just call it directly as it's the main task here.
        success = post_to_instagram(
            image_path=image_path,
            caption=full_caption
        )

        if success:
            request.status = "Posted"
            request.posted_at = datetime.utcnow()
            logger.info(f"Successfully posted request {request_id} to Instagram")
        else:
            request.status = "Failed"
            logger.error(f"Failed to post request {request_id} to Instagram")

        db.commit()
    except Exception as e:
        logger.error(f"Error in posting_worker for request {request_id}: {e}")
        if request:
            request.status = "Failed"
            request.last_error = str(e)
            db.commit()
    finally:
        db.close()
