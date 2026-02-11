from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select, SQLModel
from typing import List, Optional
import uuid
import time
import logging

logger = logging.getLogger("api.words")

from app.database import get_session
from app.gemini_service import lookup_word

from app.models import Word
from pydantic import BaseModel

router = APIRouter(prefix="/words", tags=["words"])



@router.post("", response_model=Word)
async def save_word(request: Word, session: Session = Depends(get_session)):
    """
    Mark a word as starred.
    If word exists, update star=True.
    If word doesn't exist, fetch from Gemini, create it with star=True.
    """
    # Check if word exists
    statement = select(Word).where(Word.original == request.original)
    existing_word = session.exec(statement).first()
    
    if existing_word:
        existing_word.star = True
        session.add(existing_word)
        session.commit()
        session.refresh(existing_word)
        logger.info(f"Word '{request.original}' already exists, marked as starred.")
        return existing_word
        
    # If not exists, fetch and create
    # We default target_lang to 'Chinese' for enrichment or we could accept it in request. 
    # For simplicity, default to Chinese context as per app Settings default.
    target_lang = "Chinese" 
    
    try:
        data = await lookup_word(request.original, target_lang)
        
        # Extract fields similar to /translate logic
        final_meanings = data.get("meanings", [])
        
        # Helper to find a simple translation
        simple_translation = data.get("word", request.original)
        if isinstance(final_meanings, list) and len(final_meanings) > 0:
            first_meaning = final_meanings[0]
            if isinstance(first_meaning, dict):
                defs = first_meaning.get("definitions", [])
                if isinstance(defs, list) and len(defs) > 0:
                    first_def = defs[0]
                    if isinstance(first_def, dict):
                        simple_translation = first_def.get("definition", simple_translation)
                    elif isinstance(first_def, str):
                        simple_translation = first_def

        new_word = Word(
            original=request.original,
            translation=simple_translation,
            phonetic=data.get("phonetic"),
            meanings=final_meanings,
            phonetics=[],
            audio_url=None,
            learned=False,
            star=True
        )
        session.add(new_word)
        session.commit()
        session.refresh(new_word)
        logger.info(f"Word '{request.original}' not found, fetched from Gemini and saved.")
        return new_word
        
    except Exception as e:
        logger.error(f"Failed to fetch/save word '{request.original}': {e}")
        # Fallback: create a basic entry if AI fails
        fallback_word = Word(
            original=request.original,
            translation=request.original,
            star=True
        )
        session.add(fallback_word)
        session.commit()
        session.refresh(fallback_word)
        return fallback_word
@router.get("", response_model=List[Word])
def get_words(
    session: Session = Depends(get_session), 
    limit: int = 100, 
    offset: int = 0,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None
):
    """
    Return list of saved words (sorted by newest).
    """
    query = select(Word).where(Word.star == True)
    
    if start_time:
        query = query.where(Word.timestamp >= start_time)
    if end_time:
        query = query.where(Word.timestamp <= end_time)
        
    statement = query.order_by(Word.timestamp.desc()).offset(offset).limit(limit)
    
    t0 = time.time()
    results = session.exec(statement).all()
    duration = time.time() - t0
    logger.info(f"DB Query (get_words) took: {duration:.4f}s")
    
    return results

@router.post("/save", response_model=Word)
def create_word(word_data: Word, session: Session = Depends(get_session)):
    """
    Save a new word. Checks for duplicates by 'original' text.
    If duplicate exists, returns the existing one (idempotent).
    """
    # Check for duplicate
    t0 = time.time()
    statement = select(Word).where(Word.original == word_data.original)
    existing_word = session.exec(statement).first()
    if existing_word:
        duration = time.time() - t0
        logger.info(f"DB Check (duplicate) took: {duration:.4f}s")
        return existing_word

    # Create new
    # Ensure ID is new (or let DB handle it if we didn't pass one, but Pydantic factory handles it)
    session.add(word_data)
    session.commit()
    session.refresh(word_data)
    duration = time.time() - t0
    logger.info(f"DB Create (create_word) took: {duration:.4f}s")
    return word_data

@router.delete("/{word_id}")
def unstar_word(word_id: uuid.UUID, session: Session = Depends(get_session)):
    word = session.get(Word, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    word.star = False
    session.add(word)
    session.commit()
    return {"message": "Word unstarred"}

class WordUpdate(SQLModel):
    original: Optional[str] = None
    translation: Optional[str] = None
    phonetic: Optional[str] = None
    context: Optional[str] = None
    url: Optional[str] = None
    learned: Optional[bool] = None
    star: Optional[bool] = None

@router.patch("/{word_id}", response_model=Word)
def update_word(word_id: uuid.UUID, word_update: WordUpdate, session: Session = Depends(get_session)):
    """
    Update word fields (e.g. learned=True).
    """
    db_word = session.get(Word, word_id)
    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")

    word_data = word_update.model_dump(exclude_unset=True)
    
    for key, value in word_data.items():
        if hasattr(db_word, key):
            setattr(db_word, key, value)
    
    session.add(db_word)
    session.commit()
    session.refresh(db_word)
    return db_word
