# RSS China News Filter

Sistema para descargar feeds RSS de medios españoles, parsear noticias y filtrar aquellas que mencionan a China.

## Características

- **Descarga robusta**: Reintentos automáticos con backoff exponencial
- **Modo asíncrono**: Descargas concurrentes para mejor rendimiento
- **Filtrado inteligente**: Búsqueda de palabras clave con word boundaries
- **Deduplicación**: Por URL y hash de contenido
- **Múltiples formatos**: Salida en JSON Lines y CSV
- **Logging completo**: Consola y archivo con niveles configurables

## Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes)

## Instalación

1. **Crear entorno virtual** (recomendado):

```bash
python -m venv venv
```

2. **Activar entorno virtual**:

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

3. **Instalar dependencias**:

```bash
pip install -r requirements.txt
```

## Configuración

### Feeds RSS (`config/feeds.json`)

Define los medios y sus URLs de feeds RSS:

```json
{
  "feeds": [
    {
      "nombre": "El País",
      "urls": [
        "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"
      ]
    }
  ]
}
```

### Keywords (`config/keywords.json`)

Lista de palabras clave relacionadas con China:

```json
{
  "keywords": [
    "china",
    "beijing",
    "xi jinping",
    "taiwán",
    "huawei"
  ]
}
```

## Uso

### Ejecución básica

```bash
python src/main.py
```

### Modo asíncrono (recomendado para >20 feeds)

```bash
python src/main.py --async
```

### Opciones disponibles

```bash
python src/main.py --help
```

Opciones:
- `--config PATH`: Ruta al archivo de feeds (default: `config/feeds.json`)
- `--keywords PATH`: Ruta al archivo de keywords (default: `config/keywords.json`)
- `--output-dir DIR`: Directorio de salida (default: `data/`)
- `--async`: Activar descargas asíncronas
- `--log-level LEVEL`: Nivel de logging: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `--log-dir DIR`: Directorio para logs (default: `logs/`)

### Ejemplos

**Modo verbose con async:**
```bash
python src/main.py --async --log-level DEBUG
```

**Configuración personalizada:**
```bash
python src/main.py --config mi_feeds.json --keywords mis_keywords.json --output-dir resultados/
```

## Estructura del proyecto

```
f:/pautalla/china/
├── src/
│   ├── feeds_list.py      # Carga y normaliza URLs de feeds
│   ├── downloader.py      # Descarga feeds con reintentos
│   ├── parser.py          # Parsea RSS y normaliza datos
│   ├── filtro_china.py    # Filtra noticias sobre China
│   ├── deduplicador.py    # Elimina duplicados
│   ├── almacenamiento.py  # Guarda en JSON/CSV
│   └── main.py            # Orquestador principal
├── config/
│   ├── feeds.json         # Configuración de feeds
│   └── keywords.json      # Keywords de China
├── data/                  # Archivos de salida
│   ├── output.jsonl       # Resultados en JSON Lines
│   └── output.csv         # Resultados en CSV
├── logs/                  # Archivos de log
│   └── rss_china.log
├── requirements.txt       # Dependencias Python
└── README.md             # Este archivo
```

## Formato de salida

### JSON Lines (`output.jsonl`)

Cada línea es un objeto JSON:

```json
{"nombre_del_medio": "El País", "rss_origen": "https://...", "titular": "...", "enlace": "https://...", "descripcion": "...", "fecha": "2025-11-19T18:00:00+00:00"}
```

### CSV (`output.csv`)

Formato CSV con UTF-8 BOM (compatible con Excel):

| nombre_del_medio | rss_origen | titular | enlace | descripcion | fecha |
|-----------------|------------|---------|--------|-------------|-------|
| El País | https://... | ... | https://... | ... | 2025-11-19T18:00:00+00:00 |

## Resumen de ejecución

Al finalizar, el programa muestra estadísticas:

```
============================================================
RESUMEN DE EJECUCIÓN
============================================================
Feeds consultados:        20
  - Exitosos:             18
  - Fallidos:             2
Ítems analizados:         450
Ítems sobre China:        35
Ítems únicos guardados:   32
============================================================
```

## Manejo de errores

El sistema es robusto ante fallos:

- **Feeds inaccesibles**: Se registra el error y continúa con los demás
- **Feeds mal formados**: Se intenta parsear y se registra advertencia
- **Timeouts**: Reintentos automáticos (3 intentos con backoff exponencial)
- **Errores de red**: Se capturan y registran sin interrumpir el proceso

Todos los errores se registran en:
- Consola (según nivel de log)
- Archivo `logs/rss_china.log`

## Verificación

### Comprobar salida

**JSON Lines:**
```bash
# Ver primeras líneas
head -n 5 data/output.jsonl

# Contar noticias
wc -l data/output.jsonl

# Parsear con jq (si está instalado)
jq . data/output.jsonl | less
```

**CSV:**
- Abrir con Excel, LibreOffice Calc o cualquier editor de hojas de cálculo
- El archivo usa UTF-8 con BOM para correcta visualización de tildes

### Revisar logs

```bash
# Ver últimas líneas del log
tail -n 50 logs/rss_china.log

# Buscar errores
grep ERROR logs/rss_china.log

# Buscar advertencias
grep WARNING logs/rss_china.log
```

## Troubleshooting

### No se encuentran noticias sobre China

- Verificar que `config/keywords.json` contiene keywords relevantes
- Ejecutar con `--log-level DEBUG` para ver qué se está filtrando
- Revisar que los feeds RSS estén activos y contengan noticias recientes

### Errores de descarga

- Verificar conexión a Internet
- Comprobar que las URLs de feeds son correctas
- Algunos feeds pueden tener rate limiting: usar `--async` con cuidado
- Revisar logs para ver errores HTTP específicos

### Problemas con dependencias

```bash
# Reinstalar dependencias
pip install --upgrade -r requirements.txt

# Verificar versión de Python
python --version  # Debe ser 3.10+
```

## Licencia

Proyecto educativo/interno.
