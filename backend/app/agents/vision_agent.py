"""
Vision Agent Module
Analyzes ad creative images using Gemini Vision API.
"""
import google.generativeai as genai
import json
import time
import re
import os
from pydantic import BaseModel, Field, model_validator
from typing import Optional


class AdContext(BaseModel):
    """Structured output from ad creative analysis."""
    hook: Optional[str] = Field(default="", description="The main attention-grabbing hook/headline from the ad")
    offer: Optional[str] = Field(default="", description="The core offer or value proposition")
    audience: Optional[str] = Field(default="", description="Target audience the ad is aimed at")
    tone: Optional[str] = Field(default="", description="Communication tone (e.g. urgent, friendly, professional)")
    keywords: Optional[list[str]] = Field(default_factory=list, description="Key terms and phrases from the ad")
    cta_text: Optional[str] = Field(default="Learn More", description="Call-to-action text from the ad")
    visual_theme: Optional[str] = Field(default="", description="Visual style description (colors, mood, imagery)")
    dominant_colors: Optional[list[str]] = Field(default_factory=list, description="Dominant colors in HEX format if identifiable, or color names")
    key_visuals: Optional[list[str]] = Field(default_factory=list, description="Key visual elements (e.g., product, person, logo)")

    @model_validator(mode='before')
    @classmethod
    def replace_none_values(cls, data):
        """Convert None values to sensible defaults."""
        if isinstance(data, dict):
            defaults = {
                "hook": "", "offer": "", "audience": "", "tone": "", 
                "keywords": [], "cta_text": "Learn More", "visual_theme": "",
                "dominant_colors": [], "key_visuals": []
            }
            for key, default in defaults.items():
                if data.get(key) is None:
                    data[key] = default
        return data


class VisionAgent:
    """Agent for analyzing ad creatives using Gemini Vision."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=2048,
                response_mime_type="application/json",
            )
        )
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load prompt from external file."""
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/vision_prompt.txt")
        try:
            with open(prompt_path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Failed to load prompt from {prompt_path}. Using fallback. Error: {e}")
            return "You are an expert advertising analyst. Analyze the given ad creative image."

    def analyze_ad_creative(self, image_bytes: bytes) -> dict:
        """
        Analyze an ad creative image using Gemini Vision API.
        
        Returns:
            {
                "success": bool,
                "context": AdContext dict or None,
                "error": str or None
            }
        """
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                image_part = {
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                }
                
                response = self.model.generate_content(
                    [self.prompt, image_part]
                )
                
                raw_text = response.text.strip()
                raw_text = self._clean_json_response(raw_text)
                raw_text = self._repair_json(raw_text)
                
                parsed = json.loads(raw_text)
                context = AdContext(**parsed)
                
                return {
                    "success": True,
                    "context": context.model_dump(),
                    "error": None
                }
                
            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON from Vision API (attempt {attempt + 1}): {str(e)}"
            except Exception as e:
                last_error = f"Vision API error (attempt {attempt + 1}): {str(e)}"
            
            if attempt < max_retries - 1:
                time.sleep(15)
        
        return {
            "success": False,
            "context": None,
            "error": f"Failed after {max_retries} attempts. Last error: {last_error}"
        }

    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code fences from JSON response."""
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return text.strip()

    def _repair_json(self, text: str) -> str:
        """Attempt to repair truncated JSON responses."""
        text = text.strip()
        
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        in_string = False
        escaped = False
        for ch in text:
            if escaped:
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if ch == '"':
                in_string = not in_string
        
        if in_string:
            text += '"'
        
        text += ']' * max(0, open_brackets)
        text += '}' * max(0, open_braces)
        
        return text
