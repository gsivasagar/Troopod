"""
Designer Agent Module
Critiques landing page designs against the ad creative.
"""
import google.generativeai as genai
import json
import re
import os

class DesignerAgent:
    """Agent for critiquing design and suggesting color overrides."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-flash-latest")
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load prompt from external file."""
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/designer_prompt.txt")
        try:
            with open(prompt_path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Failed to load prompt from {prompt_path}. Using fallback. Error: {e}")
            return "You are an expert UI/UX designer."

    def critique_design(self, screenshot_bytes: bytes, ad_image_bytes: bytes) -> str:
        """Critique the design using Vision against the original ad."""
        screenshot_part = {
            "mime_type": "image/jpeg",
            "data": screenshot_bytes
        }
        
        ad_part = {
            "mime_type": "image/jpeg",
            "data": ad_image_bytes
        }
        
        try:
            response = self.model.generate_content([self.prompt, ad_part, screenshot_part])
            return response.text.strip()
        except Exception as e:
            return f"ERROR: {str(e)}"
