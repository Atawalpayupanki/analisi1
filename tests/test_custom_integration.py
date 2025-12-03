
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.custom_scrapers import scrape_custom
from src.article_processor import process_single_article, ArticleResult

class TestCustomIntegration(unittest.TestCase):
    def test_scrape_custom_elmundo(self):
        # Mock the scraper module
        with patch('src.custom_scrapers.elmundo_scraper') as mock_scraper:
            mock_scraper.scrape_elmundo_article.return_value = {'titulo': 'Test Mundo', 'texto': 'Contenido Mundo'}
            
            result = scrape_custom('http://elmundo.es/test', 'El Mundo')
            
            self.assertIsNotNone(result)
            self.assertEqual(result['titulo'], 'Test Mundo')
            mock_scraper.scrape_elmundo_article.assert_called_once()

    def test_scrape_custom_elpais(self):
        # Mock the scraper module
        with patch('src.custom_scrapers.elpais_scraper') as mock_scraper:
            mock_scraper.scrape_elpais_article.return_value = {'titulo': 'Test Pais', 'texto': 'Contenido Pais'}
            
            result = scrape_custom('http://elpais.com/test', 'El País')
            
            self.assertIsNotNone(result)
            self.assertEqual(result['titulo'], 'Test Pais')
            mock_scraper.scrape_elpais_article.assert_called_once()

    def test_process_single_article_integration(self):
        # Test that process_single_article calls scrape_custom
        news_item = {
            'nombre_del_medio': 'El Mundo',
            'enlace': 'http://elmundo.es/test',
            'titular': 'Titular RSS',
            'fecha': '2023-01-01',
            'descripcion': '' # Empty description to force scraping
        }
        
        with patch('src.article_processor.scrape_custom') as mock_scrape:
            mock_scrape.return_value = {'titulo': 'Titular Scraped', 'texto': 'Texto Scraped'}
            
            result = process_single_article(news_item)
            
            self.assertEqual(result.texto, 'Texto Scraped')
            self.assertEqual(result.extraction_method, 'custom_scraper')
            mock_scrape.assert_called_once_with('http://elmundo.es/test', 'El Mundo')

if __name__ == '__main__':
    unittest.main()
