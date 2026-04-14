"""
Routes Module
Defines the API endpoints for the Troopod Ad-to-LP Harmonizer.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.services.personalization import PersonalizationService, DefaultPersonalizationService
from app.core.config import config

router = APIRouter()

def get_personalization_service() -> PersonalizationService:
    """Dependency provider for PersonalizationService."""
    return DefaultPersonalizationService()


@router.get("/")
def root():
    return {"status": "ok", "service": "Troopod Ad-to-LP Harmonizer API"}


@router.get("/api/health")
def health_check():
    return {"status": "healthy"}


@router.post("/api/generate")
async def generate_personalized_page(
    ad_image: UploadFile = File(...),
    landing_page_url: str = Form(...),
    service: PersonalizationService = Depends(get_personalization_service)
):
    """
    Main endpoint: accepts ad creative image + landing page URL.
    Performs API gateway sanity checks and delegates to service.
    """
    # 1. URL Sanity Check
    if not landing_page_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400, 
            detail="Invalid landing page URL. Must start with http:// or https://"
        )
        
    # 2. Content Type Sanity Check
    if not ad_image.content_type or not ad_image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, 
            detail="Uploaded file must be an image."
        )
        
    # Read image bytes
    image_bytes = await ad_image.read()
    
    # 3. File Size Sanity Check (Limit to 10MB for large creatives)
    MAX_SIZE = 10 * 1024 * 1024 # 10MB
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=400, 
            detail="Image size exceeds the 10MB limit."
        )
        
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400, 
            detail="Uploaded image file is empty."
        )
        
    # Delegate to service passing clean bytes
    return await service.personalize(image_bytes, landing_page_url)
