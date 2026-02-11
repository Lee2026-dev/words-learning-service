"""
ECDICT Local Dictionary Service
Provides fast local English-Chinese dictionary lookups using ECDICT database.
"""
import sqlite3
from typing import Optional, Dict, List
import logging
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "ecdict.db")

def parse_pos(pos_str: str) -> List[Dict]:
    """
    Parse POS string like 'n:46/v:54' into structured meanings.
    Returns list of POS groups sorted by frequency.
    """
    if not pos_str:
        return []
    
    pos_parts = pos_str.split('/')
    pos_list = []
    
    for part in pos_parts:
        if ':' in part:
            pos_type, freq = part.split(':')
            pos_list.append({
                'pos': pos_type,
                'frequency': int(freq)
            })
    
    # Sort by frequency (descending)
    pos_list.sort(key=lambda x: x['frequency'], reverse=True)
    return pos_list


async def fetch_ecdict_data(word: str) -> Optional[Dict]:
    """
    Query ECDICT SQLite database for word definition.
    Returns structured dictionary data compatible with our API.
    """
    if not os.path.exists(DB_PATH):
        logger.error(f"ECDICT database not found at {DB_PATH}")
        logger.error("Please download from: https://github.com/skywind3000/ECDICT/releases")
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()
        
        # Query the word (case-insensitive)
        cursor.execute("""
            SELECT word, phonetic, translation, pos, collins, oxford, tag, bnc, frq
            FROM stardict 
            WHERE word = ? COLLATE NOCASE
            LIMIT 1
        """, (word.lower(),))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            logger.info(f"Word '{word}' not found in ECDICT")
            return None
        
        # Parse the data
        phonetic = row['phonetic'] or ""
        translation = row['translation'] or ""
        pos_str = row['pos'] or ""
        
        # Format phonetic (ECDICT uses /.../ format already)
        if phonetic and not phonetic.startswith('/'):
            phonetic = f"/{phonetic}/"
        
        # Parse POS and create meanings structure
        pos_list = parse_pos(pos_str)
        meanings = []
        
        if pos_list and translation:
            # Split translation by newlines or semicolons
            # ECDICT format: "n. 释义1\\nn. 释义2\\nv. 释义3"
            trans_lines = translation.replace('\\n', '\n').split('\n')
            
            # Group translations by POS
            current_pos = None
            current_defs = []
            
            for line in trans_lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts with POS marker (n., v., adj., etc.)
                if '. ' in line[:10]:  # POS markers are usually at the start
                    # Save previous group
                    if current_pos and current_defs:
                        meanings.append({
                            "partOfSpeech": current_pos,
                            "definitions": [{
                                "definition": "; ".join(current_defs),
                                "example": ""
                            }]
                        })
                    
                    # Start new group
                    parts = line.split('. ', 1)
                    if len(parts) == 2:
                        current_pos = parts[0] + '.'
                        current_defs = [parts[1]]
                    else:
                        current_defs.append(line)
                else:
                    current_defs.append(line)
            
            # Add last group
            if current_pos and current_defs:
                meanings.append({
                    "partOfSpeech": current_pos,
                    "definitions": [{
                        "definition": "; ".join(current_defs),
                        "example": ""
                    }]
                })
        
        # Fallback: if no structured meanings, use raw translation
        if not meanings and translation:
            meanings.append({
                "partOfSpeech": "general",
                "definitions": [{
                    "definition": translation.replace('\\n', '; '),
                    "example": ""
                }]
            })
        
        return {
            "phonetic": phonetic,
            "audio_url": None,  # ECDICT doesn't provide audio URLs
            "meanings": meanings,
            "phonetics": []
        }
        
    except Exception as e:
        logger.error(f"ECDICT query failed: {e}")
        return None
