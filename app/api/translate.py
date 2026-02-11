from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from app.gemini_service import lookup_word, translate_sentence, is_single_word

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "zh"

class TranslateResponse(BaseModel):
    translation: str
    phonetic: Optional[str] = None
    audio_url: Optional[str] = None
    meanings: List[Dict[str, Any]] = []
    phonetics: List[Dict[str, Any]] = []
    detected_source_lang: Optional[str] = None

@router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    # Determine target language specific name for the prompt
    target_lang_name = "Chinese"
    if request.target_lang.lower().startswith("zh"):
        target_lang_name = "Chinese"
    else:
        # Fallback for other languages, though the prompt is optimized for Chinese
        target_lang_name = request.target_lang

    try:
        if is_single_word(request.text):
            # Use Gemini lookup for single words to get rich dictionary data
            data = await lookup_word(request.text, target_lang_name)
            
            # Map Gemini response to TranslateResponse
            
            # 1. Extract meanings
            final_meanings = data.get("meanings", [])
            
            # Helper to find a simple translation (first definition)
            simple_translation = data.get("word", request.text)
            
            if isinstance(final_meanings, list) and len(final_meanings) > 0:
                # Try to get first definition as simple translation
                first_meaning = final_meanings[0]
                if isinstance(first_meaning, dict):
                    defs = first_meaning.get("definitions", [])
                    if isinstance(defs, list) and len(defs) > 0:
                        first_def = defs[0]
                        if isinstance(first_def, dict):
                            simple_translation = first_def.get("definition", simple_translation)
                        elif isinstance(first_def, str):
                            simple_translation = first_def
            
            return TranslateResponse(
                translation=simple_translation,
                phonetic=data.get("phonetic"),
                audio_url=None, # Gemini doesn't return audio URL
                meanings=final_meanings,
                phonetics=[], # Structure different, omitting for now
                detected_source_lang="en"
            )
            
        else:
            # Use Gemini for sentence translation
            translation = await translate_sentence(request.text, target_lang_name)
            return TranslateResponse(
                translation=translation,
                detected_source_lang="en"
            )

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
