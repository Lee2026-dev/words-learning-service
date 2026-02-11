import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

BING_DICT_URL = "https://cn.bing.com/dict/search?q={word}"

async def fetch_bing_data(word: str) -> Optional[Dict]:
    """
    Scrapes cn.bing.com for rich dictionary data (EN -> ZH).
    Returns structure compatible with our app's needs.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Add headers to look like a real browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            resp = await client.get(BING_DICT_URL.format(word=word), headers=headers)
            
            if resp.status_code != 200:
                logger.error(f"Bing returned {resp.status_code}")
                return None
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 1. Phonetics & Audio
            phonetic_us = ""
            phonetic_uk = ""
            audio_url = None
            
            # Bing structure for phonetics usually in <div class="hd_p1_1">
            hd_div = soup.find('div', class_='hd_p1_1')
            if hd_div:
                # Loop through standard pronunciation blocks
                # US: 美 [....]  UK: 英 [....]
                b_tags = hd_div.find_all('b')
                for b in b_tags:
                    text = b.get_text()
                    next_span = b.find_next_sibling('span')
                    ph_text = next_span.get_text(strip=True) if next_span else ""
                    
                    if '美' in text:
                        phonetic_us = ph_text.replace('[', '/').replace(']', '/')
                        
                        # Try to find audio link
                        # Bing audio is usually in an 'onmouseover' or 'onclick' event on an <a> tag
                        # Example: <a onmouseover="javascript:playSound('https://...mp3')">
                        a_audio = next_span.find_next_sibling('a')
                        if a_audio:
                            onclick = a_audio.get('onclick') or a_audio.get('onmouseover') or ""
                            if 'http' in onclick and '.mp3' in onclick:
                                start = onclick.find('http')
                                end = onclick.find('.mp3') + 4
                                audio_url = onclick[start:end]

                    elif '英' in text:
                        phonetic_uk = ph_text.replace('[', '/').replace(']', '/')

            # Prefer US phonetic if available, else UK
            primary_phonetic = phonetic_us if phonetic_us else phonetic_uk

            # 2. Meanings (POS Groups)
            # Structure: <ul> then <li> with <span class="pos">n.</span> <span class="def">...</span>
            meanings = []
            qdef_ul = soup.find('ul', class_='qdef_ul') # This is the main definition list
            
            # Sometimes it's in a different container if it's a simple word
            if not qdef_ul:
                 # Backup generic search
                 pass
            
            if qdef_ul:
                for li in qdef_ul.find_all('li'):
                    pos_span = li.find('span', class_='pos')
                    def_span = li.find('span', class_='def')
                    
                    if pos_span and def_span:
                        pos_text = pos_span.get_text(strip=True)
                        def_text = def_span.get_text(strip=True)
                        
                        # Extract first example if possible? Bing usually hides examples in sub-lists.
                        # For now, let's keep it simple: POS + Definition keywords
                        
                        meanings.append({
                            "partOfSpeech": pos_text,
                            "definitions": [{
                                "definition": def_text,
                                "example": "" 
                            }]
                        })

            if not meanings:
                # If no strict definitions found, maybe it's a web translation or suggestion
                # Verify if we found valid data
                return None

            return {
                "phonetic": primary_phonetic,
                "audio_url": audio_url,
                "meanings": meanings,
                "phonetics": [] # We could populate detailed list if needed
            }

        except Exception as e:
            logger.error(f"Bing scraping failed: {e}")
            return None
