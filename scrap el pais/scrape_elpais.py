import requests
from bs4 import BeautifulSoup

def scrape_elpais_article(url):
    """
    Extrae el texto de un artículo de El País
    
    Args:
        url: URL del artículo de El País
        
    Returns:
        dict con 'titulo' y 'texto' del artículo
    """
    # Configurar headers para simular un navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Realizar la petición
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Parsear el HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraer el título
    titulo_tag = soup.find('h1')
    titulo = titulo_tag.get_text(strip=True) if titulo_tag else "Título no encontrado"
    
    # Extraer el texto del artículo
    # El País usa la clase 'article_body' para el contenido principal
    article_body = soup.find('article')
    
    if article_body:
        # Buscar todos los párrafos dentro del artículo
        paragraphs = article_body.find_all('p')
        texto = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    else:
        texto = "Contenido no encontrado"
    
    return {
        'titulo': titulo,
        'texto': texto
    }


if __name__ == '__main__':
    # URL del artículo
    url = 'https://elpais.com/internacional/2025-12-03/malasia-retoma-la-busqueda-del-vuelo-mh370-uno-de-los-mayores-misterios-de-la-aviacion.html'
    
    print("Scrapeando artículo de El País...")
    print(f"URL: {url}\n")
    
    try:
        resultado = scrape_elpais_article(url)
        
        print("=" * 80)
        print("TÍTULO:")
        print("=" * 80)
        print(resultado['titulo'])
        print("\n" + "=" * 80)
        print("TEXTO DEL ARTÍCULO:")
        print("=" * 80)
        print(resultado['texto'])
        
    except Exception as e:
        print(f"Error al scrapear el artículo: {e}")
