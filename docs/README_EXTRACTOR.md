# Módulo de Extracción de Artículos Completos

## 📋 Descripción

Módulo complementario del **RSS China News Filter** que descarga y extrae el texto completo de artículos de noticias desde sus URLs, produciendo contenido limpio y normalizado para análisis posterior.

---

## 🎯 Características

- ✅ **Extracción robusta** con trafilatura (método principal)
- ✅ **Fallbacks inteligentes** con BeautifulSoup y Playwright
- ✅ **Detección de bloqueos** y manejo de captchas
- ✅ **Limpieza de texto** automática (elimina ruido, menús, scripts)
- ✅ **Detección de idioma** y extracción de metadatos
- ✅ **Concurrencia configurable** para procesamiento eficiente
- ✅ **Logging detallado** y reportes de ejecución
- ✅ **Salida en JSONL y CSV** compatible con Excel

---

## 📦 Instalación

### 1. Instalar dependencias

```bash
# Activar entorno virtual
cd f:/pautalla/china
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Instalar Playwright (opcional)

**Solo si necesitas fallback con JavaScript**:

```bash
# Instalar navegador Chromium
playwright install chromium
```

---

## ⚙️ Configuración

Editar `config/extractor_config.yaml` según necesidades:

```yaml
# Configuración básica
downloader:
  timeout: 15
  concurrency: 5
  delay_between_requests_same_domain: 1.0

extractor:
  min_text_length_ok: 200
  favor_precision: true

fallback:
  playwright_enabled: false  # Activar solo si es necesario
```

**Ver**: `docs/ESPECIFICACION_EXTRACTOR_ARTICULOS.md` para detalles completos.

---

## 🚀 Uso

### Ejecución Básica

```bash
# Extraer artículos desde output.jsonl
python src/main_extractor.py
```

### Opciones Avanzadas

```bash
# Especificar archivos de entrada/salida
python src/main_extractor.py \
    --input data/output.jsonl \
    --output data/articles_full.jsonl

# Ajustar concurrencia
python src/main_extractor.py --concurrency 10

# Activar fallback con Playwright
python src/main_extractor.py --enable-playwright

# Modo debug
python src/main_extractor.py --log-level DEBUG

# Procesar solo primeros N artículos (testing)
python src/main_extractor.py --max-articles 10
```

### Ayuda

```bash
python src/main_extractor.py --help
```

---

## 📊 Formato de Salida

### Archivo JSONL (`articles_full.jsonl`)

Cada línea es un objeto JSON con:

```json
{
  "nombre_del_medio": "El País",
  "enlace": "https://elpais.com/internacional/...",
  "titular": "China anuncia nuevas medidas económicas",
  "fecha": "2025-11-26T10:30:00+00:00",
  "descripcion": "El gobierno chino presenta...",
  "texto": "El gobierno de China anunció este martes...\n\nLas autoridades económicas...",
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

### Archivo CSV (`articles_full.csv`)

Formato CSV con UTF-8 BOM (compatible con Excel):

| nombre_del_medio | enlace | titular | texto | scrape_status | ... |
|-----------------|--------|---------|-------|---------------|-----|
| El País | https://... | ... | ... | ok | ... |

### Archivo de Fallos (`failed_extractions.jsonl`)

URLs que fallaron con razón del fallo:

```json
{
  "url": "https://ejemplo.com/articulo",
  "nombre_del_medio": "Ejemplo",
  "titular": "...",
  "scrape_status": "error_descarga",
  "error_message": "HTTP 404 Not Found",
  "timestamp": "2025-11-26T18:15:32"
}
```

### Reporte de Ejecución (`extraction_report.json`)

Resumen completo de la ejecución:

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
  }
}
```

---

## 🔄 Flujo de Trabajo Típico

```
1. Ejecutar filtrado RSS
   → python src/main.py --async
   → Genera: data/output.jsonl

2. Extraer texto completo
   → python src/main_extractor.py
   → Genera: data/articles_full.jsonl

3. Revisar resultados
   → Ver: data/extraction_report.json
   → Revisar: data/failed_extractions.jsonl

4. Analizar artículos
   → Usar: data/articles_full.jsonl
```

---

## 📈 Rendimiento

### Tiempos Estimados

| Artículos | Concurrency | Tiempo Estimado |
|-----------|-------------|-----------------|
| 10 | 1 | ~1 min |
| 50 | 5 | ~2-3 min |
| 100 | 5 | ~5-8 min |
| 500 | 10 | ~15-20 min |

### Recursos

- **RAM**: ~100-200 MB (sin Playwright)
- **RAM**: ~500 MB - 1 GB (con Playwright)
- **CPU**: 1-2 cores al 50-80%
- **Red**: ~5-10 MB descargados por 100 artículos

---

## 🛠️ Métodos de Extracción

### 1. Trafilatura (Principal)

**Cuándo**: Siempre como primer intento

**Ventajas**:
- Rápido (~100ms)
- Preciso para mayoría de sitios
- Detecta idioma automáticamente

**Limitaciones**:
- No funciona con JavaScript
- Puede fallar con HTML no estándar

---

### 2. BeautifulSoup (Fallback 1)

**Cuándo**: Si trafilatura falla o texto < 100 caracteres

**Ventajas**:
- Rápido (~50-100ms adicionales)
- Personalizable por dominio
- No requiere recursos extra

**Selectores configurados**:
- El País
- El Mundo
- ABC
- La Vanguardia
- La Razón

---

### 3. Playwright (Fallback 2)

**Cuándo**: Solo si niveles 1 y 2 fallan + dominio en whitelist

**Ventajas**:
- Ejecuta JavaScript
- Renderiza contenido dinámico

**Limitaciones**:
- Lento (~5-10s)
- Alto consumo de recursos
- Requiere instalación adicional

**Configuración**:
```yaml
fallback:
  playwright_enabled: false  # Desactivado por defecto
  playwright_whitelist_domains: []  # Añadir solo si es necesario
```

---

## 🚨 Estados de Extracción

| scrape_status | Significado | Acción |
|---------------|-------------|--------|
| `ok` | Extracción exitosa | ✅ Usar texto |
| `no_contenido_detectado` | Texto muy corto o vacío | ⚠️ Revisar URL |
| `error_descarga` | Error HTTP o timeout | ❌ Verificar URL |
| `error_parseo` | Error al parsear HTML | ⚠️ Revisar estructura |
| `blocked_fallback_required` | Bloqueo detectado | 🔒 Requiere Playwright |

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Extracción Básica

```bash
# Extraer todos los artículos de output.jsonl
python src/main_extractor.py

# Ver resultados
cat data/extraction_report.json
```

### Ejemplo 2: Testing con Pocos Artículos

```bash
# Procesar solo 5 artículos para probar
python src/main_extractor.py --max-articles 5 --log-level DEBUG
```

### Ejemplo 3: Activar Playwright

```bash
# 1. Editar config/extractor_config.yaml
#    playwright_enabled: true
#    playwright_whitelist_domains: ["ejemplo.com"]

# 2. Ejecutar
python src/main_extractor.py --enable-playwright
```

### Ejemplo 4: Análisis de Resultados

```bash
# Contar artículos exitosos
grep '"scrape_status": "ok"' data/articles_full.jsonl | wc -l

# Ver artículos fallidos
cat data/failed_extractions.jsonl

# Estadísticas de longitud de texto
jq -r 'select(.scrape_status=="ok") | .char_count' data/articles_full.jsonl | \
  awk '{sum+=$1; count++} END {print "Promedio:", sum/count, "caracteres"}'
```

---

## 🔍 Troubleshooting

### Problema: Alta tasa de fallos

**Solución**:
1. Revisar `failed_extractions.jsonl` para identificar patrones
2. Verificar conectividad de red
3. Aumentar timeout en config
4. Añadir selectores BS4 específicos para dominios problemáticos

### Problema: Texto extraído contiene ruido

**Solución**:
1. Revisar patrones de limpieza en config
2. Añadir patrones específicos en `cleaner.remove_patterns`
3. Ajustar selectores BS4 para ser más específicos

### Problema: Bloqueos frecuentes

**Solución**:
1. Aumentar `delay_between_requests_same_domain`
2. Reducir `concurrency`
3. Verificar si dominio requiere Playwright
4. Considerar usar proxy (implementación futura)

### Problema: Playwright muy lento

**Solución**:
1. Reducir `max_playwright_calls_per_run`
2. Revisar whitelist (solo dominios esenciales)
3. Buscar selectores BS4 alternativos
4. Considerar desactivar Playwright

---

## 📚 Documentación Adicional

- **Especificación completa**: `docs/ESPECIFICACION_EXTRACTOR_ARTICULOS.md`
- **Estrategia de fallback**: `docs/ESTRATEGIA_FALLBACK.md`
- **Configuración**: `config/extractor_config.yaml`

---

## 🔗 Integración con GUI

El módulo se puede ejecutar desde la GUI principal:

1. Abrir GUI: `python src/gui.py`
2. Ejecutar filtrado RSS
3. Clic en botón **"📝 Extraer Texto Completo"**
4. Ver resultados en tab "Artículos Completos"

---

## 📅 Mantenimiento

### Diario
- Ejecutar extracción después de filtrado RSS
- Revisar `extraction_report.json`
- Verificar `failed_extractions.jsonl`

### Semanal
- Revisar logs para errores recurrentes
- Validar calidad de texto extraído (muestra aleatoria)

### Mensual
- Actualizar selectores BS4 si sitios cambiaron
- Revisar y ajustar configuración
- Limpiar logs antiguos

---

## 🤝 Contribuir

Para añadir soporte para nuevos medios:

1. Identificar selectores CSS del contenido principal
2. Añadir a `extractor_config.yaml`:
   ```yaml
   domain_selectors:
     nuevo-medio.com:
       - "selector-principal"
       - "selector-alternativo"
   ```
3. Probar con artículos reales
4. Documentar en este README

---

## 📄 Licencia

Proyecto educativo/interno - RSS China News Filter

---

## 🆘 Soporte

Para problemas o preguntas:
1. Revisar documentación en `docs/`
2. Verificar logs en `logs/article_extractor.log`
3. Ejecutar con `--log-level DEBUG` para más detalles

---

**Última actualización**: 2025-11-26
