"""
FastAPI Orchestrator
Main API server that coordinates the Ad-to-LP Harmonizer pipeline.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.routes import router

load_dotenv()

app = FastAPI(
    title="Troopod Ad-to-LP Harmonizer",
    description="AI-powered landing page personalization based on ad creatives",
    version="1.0.0"
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
