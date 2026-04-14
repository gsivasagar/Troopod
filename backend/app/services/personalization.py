"""
Personalization Service
Defines the interface and implementation for the personalization logic.
"""
from abc import ABC, abstractmethod
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from .cache import make_cache_key, get_cached, set_cache
from app.orchestration.graph import PersonalizationPipeline
from app.core.config import config

class PersonalizationService(ABC):
    """Interface for the personalization service."""
    
    @abstractmethod
    async def personalize(self, image_bytes: bytes, landing_page_url: str) -> JSONResponse:
        """Personalize the landing page based on the ad image bytes."""
        pass

class DefaultPersonalizationService(PersonalizationService):
    """Default implementation using LangGraph and Gemini."""
    
    async def personalize(self, image_bytes: bytes, landing_page_url: str) -> JSONResponse:
        # Validate API key via config
        try:
            config.validate()
            api_key = config.GEMINI_API_KEY
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty image data provided.")
        
        # Check cache
        cache_key = make_cache_key(image_bytes, landing_page_url)
        cached = get_cached(cache_key)
        if cached:
            return JSONResponse(content=cached)
        
        # Invoke Graph
        pipeline = PersonalizationPipeline(api_key=api_key)
        
        initial_state = {
            "url": landing_page_url,
            "image_bytes": image_bytes,
            "iteration": 0
        }
        
        try:
            final_state = await pipeline.app.ainvoke(initial_state)
            
            if not final_state.get("success", True):
                raise HTTPException(status_code=502, detail=f"Pipeline failed: {final_state.get('error')}")
                
            # Build response
            response = {
                "success": True,
                "landing_page_url": landing_page_url,
                "ad_context": final_state.get("ad_context"),
                "personalization_summary": final_state.get("summary"),
                "changes": {
                    "applied": len(final_state.get("replacements", [])) + (1 if final_state.get("color_overrides") else 0) + (1 if final_state.get("custom_section") else 0),
                    "failed": 0,
                    "diff": final_state.get("replacements", [])
                },
                "original_html": final_state.get("original_html"),
                "modified_html": final_state.get("modified_html"),
                "meta": final_state.get("meta", {}),
                "dom_nodes_extracted": len(final_state.get("dom_nodes", []))
            }
            
            # Cache result
            set_cache(cache_key, response)
            
            return JSONResponse(content=response)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Graph execution error: {str(e)}")
