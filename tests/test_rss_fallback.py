import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.article_processor import process_single_article, ArticleResult

class TestRSSFallback(unittest.TestCase):
    
    @patch('src.article_processor.download_article_html')
    @patch('src.article_processor.extract_article_text')
    def test_fallback_when_extraction_fails(self, mock_extract, mock_download):
        # Setup mock download response (success)
        mock_download_res = MagicMock()
        mock_download_res.status_code = 200
        mock_download_res.html = "<html><body>Some content</body></html>"
        mock_download_res.download_time = 0.1
        mock_download_res.is_blocked = False
        mock_download.return_value = mock_download_res
        
        # Setup mock extraction response (failure/no content)
        mock_extract_res = MagicMock()
        mock_extract_res.text = None
        mock_extract_res.extraction_status = 'no_content'
        mock_extract_res.extraction_method = 'bs4_failed'
        mock_extract_res.metadata = {}
        mock_extract.return_value = mock_extract_res
        
        # Input item with description
        news_item = {
            'nombre_del_medio': 'Test Media',
            'rss_origen': 'http://test.com/rss',
            'titular': 'Test Article',
            'enlace': 'http://test.com/article',
            'descripcion': 'This is the RSS summary description.',
            'fecha': '2023-10-27T10:00:00Z'
        }
        
        # Run function
        result = process_single_article(news_item)
        
        # Verify results
        self.assertEqual(result.scrape_status, 'ok')
        self.assertEqual(result.texto, 'This is the RSS summary description.')
        self.assertEqual(result.extraction_method, 'rss_summary')
        print("\nTest passed: Fallback used correctly!")

    @patch('src.article_processor.download_article_html')
    @patch('src.article_processor.extract_article_text')
    def test_no_fallback_when_no_description(self, mock_extract, mock_download):
        # Setup mock download response (success)
        mock_download_res = MagicMock()
        mock_download_res.status_code = 200
        mock_download_res.html = "<html><body>Some content</body></html>"
        mock_download.return_value = mock_download_res
        
        # Setup mock extraction response (failure)
        mock_extract_res = MagicMock()
        mock_extract_res.text = None
        mock_extract_res.extraction_status = 'no_content'
        mock_extract.return_value = mock_extract_res
        
        # Input item WITHOUT description
        news_item = {
            'nombre_del_medio': 'Test Media',
            'enlace': 'http://test.com/article',
            'descripcion': '' 
        }
        
        # Run function
        result = process_single_article(news_item)
        
        # Verify results
        self.assertNotEqual(result.scrape_status, 'ok')
        self.assertEqual(result.error_message, "No se pudo extraer texto ni hay resumen RSS")
        print("Test passed: No fallback when description is empty!")

if __name__ == '__main__':
    unittest.main()
