# 📋 Resumen Ejecutivo: Módulo de Extracción de Artículos

## 🎯 Objetivo

Añadir capacidad de extracción de texto completo de artículos al proyecto **RSS China News Filter**, permitiendo obtener el contenido íntegro de las noticias filtradas para análisis profundo.

---

## 📦 Entregables Creados

### 1. Documentación Técnica

| Documento | Ubicación | Descripción |
|-----------|-----------|-------------|
| **Especificación Técnica Completa** | `docs/ESPECIFICACION_EXTRACTOR_ARTICULOS.md` | Arquitectura, módulos, APIs, configuración, testing |
| **Estrategia de Fallback** | `docs/ESTRATEGIA_FALLBACK.md` | Jerarquía de métodos, detección de bloqueos, Playwright |
| **README del Extractor** | `docs/README_EXTRACTOR.md` | Guía de uso, instalación, ejemplos, troubleshooting |

### 2. Configuración

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| **Configuración YAML** | `config/extractor_config.yaml` | Parámetros completos con valores por defecto |
| **Dependencias** | `requirements.txt` | Actualizado con nuevas librerías |

---

## 🏗️ Arquitectura Propuesta

### Módulos Nuevos (a implementar)

```
src/
├── article_downloader.py    # Descarga HTML con reintentos
├── article_extractor.py     # Extrae texto (trafilatura + BS4)
├── article_cleaner.py       # Limpia y normaliza texto
├── article_enricher.py      # Detecta idioma y metadatos
├── article_fallback.py      # Fallback con Playwright (opcional)
├── article_processor.py     # Orquestador principal
└── main_extractor.py        # CLI para ejecución
```

### Flujo de Datos

```
output.jsonl (noticias filtradas)
    ↓
article_downloader (HTML)
    ↓
article_extractor (trafilatura)
    ↓
┌───────────┴───────────┐
↓                       ↓
[OK]              [Fallo/Corto]
↓                       ↓
article_cleaner    BS4 Fallback
↓                       ↓
article_enricher   Playwright (si enabled)
↓                       ↓
└───────────┬───────────┘
            ↓
    articles_full.jsonl
    articles_full.csv
    failed_extractions.jsonl
```

---

## 🔧 Tecnologías Clave

| Tecnología | Propósito | Obligatoria |
|------------|-----------|-------------|
| **trafilatura** | Extracción principal de texto | ✅ Sí |
| **BeautifulSoup** | Fallback con selectores CSS | ✅ Sí (ya existe) |
| **Playwright** | Fallback para JavaScript | ❌ Opcional |
| **PyYAML** | Configuración | ✅ Sí |
| **langdetect** | Detección de idioma | ✅ Sí |
| **tenacity** | Reintentos con backoff | ✅ Sí (ya existe) |

---

## 📊 Modelo de Datos de Salida

```json
{
  "nombre_del_medio": "El País",
  "enlace": "https://...",
  "titular": "...",
  "fecha": "2025-11-26T10:30:00+00:00",
  "descripcion": "...",
  
  "texto": "Texto completo del artículo...",
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

---

## ⚙️ Configuración Recomendada

### Configuración Inicial (Conservadora)

```yaml
downloader:
  timeout: 15
  max_retries: 3
  delay_between_requests_same_domain: 1.0

processing:
  concurrency: 5

fallback:
  playwright_enabled: false  # Activar solo después de análisis
  playwright_whitelist_domains: []
```

### Configuración Optimizada (Después de Testing)

```yaml
processing:
  concurrency: 10  # Si se necesita más velocidad

fallback:
  playwright_enabled: true  # Si hay dominios que lo requieren
  playwright_whitelist_domains:
    - "dominio-verificado.com"
```

---

## 🚀 Roadmap de Implementación

### Fase 1: Core (Semana 1-2)
- [ ] `article_downloader.py`
- [ ] `article_extractor.py` (solo trafilatura)
- [ ] `article_cleaner.py`
- [ ] `article_processor.py` (básico)
- [ ] `main_extractor.py` (CLI)
- [ ] Tests básicos
- [ ] Ejecutar con 10-20 artículos de prueba

### Fase 2: Robustez (Semana 2-3)
- [ ] Fallback BS4 en `article_extractor.py`
- [ ] `article_enricher.py`
- [ ] Manejo de errores completo
- [ ] Rate limiting por dominio
- [ ] Tests de integración
- [ ] Ejecutar con 100 artículos reales

### Fase 3: Fallback Playwright (Semana 3-4)
- [ ] `article_fallback.py`
- [ ] Configuración de whitelist
- [ ] Tests con sitios dinámicos
- [ ] Optimización de rendimiento

### Fase 4: Integración (Semana 4)
- [ ] Integración con GUI
- [ ] Documentación completa
- [ ] Validación final
- [ ] Despliegue en producción

---

## 📈 Métricas de Éxito

| Métrica | Objetivo | Crítico si |
|---------|----------|------------|
| **Tasa de éxito** | > 85% | < 70% |
| **Tiempo/artículo** | < 10s | > 20s |
| **Texto completo** | > 80% | < 60% |
| **Uso Playwright** | < 5% | > 20% |

---

## 💡 Decisiones de Diseño Clave

### 1. Trafilatura como Método Principal
**Razón**: Rápido, preciso, bajo consumo de recursos

### 2. BeautifulSoup como Fallback 1
**Razón**: Permite personalización por dominio sin overhead de Playwright

### 3. Playwright como Último Recurso
**Razón**: Lento y costoso, solo para casos excepcionales

### 4. Whitelist para Playwright
**Razón**: Control explícito de qué dominios pueden usar recursos pesados

### 5. Configuración YAML
**Razón**: Facilita ajustes sin modificar código

### 6. Concurrencia con ThreadPoolExecutor
**Razón**: Balance entre velocidad y simplicidad (vs asyncio)

---

## 🎯 Casos de Uso Principales

### Caso 1: Análisis de Sentimiento
- Extraer texto completo
- Analizar tono y sentimiento sobre China
- Identificar narrativas dominantes

### Caso 2: Búsqueda Avanzada
- Buscar términos específicos en texto completo
- No limitarse a titular y descripción RSS

### Caso 3: Archivo Histórico
- Guardar contenido completo antes de que desaparezca
- Crear base de datos de noticias sobre China

### Caso 4: Análisis Comparativo
- Comparar cobertura entre medios
- Identificar diferencias en profundidad y enfoque

---

## ⚠️ Consideraciones Importantes

### Limitaciones Conocidas

1. **Paywalls**: Artículos de pago no son accesibles
2. **JavaScript pesado**: Algunos sitios requieren Playwright (lento)
3. **Rate limiting**: Medios pueden bloquear si se excede límite
4. **Cambios en estructura**: Selectores pueden quedar obsoletos

### Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Bloqueos frecuentes | Media | Alto | Rate limiting, User-Agent, Playwright |
| Selectores obsoletos | Alta | Medio | Mantenimiento mensual, auto-detección |
| Playwright lento | Baja | Medio | Whitelist limitada, límite de llamadas |
| Cambios en APIs | Baja | Alto | Monitoreo, alertas automáticas |

---

## 📋 Checklist de Despliegue

### Pre-Despliegue
- [ ] Revisar especificación técnica completa
- [ ] Verificar que `requirements.txt` está actualizado
- [ ] Revisar `extractor_config.yaml`
- [ ] Preparar entorno de testing

### Implementación
- [ ] Implementar módulos según roadmap
- [ ] Ejecutar tests unitarios
- [ ] Ejecutar tests de integración
- [ ] Validar con artículos reales

### Post-Despliegue
- [ ] Ejecutar con 100 artículos en producción
- [ ] Revisar `extraction_report.json`
- [ ] Analizar `failed_extractions.jsonl`
- [ ] Ajustar configuración según resultados
- [ ] Documentar lecciones aprendidas

---

## 🔗 Enlaces Rápidos

| Documento | Propósito |
|-----------|-----------|
| [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) | Arquitectura y especificación completa |
| [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) | Guía de fallbacks y Playwright |
| [README_EXTRACTOR.md](./README_EXTRACTOR.md) | Guía de usuario y ejemplos |
| [extractor_config.yaml](../config/extractor_config.yaml) | Configuración completa |

---

## 📞 Próximos Pasos

1. **Revisar documentación** completa en `docs/`
2. **Validar arquitectura** propuesta
3. **Comenzar implementación** según roadmap
4. **Ejecutar tests** con artículos reales
5. **Iterar y optimizar** según resultados

---

## 📝 Notas Finales

### Flexibilidad de la Especificación

La especificación es **adaptable**. Puedes:
- Usar bibliotecas alternativas si lo prefieres
- Ajustar arquitectura según necesidades
- Simplificar o expandir funcionalidades
- Modificar configuración según casos de uso

### Enfoque Incremental

**Recomendación**: Implementar en fases
1. Empezar con lo básico (trafilatura + limpieza)
2. Añadir fallbacks progresivamente
3. Activar Playwright solo si es necesario
4. Optimizar según métricas reales

### Mantenimiento Continuo

El módulo requiere **mantenimiento regular**:
- Actualizar selectores si sitios cambian
- Revisar logs para patrones de error
- Ajustar configuración según volumen
- Monitorear métricas de calidad

---

**Fecha de creación**: 2025-11-26  
**Versión**: 1.0  
**Estado**: Especificación completa - Lista para implementación

---

## ✅ Resumen de Archivos Creados

```
f:/pautalla/china/
├── docs/
│   ├── ESPECIFICACION_EXTRACTOR_ARTICULOS.md  ✅ Creado
│   ├── ESTRATEGIA_FALLBACK.md                 ✅ Creado
│   ├── README_EXTRACTOR.md                    ✅ Creado
│   └── RESUMEN_EJECUTIVO.md                   ✅ Este archivo
├── config/
│   └── extractor_config.yaml                  ✅ Creado
└── requirements.txt                           ✅ Actualizado
```

**Total**: 5 archivos creados/actualizados

**Tamaño total de documentación**: ~50 KB de especificaciones técnicas

---

**¡Especificación completa lista para implementación!** 🚀
