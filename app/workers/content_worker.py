from app.llm.generator import generate_poster_json
from app.utils.parser import parse_llm_json
from app.database.db import SessionLocal
from app.database.models import PosterRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)

def generate_content_job(request_id: int):
    db = SessionLocal()
    try:
        request = db.query(PosterRequest).filter(PosterRequest.id == request_id).first()
        if not request:
            logger.error(f"Request {request_id} not found")
            return

        request.status = "Generating Content"
        db.commit()

        # Call LLM
        json_str = generate_poster_json(request.topic, request.style)
        data = parse_llm_json(json_str)

        if data:
            request.title = data.get("title")
            request.caption = data.get("caption")
            request.call_to_action = data.get("call_to_action")
            request.hashtags = data.get("hashtags")
            request.image_prompt = data.get("image_prompt")
            request.design_instructions = data.get("design_instructions")
            request.status = "Content Generated"
            logger.info(f"Content generated for request {request_id}")
        else:
            request.status = "Failed Content Generation"
            logger.error(f"Failed to parse JSON for request {request_id}")

        db.commit()
    except Exception as e:
        logger.error(f"Error in content_worker for request {request_id}: {e}")
        if request:
            request.status = "Failed"
            db.commit()
    finally:
        db.close()
