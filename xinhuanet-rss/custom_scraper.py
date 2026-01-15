"""
Custom RSS Feed Generator for Xinhuanet
Scraper sencillo con requests y BeautifulSoup
"""

import sys
import io

# Configurar salida UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict
import time
import re
import os


class XinhuanetScraper:
    """Scraper personalizado para generar feeds RSS de Xinhuanet"""
    
    def __init__(self):
        self.base_url = "http://www.news.cn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Mapeo de categorías con múltiples URLs como fallback
        self.categories = {
            'china': {
                'urls': [
                    '/politics/index.htm',
                    '/politics/',
                    '/politics/xxjxs/index.htm',  # Sección Xi Jinping
                ],
                'title': '国内新闻',
                'section_patterns': ['/politics/', '/szyw/', '/local/']
            },
            'world': {
                'urls': [
                    '/world/index.htm',
                    '/world/',
                ],
                'title': '国际新闻',
                'section_patterns': ['/world/', '/silkroad/']
            },
            'finance': {
                'urls': [
                    '/fortune/index.htm',
                    '/fortune/',
                ],
                'title': '财经新闻',
                'section_patterns': ['/fortune/', '/money/', '/house/']
            },
            'tech': {
                'urls': [
                    '/tech/index.htm',
                    '/tech/',
                    '/science/',
                ],
                'title': '科技新闻',
                'section_patterns': ['/tech/', '/science/', '/it/']
            },
            'sports': {
                'urls': [
                    '/sports/index.htm',
                    '/sports/',
                ],
                'title': '体育新闻',
                'section_patterns': ['/sports/']
            },
            'ent': {
                'urls': [
                    '/ent/index.htm',
                    '/ent/',
                    '/culture/',
                ],
                'title': '娱乐新闻',
                'section_patterns': ['/ent/', '/culture/', '/book/']
            },
        }
    
    def _extract_date_from_url(self, url: str) -> tuple:
        """Extrae la fecha de la URL de Xinhuanet. Retorna (fecha_str, datetime_obj)"""
        # Patrón: /fortune/20260114/ o /fortune/2022-07/13/
        patterns = [
            r'/(\d{4})(\d{2})(\d{2})/',  # 20260114
            r'/(\d{4})-(\d{2})/(\d{2})/',  # 2022-07/13
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                groups = match.groups()
                try:
                    year = int(groups[0])
                    month = int(groups[1])
                    day = int(groups[2])
                    dt = datetime(year, month, day)
                    return (dt.strftime('%a, %d %b %Y %H:%M:%S +0800'), dt)
                except (ValueError, IndexError):
                    pass
        
        return (datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800'), None)
    
    def _is_recent_article(self, url: str, days_threshold: int = 90) -> bool:
        """Verifica si un artículo es reciente (últimos N días)"""
        _, date_obj = self._extract_date_from_url(url)
        if date_obj:
            days_ago = (datetime.now() - date_obj).days
            return 0 <= days_ago <= days_threshold
        return False
    
    def _is_valid_news_url(self, href: str, section_patterns: list = None) -> bool:
        """Verifica si una URL es de una noticia válida"""
        if not href:
            return False
        
        # Excluir URLs que no son noticias
        exclude_patterns = [
            'index.htm',
            'index.html',
            'javascript:',
            '#',
            '.jpg', '.png', '.gif', '.css', '.js',
            '/video/', '/live/', '/vod/',
            'weixin', 'weibo',
        ]
        
        for pattern in exclude_patterns:
            if pattern in href.lower():
                return False
        
        # Debe tener un patrón de fecha
        has_date = bool(re.search(r'/\d{8}/', href) or re.search(r'/\d{4}-\d{2}/\d{2}/', href))
        
        # Si hay patrones de sección, verificar que la URL pertenezca a una sección válida
        if section_patterns and has_date:
            for pattern in section_patterns:
                if pattern in href:
                    return True
        
        # Aceptar URLs con /c.html que son artículos típicos
        if '/c.html' in href and has_date:
            return True
        
        return has_date
    
    def _fetch_page(self, url: str) -> BeautifulSoup:
        """Descarga y parsea una página"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"    Error fetching {url}: {e}")
            return None
    
    def scrape_category(self, category: str, max_items: int = 30) -> List[Dict]:
        """
        Extrae noticias de una categoría específica
        
        Args:
            category: Nombre de la categoría (china, world, finance, etc.)
            max_items: Número máximo de noticias a extraer
            
        Returns:
            Lista de diccionarios con información de las noticias
        """
        if category not in self.categories:
            raise ValueError(f"Categoría no válida: {category}")
        
        cat_info = self.categories[category]
        section_patterns = cat_info.get('section_patterns', [])
        articles = []
        seen_urls = set()
        
        # Intentar cada URL de la categoría
        for url_path in cat_info['urls']:
            if len(articles) >= max_items:
                break
            
            url = self.base_url + url_path
            print(f"    Fetching: {url}")
            
            soup = self._fetch_page(url)
            if not soup:
                continue
            
            # Buscar todos los enlaces
            all_links = soup.find_all('a', href=True)
            print(f"    Found {len(all_links)} links")
            
            for link in all_links:
                if len(articles) >= max_items:
                    break
                
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # Filtrar enlaces inválidos
                if not title or len(title) < 6:
                    continue
                
                # Construir URL completa
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = self.base_url + href
                elif not href.startswith('http'):
                    continue
                
                # Verificar si es una URL de noticia válida
                if not self._is_valid_news_url(href, section_patterns):
                    continue
                
                # Solo incluir artículos recientes
                if not self._is_recent_article(href, days_threshold=90):
                    continue
                
                # Evitar duplicados
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                # Extraer fecha de la URL
                pub_date, date_obj = self._extract_date_from_url(href)
                
                articles.append({
                    'title': title,
                    'link': href,
                    'description': title,
                    'pub_date': pub_date,
                    'guid': href,
                    'date_obj': date_obj  # Para ordenar
                })
            
            # Pausa breve entre URLs
            time.sleep(0.5)
        
        # Ordenar por fecha (más recientes primero)
        articles.sort(key=lambda x: x.get('date_obj') or datetime.min, reverse=True)
        
        # Remover el campo auxiliar date_obj
        for article in articles:
            article.pop('date_obj', None)
        
        print(f"    Total: {len(articles)} recent articles")
        return articles
    
    def generate_rss(self, category: str, output_file: str = None) -> str:
        """
        Genera un feed RSS para una categoría
        
        Args:
            category: Nombre de la categoría
            output_file: Ruta del archivo de salida (opcional)
            
        Returns:
            String con el XML del feed RSS
        """
        articles = self.scrape_category(category)
        
        # Crear estructura RSS
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        
        # Metadatos del canal
        ET.SubElement(channel, 'title').text = f"新华网 - {self.categories[category]['title']}"
        ET.SubElement(channel, 'link').text = self.base_url + self.categories[category]['urls'][0]
        
        if articles:
            ET.SubElement(channel, 'description').text = f"新华网{self.categories[category]['title']}RSS订阅"
        else:
            ET.SubElement(channel, 'description').text = f"新华网{self.categories[category]['title']}RSS订阅 - Sin artículos disponibles"
            print(f"    Warning: No se encontraron artículos para {category}")
        
        ET.SubElement(channel, 'language').text = 'zh-CN'
        ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')
        
        # Agregar artículos
        for article in articles:
            item = ET.SubElement(channel, 'item')
            ET.SubElement(item, 'title').text = article['title']
            ET.SubElement(item, 'link').text = article['link']
            ET.SubElement(item, 'description').text = article['description']
            ET.SubElement(item, 'pubDate').text = article['pub_date']
            ET.SubElement(item, 'guid').text = article['guid']
        
        # Formatear XML
        xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
        
        # Guardar si se especifica archivo
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            print(f"    Saved: {output_file}")
        
        return xml_str
    
    def generate_all_feeds(self, output_dir: str = './feeds'):
        """Genera feeds RSS para todas las categorías"""
        os.makedirs(output_dir, exist_ok=True)
        
        total = len(self.categories)
        success_count = 0
        
        for idx, (category, info) in enumerate(self.categories.items(), 1):
            print(f"[{idx}/{total}] Generando feed: {category} ({info['title']})")
            output_file = os.path.join(output_dir, f'xinhua_{category}.xml')
            
            try:
                xml = self.generate_rss(category, output_file)
                if xml and '<item>' in xml:
                    success_count += 1
                    print(f"    OK")
                else:
                    print(f"    Warning: Feed vacío")
            except Exception as e:
                print(f"    ERROR: {e}")
            
            print()
        
        print("=" * 60)
        print(f"Resultado: {success_count}/{total} feeds generados correctamente")
        print(f"Feeds en: {os.path.abspath(output_dir)}")


def main():
    """Función principal"""
    scraper = XinhuanetScraper()
    
    print("=" * 60)
    print("Generando feeds RSS para Xinhuanet (新华网)")
    print("=" * 60)
    print()
    
    scraper.generate_all_feeds('./feeds')
    
    print()
    print("Feeds disponibles:")
    print("  - xinhua_china.xml      (国内 - Nacional)")
    print("  - xinhua_world.xml      (国际 - Internacional)")
    print("  - xinhua_finance.xml    (财经 - Finanzas)")
    print("  - xinhua_tech.xml       (科技 - Tecnología)")
    print("  - xinhua_sports.xml     (体育 - Deportes)")
    print("  - xinhua_ent.xml        (娱乐 - Entretenimiento)")
    print("=" * 60)


if __name__ == '__main__':
    main()
