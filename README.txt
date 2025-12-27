RSS China News Filter - Analizador de Noticias
==============================================

DESCRIPCIÓN
-----------
Aplicación para descargar feeds RSS de medios españoles y chinos, filtrar 
noticias relacionadas con China, clasificarlas mediante IA y exportar a Excel.

CÓMO EJECUTAR
-------------
1. Activar el entorno virtual:
   .\venv\Scripts\activate

2. Ejecutar la interfaz gráfica:
   python src/gui.py

3. Alternativa: ejecutar desde línea de comandos:
   python src/main.py

CONFIGURACIÓN NECESARIA
-----------------------
Crear archivo .env con las API keys de Groq para el clasificador:
   GROQ_API_KEY=tu_api_key
   GROQ_API_KEY_BACKUP=tu_backup_key

ESTRUCTURA DE ARCHIVOS
----------------------
src/                    - Código fuente principal
  gui.py                - Interfaz gráfica principal
  main.py               - Entrada por línea de comandos
  clasificador_langchain.py - Clasificador con IA
  parser.py             - Parser de feeds RSS
  downloader.py         - Descarga de feeds
  article_processor.py  - Procesamiento de artículos
  excel_storage.py      - Exportación a Excel
  noticias_db.py        - Base de datos CSV
  
config/                 - Archivos de configuración
  feeds.json            - Feeds RSS españoles
  rss_feeds_zh.json     - Feeds RSS chinos
  keywords.json         - Palabras clave para filtro

data/                   - Datos generados
  noticias_china.csv    - Base de datos de noticias
  noticias_historico.xlsx - Excel con análisis

scrap el mundo/         - Scraper personalizado El Mundo
scrap el pais/          - Scraper personalizado El País

visualizador.html       - Visualizador web de datos
abrir_visualizador.py   - Script para abrir visualizador

DEPENDENCIAS
------------
Ver requirements.txt. Instalar con: pip install -r requirements.txt
