# Estrategia de Fallback para Extracción de Artículos

## 1. Introducción

Este documento describe la estrategia de fallback para la extracción de texto completo de artículos cuando el método principal (trafilatura) no es suficiente.

---

## 2. Jerarquía de Métodos de Extracción

### Nivel 1: Trafilatura (Principal)
**Cuándo usar**: Siempre como primer intento

**Ventajas**:
- Rápido (~100ms por artículo)
- Preciso para la mayoría de sitios de noticias
- Detecta idioma automáticamente
- Bajo consumo de recursos

**Limitaciones**:
- No funciona con contenido cargado por JavaScript
- Puede fallar con estructuras HTML no estándar
- Algunos sitios con anti-scraping agresivo

**Criterios de éxito**:
- Texto extraído > 200 caracteres
- No contiene patrones de bloqueo
- Estructura coherente (párrafos detectables)

---

### Nivel 2: BeautifulSoup con Selectores Específicos (Fallback 1)
**Cuándo usar**: Si trafilatura devuelve None o texto < 100 caracteres

**Ventajas**:
- Rápido (~50-100ms adicionales)
- Personalizable por dominio
- No requiere recursos adicionales

**Limitaciones**:
- Requiere mantenimiento de selectores
- Puede incluir ruido si selectores no son precisos
- No funciona con JavaScript

**Selectores por Dominio**:

```python
DOMAIN_SELECTORS = {
    'elpais.com': [
        'article.a_c',
        'div.a_c_text',
        'div.articulo-cuerpo',
        'div[itemprop="articleBody"]'
    ],
    'elmundo.es': [
        'article.ue-l-article__body',
        'div.ue-c-article__body',
        'div.ue-c-article__premium-body'
    ],
    'abc.es': [
        'div.voc-article-content',
        'div.cuerpo-texto',
        'article[itemprop="articleBody"]'
    ],
    'lavanguardia.com': [
        'div.article-modules',
        'div.article-body',
        'div.main-article-body'
    ],
    'larazon.es': [
        'div.article-content',
        'div.texto-noticia',
        'div.article-body-content'
    ]
}
```

**Estrategia de selección**:
1. Intentar selectores en orden de especificidad
2. Validar que el texto extraído > 100 caracteres
3. Limpiar HTML residual (scripts, estilos)
4. Si múltiples selectores coinciden, elegir el más largo

**Mantenimiento**:
- Revisar selectores mensualmente
- Actualizar si cambia estructura de sitios
- Añadir nuevos dominios según necesidad

---

### Nivel 3: Playwright (Fallback 2 - Último Recurso)
**Cuándo usar**: 
- Solo si niveles 1 y 2 fallan
- Solo si dominio está en whitelist
- Solo si no se superó límite de llamadas

**Ventajas**:
- Ejecuta JavaScript
- Puede superar algunos anti-scraping básicos
- Renderiza contenido dinámico

**Limitaciones**:
- Lento (~5-10s por artículo)
- Alto consumo de recursos (200MB RAM por instancia)
- Puede ser detectado y bloqueado
- Requiere instalación adicional

**Configuración**:
```yaml
fallback:
  playwright_enabled: false  # Desactivado por defecto
  playwright_timeout: 30000  # 30 segundos
  playwright_browser: "chromium"
  playwright_headless: true
  max_playwright_calls_per_run: 10
  playwright_whitelist_domains: []
```

**Política de activación**:
```python
def should_use_playwright(url, extraction_result, config):
    # 1. Verificar que está habilitado
    if not config['fallback']['playwright_enabled']:
        return False
    
    # 2. Verificar que falló extracción normal
    if extraction_result.extraction_status == 'ok':
        return False
    
    # 3. Verificar whitelist
    domain = urlparse(url).netloc
    if domain not in config['fallback']['playwright_whitelist_domains']:
        return False
    
    # 4. Verificar límite de llamadas
    if playwright_calls_count >= config['fallback']['max_playwright_calls_per_run']:
        logger.warning(f"Playwright limit reached: {playwright_calls_count}")
        return False
    
    return True
```

---

## 3. Detección de Bloqueos

### 3.1 Patrones de Bloqueo Comunes

```python
BLOCK_PATTERNS = [
    # Captchas
    r'captcha',
    r'recaptcha',
    r'hcaptcha',
    
    # Mensajes de bloqueo
    r'access denied',
    r'acceso denegado',
    r'blocked',
    r'bloqueado',
    r'robot',
    r'bot detected',
    
    # Cloudflare
    r'checking your browser',
    r'cloudflare',
    r'ray id',
    
    # Otros
    r'enable javascript',
    r'javascript required',
    r'cookies required'
]

def detect_blocking(html: str, status_code: int) -> bool:
    # 1. Verificar status code sospechoso
    if status_code in [403, 429]:
        return True
    
    # 2. Verificar tamaño sospechoso
    if len(html) < 500:
        return True
    
    # 3. Buscar patrones de bloqueo
    html_lower = html.lower()
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, html_lower):
            logger.warning(f"Block pattern detected: {pattern}")
            return True
    
    return False
```

### 3.2 Respuesta a Bloqueos

**Si se detecta bloqueo**:
1. Marcar `scrape_status = 'blocked_fallback_required'`
2. Registrar en logs con detalles
3. Añadir a lista de URLs problemáticas
4. Si Playwright está habilitado y dominio en whitelist → intentar
5. Si no → marcar como fallido y continuar

**Monitoreo de bloqueos**:
- Contar bloqueos por dominio
- Si dominio tiene > 50% bloqueos → investigar
- Considerar añadir a whitelist de Playwright
- O buscar selectores BS4 específicos

---

## 4. Gestión de Whitelist de Playwright

### 4.1 Criterios para Añadir Dominio

**Añadir a whitelist solo si**:
1. Es fuente importante (> 10 artículos/mes)
2. Falla consistentemente con trafilatura y BS4
3. Verificado manualmente que requiere JavaScript
4. No hay API alternativa disponible
5. No hay paywall que impida acceso

**Proceso de verificación**:
```bash
# 1. Probar manualmente con trafilatura
python -c "import trafilatura; print(trafilatura.extract(trafilatura.fetch_url('URL')))"

# 2. Inspeccionar HTML con requests
python -c "import requests; print(len(requests.get('URL').text))"

# 3. Probar con navegador (DevTools → Disable JavaScript)
# Si contenido desaparece → requiere JS

# 4. Probar con Playwright
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); page = browser.new_page(); page.goto('URL'); print(page.content())"
```

### 4.2 Whitelist Inicial

**Recomendación**: Empezar con whitelist vacía

```yaml
playwright_whitelist_domains: []
```

**Añadir dominios progresivamente** después de:
1. Ejecutar extracción en 100+ artículos
2. Revisar `failed_extractions.jsonl`
3. Identificar dominios con alta tasa de fallo
4. Verificar manualmente que requieren JS

### 4.3 Ejemplo de Whitelist Poblada

```yaml
playwright_whitelist_domains:
  - "ejemplo-dinamico.com"  # Requiere JS para cargar artículos
  # - "otro-sitio.com"      # Descomentar si se verifica necesidad
```

---

## 5. Límites Operativos de Playwright

### 5.1 Límite de Llamadas

**Configuración**:
```yaml
max_playwright_calls_per_run: 10
```

**Justificación**:
- Evitar ejecuciones excesivamente largas
- Limitar consumo de recursos
- Forzar revisión de dominios problemáticos

**Comportamiento al alcanzar límite**:
```python
if playwright_calls_count >= MAX_PLAYWRIGHT_CALLS:
    logger.warning(f"Playwright limit reached. Remaining blocked URLs will be marked as failed.")
    # Marcar URLs restantes como 'blocked_fallback_required'
    # Continuar sin Playwright
```

### 5.2 Timeout por Página

**Configuración**:
```yaml
playwright_timeout: 30000  # 30 segundos
```

**Eventos de timeout**:
- `load`: Página cargada (HTML básico)
- `domcontentloaded`: DOM construido
- `networkidle`: Sin actividad de red por 500ms (recomendado)

**Manejo de timeout**:
```python
try:
    page.goto(url, wait_until='networkidle', timeout=30000)
except PlaywrightTimeoutError:
    logger.error(f"Playwright timeout for {url}")
    return None, 'timeout'
```

### 5.3 Recursos del Sistema

**Por instancia de navegador**:
- RAM: ~200-300 MB
- CPU: 1 core al 50-100% durante carga
- Disco: ~100 MB (cache temporal)

**Concurrencia con Playwright**:
```python
# NO ejecutar Playwright en paralelo
# Usar secuencialmente para evitar sobrecarga

if config['fallback']['playwright_enabled']:
    # Forzar concurrency=1 para artículos que requieren Playwright
    logger.info("Playwright enabled: processing sequentially")
```

---

## 6. Estrategias de Optimización

### 6.1 Caché de Artículos

**Implementación futura**:
```python
# Guardar HTML descargado para evitar re-descarga
CACHE_DIR = Path("data/html_cache")

def get_cached_html(url: str) -> Optional[str]:
    cache_file = CACHE_DIR / hashlib.md5(url.encode()).hexdigest()
    if cache_file.exists():
        # Verificar edad del cache (< 7 días)
        if time.time() - cache_file.stat().st_mtime < 7 * 24 * 3600:
            return cache_file.read_text(encoding='utf-8')
    return None
```

### 6.2 Detección Automática de Selectores

**Implementación futura**:
```python
# Analizar HTML para encontrar contenedor principal automáticamente
def auto_detect_article_container(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, 'lxml')
    
    # Buscar elementos con mayor densidad de texto
    candidates = []
    for tag in soup.find_all(['article', 'div', 'section']):
        text_length = len(tag.get_text(strip=True))
        if text_length > 500:
            candidates.append((tag, text_length))
    
    # Ordenar por longitud y retornar el más largo
    if candidates:
        best_candidate = max(candidates, key=lambda x: x[1])
        return best_candidate[0].get_text(strip=True)
    
    return None
```

### 6.3 Rotación de User-Agents

**Implementación futura**:
```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...'
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)
```

---

## 7. Monitoreo y Alertas

### 7.1 Métricas a Monitorear

```python
@dataclass
class FallbackMetrics:
    # Por método
    trafilatura_success: int
    bs4_fallback_success: int
    playwright_success: int
    
    # Bloqueos
    blocked_count: int
    blocked_domains: Dict[str, int]
    
    # Tiempos
    avg_trafilatura_time: float
    avg_bs4_time: float
    avg_playwright_time: float
    
    # Límites
    playwright_calls_used: int
    playwright_calls_limit: int
```

### 7.2 Alertas Configurables

**Alerta 1: Alta tasa de bloqueos**
```python
if blocked_count / total_articles > 0.2:  # > 20%
    logger.warning(f"High blocking rate: {blocked_count}/{total_articles}")
    # Enviar notificación (email, Slack, etc.)
```

**Alerta 2: Dominio problemático**
```python
for domain, count in blocked_domains.items():
    if count > 5:
        logger.warning(f"Domain {domain} blocked {count} times")
        # Sugerir añadir a whitelist de Playwright
```

**Alerta 3: Playwright cerca del límite**
```python
if playwright_calls_used >= playwright_calls_limit * 0.8:
    logger.warning(f"Playwright usage at {playwright_calls_used}/{playwright_calls_limit}")
    # Considerar aumentar límite o revisar whitelist
```

---

## 8. Casos de Uso y Ejemplos

### 8.1 Caso 1: Artículo Normal (El País)

**Flujo**:
1. Descargar HTML → OK (200)
2. Trafilatura → Extrae 3500 caracteres → ✅ OK
3. No requiere fallback

**Tiempo**: ~2-3 segundos

---

### 8.2 Caso 2: Artículo con Estructura No Estándar

**Flujo**:
1. Descargar HTML → OK (200)
2. Trafilatura → Extrae 50 caracteres (insuficiente)
3. BS4 Fallback → Busca selectores específicos → Extrae 2800 caracteres → ✅ OK
4. No requiere Playwright

**Tiempo**: ~3-4 segundos

---

### 8.3 Caso 3: Artículo con JavaScript Requerido

**Flujo**:
1. Descargar HTML → OK (200)
2. Trafilatura → None (HTML sin contenido)
3. BS4 Fallback → None (selectores no encuentran contenido)
4. Detectar bloqueo → No (solo falta JS)
5. Verificar whitelist → Dominio en whitelist → ✅
6. Playwright → Renderiza página → Extrae 4200 caracteres → ✅ OK

**Tiempo**: ~8-12 segundos

---

### 8.4 Caso 4: Artículo Bloqueado (Captcha)

**Flujo**:
1. Descargar HTML → OK (200)
2. Detectar bloqueo → ✅ (patrón "captcha" encontrado)
3. Marcar `scrape_status = 'blocked_fallback_required'`
4. Verificar whitelist → Dominio NO en whitelist
5. No intentar Playwright → ❌ Marcar como fallido

**Tiempo**: ~2-3 segundos

---

### 8.5 Caso 5: Error de Red

**Flujo**:
1. Descargar HTML → Timeout después de 3 reintentos
2. Marcar `scrape_status = 'error_descarga'`
3. No intentar extracción → ❌ Marcar como fallido

**Tiempo**: ~30-45 segundos (3 reintentos con backoff)

---

## 9. Checklist de Decisión para Fallbacks

### ¿Usar BS4 Fallback?

- [ ] Trafilatura devolvió None o texto < 100 caracteres
- [ ] HTML descargado correctamente (status 200)
- [ ] No se detectó bloqueo
- [ ] Dominio tiene selectores configurados

**Si todas ✅ → Usar BS4 Fallback**

---

### ¿Usar Playwright?

- [ ] Trafilatura y BS4 fallaron
- [ ] Playwright está habilitado en config
- [ ] Dominio está en whitelist
- [ ] No se superó límite de llamadas
- [ ] No es error de red (404, timeout, etc.)

**Si todas ✅ → Usar Playwright**

---

## 10. Recomendaciones Finales

### 10.1 Configuración Inicial

```yaml
# Configuración conservadora para empezar
fallback:
  playwright_enabled: false  # Activar solo después de análisis
  max_playwright_calls_per_run: 10
  playwright_whitelist_domains: []
```

### 10.2 Proceso de Optimización

**Semana 1-2**:
1. Ejecutar con Playwright desactivado
2. Recopilar métricas de fallos
3. Identificar dominios problemáticos

**Semana 3-4**:
1. Verificar manualmente dominios con alta tasa de fallo
2. Añadir selectores BS4 específicos si es posible
3. Añadir a whitelist de Playwright solo si es necesario

**Mensual**:
1. Revisar métricas de fallback
2. Actualizar selectores BS4 si sitios cambiaron
3. Ajustar límites de Playwright según necesidad

### 10.3 Principios Operativos

1. **Trafilatura primero**: Siempre intentar primero, es el más eficiente
2. **BS4 como puente**: Usar para casos específicos conocidos
3. **Playwright como último recurso**: Solo para casos excepcionales
4. **Monitorear constantemente**: Revisar logs y métricas regularmente
5. **Optimizar progresivamente**: Añadir selectores antes que Playwright

---

**Fin del Documento de Estrategia de Fallback**

**Versión**: 1.0  
**Fecha**: 2025-11-26  
**Mantenimiento**: Revisar mensualmente
