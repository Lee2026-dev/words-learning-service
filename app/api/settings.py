from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database import get_session
from app.models import Settings

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("", response_model=Settings)
def get_settings(session: Session = Depends(get_session)):
    """
    Return current settings. Initialize defaults if empty.
    """
    settings = session.get(Settings, 1)
    if not settings:
        settings = Settings(id=1)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings

@router.put("", response_model=Settings)
def update_settings(settings_data: Settings, session: Session = Depends(get_session)):
    """
    Update settings. Enforces singleton pattern (ID=1).
    """
    db_settings = session.get(Settings, 1)
    if not db_settings:
        db_settings = Settings(id=1)
    
    # Update fields
    db_settings.target_language = settings_data.target_language
    db_settings.highlight_enabled = settings_data.highlight_enabled
    db_settings.immersion_mode = settings_data.immersion_mode
    
    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)
    return db_settings
