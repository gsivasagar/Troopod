"""
State Module
Defines the state schema for the LangGraph workflow.
"""
from typing import TypedDict, List, Optional

class GraphState(TypedDict):
                                   
    url: str
    image_bytes: bytes
    
          
    original_html: str
    dom_nodes: List[dict]
    ad_context: dict
    meta: Optional[dict]
    
                     
    color_overrides: Optional[dict]
    custom_section: Optional[dict]
    replacements: List[dict]
    summary: str
    
            
    modified_html: str
    
                
    screenshot: Optional[bytes]
    critique: Optional[str]
    iteration: int
    
            
    success: bool
    error: Optional[str]
