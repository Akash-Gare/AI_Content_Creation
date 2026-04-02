import asyncio
from app.image.sd_client import generate_image
from app.database.db import SessionLocal
from app.database.models import PosterRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def generate_image_job(request_id: int):
    db = SessionLocal()
    try:
        request = db.query(PosterRequest).filter(PosterRequest.id == request_id).first()
        if not request or not request.image_prompt:
            logger.error(f"Request {request_id} or image prompt not found")
            return

        request.status = "Generating Image"
        db.commit()

        # Call SD API
        image_path = await generate_image(request.image_prompt)

        if image_path:
            request.image_url = image_path
            request.status = "Generated"
            logger.info(f"Image generated for request {request_id}: {image_path}")
        else:
            request.status = "Failed Image Generation"
            logger.error(f"Failed to generate image for request {request_id}")

        db.commit()
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in image_worker for request {request_id}: {error_msg}")
        if request:
            request.status = "Failed"
            request.last_error = error_msg
            db.commit()
    finally:
        db.close()
