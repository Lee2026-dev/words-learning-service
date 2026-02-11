from googletrans import Translator
import json

def test_translation():
    translator = Translator()
    # Translate to Chinese
    result = translator.translate('files', dest='zh-cn')
    
    print(f"Original: {result.origin}")
    print(f"Translation: {result.text}")
    
    # Check for extra data (synonyms, definitions, etc.)
    if hasattr(result, 'extra_data'):
        print("\n--- Extra Data Found ---")
        # print(json.dumps(result.extra_data, ensure_ascii=False, indent=2))
        
        # Try to find the structure that matches:
        # [
        #   ["noun", ["word", "word2"], ...],
        #   ["verb", ["word3"], ...]
        # ]
        try:
            # Usually extra_data['translation'] has detailed breakdowns 
            # Or sometimes it is in a different field depending on library version
            # Let's inspect the raw dictionary to be safe
            print(result.extra_data)
        except:
            pass
            
if __name__ == "__main__":
    test_translation()
