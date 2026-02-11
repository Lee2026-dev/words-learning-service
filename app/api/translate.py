from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
import logging
from app.gemini_service import lookup_word, translate_sentence, is_single_word
from app.database import get_session
from app.models import Word

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
async def translate_text(request: TranslateRequest, session: Session = Depends(get_session)):
    # Determine target language specific name for the prompt
    target_lang_name = "Chinese"
    if request.target_lang.lower().startswith("zh"):
        target_lang_name = "Chinese"
    else:
        # Fallback for other languages, though the prompt is optimized for Chinese
        target_lang_name = request.target_lang

    try:
        if is_single_word(request.text):
            # 1. Check DB first
            # Use lower case for case-insensitive lookup if desired, but here we invoke strict check or simple logic
            # For now, let's query exact match or case-insensitive match.
            # SQLite default is case-insensitive for ASCII text, Postgres is case-sensitive.
            # We'll normalize to lower() for search to be user-friendly, assuming we want to cache "Book" and "book" as same or similar.
            # But wait, "Book" (proper noun) vs "book" (common noun)?
            # Let's stick to simple Case-Insensitive search for now to maximize cache hits.
            # However, SQLModel/SQLAlchemy 'ilike' is safer.
            
            # Simple approach: Check exact match first.
            statement = select(Word).where(Word.original == request.text)
            cached_word = session.exec(statement).first()
            
            if cached_word:
                logger.info(f"Cache hit for word: {request.text}")
                return TranslateResponse(
                    translation=cached_word.translation,
                    phonetic=cached_word.phonetic,
                    audio_url=cached_word.audio_url,
                    meanings=cached_word.meanings if cached_word.meanings else [],
                    phonetics=cached_word.phonetics if cached_word.phonetics else [],
                    detected_source_lang="en"
                )

            # 2. Not in DB, fetch from Gemini
            logger.info(f"Cache miss for word: {request.text}, fetching from Gemini...")
            data = await lookup_word(request.text, target_lang_name)
            
            # Map Gemini response to TranslateResponse
            
            # Extract meanings
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
                            # Fallback if Gemini returns simple string list
                            simple_translation = first_def
            
            # 3. Save to DB
            try:
                new_word = Word(
                    original=request.text,
                    translation=simple_translation,
                    phonetic=data.get("phonetic"),
                    meanings=final_meanings,
                    phonetics=[], # Structure different, omitting for now
                    audio_url=None,
                    learned=False
                )
                session.add(new_word)
                session.commit()
                session.refresh(new_word)
                logger.info(f"Saved new word to DB: {request.text}")
            except Exception as db_err:
                logger.error(f"Failed to save word to DB: {db_err}")
                # Continue even if save fails, just return results
            
            return TranslateResponse(
                translation=simple_translation,
                phonetic=data.get("phonetic"),
                audio_url=None, 
                meanings=final_meanings,
                phonetics=[], 
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
