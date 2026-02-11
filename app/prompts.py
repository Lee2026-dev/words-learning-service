# Prompt Templates for Gemini Translation and Dictionary Service

DICTIONARY_PROMPT_TEMPLATE = """
You are a professional English-{target_lang} dictionary.

Return ONLY valid JSON in this exact format:

{{
  "word": "",
  "phonetic": "",
  "meanings": [
    {{
      "partOfSpeech": "",
      "definitions": [
        {{
          "definition": "",
          "example": ""
        }}
      ]
    }}
  ]
}}

Rules:
- Only include parts of speech that exist.
- Keep meanings short and accurate.
- No explanations.
- No markdown.
- No comments.

Word: {word}
"""

TRANSLATE_PROMPT_TEMPLATE = """
Translate the following English sentence into natural {target_lang}.
Return ONLY the {target_lang} translation.
No explanation.

Sentence:
{sentence}
"""
