"""
FastAPI Backend for Phipatia Analitzador.
Serves news data and statistics to the frontend.
"""
import sys
import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add src to path to import existing modules
sys.path.append(os.path.join(os.getcwd(), '..', 'src'))

# Import from core
try:
    from noticias_db import obtener_db, NoticiasDB
except ImportError:
    # Handle direct execution vs module import
    sys.path.append(os.path.join(os.getcwd(), '../src'))
    from noticias_db import obtener_db

app = FastAPI(
    title="Phipatia Analitzador API",
    description="Backend API for China News Analysis Tool",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class NewsItem(BaseModel):
    url: str
    medio: str
    titular: str
    fecha: str
    descripcion: str
    texto_completo: str
    tema: str
    imagen_de_china: str
    estado: str
    fecha_procesado: str

class Stats(BaseModel):
    total_articles: int
    by_state: dict
    last_update: str

# Endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/articles", response_model=List[NewsItem])
async def get_articles(
    limit: int = 50, 
    offset: int = 0,
    state: Optional[str] = None
):
    """Get list of articles with optional filtering."""
    db = obtener_db("../data/noticias_china.csv")
    db.cargar()  # Reload to get latest
    
    all_data = db.datos
    
    if state:
        filtered = [d for d in all_data if d.get('estado') == state]
    else:
        filtered = all_data
        
    # Sort by date (newest first) - assuming date format allows string sort
    # Ideally should parse date, but string sort might work for ISO
    filtered.sort(key=lambda x: x.get('fecha_procesado', ''), reverse=True)
    
    return filtered[offset : offset + limit]

@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """Get database statistics."""
    db = obtener_db("../data/noticias_china.csv")
    db.cargar()
    
    from datetime import datetime
    
    return {
        "total_articles": db.total(),
        "by_state": db.contar_por_estado(),
        "last_update": datetime.now().isoformat()
    }

# Run with: uvicorn main:app --reload
