from abc import ABC, abstractmethod
from typing import Dict, Any
import os
import json
import re
import logging
from google import genai
from openai import OpenAI
from app.prompts import DICTIONARY_PROMPT_TEMPLATE, TRANSLATE_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

class LLMService(ABC):
    @abstractmethod
    def lookup_word(self, word: str, target_lang: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def translate_sentence(self, sentence: str, target_lang: str) -> str:
        pass

class GeminiService(LLMService):
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        try:
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-3-flash-preview"
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None

    def lookup_word(self, word: str, target_lang: str) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("Gemini client not initialized")
        
        prompt = DICTIONARY_PROMPT_TEMPLATE.format(target_lang=target_lang, word=word)
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0},
            )
            text = response.text.strip()
            text = re.sub(r"```json|```", "", text).strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini lookup_word failed: {e}")
            raise e

    def translate_sentence(self, sentence: str, target_lang: str) -> str:
        if not self.client:
            raise RuntimeError("Gemini client not initialized")
            
        prompt = TRANSLATE_PROMPT_TEMPLATE.format(target_lang=target_lang, sentence=sentence)
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0},
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini translate_sentence failed: {e}")
            return sentence

class OpenRouterService(LLMService):
    def __init__(self):
        # Allow override via env var, but fallback to provided key if needed (though providing keys in code is discouraged)
        # Using a placeholder here for the example, expects OPENROUTER_API_KEY env var
        api_key = os.environ.get("OPENROUTER_API_KEY") 
        if not api_key:
             logger.warning("OPENROUTER_API_KEY not set. OpenRouter service may fail.")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = "deepseek/deepseek-r1-0528:free" # Using the exact user-specified model name
        # self.model = "meta-llama/llama-3.3-70b-instruct:free"
        # self.model = "openai/gpt-oss-20b:free"
        # self.model = "meta-llama/llama-3.3-70b-instruct:free"
        # self.model = "qwen/qwen3-4b:free"

    def lookup_word(self, word: str, target_lang: str) -> Dict[str, Any]:
        prompt = DICTIONARY_PROMPT_TEMPLATE.format(target_lang=target_lang, word=word)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            text = response.choices[0].message.content.strip()
            
            # Clean up <think> blocks if present (common in DeepSeek R1)
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            
            text = re.sub(r"```json|```", "", text).strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"OpenRouter lookup_word failed: {e}")
            raise e

    def translate_sentence(self, sentence: str, target_lang: str) -> str:
        prompt = TRANSLATE_PROMPT_TEMPLATE.format(target_lang=target_lang, sentence=sentence)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            text = response.choices[0].message.content.strip()
            # Clean up <think> blocks if present
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return text
        except Exception as e:
            logger.error(f"OpenRouter translate_sentence failed: {e}")
            return sentence

class LLMManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMManager, cls).__new__(cls)
            cls._instance._init_services()
        return cls._instance
    
    def _init_services(self):
        self.services = {
            "gemini": GeminiService(),
            "openrouter": OpenRouterService(),
        }
        # Default can be configured via env or settings
        self.default_service_name = os.environ.get("LLM_PROVIDER", "openrouter") 

    def get_service(self, name: str = None) -> LLMService:
        service_name = name or self.default_service_name
        service = self.services.get(service_name)
        if not service:
            logger.warning(f"Service '{service_name}' not found, falling back to Gemini")
            return self.services.get("gemini")
        return service

# Global instance
llm_manager = LLMManager()

def get_llm_service() -> LLMService:
    return llm_manager.get_service()
