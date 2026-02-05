from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select, SQLModel
from typing import List, Optional
import uuid

from app.database import get_session
from app.models import Word

router = APIRouter(prefix="/words", tags=["words"])

@router.get("", response_model=List[Word])
def get_words(session: Session = Depends(get_session), limit: int = 100, offset: int = 0):
    """
    Return list of saved words (sorted by newest).
    """
    statement = select(Word).order_by(Word.timestamp.desc()).offset(offset).limit(limit)
    return session.exec(statement).all()

@router.post("", response_model=Word)
def create_word(word_data: Word, session: Session = Depends(get_session)):
    """
    Save a new word. Checks for duplicates by 'original' text.
    If duplicate exists, returns the existing one (idempotent).
    """
    # Check for duplicate
    statement = select(Word).where(Word.original == word_data.original)
    existing_word = session.exec(statement).first()
    if existing_word:
        return existing_word

    # Create new
    # Ensure ID is new (or let DB handle it if we didn't pass one, but Pydantic factory handles it)
    session.add(word_data)
    session.commit()
    session.refresh(word_data)
    return word_data

@router.delete("/{word_id}")
def delete_word(word_id: uuid.UUID, session: Session = Depends(get_session)):
    word = session.get(Word, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    session.delete(word)
    session.commit()
    return {"message": "Word deleted"}

class WordUpdate(SQLModel):
    original: Optional[str] = None
    translation: Optional[str] = None
    context: Optional[str] = None
    url: Optional[str] = None
    learned: Optional[bool] = None

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
