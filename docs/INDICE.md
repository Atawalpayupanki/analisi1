# 📚 Índice de Documentación - Módulo de Extracción de Artículos

## 🎯 Inicio Rápido

**¿Primera vez?** Empieza aquí:

1. 📋 **[RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md)** - Visión general en 5 minutos
2. 📖 **[README_EXTRACTOR.md](./README_EXTRACTOR.md)** - Guía de usuario y ejemplos
3. ⚙️ **[extractor_config.yaml](../config/extractor_config.yaml)** - Configuración

---

## 📑 Documentación Completa

### 1️⃣ Especificación Técnica

**Archivo**: [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md)

**Contenido**:
- ✅ Arquitectura del sistema
- ✅ Módulos y responsabilidades
- ✅ Modelo de datos
- ✅ Configuración detallada
- ✅ Dependencias
- ✅ Manejo de errores
- ✅ Concurrencia y rendimiento
- ✅ Logging y monitoreo
- ✅ Testing y validación
- ✅ Integración con GUI
- ✅ Despliegue y operación

**Cuándo leer**: Antes de implementar el módulo

**Audiencia**: Desarrolladores

**Tiempo de lectura**: 30-40 minutos

---

### 2️⃣ Estrategia de Fallback

**Archivo**: [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md)

**Contenido**:
- ✅ Jerarquía de métodos (trafilatura → BS4 → Playwright)
- ✅ Detección de bloqueos
- ✅ Gestión de whitelist de Playwright
- ✅ Límites operativos
- ✅ Estrategias de optimización
- ✅ Monitoreo y alertas
- ✅ Casos de uso y ejemplos
- ✅ Checklist de decisión

**Cuándo leer**: Al configurar fallbacks y Playwright

**Audiencia**: Desarrolladores y operadores

**Tiempo de lectura**: 20-30 minutos

---

### 3️⃣ README del Extractor

**Archivo**: [README_EXTRACTOR.md](./README_EXTRACTOR.md)

**Contenido**:
- ✅ Instalación paso a paso
- ✅ Configuración básica
- ✅ Ejemplos de uso
- ✅ Formato de salida
- ✅ Flujo de trabajo típico
- ✅ Rendimiento y recursos
- ✅ Métodos de extracción
- ✅ Troubleshooting
- ✅ Mantenimiento

**Cuándo leer**: Al usar el módulo por primera vez

**Audiencia**: Usuarios finales y operadores

**Tiempo de lectura**: 15-20 minutos

---

### 4️⃣ Resumen Ejecutivo

**Archivo**: [RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md)

**Contenido**:
- ✅ Objetivo y entregables
- ✅ Arquitectura propuesta
- ✅ Tecnologías clave
- ✅ Modelo de datos
- ✅ Roadmap de implementación
- ✅ Métricas de éxito
- ✅ Decisiones de diseño
- ✅ Consideraciones importantes
- ✅ Checklist de despliegue

**Cuándo leer**: Para visión general rápida

**Audiencia**: Todos

**Tiempo de lectura**: 10-15 minutos

---

## ⚙️ Configuración

### Archivo de Configuración Principal

**Archivo**: [extractor_config.yaml](../config/extractor_config.yaml)

**Secciones**:
- 🔽 **downloader**: Timeout, reintentos, rate limiting
- 🔍 **extractor**: Trafilatura, selectores BS4
- 🧹 **cleaner**: Normalización de texto
- 📊 **enricher**: Metadatos e idioma
- 🎭 **fallback**: Playwright (opcional)
- ⚡ **processing**: Concurrencia
- 💾 **output**: Rutas de archivos
- 📝 **logging**: Configuración de logs

**Formato**: YAML con comentarios explicativos

---

## 🗺️ Mapa de Navegación

### Por Rol

#### 👨‍💻 Desarrollador
1. [RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md) - Visión general
2. [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) - Arquitectura completa
3. [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) - Implementación de fallbacks
4. [extractor_config.yaml](../config/extractor_config.yaml) - Configuración

#### 👤 Usuario Final
1. [README_EXTRACTOR.md](./README_EXTRACTOR.md) - Guía de uso
2. [RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md) - Contexto general
3. [extractor_config.yaml](../config/extractor_config.yaml) - Ajustes básicos

#### 🔧 Operador/DevOps
1. [README_EXTRACTOR.md](./README_EXTRACTOR.md) - Instalación y uso
2. [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) - Troubleshooting
3. [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) - Sección de despliegue
4. [extractor_config.yaml](../config/extractor_config.yaml) - Optimización

---

### Por Tarea

#### 🚀 Instalación Inicial
1. [README_EXTRACTOR.md](./README_EXTRACTOR.md) → Sección "Instalación"
2. [extractor_config.yaml](../config/extractor_config.yaml) → Revisar valores por defecto

#### ⚙️ Configuración
1. [extractor_config.yaml](../config/extractor_config.yaml) → Editar parámetros
2. [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) → Sección "Configuración"
3. [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) → Configurar fallbacks

#### 🐛 Troubleshooting
1. [README_EXTRACTOR.md](./README_EXTRACTOR.md) → Sección "Troubleshooting"
2. [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) → Casos de uso
3. [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) → Manejo de errores

#### 🔧 Optimización
1. [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) → Estrategias de optimización
2. [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) → Concurrencia y rendimiento
3. [extractor_config.yaml](../config/extractor_config.yaml) → Ajustar parámetros

#### 🏗️ Implementación
1. [RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md) → Roadmap
2. [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) → Arquitectura completa
3. [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) → Implementar fallbacks

---

## 📊 Estructura de Archivos

```
f:/pautalla/china/
│
├── docs/                                    📚 DOCUMENTACIÓN
│   ├── INDICE.md                           ← ESTÁS AQUÍ
│   ├── RESUMEN_EJECUTIVO.md                🎯 Inicio rápido
│   ├── ESPECIFICACION_EXTRACTOR_ARTICULOS.md  📋 Especificación técnica
│   ├── ESTRATEGIA_FALLBACK.md              🔄 Guía de fallbacks
│   └── README_EXTRACTOR.md                 📖 Guía de usuario
│
├── config/                                  ⚙️ CONFIGURACIÓN
│   └── extractor_config.yaml               ⚙️ Config principal
│
├── src/                                     💻 CÓDIGO (A IMPLEMENTAR)
│   ├── article_downloader.py               🔽 Descarga HTML
│   ├── article_extractor.py                🔍 Extrae texto
│   ├── article_cleaner.py                  🧹 Limpia texto
│   ├── article_enricher.py                 📊 Enriquece metadatos
│   ├── article_fallback.py                 🎭 Fallback Playwright
│   ├── article_processor.py                ⚡ Orquestador
│   └── main_extractor.py                   🚀 CLI
│
└── requirements.txt                         📦 Dependencias
```

---

## 🔍 Búsqueda Rápida

### Conceptos Clave

| Concepto | Documento | Sección |
|----------|-----------|---------|
| **Trafilatura** | [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) | Nivel 1: Trafilatura |
| **BeautifulSoup** | [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) | Nivel 2: BeautifulSoup |
| **Playwright** | [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) | Nivel 3: Playwright |
| **Selectores CSS** | [extractor_config.yaml](../config/extractor_config.yaml) | extractor.domain_selectors |
| **Concurrencia** | [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) | Sección 7 |
| **Rate Limiting** | [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) | Sección 6.4 |
| **Detección de bloqueos** | [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) | Sección 3 |
| **Modelo de datos** | [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) | Sección 3.6 |
| **Instalación** | [README_EXTRACTOR.md](./README_EXTRACTOR.md) | Instalación |
| **Ejemplos de uso** | [README_EXTRACTOR.md](./README_EXTRACTOR.md) | Ejemplos de Uso |

---

## 📈 Flujo de Lectura Recomendado

### 🎯 Para Empezar (30 min)

```
1. RESUMEN_EJECUTIVO.md (10 min)
   ↓
2. README_EXTRACTOR.md (15 min)
   ↓
3. extractor_config.yaml (5 min - revisar)
```

### 🏗️ Para Implementar (2-3 horas)

```
1. RESUMEN_EJECUTIVO.md (10 min)
   ↓
2. ESPECIFICACION_EXTRACTOR_ARTICULOS.md (40 min)
   ↓
3. ESTRATEGIA_FALLBACK.md (30 min)
   ↓
4. extractor_config.yaml (10 min - revisar detalladamente)
   ↓
5. README_EXTRACTOR.md (20 min - ejemplos)
```

### 🔧 Para Operar (1 hora)

```
1. README_EXTRACTOR.md (20 min)
   ↓
2. ESTRATEGIA_FALLBACK.md (20 min - troubleshooting)
   ↓
3. extractor_config.yaml (10 min - optimización)
   ↓
4. ESPECIFICACION_EXTRACTOR_ARTICULOS.md (10 min - sección despliegue)
```

---

## 💡 Tips de Navegación

### 🔖 Marcadores Útiles

Guarda estos enlaces para acceso rápido:

- **Configuración**: [extractor_config.yaml](../config/extractor_config.yaml)
- **Troubleshooting**: [README_EXTRACTOR.md](./README_EXTRACTOR.md#-troubleshooting)
- **Fallbacks**: [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md#-jerarqu%C3%ADa-de-m%C3%A9todos-de-extracci%C3%B3n)
- **Ejemplos**: [README_EXTRACTOR.md](./README_EXTRACTOR.md#-ejemplos-de-uso)

### 🔍 Búsqueda en Documentos

Usa Ctrl+F (o Cmd+F) para buscar:
- `playwright` → Configuración de fallback
- `selector` → Selectores CSS por dominio
- `concurrency` → Configuración de paralelismo
- `timeout` → Configuración de timeouts
- `error` → Manejo de errores

---

## 📞 Soporte

### ❓ Preguntas Frecuentes

**P: ¿Por dónde empiezo?**  
R: Lee [RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md) primero

**P: ¿Cómo instalo el módulo?**  
R: Ver [README_EXTRACTOR.md](./README_EXTRACTOR.md) → Instalación

**P: ¿Cómo configuro Playwright?**  
R: Ver [ESTRATEGIA_FALLBACK.md](./ESTRATEGIA_FALLBACK.md) → Sección 4

**P: ¿Qué hacer si hay muchos errores?**  
R: Ver [README_EXTRACTOR.md](./README_EXTRACTOR.md) → Troubleshooting

**P: ¿Cómo optimizar rendimiento?**  
R: Ver [ESPECIFICACION_EXTRACTOR_ARTICULOS.md](./ESPECIFICACION_EXTRACTOR_ARTICULOS.md) → Sección 7

---

## 📝 Notas de Versión

**Versión**: 1.0  
**Fecha**: 2025-11-26  
**Estado**: Especificación completa

**Documentos incluidos**:
- ✅ Especificación técnica completa
- ✅ Estrategia de fallback
- ✅ README de usuario
- ✅ Resumen ejecutivo
- ✅ Configuración YAML
- ✅ Este índice

**Total de páginas**: ~50 páginas de documentación técnica

---

## 🎯 Próximos Pasos

1. ✅ **Revisar documentación** - Leer documentos según tu rol
2. ⏳ **Implementar módulos** - Seguir roadmap en RESUMEN_EJECUTIVO.md
3. ⏳ **Configurar sistema** - Ajustar extractor_config.yaml
4. ⏳ **Ejecutar tests** - Validar con artículos reales
5. ⏳ **Desplegar** - Poner en producción

---

**¡Documentación completa y lista para usar!** 📚✨

---

_Última actualización: 2025-11-26_
