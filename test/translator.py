import os
import json
import re
from google import genai

# Create client (reads GOOGLE_API_KEY from env)
client = genai.Client(api_key="AIzaSyBmJclRQyOSsRxpQNGUZH4REXr2WV_OnNA")

MODEL = "gemini-2.5-flash"


def is_single_word(text: str) -> bool:
    return len(text.strip().split()) == 1


def lookup_word(word: str) -> dict:
    prompt = f"""
You are a professional English-Chinese dictionary.

Return ONLY valid JSON in this exact format:

{{
  "word": "",
  "phonetic": "",
  "meanings": {{
    "noun": [],
    "verb": [],
    "adjective": [],
    "adverb": []
  }}
}}

Rules:
- Only include parts of speech that exist.
- Keep meanings short and accurate.
- No explanations.
- No markdown.
- No comments.

Word: {word}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "temperature": 0,
        },
    )

    text = response.text.strip()

    # Remove accidental markdown fences
    text = re.sub(r"```json|```", "", text).strip()

    return json.loads(text)


def translate_sentence(sentence: str) -> str:
    prompt = f"""
Translate the following English sentence into natural Chinese.
Return ONLY the Chinese translation.
No explanation.

Sentence:
{sentence}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"temperature": 0},
    )

    return response.text.strip()


def translate(text: str):
    if is_single_word(text):
        return lookup_word(text)
    else:
        return translate_sentence(text)


if __name__ == "__main__":
    # while True:
    #     user_input = input("\nEnter English (q to quit): ").strip()
    #     if user_input.lower() == "q":
    #         break

    try:
        result = translate("English Words")

        print("\nResult:")
        if isinstance(result, dict):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result)

    except Exception as e:
        print("Error:", e)
