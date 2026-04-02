import ollama
from groq import Groq
from app.llm.prompt import MASTER_PROMPT
from app.utils.logger import get_logger
from app.config import GROQ_API_KEY

logger = get_logger(__name__)

def generate_with_ollama(prompt: str) -> str:
    """Fallback method using local Ollama."""
    logger.info("Falling back to Ollama (Llama 3)...")
    try:
        response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        return response['message']['content']
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}")
        return "{}"

def generate_poster_json(topic: str, style: str) -> str:
    prompt = MASTER_PROMPT.format(topic=topic, style=style)
    
    # 1. Try Groq first if key is present (Cloud High Speed)
    if GROQ_API_KEY and GROQ_API_KEY.strip() != "":
        logger.info(f"Generating content for topic='{topic}' using Groq (llama-3.3-70b-versatile)")
        try:
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a professional marketing designer. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq generation failed, falling back to Ollama: {e}")
            return generate_with_ollama(prompt)
    
    # 2. Default to Ollama if no Groq key
    logger.info(f"Generating content for topic='{topic}' style='{style}' using Ollama (Llama 3)")
    return generate_with_ollama(prompt)
