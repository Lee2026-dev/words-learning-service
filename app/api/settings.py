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
    
    # Update fields dynamically
    settings_dict = settings_data.model_dump(exclude_unset=True)
    for key, value in settings_dict.items():
        if key != "id" and hasattr(db_settings, key):
            setattr(db_settings, key, value)
    
    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)
    return db_settings
