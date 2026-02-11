from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from googletrans import Translator
import logging
from app.dictionary_service import fetch_dictionary_data
from app.ecdict_service import fetch_ecdict_data  # Use ECDICT instead of Bing

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
    # Normalize language code for Google Translate / Custom logic
    dest_lang = request.target_lang.lower()
    if dest_lang == 'zh':
        dest_lang = 'zh-cn'
    elif dest_lang == 'zh-tw':
        dest_lang = 'zh-tw'
    
    # ---------------------------------------------------------
    # STRATEGY A: If Target is Chinese, Use ECDICT (Local Dictionary)
    # ---------------------------------------------------------
    if dest_lang in ['zh-cn', 'zh-tw']:
        try:
            ecdict_data = await fetch_ecdict_data(request.text)
            if ecdict_data:
                # ECDICT lookup successful! Return rich local data.
                # Extract simple translation from first definition
                simple_translation = request.text
                if ecdict_data['meanings']:
                    first_def = ecdict_data['meanings'][0]['definitions'][0]['definition']
                    # Take first part before semicolon as simple translation
                    simple_translation = first_def.split('；')[0].split(';')[0]
                
                return TranslateResponse(
                    translation=simple_translation,
                    phonetic=ecdict_data.get('phonetic'),
                    audio_url=ecdict_data.get('audio_url'),
                    meanings=ecdict_data.get('meanings', []),
                    phonetics=[],
                    detected_source_lang="en"  # ECDICT is En->Zh
                )
        except Exception as e:
            logger.error(f"ECDICT strategy failed: {e}")
            # Fall through to Google strategy

    # ---------------------------------------------------------
    # STRATEGY B: Google Translate (Universal Fallback)
    # ---------------------------------------------------------

    # Step 1: Fetch English dictionary data (for phonetics/audio if Bing failed/skipped)
    dictionary_data = None
    try:
        dictionary_data = await fetch_dictionary_data(request.text)
    except Exception as e:
        logger.error(f"Dictionary fetch failed: {e}")
    
    # Step 2: Translate the word itself
    word_translation = await _translate_single(request.text, dest_lang)
    
    # Step 3: Process meanings if dictionary data exists
    final_meanings = []
    
    # Special optimization for Google Translate Rich Data (The "n. word" format)
    # We try to extract POS directly from Google if possible (see previous logic)
    # ... (omitted for brevity, utilizing standard translation logic below) ...

    if dictionary_data and dictionary_data.get('meanings'):
        final_meanings = await _translate_meanings(
            dictionary_data.get('meanings', []),
            dest_lang
        )
    
    # Step 4: Construct response
    return TranslateResponse(
        translation=word_translation,
        phonetic=dictionary_data.get('phonetic') if dictionary_data else None,
        audio_url=dictionary_data.get('audio_url') if dictionary_data else None,
        meanings=final_meanings,
        phonetics=dictionary_data.get('phonetics', []) if dictionary_data else [],
        detected_source_lang="en"
    )


async def _translate_single(text: str, dest_lang: str) -> str:
    """Translate a single text string"""
    try:
        translator = Translator(service_urls=['translate.google.com'])
        result = translator.translate(text, dest=dest_lang)
        return result.text if result and hasattr(result, 'text') else text
    except Exception as e:
        logger.error(f"Translation failed for '{text}': {e}")
        return text


async def _translate_meanings(meanings: List[Dict], dest_lang: str) -> List[Dict]:
    """Translate all definitions in meanings structure"""
    # Collect all unique definitions
    all_definitions = []
    for meaning in meanings:
        for d in meaning.get('definitions', []):
            if d.get('definition'):
                all_definitions.append(d['definition'])
    
    if not all_definitions:
        return []
    
    # Batch translate all definitions
    try:
        translator = Translator(service_urls=['translate.google.com'])
        results = translator.translate(all_definitions, dest=dest_lang)
        
        if not isinstance(results, list):
            results = [results]
        
        # Create translation map
        translation_map = {}
        for i, result in enumerate(results):
            if i < len(all_definitions):
                original = all_definitions[i]
                translated = result.text if result and hasattr(result, 'text') else original
                translation_map[original] = translated
    
    except Exception as e:
        logger.error(f"Batch translation failed: {e}")
        # Fallback: use original text
        translation_map = {d: d for d in all_definitions}
    
    # Reconstruct meanings with translated definitions
    final_meanings = []
    for meaning in meanings:
        translated_defs = []
        for d in meaning.get('definitions', []):
            orig_def = d.get('definition', '')
            translated_defs.append({
                "definition": translation_map.get(orig_def, orig_def),
                "example": d.get('example', '')
            })
        
        final_meanings.append({
            "partOfSpeech": meaning.get('partOfSpeech', ''),
            "definitions": translated_defs
        })
    
    return final_meanings
