import os
import json
import re
import logging
from typing import Dict, Any, Optional
from google import genai
from fastapi.concurrency import run_in_threadpool

from app.prompts import DICTIONARY_PROMPT_TEMPLATE, TRANSLATE_PROMPT_TEMPLATE

# Initialize logger
logger = logging.getLogger(__name__)

# Configure API Key (fallback to the one from user script if env var not set)
# Note: In production, always use environment variables.
API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyBmJclRQyOSsRxpQNGUZH4REXr2WV_OnNA")
MODEL = "gemini-2.5-flash"

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Gemini client: {e}")
    client = None

def is_single_word(text: str) -> bool:
    return len(text.strip().split()) == 1

def _lookup_word_sync(word: str, target_lang: str = "Chinese") -> Dict[str, Any]:
    if not client:
        raise RuntimeError("Gemini client not initialized")
        
    prompt = DICTIONARY_PROMPT_TEMPLATE.format(target_lang=target_lang, word=word)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "temperature": 0,
            },
        )
        
        text = response.text.strip()
        # Remove accidental markdown fences
        text = re.sub(r"```json|```", "", text).strip()
        
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini lookup_word failed: {e}")
        raise e

def _translate_sentence_sync(sentence: str, target_lang: str = "Chinese") -> str:
    if not client:
        raise RuntimeError("Gemini client not initialized")
        
    prompt = TRANSLATE_PROMPT_TEMPLATE.format(target_lang=target_lang, sentence=sentence)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={"temperature": 0},
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini translate_sentence failed: {e}")
        return sentence

async def lookup_word(word: str, target_lang: str = "Chinese") -> Dict[str, Any]:
    return await run_in_threadpool(_lookup_word_sync, word, target_lang)

async def translate_sentence(sentence: str, target_lang: str = "Chinese") -> str:
    return await run_in_threadpool(_translate_sentence_sync, sentence, target_lang)
