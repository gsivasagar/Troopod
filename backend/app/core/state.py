"""
State Module
Defines the state schema for the LangGraph workflow.
"""
from typing import TypedDict, List, Optional

class GraphState(TypedDict):
    # Inputs (Data only, no config)
    url: str
    image_bytes: bytes
    
    # Data
    original_html: str
    dom_nodes: List[dict]
    ad_context: dict
    meta: Optional[dict]
    
    # Personalization
    color_overrides: Optional[dict]
    custom_section: Optional[dict]
    replacements: List[dict]
    summary: str
    
    # Output
    modified_html: str
    
    # Loop State
    screenshot: Optional[bytes]
    critique: Optional[str]
    iteration: int
    
    # Status
    success: bool
    error: Optional[str]
