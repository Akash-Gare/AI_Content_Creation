import json
import re

def parse_llm_json(text: str) -> dict:
    """Extracts and parses JSON from LLM output."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    try:
        match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
            
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"Failed to parse LLM JSON: {e}")
        
    return {}
