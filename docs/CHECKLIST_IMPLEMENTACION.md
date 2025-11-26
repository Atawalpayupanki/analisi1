# ✅ Checklist de Implementación - Módulo de Extracción de Artículos

## 📋 Visión General

Este checklist guía la implementación completa del módulo de extracción de artículos, desde la preparación inicial hasta el despliegue en producción.

**Tiempo estimado total**: 3-4 semanas (según dedicación)

---

## 🎯 Fase 0: Preparación (1-2 días)

### Revisión de Documentación

- [ ] Leer `docs/RESUMEN_EJECUTIVO.md` (10 min)
- [ ] Leer `docs/ESPECIFICACION_EXTRACTOR_ARTICULOS.md` (40 min)
- [ ] Leer `docs/ESTRATEGIA_FALLBACK.md` (30 min)
- [ ] Leer `docs/README_EXTRACTOR.md` (20 min)
- [ ] Revisar `config/extractor_config.yaml` (10 min)
- [ ] Revisar `examples/ejemplo_uso_extractor.py` (10 min)

### Preparación del Entorno

- [ ] Activar entorno virtual: `.venv\Scripts\activate`
- [ ] Instalar nuevas dependencias: `pip install -r requirements.txt`
- [ ] Verificar instalación de trafilatura: `python -c "import trafilatura; print(trafilatura.__version__)"`
- [ ] Verificar instalación de PyYAML: `python -c "import yaml; print(yaml.__version__)"`
- [ ] (Opcional) Instalar Playwright: `playwright install chromium`

### Estructura de Directorios

- [ ] Crear directorio `tests/test_article_extractor/`
- [ ] Crear directorio `examples/` (ya existe)
- [ ] Verificar que `docs/` existe con toda la documentación
- [ ] Verificar que `config/extractor_config.yaml` existe

---

## 🏗️ Fase 1: Core - Funcionalidad Básica (Semana 1)

### 1.1 Módulo: `article_downloader.py`

**Objetivo**: Descargar HTML de artículos con reintentos

- [ ] Crear archivo `src/article_downloader.py`
- [ ] Implementar clase `DownloadResult` (dataclass)
- [ ] Implementar función `download_article_html(url, timeout, headers)`
  - [ ] Usar `requests.get()` con timeout
  - [ ] Añadir decorador `@retry` de tenacity
  - [ ] Manejar excepciones (Timeout, ConnectionError, HTTPError)
  - [ ] Retornar tupla `(html, final_url, status_code)`
- [ ] Implementar función `detect_blocking(html, status_code)`
  - [ ] Buscar patrones de bloqueo (captcha, etc.)
  - [ ] Verificar tamaño sospechoso
  - [ ] Retornar True/False
- [ ] Implementar clase `DomainRateLimiter`
  - [ ] Diccionario de última petición por dominio
  - [ ] Método `wait_if_needed(domain)`
- [ ] Implementar función `download_articles_batch(urls, concurrency, delay)`
  - [ ] Usar `ThreadPoolExecutor` para concurrencia
  - [ ] Aplicar rate limiting por dominio
  - [ ] Retornar lista de `DownloadResult`
- [ ] Añadir logging en puntos clave
- [ ] **Test**: Probar con 3-5 URLs reales

**Tiempo estimado**: 1-2 días

---

### 1.2 Módulo: `article_extractor.py`

**Objetivo**: Extraer texto con trafilatura (sin fallbacks aún)

- [ ] Crear archivo `src/article_extractor.py`
- [ ] Implementar clase `ExtractionResult` (dataclass)
- [ ] Implementar función `extract_article_text(html, url)`
  - [ ] Usar `trafilatura.extract()` con configuración
  - [ ] Detectar idioma con trafilatura
  - [ ] Validar longitud mínima de texto
  - [ ] Retornar `ExtractionResult`
- [ ] Configurar parámetros de trafilatura
  - [ ] `include_comments=False`
  - [ ] `include_tables=True`
  - [ ] `favor_precision=True`
- [ ] Añadir logging
- [ ] **Test**: Probar con HTML de artículos reales

**Tiempo estimado**: 1 día

---

### 1.3 Módulo: `article_cleaner.py`

**Objetivo**: Limpiar y normalizar texto extraído

- [ ] Crear archivo `src/article_cleaner.py`
- [ ] Implementar función `clean_article_text(text)`
  - [ ] Normalizar Unicode (NFKC)
  - [ ] Eliminar scripts/estilos residuales
  - [ ] Aplicar regex para eliminar fragmentos comunes
  - [ ] Unificar saltos de línea (máx 2 consecutivos)
  - [ ] Normalizar espacios en blanco
  - [ ] Trimming final
  - [ ] Retornar texto limpio
- [ ] Definir patrones de limpieza (REMOVE_PATTERNS)
- [ ] Añadir logging
- [ ] **Test**: Probar con texto con ruido

**Tiempo estimado**: 1 día

---

### 1.4 Módulo: `article_processor.py` (Versión Básica)

**Objetivo**: Orquestador que une descarga + extracción + limpieza

- [ ] Crear archivo `src/article_processor.py`
- [ ] Implementar clase `ArticleResult` (dataclass)
- [ ] Implementar clase `ProcessingReport` (dataclass)
- [ ] Implementar función `process_single_article(news_item, config)`
  - [ ] Descargar HTML
  - [ ] Extraer texto
  - [ ] Limpiar texto
  - [ ] Manejar errores sin interrumpir
  - [ ] Retornar `ArticleResult`
- [ ] Implementar función `process_articles(input_file, config)`
  - [ ] Cargar noticias desde JSONL
  - [ ] Procesar con ThreadPoolExecutor
  - [ ] Mostrar progreso con tqdm
  - [ ] Generar `ProcessingReport`
  - [ ] Guardar resultados en JSONL y CSV
- [ ] Implementar función `save_results(results, output_path)`
- [ ] Añadir logging detallado
- [ ] **Test**: Probar con 10 artículos reales

**Tiempo estimado**: 2 días

---

### 1.5 Módulo: `main_extractor.py` (CLI Básico)

**Objetivo**: Interfaz de línea de comandos

- [ ] Crear archivo `src/main_extractor.py`
- [ ] Implementar función `parse_args()`
  - [ ] `--input`: Archivo de entrada
  - [ ] `--output`: Archivo de salida
  - [ ] `--config`: Archivo de configuración
  - [ ] `--concurrency`: Nivel de concurrencia
  - [ ] `--log-level`: Nivel de logging
  - [ ] `--max-articles`: Límite de artículos (testing)
- [ ] Implementar función `load_config(config_path)`
- [ ] Implementar función `setup_logging(log_file, log_level)`
- [ ] Implementar función `main()`
  - [ ] Parsear argumentos
  - [ ] Cargar configuración
  - [ ] Configurar logging
  - [ ] Ejecutar procesamiento
  - [ ] Mostrar resumen
- [ ] Añadir manejo de excepciones
- [ ] **Test**: Ejecutar con `python src/main_extractor.py --max-articles 5`

**Tiempo estimado**: 1 día

---

### 1.6 Tests Básicos

- [ ] Crear `tests/test_article_extractor/test_downloader.py`
  - [ ] Test: descarga exitosa (mock 200)
  - [ ] Test: error 404
  - [ ] Test: timeout
  - [ ] Test: detección de bloqueo
- [ ] Crear `tests/test_article_extractor/test_extractor.py`
  - [ ] Test: extracción con trafilatura
  - [ ] Test: texto muy corto
- [ ] Crear `tests/test_article_extractor/test_cleaner.py`
  - [ ] Test: normalización Unicode
  - [ ] Test: eliminación de fragmentos
  - [ ] Test: unificación de espacios
- [ ] Ejecutar todos los tests: `pytest tests/test_article_extractor/`

**Tiempo estimado**: 1 día

---

### ✅ Checkpoint Fase 1

**Validación**:
- [ ] Ejecutar con 20 artículos reales
- [ ] Verificar que genera `articles_full.jsonl`
- [ ] Verificar que genera `articles_full.csv`
- [ ] Revisar logs en `logs/article_extractor.log`
- [ ] Validar calidad de texto extraído (revisar 5 artículos manualmente)
- [ ] Verificar que `scrape_status` se asigna correctamente

**Criterios de éxito**:
- ✅ Al menos 70% de artículos con `scrape_status='ok'`
- ✅ Texto extraído sin ruido evidente
- ✅ No hay crashes durante ejecución
- ✅ Logs son informativos

---

## 🔧 Fase 2: Robustez - Fallbacks y Enriquecimiento (Semana 2)

### 2.1 Fallback BeautifulSoup en `article_extractor.py`

- [ ] Añadir función `extract_with_fallback_bs4(html, url)`
  - [ ] Detectar dominio de la URL
  - [ ] Buscar selectores específicos del dominio
  - [ ] Intentar selectores genéricos si no hay específicos
  - [ ] Retornar texto extraído o None
- [ ] Modificar `extract_article_text()` para usar fallback
  - [ ] Si trafilatura devuelve None → intentar BS4
  - [ ] Si texto < MIN_LENGTH → intentar BS4
  - [ ] Actualizar `extraction_method` en resultado
- [ ] Añadir selectores para dominios principales
  - [ ] El País
  - [ ] El Mundo
  - [ ] ABC
  - [ ] La Vanguardia
  - [ ] La Razón
- [ ] **Test**: Probar con artículos que trafilatura no puede parsear

**Tiempo estimado**: 1-2 días

---

### 2.2 Módulo: `article_enricher.py`

**Objetivo**: Detectar idioma y extraer metadatos

- [ ] Crear archivo `src/article_enricher.py`
- [ ] Implementar función `detect_language(text)`
  - [ ] Usar detección de trafilatura primero
  - [ ] Fallback a langdetect si es necesario
  - [ ] Retornar código de idioma (es, en, etc.)
- [ ] Implementar función `extract_metadata_from_html(html, url)`
  - [ ] Buscar meta tags (Open Graph, Twitter Cards)
  - [ ] Extraer autor si está disponible
  - [ ] Extraer fecha de publicación
  - [ ] Retornar diccionario con metadatos
- [ ] Integrar en `article_processor.py`
- [ ] **Test**: Probar con artículos reales

**Tiempo estimado**: 1 día

---

### 2.3 Mejoras en Manejo de Errores

- [ ] Implementar clasificación detallada de errores
  - [ ] `error_descarga`: HTTP 4xx/5xx, timeout
  - [ ] `error_parseo`: Excepciones en extracción
  - [ ] `no_contenido_detectado`: Texto muy corto
  - [ ] `blocked_fallback_required`: Bloqueo detectado
- [ ] Añadir archivo de salida `failed_extractions.jsonl`
  - [ ] Guardar URLs fallidas con razón
  - [ ] Incluir timestamp y detalles
- [ ] Mejorar logging de errores
  - [ ] Stack trace para debugging
  - [ ] Resumen de errores por tipo
- [ ] **Test**: Simular diferentes tipos de errores

**Tiempo estimado**: 1 día

---

### 2.4 Optimización de Rate Limiting

- [ ] Implementar rate limiting más sofisticado
  - [ ] Delay configurable por dominio
  - [ ] Detectar respuestas 429 (Too Many Requests)
  - [ ] Aumentar delay automáticamente si se detecta rate limiting
- [ ] Añadir estadísticas de rate limiting en reporte
- [ ] **Test**: Ejecutar con concurrency alta y verificar delays

**Tiempo estimado**: 1 día

---

### 2.5 Generación de Reportes

- [ ] Implementar función `generate_report(results)`
  - [ ] Calcular estadísticas completas
  - [ ] Identificar dominios problemáticos
  - [ ] Calcular tiempos promedio
  - [ ] Generar JSON con reporte
- [ ] Guardar reporte en `data/extraction_report.json`
- [ ] Mostrar resumen en consola al finalizar
- [ ] **Test**: Verificar que reporte es completo y preciso

**Tiempo estimado**: 1 día

---

### 2.6 Tests de Integración

- [ ] Crear `tests/test_article_extractor/test_integration.py`
  - [ ] Test: flujo completo con artículo normal
  - [ ] Test: flujo con artículo que requiere BS4 fallback
  - [ ] Test: flujo con artículo que falla
  - [ ] Test: procesamiento de batch de artículos
- [ ] Ejecutar tests de integración
- [ ] Validar con artículos reales de cada medio

**Tiempo estimado**: 1 día

---

### ✅ Checkpoint Fase 2

**Validación**:
- [ ] Ejecutar con 100 artículos reales
- [ ] Verificar tasa de éxito > 80%
- [ ] Revisar `extraction_report.json`
- [ ] Revisar `failed_extractions.jsonl`
- [ ] Validar que BS4 fallback funciona
- [ ] Verificar detección de idioma
- [ ] Revisar calidad de metadatos extraídos

**Criterios de éxito**:
- ✅ Tasa de éxito > 80%
- ✅ BS4 fallback usado en < 20% de casos
- ✅ Idioma detectado correctamente en > 90%
- ✅ Tiempo promedio < 10s por artículo

---

## 🎭 Fase 3: Fallback Playwright (Semana 3) - OPCIONAL

### 3.1 Módulo: `article_fallback.py`

**Objetivo**: Fallback con Playwright para contenido dinámico

- [ ] Crear archivo `src/article_fallback.py`
- [ ] Implementar función `extract_with_playwright(url, timeout)`
  - [ ] Lanzar navegador Chromium headless
  - [ ] Navegar a URL
  - [ ] Esperar carga completa (networkidle)
  - [ ] Extraer HTML renderizado
  - [ ] Cerrar navegador
  - [ ] Retornar HTML
- [ ] Implementar función `should_use_playwright(url, extraction_result, config)`
  - [ ] Verificar que está habilitado
  - [ ] Verificar whitelist de dominios
  - [ ] Verificar límite de llamadas
  - [ ] Retornar True/False
- [ ] Añadir contador de llamadas a Playwright
- [ ] Integrar en `article_processor.py`
- [ ] **Test**: Probar con sitio que requiere JavaScript

**Tiempo estimado**: 2 días

---

### 3.2 Configuración de Whitelist

- [ ] Analizar `failed_extractions.jsonl` de Fase 2
- [ ] Identificar dominios que requieren JavaScript
- [ ] Verificar manualmente con navegador
- [ ] Añadir a `playwright_whitelist_domains` en config
- [ ] Documentar razón para cada dominio en whitelist
- [ ] **Test**: Ejecutar con Playwright activado

**Tiempo estimado**: 1 día

---

### 3.3 Optimización de Playwright

- [ ] Implementar pool de navegadores (reutilizar instancias)
- [ ] Añadir timeout configurable
- [ ] Implementar captura de screenshots para debugging
- [ ] Añadir métricas de uso de Playwright en reporte
- [ ] **Test**: Verificar que no hay memory leaks

**Tiempo estimado**: 1 día

---

### 3.4 Tests con Playwright

- [ ] Crear tests específicos para Playwright
  - [ ] Test: extracción con JavaScript
  - [ ] Test: timeout de Playwright
  - [ ] Test: límite de llamadas
- [ ] Ejecutar tests
- [ ] Validar con sitios reales

**Tiempo estimado**: 1 día

---

### ✅ Checkpoint Fase 3

**Validación**:
- [ ] Ejecutar con Playwright activado
- [ ] Verificar que solo se usa para dominios en whitelist
- [ ] Verificar que no supera límite de llamadas
- [ ] Revisar tiempo de ejecución (debe ser aceptable)
- [ ] Validar que extrae contenido correctamente

**Criterios de éxito**:
- ✅ Playwright usado en < 5% de artículos
- ✅ Tasa de éxito con Playwright > 70%
- ✅ No hay memory leaks
- ✅ Tiempo promedio con Playwright < 15s

---

## 🚀 Fase 4: Integración y Despliegue (Semana 4)

### 4.1 Integración con GUI

- [ ] Modificar `src/gui.py`
  - [ ] Añadir botón "📝 Extraer Texto Completo"
  - [ ] Implementar método `extract_full_articles()`
  - [ ] Implementar método `run_article_extraction()`
  - [ ] Añadir tab "Artículos Completos" en notebook
- [ ] Añadir viewer de texto completo en GUI
- [ ] Añadir estadísticas de extracción en GUI
- [ ] **Test**: Ejecutar desde GUI con artículos reales

**Tiempo estimado**: 2 días

---

### 4.2 Documentación Final

- [ ] Actualizar `README.md` principal del proyecto
  - [ ] Añadir sección sobre extracción de artículos
  - [ ] Actualizar diagrama de flujo
  - [ ] Añadir ejemplos de uso
- [ ] Revisar y actualizar toda la documentación en `docs/`
- [ ] Crear guía de troubleshooting con casos reales
- [ ] Documentar lecciones aprendidas

**Tiempo estimado**: 1 día

---

### 4.3 Validación Final

- [ ] Ejecutar con dataset completo (500+ artículos)
- [ ] Analizar resultados detalladamente
  - [ ] Tasa de éxito por medio
  - [ ] Métodos de extracción usados
  - [ ] Tiempos de ejecución
  - [ ] Calidad de texto extraído
- [ ] Identificar y documentar limitaciones
- [ ] Crear lista de mejoras futuras

**Tiempo estimado**: 1 día

---

### 4.4 Configuración de Despliegue

- [ ] Crear script de instalación automatizada
- [ ] Configurar Task Scheduler (Windows) para ejecución diaria
- [ ] Configurar rotación de logs
- [ ] Configurar backup de datos
- [ ] Documentar procedimiento de despliegue

**Tiempo estimado**: 1 día

---

### 4.5 Capacitación y Handoff

- [ ] Crear guía de operación diaria
- [ ] Documentar procedimientos de mantenimiento
- [ ] Crear checklist de monitoreo
- [ ] Preparar presentación de resultados
- [ ] Capacitar a usuarios finales (si aplica)

**Tiempo estimado**: 1 día

---

### ✅ Checkpoint Final

**Validación Completa**:
- [ ] Módulo funciona end-to-end
- [ ] Tasa de éxito > 85% en producción
- [ ] Tiempo de ejecución aceptable
- [ ] Calidad de texto validada
- [ ] Integración con GUI funcional
- [ ] Documentación completa
- [ ] Tests pasan al 100%
- [ ] Despliegue configurado

**Criterios de éxito**:
- ✅ Tasa de éxito > 85%
- ✅ Tiempo promedio < 10s por artículo
- ✅ Texto extraído de alta calidad
- ✅ Sistema robusto ante errores
- ✅ Fácil de operar y mantener

---

## 📊 Métricas de Seguimiento

### Durante Implementación

| Métrica | Objetivo | Actual | Estado |
|---------|----------|--------|--------|
| Cobertura de tests | > 80% | ___ | ⏳ |
| Tasa de éxito | > 85% | ___ | ⏳ |
| Tiempo/artículo | < 10s | ___ | ⏳ |
| Uso de BS4 fallback | < 20% | ___ | ⏳ |
| Uso de Playwright | < 5% | ___ | ⏳ |

### Post-Despliegue

| Métrica | Objetivo | Semana 1 | Semana 2 | Semana 3 |
|---------|----------|----------|----------|----------|
| Artículos procesados | 500+ | ___ | ___ | ___ |
| Tasa de éxito | > 85% | ___ | ___ | ___ |
| Errores críticos | 0 | ___ | ___ | ___ |
| Tiempo total | < 60 min | ___ | ___ | ___ |

---

## 🎯 Hitos Clave

- [ ] **Hito 1**: Core funcional (Fase 1 completa)
- [ ] **Hito 2**: Fallbacks implementados (Fase 2 completa)
- [ ] **Hito 3**: Playwright funcional (Fase 3 completa - opcional)
- [ ] **Hito 4**: Integración completa (Fase 4 completa)
- [ ] **Hito 5**: Despliegue en producción

---

## 📝 Notas y Lecciones Aprendidas

### Fase 1
```
[Espacio para notas durante implementación]
```

### Fase 2
```
[Espacio para notas durante implementación]
```

### Fase 3
```
[Espacio para notas durante implementación]
```

### Fase 4
```
[Espacio para notas durante implementación]
```

---

## 🆘 Problemas Comunes y Soluciones

### Problema: Baja tasa de éxito
**Solución**:
- Revisar selectores BS4
- Aumentar timeout
- Verificar conectividad

### Problema: Texto con mucho ruido
**Solución**:
- Ajustar patrones de limpieza
- Revisar selectores BS4
- Usar `favor_precision=True` en trafilatura

### Problema: Ejecución muy lenta
**Solución**:
- Reducir concurrency
- Aumentar delay entre peticiones
- Desactivar Playwright si no es necesario

---

## ✅ Checklist de Entrega Final

- [ ] Código implementado y testeado
- [ ] Documentación completa
- [ ] Tests pasando al 100%
- [ ] Integración con GUI funcional
- [ ] Configuración optimizada
- [ ] Despliegue configurado
- [ ] Capacitación completada
- [ ] Handoff realizado

---

**¡Éxito en la implementación!** 🚀

---

_Última actualización: 2025-11-26_
