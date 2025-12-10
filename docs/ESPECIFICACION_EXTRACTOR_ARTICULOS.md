
# Especificación Técnica: Módulo de Extracción de Texto Completo de Artículos

## 1. Visión General

### 1.1 Objetivo
Desarrollar un módulo integrado en el proyecto **RSS China News Filter** que descargue y extraiga el texto completo de artículos de noticias desde sus URLs, produciendo contenido limpio y normalizado para análisis posterior.

### 1.2 Alcance
- Procesamiento de ~100-500 noticias/día
- Extracción robusta con fallbacks inteligentes
- Integración con la arquitectura modular existente
- Soporte para medios españoles (El País, El Mundo, ABC, La Vanguardia, La Razón)
- Manejo de bloqueos y contenido dinámico

### 1.3 Principios de Diseño
- **Coherencia**: Mantener el estilo arquitectónico del proyecto actual
- **Robustez**: Nunca fallar completamente; degradar gracefully
- **Eficiencia**: Optimizado para volumen medio sin sobrecarga
- **Observabilidad**: Logging detallado y métricas de ejecución

---

## 2. Arquitectura del Sistema

### 2.1 Integración con Proyecto Existente

```
f:/pautalla/china/
├── src/
│   ├── feeds_list.py           # [EXISTENTE] Carga feeds
│   ├── downloader.py           # [EXISTENTE] Descarga RSS
│   ├── parser.py               # [EXISTENTE] Parsea RSS
│   ├── filtro_china.py         # [EXISTENTE] Filtra keywords
│   ├── deduplicador.py         # [EXISTENTE] Deduplicación
│   ├── almacenamiento.py       # [EXISTENTE] Guarda resultados
│   ├── main.py                 # [EXISTENTE] CLI principal
│   ├── gui.py                  # [EXISTENTE] GUI Tkinter
│   │
│   ├── article_downloader.py   # [NUEVO] Descarga HTML de artículos
│   ├── article_extractor.py    # [NUEVO] Extrae texto con trafilatura
│   ├── article_cleaner.py      # [NUEVO] Limpia y normaliza texto
│   ├── article_enricher.py     # [NUEVO] Detecta idioma y metadatos
│   ├── article_fallback.py     # [NUEVO] Fallback con Playwright (opcional)
│   ├── article_processor.py    # [NUEVO] Orquestador principal
│   └── main_extractor.py       # [NUEVO] CLI para extracción
│
├── config/
│   ├── feeds.json              # [EXISTENTE]
│   ├── keywords.json           # [EXISTENTE]
│   └── extractor_config.yaml   # [NUEVO] Configuración extractor
│
├── data/
│   ├── output.jsonl            # [EXISTENTE] Noticias filtradas
│   ├── output.csv              # [EXISTENTE]
│   ├── articles_full.jsonl     # [NUEVO] Artículos completos
│   ├── articles_full.csv       # [NUEVO]
│   └── failed_extractions.jsonl # [NUEVO] URLs fallidas
│
├── logs/
│   ├── rss_china.log           # [EXISTENTE]
│   ├── rss_china_gui.log       # [EXISTENTE]
│   └── article_extractor.log   # [NUEVO]
│
├── docs/
│   ├── ESPECIFICACION_EXTRACTOR_ARTICULOS.md  # [ESTE DOCUMENTO]
│   └── ESTRATEGIA_FALLBACK.md  # [NUEVO] Guía de fallbacks
│
├── tests/
│   └── test_article_extractor/ # [NUEVO] Tests unitarios
│       ├── test_downloader.py
│       ├── test_extractor.py
│       ├── test_cleaner.py
│       └── test_integration.py
│
├── requirements.txt            # [ACTUALIZAR] Añadir nuevas deps
└── README.md                   # [ACTUALIZAR] Documentar nuevo módulo
```

### 2.2 Flujo de Datos

```
[output.jsonl] → article_processor
                      ↓
              article_downloader (HTML)
                      ↓
              article_extractor (trafilatura)
                      ↓
         ┌────────────┴────────────┐
         ↓                         ↓
   [texto OK]              [texto vacío/corto]
         ↓                         ↓
   article_cleaner         article_fallback (Playwright)
         ↓                         ↓
   article_enricher         article_cleaner
         ↓                         ↓
         └────────────┬────────────┘
                      ↓
              [articles_full.jsonl]
              [articles_full.csv]
              [failed_extractions.jsonl]
```

---

## 3. Módulos y Responsabilidades

### 3.1 `article_downloader.py`

**Responsabilidad**: Descarga HTML de URLs de artículos con reintentos y rate limiting.

**Funciones principales**:
- `download_article_html(url: str, timeout: int, headers: dict) -> Tuple[str, str, int]`
  - Retorna: `(html_content, final_url, status_code)`
  - Maneja redirecciones automáticas
  - Aplica reintentos con backoff exponencial (tenacity)

- `download_articles_batch(urls: List[str], concurrency: int, delay_per_domain: float) -> List[DownloadResult]`
  - Descarga batch con control de concurrencia
  - Rate limiting por dominio
  - Retorna lista de `DownloadResult` (dataclass)

**Configuración**:
```python
DEFAULT_TIMEOUT = 15  # segundos
MAX_RETRIES = 3
BACKOFF_MULTIPLIER = 2
DELAY_BETWEEN_REQUESTS_SAME_DOMAIN = 1.0  # segundos
DEFAULT_USER_AGENT = 'Mozilla/5.0 (compatible; RSSChinaBot-ArticleExtractor/1.0)'
```

**Manejo de errores**:
- `200`: OK, devolver HTML
- `3xx`: Seguir redirecciones (automático con requests)
- `404, 410`: Error permanente, no reintentar
- `429, 503`: Rate limit / servidor ocupado, reintentar con backoff mayor
- `5xx`: Error temporal, reintentar
- `Timeout`: Reintentar hasta MAX_RETRIES
- `ConnectionError`: Reintentar hasta MAX_RETRIES

**Detección de bloqueos**:
- Buscar patrones en HTML: "captcha", "robot", "blocked", "access denied"
- Verificar Content-Type (debe ser text/html)
- Tamaño sospechoso (< 500 bytes o > 10MB)

**Dataclass de salida**:
```python
@dataclass
class DownloadResult:
    url: str
    html: Optional[str]
    final_url: str
    status_code: int
    download_status: str  # 'ok', 'error', 'blocked', 'timeout'
    error_message: str
    download_time: float  # segundos
```

---

### 3.2 `article_extractor.py`

**Responsabilidad**: Extraer texto principal del artículo usando trafilatura.

**Funciones principales**:
- `extract_article_text(html: str, url: str) -> ExtractionResult`
  - Usa `trafilatura.extract()` con configuración optimizada
  - Detecta idioma automáticamente
  - Extrae metadatos (autor, fecha publicación si disponible)

- `extract_with_fallback_bs4(html: str, url: str) -> Optional[str]`
  - Fallback con BeautifulSoup si trafilatura falla
  - Busca selectores comunes: `<article>`, `.article-body`, `.entry-content`, etc.
  - Selectores específicos por dominio (elpais.com, elmundo.es, etc.)

**Configuración trafilatura**:
```python
TRAFILATURA_CONFIG = {
    'include_comments': False,
    'include_tables': True,
    'include_images': False,
    'include_links': False,
    'output_format': 'txt',
    'favor_precision': True,  # Menos ruido, más precisión
    'deduplicate': True
}

MIN_TEXT_LENGTH_OK = 200  # caracteres mínimos para considerar OK
MIN_TEXT_LENGTH_WARNING = 100  # advertencia si es muy corto
```

**Selectores BeautifulSoup por dominio**:
```python
DOMAIN_SELECTORS = {
    'elpais.com': ['article.a_c', 'div.a_c_text', 'div.articulo-cuerpo'],
    'elmundo.es': ['article.ue-l-article__body', 'div.ue-c-article__body'],
    'abc.es': ['div.voc-article-content', 'div.cuerpo-texto'],
    'lavanguardia.com': ['div.article-modules', 'div.article-body'],
    'larazon.es': ['div.article-content', 'div.texto-noticia']
}
```

**Dataclass de salida**:
```python
@dataclass
class ExtractionResult:
    texto: str
    idioma: Optional[str]
    autor: Optional[str]
    fecha_publicacion: Optional[str]
    extraction_method: str  # 'trafilatura', 'bs4_fallback', 'playwright'
    extraction_status: str  # 'ok', 'no_contenido', 'error'
    char_count: int
    word_count: int
```

---

### 3.3 `article_cleaner.py`

**Responsabilidad**: Limpiar y normalizar texto extraído.

**Funciones principales**:
- `clean_article_text(text: str) -> str`
  - Normalización Unicode (NFKC)
  - Eliminar scripts, estilos residuales
  - Eliminar fragmentos repetitivos comunes
  - Unificar saltos de línea
  - Trimming y saneamiento

**Patrones de limpieza**:
```python
REMOVE_PATTERNS = [
    r'Leer también:.*?(?=\n|$)',
    r'Ver galería.*?(?=\n|$)',
    r'Relacionado:.*?(?=\n|$)',
    r'Suscríbete.*?(?=\n|$)',
    r'Más información.*?(?=\n|$)',
    r'\[foto\]|\[vídeo\]|\[galería\]',
    r'Compartir en.*?(?=\n|$)',
    r'Síguenos en.*?(?=\n|$)'
]

MAX_CONSECUTIVE_NEWLINES = 2
MAX_CONSECUTIVE_SPACES = 1
```

**Normalización**:
- Convertir entidades HTML residuales
- Normalizar comillas tipográficas a ASCII
- Eliminar caracteres de control
- Unificar espacios en blanco
- Eliminar líneas vacías múltiples

---

### 3.4 `article_enricher.py`

**Responsabilidad**: Enriquecer metadatos del artículo.

**Funciones principales**:
- `detect_language(text: str) -> str`
  - Usar detección de trafilatura primero
  - Fallback a heurística simple (contar palabras españolas comunes)

- `extract_metadata_from_html(html: str, url: str) -> dict`
  - Buscar metadatos en `<meta>` tags (Open Graph, Twitter Cards)
  - Extraer autor de selectores comunes
  - Extraer fecha de publicación si no está en RSS

**Metadatos a extraer**:
```python
METADATA_FIELDS = {
    'og:title': 'titulo_og',
    'og:description': 'descripcion_og',
    'og:image': 'imagen_og',
    'article:author': 'autor',
    'article:published_time': 'fecha_publicacion',
    'article:section': 'seccion'
}
```

---

### 3.5 `article_fallback.py`

**Responsabilidad**: Fallback con Playwright para contenido dinámico (JavaScript).

**Funciones principales**:
- `extract_with_playwright(url: str, timeout: int) -> Tuple[str, str]`
  - Lanza navegador headless
  - Espera carga completa (networkidle)
  - Extrae HTML renderizado
  - Retorna: `(html, screenshot_path)`

**Configuración**:
```python
PLAYWRIGHT_ENABLED = False  # Desactivado por defecto
PLAYWRIGHT_TIMEOUT = 30000  # ms
PLAYWRIGHT_WAIT_FOR = 'networkidle'
PLAYWRIGHT_BROWSER = 'chromium'
PLAYWRIGHT_HEADLESS = True
MAX_PLAYWRIGHT_CALLS_PER_RUN = 10  # Límite de seguridad
```

**Política de activación**:
- Solo si `extraction_status == 'blocked'` o `'no_contenido'`
- Solo si dominio está en whitelist configurable
- Solo si no se ha superado límite de llamadas

**Whitelist de dominios**:
```python
PLAYWRIGHT_WHITELIST_DOMAINS = [
    # Añadir solo dominios que requieren JS
    # Ejemplo: 'ejemplo-dinamico.com'
]
```

---

### 3.6 `article_processor.py`

**Responsabilidad**: Orquestador principal del flujo de extracción.

**Funciones principales**:
- `process_articles(input_file: str, config: dict) -> ProcessingReport`
  - Lee noticias desde `output.jsonl`
  - Orquesta descarga → extracción → limpieza → enriquecimiento
  - Guarda resultados en `articles_full.jsonl` y `articles_full.csv`
  - Genera reporte de ejecución

- `process_single_article(news_item: dict, config: dict) -> ArticleResult`
  - Procesa un artículo individual
  - Maneja errores sin interrumpir flujo
  - Retorna resultado completo

**Modelo de datos de salida**:
```python
@dataclass
class ArticleResult:
    # Campos originales (del RSS)
    nombre_del_medio: str
    enlace: str
    titular: str
    fecha: str
    descripcion: str
    
    # Campos nuevos (extracción)
    texto: str
    idioma: str
    autor: Optional[str]
    fecha_publicacion: Optional[str]
    
    # Metadatos de extracción
    scrape_status: str  # 'ok', 'no_contenido_detectado', 'error_descarga', 
                        # 'error_parseo', 'blocked_fallback_required'
    error_message: str
    extraction_method: str  # 'trafilatura', 'bs4_fallback', 'playwright'
    char_count: int
    word_count: int
    download_time: float
    extraction_time: float
```

**Reporte de ejecución**:
```python
@dataclass
class ProcessingReport:
    total_articles: int
    successful: int
    failed_download: int
    failed_extraction: int
    no_content: int
    blocked: int
    playwright_used: int
    
    total_time: float
    avg_time_per_article: float
    
    failed_urls: List[Tuple[str, str]]  # (url, reason)
    domains_needing_fallback: Set[str]
```

---

### 3.7 `main_extractor.py`

**Responsabilidad**: CLI para ejecutar extracción de artículos.

**Interfaz CLI**:
```bash
python src/main_extractor.py \
    --input data/output.jsonl \
    --output data/articles_full.jsonl \
    --config config/extractor_config.yaml \
    --concurrency 5 \
    --enable-playwright \
    --log-level INFO
```

**Argumentos**:
- `--input`: Archivo JSONL con noticias filtradas (default: `data/output.jsonl`)
- `--output`: Archivo JSONL de salida (default: `data/articles_full.jsonl`)
- `--config`: Archivo de configuración (default: `config/extractor_config.yaml`)
- `--concurrency`: Nivel de concurrencia (default: 5)
- `--enable-playwright`: Activar fallback Playwright (flag)
- `--log-level`: Nivel de logging (default: INFO)
- `--max-articles`: Límite de artículos a procesar (para testing)

**Salida**:
- `articles_full.jsonl`: Artículos completos
- `articles_full.csv`: Artículos completos en CSV
- `failed_extractions.jsonl`: URLs fallidas con razón
- `extraction_report.json`: Reporte de ejecución

---

## 4. Configuración

### 4.1 `config/extractor_config.yaml`

```yaml
# Configuración del extractor de artículos

downloader:
  timeout: 15
  max_retries: 3
  backoff_multiplier: 2
  delay_between_requests_same_domain: 1.0
  user_agent: "Mozilla/5.0 (compatible; RSSChinaBot-ArticleExtractor/1.0)"
  headers:
    Accept-Language: "es-ES,es;q=0.9,en;q=0.8"
    Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

extractor:
  min_text_length_ok: 200
  min_text_length_warning: 100
  favor_precision: true
  include_tables: true
  include_comments: false

cleaner:
  max_consecutive_newlines: 2
  normalize_unicode: true
  remove_common_fragments: true

enricher:
  extract_metadata: true
  detect_language: true

fallback:
  playwright_enabled: false
  playwright_timeout: 30000
  playwright_browser: "chromium"
  playwright_headless: true
  max_playwright_calls_per_run: 10
  playwright_whitelist_domains: []

processing:
  concurrency: 5
  max_articles_per_run: null  # null = sin límite
  skip_already_processed: true

output:
  jsonl_path: "data/articles_full.jsonl"
  csv_path: "data/articles_full.csv"
  failed_path: "data/failed_extractions.jsonl"
  report_path: "data/extraction_report.json"
  csv_encoding: "utf-8-sig"  # UTF-8 con BOM para Excel

logging:
  log_file: "logs/article_extractor.log"
  log_level: "INFO"
  log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## 5. Dependencias

### 5.1 `requirements.txt` (actualizado)

```txt
# Dependencias existentes
feedparser>=6.0.10
requests>=2.31.0
aiohttp>=3.9.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
python-dateutil>=2.8.2
tenacity>=8.2.0
tqdm>=4.66.0
pydantic>=2.5.0

# Nuevas dependencias para extracción de artículos
trafilatura>=1.6.0
playwright>=1.40.0
PyYAML>=6.0.1
langdetect>=1.0.9
```

### 5.2 Instalación de Playwright

```bash
# Después de pip install playwright
playwright install chromium
```

---

## 6. Manejo de Errores y Robustez

### 6.1 Política de Errores

**Principio**: Nunca detener ejecución completa por error en un artículo.

**Estrategia**:
1. Capturar excepciones a nivel de artículo individual
2. Registrar error con stack trace en logs
3. Marcar artículo con `scrape_status` apropiado
4. Continuar con siguiente artículo
5. Generar reporte de URLs fallidas al final

### 6.2 Clasificación de Errores

| Error | scrape_status | Acción |
|-------|---------------|--------|
| Timeout descarga | `error_descarga` | Reintentar hasta MAX_RETRIES |
| HTTP 404/410 | `error_descarga` | No reintentar, marcar permanente |
| HTTP 5xx | `error_descarga` | Reintentar con backoff |
| Bloqueo detectado | `blocked_fallback_required` | Activar Playwright si enabled |
| Trafilatura devuelve None | `no_contenido_detectado` | Intentar BS4 fallback |
| Texto < MIN_LENGTH | `no_contenido_detectado` | Intentar BS4 fallback |
| Error en limpieza | `error_parseo` | Guardar texto sin limpiar |
| Error en Playwright | `blocked_fallback_required` | Marcar y continuar |

### 6.3 Reintentos con Tenacity

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((
        requests.Timeout,
        requests.ConnectionError,
        requests.HTTPError
    ))
)
def download_with_retry(url, timeout):
    # Implementación
    pass
```

### 6.4 Rate Limiting por Dominio

```python
from collections import defaultdict
import time

class DomainRateLimiter:
    def __init__(self, delay: float):
        self.delay = delay
        self.last_request = defaultdict(float)
    
    def wait_if_needed(self, domain: str):
        elapsed = time.time() - self.last_request[domain]
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request[domain] = time.time()
```

---

## 7. Concurrencia y Rendimiento

### 7.1 Estrategias de Concurrencia

**Opción 1: Secuencial** (`concurrency=1`)
- Más simple y seguro
- Adecuado para < 50 artículos
- Tiempo estimado: ~5-10s por artículo = 8-17 min para 100 artículos

**Opción 2: ThreadPoolExecutor** (`concurrency=5`)
- Balance entre velocidad y cortesía
- Adecuado para 50-500 artículos
- Tiempo estimado: ~2-3s por artículo = 3-5 min para 100 artículos

**Opción 3: AsyncIO + aiohttp** (`concurrency=10`)
- Máxima velocidad
- Requiere más recursos
- Adecuado para > 500 artículos
- Tiempo estimado: ~1-2s por artículo = 2-3 min para 100 artículos

### 7.2 Implementación Recomendada

**Para el proyecto actual**: ThreadPoolExecutor con `concurrency=5`

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_articles_concurrent(articles, config):
    concurrency = config['processing']['concurrency']
    results = []
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(process_single_article, article, config): article
            for article in articles
        }
        
        for future in tqdm(as_completed(futures), total=len(articles)):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing article: {e}")
    
    return results
```

### 7.3 Límites y Recomendaciones

- **Concurrency recomendada**: 5 (balance óptimo)
- **Delay por dominio**: 1.0s (respetuoso con servidores)
- **Timeout por artículo**: 15s (suficiente para mayoría de casos)
- **Volumen diario recomendado**: 100-500 artículos
- **Tiempo ejecución estimado**: 5-15 minutos para 100 artículos

---

## 8. Logging y Monitoreo

### 8.1 Configuración de Logging

```python
import logging
from pathlib import Path

def setup_logging(log_file: str, log_level: str):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
```

### 8.2 Eventos a Registrar

**INFO**:
- Inicio/fin de ejecución
- Número de artículos a procesar
- Progreso cada 10 artículos
- Resumen final

**WARNING**:
- Texto extraído muy corto (< MIN_LENGTH_WARNING)
- Bloqueo detectado
- Fallback activado
- Reintentos

**ERROR**:
- Errores de descarga permanentes
- Errores de extracción
- Excepciones no esperadas

### 8.3 Métricas a Recopilar

```python
@dataclass
class ExecutionMetrics:
    start_time: datetime
    end_time: datetime
    total_articles: int
    
    # Por status
    status_counts: Dict[str, int]
    
    # Por método de extracción
    extraction_method_counts: Dict[str, int]
    
    # Tiempos
    total_download_time: float
    total_extraction_time: float
    avg_time_per_article: float
    
    # Dominios problemáticos
    domains_with_errors: Dict[str, int]
    domains_needing_playwright: Set[str]
```

### 8.4 Reporte Final

```json
{
  "execution_summary": {
    "start_time": "2025-11-26T18:00:00",
    "end_time": "2025-11-26T18:12:34",
    "duration_seconds": 754,
    "total_articles": 100
  },
  "results": {
    "successful": 87,
    "failed_download": 5,
    "failed_extraction": 3,
    "no_content": 4,
    "blocked": 1
  },
  "extraction_methods": {
    "trafilatura": 82,
    "bs4_fallback": 5,
    "playwright": 0
  },
  "performance": {
    "avg_time_per_article": 7.54,
    "total_download_time": 423.2,
    "total_extraction_time": 89.3
  },
  "problematic_domains": {
    "ejemplo.com": {
      "errors": 3,
      "needs_playwright": false
    }
  },
  "failed_urls": [
    {
      "url": "https://ejemplo.com/articulo",
      "reason": "HTTP 404",
      "status": "error_descarga"
    }
  ]
}
```

---

## 9. Testing y Validación

### 9.1 Tests Unitarios

**`tests/test_article_extractor/test_downloader.py`**:
```python
def test_download_success():
    # Mock requests.get con respuesta 200
    # Verificar que devuelve HTML correcto

def test_download_404():
    # Mock requests.get con respuesta 404
    # Verificar que marca error_descarga

def test_download_timeout():
    # Mock timeout
    # Verificar reintentos

def test_download_blocked():
    # Mock respuesta con captcha
    # Verificar detección de bloqueo
```

**`tests/test_article_extractor/test_extractor.py`**:
```python
def test_extract_with_trafilatura():
    # HTML con artículo bien formado
    # Verificar extracción correcta

def test_extract_no_content():
    # HTML sin contenido de artículo
    # Verificar que devuelve no_contenido

def test_extract_bs4_fallback():
    # HTML que trafilatura no puede parsear
    # Verificar que BS4 fallback funciona
```

**`tests/test_article_extractor/test_cleaner.py`**:
```python
def test_clean_unicode():
    # Texto con caracteres especiales
    # Verificar normalización

def test_remove_fragments():
    # Texto con "Leer también:", etc.
    # Verificar eliminación

def test_normalize_whitespace():
    # Texto con múltiples saltos de línea
    # Verificar unificación
```

### 9.2 Tests de Integración

**Escenario 1: Artículo normal**
```python
def test_integration_normal_article():
    # URL de artículo real (El País)
    # Verificar flujo completo: descarga → extracción → limpieza
    # Verificar que scrape_status == 'ok'
    # Verificar que texto tiene > MIN_LENGTH
```

**Escenario 2: Artículo bloqueado**
```python
def test_integration_blocked_article():
    # URL que requiere JS (si existe)
    # Verificar que detecta bloqueo
    # Verificar que marca blocked_fallback_required
```

**Escenario 3: Artículo sin contenido**
```python
def test_integration_no_content():
    # URL válida pero sin artículo (página de categoría)
    # Verificar que marca no_contenido_detectado
```

### 9.3 Datos de Prueba

Crear archivo `tests/test_data/sample_articles.json`:
```json
[
  {
    "nombre_del_medio": "El País",
    "enlace": "https://elpais.com/internacional/...",
    "titular": "Ejemplo de titular",
    "fecha": "2025-11-26T18:00:00",
    "descripcion": "Descripción de prueba"
  }
]
```

### 9.4 Validación Manual

**Checklist de validación**:
- [ ] Ejecutar con 10 artículos reales
- [ ] Verificar que todos tienen `scrape_status`
- [ ] Revisar calidad de texto extraído (sin ruido)
- [ ] Verificar que CSV es legible en Excel
- [ ] Verificar que JSONL es válido
- [ ] Revisar logs para errores
- [ ] Verificar reporte de ejecución

---

## 10. Integración con GUI

### 10.1 Modificaciones en `gui.py`

**Añadir botón en toolbar**:
```python
tk.Button(results_toolbar, text="📝 Extraer Texto Completo",
         command=self.extract_full_articles,
         bg=self.colors['warning'], fg='white',
         font=('Segoe UI', 9, 'bold'),
         relief='flat', padx=15, pady=8,
         cursor='hand2').pack(side=tk.LEFT, padx=5)
```

**Añadir método**:
```python
def extract_full_articles(self):
    """Ejecuta extracción de texto completo en thread separado."""
    if not Path(self.output_dir.get() + "/output.jsonl").exists():
        messagebox.showwarning("Sin datos",
                             "Primero ejecuta el filtrado de noticias.")
        return
    
    # Confirmar
    if not messagebox.askyesno("Confirmar",
                              "¿Extraer texto completo de los artículos?\n"
                              "Esto puede tardar varios minutos."):
        return
    
    # Ejecutar en thread
    thread = threading.Thread(target=self.run_article_extraction, daemon=True)
    thread.start()

def run_article_extraction(self):
    """Ejecuta extracción (en thread separado)."""
    from article_processor import process_articles
    
    try:
        config = load_config('config/extractor_config.yaml')
        report = process_articles(
            input_file=self.output_dir.get() + "/output.jsonl",
            config=config
        )
        
        self.root.after(0, lambda: messagebox.showinfo(
            "Extracción completada",
            f"Artículos procesados: {report.total_articles}\n"
            f"Exitosos: {report.successful}\n"
            f"Fallidos: {report.total_articles - report.successful}"
        ))
    except Exception as e:
        logger.error(f"Error en extracción: {e}", exc_info=True)
        self.root.after(0, lambda: messagebox.showerror(
            "Error", f"Error durante extracción:\n{str(e)}"
        ))
```

### 10.2 Nueva Tab en Notebook

**Añadir tab "Artículos Completos"**:
```python
# Tab 3: Artículos Completos
articles_frame = tk.Frame(self.notebook, bg='white')
self.notebook.add(articles_frame, text='📝 Artículos Completos')

# Viewer de texto completo
# Similar a tab de resultados pero con preview de texto
```

---

## 11. Despliegue y Operación

### 11.1 Instalación

```bash
# 1. Activar entorno virtual
cd f:/pautalla/china
.venv\Scripts\activate

# 2. Instalar nuevas dependencias
pip install -r requirements.txt

# 3. Instalar navegador Playwright (solo si se usa fallback)
playwright install chromium

# 4. Verificar instalación
python src/main_extractor.py --help
```

### 11.2 Ejecución Manual

```bash
# Extracción básica
python src/main_extractor.py

# Con configuración personalizada
python src/main_extractor.py \
    --input data/output.jsonl \
    --output data/articles_full.jsonl \
    --concurrency 5 \
    --log-level INFO

# Con Playwright activado
python src/main_extractor.py --enable-playwright
```

### 11.3 Ejecución Programada (Cron)

**Windows Task Scheduler**:
```batch
@echo off
cd f:\pautalla\china
call .venv\Scripts\activate
python src/main_extractor.py --log-level INFO
```

**Frecuencia recomendada**: Diaria, después de ejecutar filtrado RSS

### 11.4 Rotación de Logs

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/article_extractor.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
```

### 11.5 Checklist de Despliegue Diario

- [ ] Verificar que `output.jsonl` tiene noticias nuevas
- [ ] Ejecutar `main_extractor.py`
- [ ] Revisar `extraction_report.json`
- [ ] Verificar que `articles_full.jsonl` se actualizó
- [ ] Revisar `failed_extractions.jsonl` para URLs problemáticas
- [ ] Revisar logs para errores
- [ ] Backup de datos (opcional)

---

## 12. Estrategia de Fallback con Playwright

### 12.1 Cuándo Activar Playwright

**Activar solo si**:
1. `scrape_status == 'blocked_fallback_required'` o `'no_contenido_detectado'`
2. Dominio está en whitelist configurable
3. No se ha superado límite de llamadas (`MAX_PLAYWRIGHT_CALLS_PER_RUN`)

**No activar si**:
- Error de red (timeout, connection error)
- HTTP 404/410 (recurso no existe)
- Texto extraído es suficiente (> MIN_LENGTH)

### 12.2 Whitelist de Dominios

Inicialmente vacía. Añadir dominios solo después de verificar que:
1. Requieren JavaScript para cargar contenido
2. No tienen API alternativa
3. Son fuentes importantes

```yaml
fallback:
  playwright_whitelist_domains:
    # - "ejemplo-dinamico.com"
```

### 12.3 Límites Operativos

- **Máximo llamadas por ejecución**: 10 (configurable)
- **Timeout por página**: 30s
- **Navegador**: Chromium headless
- **Recursos**: ~200MB RAM por instancia

### 12.4 Monitoreo de Playwright

Registrar en logs:
- Número de veces activado
- Dominios que lo requieren
- Tiempo de ejecución
- Éxito/fallo

Si un dominio requiere Playwright frecuentemente:
1. Investigar si hay selector BS4 específico
2. Considerar añadir a whitelist permanente
3. Evaluar si vale la pena el overhead

---

## 13. Métricas de Éxito

### 13.1 KPIs del Sistema

| Métrica | Objetivo | Crítico si |
|---------|----------|------------|
| Tasa de éxito | > 85% | < 70% |
| Tiempo promedio/artículo | < 10s | > 20s |
| Artículos con texto completo | > 80% | < 60% |
| Uso de Playwright | < 5% | > 20% |
| Errores de descarga | < 10% | > 25% |

### 13.2 Calidad del Texto Extraído

**Criterios de calidad**:
- Longitud > 200 caracteres
- Sin fragmentos de menú/navegación
- Sin scripts/estilos residuales
- Párrafos coherentes
- Idioma detectado correctamente

**Validación manual**: Revisar 10 artículos aleatorios semanalmente

---

## 14. Roadmap de Implementación

### Fase 1: Core (Semana 1)
- [ ] Implementar `article_downloader.py`
- [ ] Implementar `article_extractor.py` (solo trafilatura)
- [ ] Implementar `article_cleaner.py`
- [ ] Implementar `article_processor.py` (básico)
- [ ] Tests unitarios básicos
- [ ] Ejecutar con 10 artículos de prueba

### Fase 2: Robustez (Semana 2)
- [ ] Añadir fallback BS4 en `article_extractor.py`
- [ ] Implementar `article_enricher.py`
- [ ] Mejorar manejo de errores
- [ ] Añadir rate limiting por dominio
- [ ] Tests de integración
- [ ] Ejecutar con 100 artículos reales

### Fase 3: Fallback Playwright (Semana 3)
- [ ] Implementar `article_fallback.py`
- [ ] Configurar whitelist de dominios
- [ ] Tests con sitios dinámicos
- [ ] Optimizar rendimiento

### Fase 4: CLI y Configuración (Semana 4)
- [ ] Implementar `main_extractor.py`
- [ ] Crear `extractor_config.yaml`
- [ ] Documentación completa
- [ ] Integración con GUI
- [ ] Despliegue en producción

---

## 15. Consideraciones Finales

### 15.1 Limitaciones Conocidas

- **JavaScript pesado**: Algunos sitios requieren Playwright (overhead)
- **Paywalls**: Artículos de pago no son accesibles
- **Rate limiting**: Algunos medios pueden bloquear si se excede límite
- **Cambios en estructura**: Selectores BS4 pueden quedar obsoletos

### 15.2 Mejoras Futuras

- Cache de artículos ya procesados (evitar re-descarga)
- Detección automática de selectores por dominio
- Integración con base de datos (SQLite/PostgreSQL)
- API REST para consultar artículos
- Dashboard web para monitoreo

### 15.3 Mantenimiento

**Mensual**:
- Revisar dominios con alta tasa de fallo
- Actualizar selectores BS4 si es necesario
- Revisar y limpiar logs antiguos

**Trimestral**:
- Actualizar dependencias (pip)
- Revisar y optimizar configuración
- Evaluar métricas de calidad

---

## Apéndices

### A. Ejemplo de Artículo Procesado

```json
{
  "nombre_del_medio": "El País",
  "enlace": "https://elpais.com/internacional/2025-11-26/china-anuncia-nuevas-medidas.html",
  "titular": "China anuncia nuevas medidas económicas",
  "fecha": "2025-11-26T10:30:00+00:00",
  "descripcion": "El gobierno chino presenta un paquete de estímulos...",
  "texto": "El gobierno de China anunció este martes un nuevo paquete de medidas económicas destinadas a impulsar el crecimiento...\n\nLas autoridades económicas del país asiático...",
  "idioma": "es",
  "autor": "Juan Pérez",
  "fecha_publicacion": "2025-11-26T10:00:00+00:00",
  "scrape_status": "ok",
  "error_message": "",
  "extraction_method": "trafilatura",
  "char_count": 3542,
  "word_count": 587,
  "download_time": 2.34,
  "extraction_time": 0.12
}
```

### B. Ejemplo de URL Fallida

```json
{
  "url": "https://ejemplo.com/articulo-bloqueado",
  "nombre_del_medio": "Ejemplo",
  "titular": "Artículo de prueba",
  "scrape_status": "blocked_fallback_required",
  "error_message": "Captcha detected in HTML response",
  "timestamp": "2025-11-26T18:15:32",
  "http_status": 200,
  "attempts": 3
}
```

### C. Comandos Útiles

```bash
# Ver estadísticas de artículos procesados
python -c "import json; data=[json.loads(l) for l in open('data/articles_full.jsonl')]; print(f'Total: {len(data)}'); print(f'OK: {sum(1 for d in data if d[\"scrape_status\"]==\"ok\")}')"

# Listar dominios con más errores
grep "error_descarga" data/articles_full.jsonl | jq -r '.enlace' | sed 's|https\?://||' | cut -d/ -f1 | sort | uniq -c | sort -rn

# Ver artículos más largos
jq -r 'select(.scrape_status=="ok") | "\(.char_count)\t\(.titular)"' data/articles_full.jsonl | sort -rn | head -10
```

---

**Fin de la Especificación Técnica**

**Versión**: 1.0  
**Fecha**: 2025-11-26  
**Autor**: Especificación para RSS China News Filter - Article Extractor Module
