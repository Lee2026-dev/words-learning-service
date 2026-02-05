from fastapi import APIRouter
from pydantic import BaseModel
from googletrans import Translator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "zh"

class TranslateResponse(BaseModel):
    translation: str
    phonetic: str | None = None
    detected_source_lang: str | None = None

@router.post("/translate", response_model=TranslateResponse)
def translate_text(request: TranslateRequest):
    try:
        # Create a new translator instance per request to avoid session timeouts
        translator = Translator()
        result = translator.translate(request.text, dest=request.target_lang)
        
        # Handle potential list response
        if isinstance(result, list):
            result = result[0]
            
        return TranslateResponse(
            translation=result.text,
            phonetic=getattr(result, 'pronunciation', None) or getattr(result, 'extra_data', {}).get('translation', [[None, None, request.text]])[0][2], # robust fallback for phonetic
            detected_source_lang=result.src
        )
    except Exception as e:
        logger.error(f"GoogleTrans API failed: {str(e)}")
        logger.info("Falling back to local mock translation.")
        
        # Fallback Logic
        # For a real service, we might switch to another provider. 
        # Here we provide a graceful degradation.
        return TranslateResponse(
            translation=f"[Offline] {request.text}",
            phonetic=None,
            detected_source_lang="auto"
        )
