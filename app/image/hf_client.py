import aiohttp
import asyncio
import os
import uuid
import time
from app.config import HF_API_KEY
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default model for Hugging Face Inference API
DEFAULT_HF_MODEL = "black-forest-labs/FLUX.1-schnell"

async def generate_image_hf(prompt: str, model: str = DEFAULT_HF_MODEL) -> str:
    """
    Generates an image using Hugging Face Inference API.
    """
    if not HF_API_KEY or HF_API_KEY.strip() == "":
        logger.error("Hugging Face API Key is missing.")
        raise ValueError("HF_API_KEY not configured.")

    logger.info(f"Using Hugging Face Inference API with model: {model}...")
    
    os.makedirs("images", exist_ok=True)
    filename = f"images/{uuid.uuid4()}.jpg"
    
    api_url = f"https://router.huggingface.co/hf-inference/models/{model}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload, timeout=120) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(filename, "wb") as f:
                        f.write(content)
                    logger.info(f"Hugging Face image saved: {filename}")
                    return filename
                elif response.status == 503:
                    # Model might be loading
                    error_data = await response.json()
                    estimated_time = error_data.get("estimated_time", 20)
                    logger.warning(f"HF Model is loading. Retrying in {estimated_time}s...")
                    await asyncio.sleep(estimated_time)
                    return await generate_image_hf(prompt, model)
                else:
                    error_text = await response.text()
                    logger.error(f"Hugging Face API failed: {response.status} - {error_text}")
                    raise ConnectionError(f"HF API failed: {response.status}")
    except Exception as e:
        logger.error(f"HF image generation failed: {e}")
        raise e
