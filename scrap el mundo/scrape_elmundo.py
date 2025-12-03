import requests
from bs4 import BeautifulSoup

def scrape_elmundo_article(url):
    """
    Extrae el texto de una noticia de El Mundo.
    
    Args:
        url: URL de la noticia
        
    Returns:
        dict con título y texto de la noticia
    """
    # Realizar la petición HTTP
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Parsear el HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraer el título
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else "Sin título"
    
    # Extraer el texto del artículo
    # En El Mundo, el contenido está en divs con clase 'ue-l-article__body'
    article_body = soup.find('div', class_='ue-l-article__body')
    
    if article_body:
        # Obtener todos los párrafos dentro del cuerpo del artículo
        paragraphs = article_body.find_all('p')
        text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    else:
        text = "No se pudo extraer el texto del artículo"
    
    return {
        'titulo': title,
        'texto': text
    }


if __name__ == '__main__':
    # URL de la noticia
    url = 'https://www.elmundo.es/papel/historias/2025/03/19/67d42506e9cf4a15708b459c.html'
    
    print("Extrayendo noticia de El Mundo...")
    print(f"URL: {url}\n")
    
    try:
        resultado = scrape_elmundo_article(url)
        
        print("=" * 80)
        print(f"TÍTULO: {resultado['titulo']}")
        print("=" * 80)
        print(f"\n{resultado['texto']}\n")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error al extraer la noticia: {e}")
