from typing import Optional
import uuid
from datetime import datetime
from sqlmodel import Field, SQLModel

class Word(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    original: str = Field(index=True)  # Index for faster duplicate checks
    translation: str
    phonetic: Optional[str] = None
    context: Optional[str] = None
    url: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    learned: bool = Field(default=False)

class Settings(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    target_language: str = "zh"
    highlight_enabled: bool = True
    immersion_mode: bool = False
    youtube_subtitles_enabled: bool = True
