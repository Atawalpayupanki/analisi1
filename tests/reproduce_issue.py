
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.article_processor import process_single_article

class TestReproduction(unittest.TestCase):
    def test_rss_description_priority(self):
        # News item with both description and a URL that should be scraped
        news_item = {
            'nombre_del_medio': 'El Mundo',
            'enlace': 'http://elmundo.es/test',
            'titular': 'Titular',
            'fecha': '2023-01-01',
            'descripcion': 'RSS Summary'
        }
        
        # Mock scrape_custom to return full text
        with patch('src.article_processor.scrape_custom') as mock_scrape:
            mock_scrape.return_value = {'titulo': 'Full Title', 'texto': 'Full Article Text'}
            
            result = process_single_article(news_item)
            
            # If the bug exists, result.texto will be 'RSS Summary' instead of 'Full Article Text'
            print(f"\nResult text: {result.texto}")
            print(f"Extraction method: {result.extraction_method}")
            
            self.assertEqual(result.texto, 'Full Article Text', "Should have extracted full text, but got RSS summary")
            self.assertEqual(result.extraction_method, 'custom_scraper')

if __name__ == '__main__':
    unittest.main()
