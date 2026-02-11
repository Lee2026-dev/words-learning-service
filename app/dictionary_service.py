import httpx
from typing import Dict, Optional, List

# Using the Free Dictionary API
DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

async def fetch_dictionary_data(word: str) -> Optional[Dict]:
    """
    Fetches dictionary data (phonetics, meanings, audio) for a given word.
    Returns a simplified dictionary structure or None if not found.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(DICTIONARY_API_URL.format(word=word))
            if resp.status_code != 200:
                print(f"Dictionary API failed for {word}: {resp.status_code}")
                return None
            
            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                return None
            
            entry = data[0] # Take the first entry
            
            # --- Extract Phonetics ---
            phonetic_text = entry.get('phonetic', '')
            audio_url = None
            phonetics_list = []
            
            for p in entry.get('phonetics', []):
                p_text = p.get('text', '')
                p_audio = p.get('audio', '')
                
                if p_text and not phonetic_text:
                    phonetic_text = p_text
                
                if p_audio and not audio_url:
                    audio_url = p_audio
                
                phonetics_list.append({
                    "text": p_text,
                    "audio": p_audio
                })
            
            # --- Extract Meanings ---
            meanings_list = []
            for m in entry.get('meanings', []):
                pos = m.get('partOfSpeech', 'general')
                definitions = []
                for d in m.get('definitions', []):
                    definitions.append({
                        "definition": d.get('definition', ''),
                        "example": d.get('example', '')
                    })
                
                meanings_list.append({
                    "partOfSpeech": pos,
                    "definitions": definitions
                })

            return {
                "phonetic": phonetic_text,
                "audio_url": audio_url,
                "phonetics": phonetics_list,
                "meanings": meanings_list
            }

        except Exception as e:
            print(f"Error fetching dictionary data: {e}")
            return None
