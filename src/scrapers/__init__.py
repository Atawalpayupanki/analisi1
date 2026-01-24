"""
Scrapers module for Phipatia Analitzador.

Provides custom web scrapers for specific news sources that require
special handling beyond standard RSS extraction.
"""

from .elmundo import scrape_elmundo_article
from .elpais import scrape_elpais_article
from .lavanguardia import scrape_lavanguardia_article

__all__ = [
    'scrape_elmundo_article',
    'scrape_elpais_article',
    'scrape_lavanguardia_article',
]
