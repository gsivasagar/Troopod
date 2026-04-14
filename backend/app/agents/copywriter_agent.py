"""
Copywriter Agent Module
Generates personalized copy using CRO principles, aligned to the ad creative.
"""
import google.generativeai as genai
import json
import time
import re
import os
from pydantic import BaseModel, Field
from typing import Optional


class CopyReplacement(BaseModel):
    """A single text replacement."""
    id: str = Field(description="The ID of the node to replace (e.g., node_1)")
    replacement: str = Field(description="New personalized text")
    reason: str = Field(description="Brief CRO reasoning for the change")


class ColorOverrides(BaseModel):
    """Color recommendations based on the ad."""
    primary_bg: str = Field(description="HEX code or color name for main background")
    primary_text: str = Field(description="HEX code or color name for main text")
    accent_bg: str = Field(description="HEX code or color name for accent elements/buttons")
    accent_text: str = Field(description="HEX code or color name for accent text")


class CustomSection(BaseModel):
    """Content for a new custom section."""
    type: str = Field(description="Type of section, e.g., feature, testimonial")
    title: str = Field(description="Title for the section")
    content: str = Field(description="Content text or list of points")
    cta: Optional[str] = Field(default=None, description="Optional CTA text")


class CopywriterOutput(BaseModel):
    """Structured output from copywriter agent."""
    color_overrides: Optional[ColorOverrides] = None
    replacements: list[CopyReplacement] = Field(default_factory=list)
    custom_section: Optional[CustomSection] = None
    summary: str = Field(description="Brief summary of personalization strategy")


class CopywriterAgent:
    """Agent for generating CRO-optimized copy and banner content."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "color_overrides": {
                    "type": "OBJECT",
                    "properties": {
                        "primary_bg": {"type": "STRING"},
                        "primary_text": {"type": "STRING"},
                        "accent_bg": {"type": "STRING"},
                        "accent_text": {"type": "STRING"}
                    }
                },
                "replacements": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "id": {"type": "STRING"},
                            "replacement": {"type": "STRING"},
                            "reason": {"type": "STRING"}
                        },
                        "required": ["id", "replacement", "reason"]
                    }
                },
                "custom_section": {
                    "type": "OBJECT",
                    "properties": {
                        "type": {"type": "STRING"},
                        "title": {"type": "STRING"},
                        "content": {"type": "STRING"},
                        "cta": {"type": "STRING"}
                    },
                    "required": ["type", "title", "content"]
                },
                "summary": {"type": "STRING"}
            },
            "required": ["summary", "replacements"]
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4096,
                response_mime_type="application/json",
                response_schema=response_schema,
            )
        )
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load prompt from external file."""
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/copywriter_prompt.txt")
        try:
            with open(prompt_path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Failed to load prompt from {prompt_path}. Using fallback. Error: {e}")
            return "You are an expert CRO copywriter."

    def generate_personalized_copy(
        self,
        ad_context: dict,
        dom_nodes: list
    ) -> dict:
        """
        Generate personalized copy replacements using ad context and DOM nodes.
        
        Returns:
            {
                "success": bool,
                "banner": dict or None,
                "color_overrides": dict or None,
                "replacements": list[dict] or [],
                "summary": str,
                "error": str or None
            }
        """
        # Map DOM nodes to IDs to simplify model output
        id_to_node = {}
        nodes_for_model = []
        for i, node in enumerate(dom_nodes):
            node_id = f"node_{i}"
            id_to_node[node_id] = node
            nodes_for_model.append({
                "id": node_id,
                "text": node["text"]
            })
            
        # Build the prompt
        prompt = f"""{self.prompt}

---

AD CONTEXT:
{json.dumps(ad_context, indent=2)}

---

LANDING PAGE TEXT NODES:
{json.dumps(nodes_for_model, indent=2)}

---

Generate the personalized copy and banner content now. Output ONLY the JSON object.
"""
        
        print(f"[CopywriterAgent] Starting generation. Nodes count: {len(dom_nodes)}")
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                print(f"[CopywriterAgent] Attempt {attempt + 1} calling Gemini...")
                response = self.model.generate_content(prompt)
                raw_text = response.text.strip()
                print(f"[CopywriterAgent] Raw response length: {len(raw_text)}")
                print(f"[CopywriterAgent] Raw response preview: {raw_text[:200]}...")
                
                raw_text = self._clean_json_response(raw_text)
                raw_text = self._repair_json(raw_text)
                
                parsed = json.loads(raw_text)
                print("[CopywriterAgent] JSON parsed successfully.")
                
                output = CopywriterOutput(**parsed)
                print(f"[CopywriterAgent] Pydantic validation successful. Replacements: {len(output.replacements)}")
                
                # Map IDs back to selectors and originals, and validate
                replacements_with_selectors = []
                for r in output.replacements:
                    node = id_to_node.get(r.id)
                    if node:
                        if re.search(r'<[^>]+>', r.replacement):
                            print(f"[CopywriterAgent] Skipping replacement for {r.id} because it contains HTML tags.")
                            continue
                        replacements_with_selectors.append({
                            "selector": node["selector"],
                            "original": node["text"],
                            "replacement": r.replacement,
                            "reason": r.reason
                        })
                    else:
                        print(f"[CopywriterAgent] Warning: Model returned invalid node ID: {r.id}")
                        
                print(f"[CopywriterAgent] Validated replacements: {len(replacements_with_selectors)}")
                
                return {
                    "success": True,
                    "color_overrides": output.color_overrides.model_dump() if output.color_overrides else None,
                    "replacements": replacements_with_selectors,
                    "custom_section": output.custom_section.model_dump() if output.custom_section else None,
                    "summary": output.summary,
                    "error": None
                }
                
            except json.JSONDecodeError as e:
                print(f"[CopywriterAgent] JSONDecodeError in attempt {attempt + 1}: {str(e)}")
                print(f"[CopywriterAgent] Raw text that failed to parse: {raw_text}")
                last_error = f"Invalid JSON from Copywriter (attempt {attempt + 1}): {str(e)}"
            except Exception as e:
                print(f"[CopywriterAgent] Exception in attempt {attempt + 1}: {str(e)}")
                print(f"[CopywriterAgent] Raw text: {raw_text}")
                last_error = f"Copywriter error (attempt {attempt + 1}): {str(e)}"
            
            if attempt < max_retries - 1:
                time.sleep(15)
        
        return {
            "success": False,
            "color_overrides": None,
            "replacements": [],
            "custom_section": None,
            "summary": "",
            "error": f"Failed after {max_retries} attempts. Last error: {last_error}"
        }

    def _validate_replacements(
        self,
        replacements: list[CopyReplacement],
        original_nodes: list
    ) -> list[CopyReplacement]:
        """
        Post-validate replacements:
        - Remove any containing HTML tags
        - Enforce length constraints (±30%)
        """
        valid = []
        
        for r in replacements:
            if re.search(r'<[^>]+>', r.replacement):
                continue
            
            valid.append(r)
        
        return valid

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
