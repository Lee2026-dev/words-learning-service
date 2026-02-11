import logging
from typing import Dict, Any
from fastapi.concurrency import run_in_threadpool
from app.llm_service import get_llm_service

# Initialize logger
logger = logging.getLogger(__name__)

def is_single_word(text: str) -> bool:
    return len(text.strip().split()) == 1

def _lookup_word_sync(word: str, target_lang: str = "Chinese") -> Dict[str, Any]:
    service = get_llm_service()
    return service.lookup_word(word, target_lang)

def _translate_sentence_sync(sentence: str, target_lang: str = "Chinese") -> str:
    service = get_llm_service()
    return service.translate_sentence(sentence, target_lang)

async def lookup_word(word: str, target_lang: str = "Chinese") -> Dict[str, Any]:
    return await run_in_threadpool(_lookup_word_sync, word, target_lang)

async def translate_sentence(sentence: str, target_lang: str = "Chinese") -> str:
    return await run_in_threadpool(_translate_sentence_sync, sentence, target_lang)
