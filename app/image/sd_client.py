import os
import uuid
import aiohttp
import base64
import urllib.parse
from app.config import SD_API_URL, MOCK_SD, USE_POLLINATIONS, HF_API_KEY
from app.utils.logger import get_logger
from app.image.hf_client import generate_image_hf
from PIL import Image, ImageDraw, ImageFont

logger = get_logger(__name__)

async def generate_image_pollinations(prompt: str, filename: str) -> str:
    """
    Generates an image using Pollinations.ai (Free API).
    """
    logger.info(f"Using Pollinations.ai for image generation...")
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://pollinations.ai/p/{encoded_prompt}?width=768&height=768&model=flux&nologo=true"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(filename, "wb") as f:
                        f.write(content)
                    logger.info(f"Pollinations image saved: {filename}")
                    return filename
                else:
                    raise ConnectionError(f"Pollinations API failed with status {response.status}")
    except Exception as e:
        logger.error(f"Pollinations generation failed: {e}")
        raise e

async def generate_image(prompt: str) -> str:
    """
    Generates a poster using prioritized AI APIs.
    Priority: Local SD -> Hugging Face -> Pollinations
    """
    os.makedirs("images", exist_ok=True)
    filename = f"images/{uuid.uuid4()}.jpg"
    
    if MOCK_SD:
        logger.info(f"MOCK_SD is enabled. Generating placeholder image for prompt: {prompt[:50]}...")
        img = Image.new('RGB', (768, 768), color = (73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((100, 350), f"MOCK IMAGE\nPrompt: {prompt[:30]}...", fill=(255, 255, 0))
        img.save(filename)
        logger.info(f"Mock image saved: {filename}")
        return filename

    # 1. Try Hugging Face first if key is present (Cloud High Quality)
    if HF_API_KEY and HF_API_KEY.strip() != "":
        try:
            logger.info("HF_API_KEY detected. Using Hugging Face for image generation...")
            return await generate_image_hf(prompt)
        except Exception as e:
            logger.warning(f"Hugging Face generation failed, falling back: {e}")

    # 2. Try Pollinations if requested or as fallback
    if USE_POLLINATIONS:
        return await generate_image_pollinations(prompt, filename)

    payload = {
        "prompt": prompt,
        "steps": 30,
        "width": 768,
        "height": 768,
        "cfg_scale": 8,
        "sampler_name": "DPM++ 2M Karras",
        "negative_prompt": "text, watermark, blurry, low quality"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"Connecting to Local SD API: {SD_API_URL}")
            async with session.post(SD_API_URL, json=payload, timeout=120) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "images" in data and len(data["images"]) > 0:
                        image_base64 = data["images"][0]
                        
                        # Save base64 to image file
                        with open(filename, "wb") as f:
                            f.write(base64.b64decode(image_base64))
                            
                        logger.info(f"Poster generated successfully: {filename}")
                        return filename
                    else:
                        raise ValueError("SD API returned successful status but no images field.")
                else:
                    error_text = await response.text()
                    raise ConnectionError(f"SD API connection failed with status {response.status}: {error_text}")
    except aiohttp.ClientConnectorError:
        error_msg = (
            f"Could not connect to Stable Diffusion at {SD_API_URL}. "
            "Falling back to Pollinations.ai (Free Cloud Mode)..."
        )
        logger.warning(error_msg)
        return await generate_image_pollinations(prompt, filename)
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise e
