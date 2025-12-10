# Módulo de Clasificación de Noticias con LangChain y Groq

Este documento describe el módulo de clasificación de noticias implementado con LangChain y la API de Groq.

## Descripción

El módulo `clasificador_langchain.py` recibe noticias ya procesadas (con texto completo extraído) y las clasifica automáticamente usando un modelo de lenguaje grande (LLM) de Groq. Devuelve un JSON estructurado con:

- **tema**: Categoría temática de la noticia
- **imagen_de_china**: Percepción de China en la noticia
- **resumen_dos_frases**: Resumen conciso en dos frases

## Características

### ✅ Integración con LangChain
- Uso idiomático de `PromptTemplate` y `RunnableSequence`
- Modelo Groq LLM (`llama-3.3-70b-versatile`)
- Configuración optimizada para clasificación (temperatura 0.0)

### ✅ Failover Automático de API Keys
- Dos claves API configurables: primaria y respaldo
- Cambio automático a clave de respaldo si la primaria falla
- Reintentos con backoff exponencial

### ✅ Validación y Reparación de JSON
- Validación estricta de campos requeridos
- Extracción automática de JSON de respuestas con texto adicional
- Normalización de categorías
- Manejo robusto de errores

### ✅ Diseño Modular
- Funciones separadas para cada responsabilidad
- Fácil integración con el pipeline existente
- Logging detallado para depuración

## Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Las nuevas dependencias incluyen:
- `langchain>=0.1.0`
- `langchain-groq>=0.0.1`
- `langchain-core>=0.1.0`
- `python-dotenv>=1.0.0`

### 2. Configurar API Keys

Copia el archivo de ejemplo y configura tus claves:

```bash
cp .env.example .env
```

Edita `.env` y agrega tus claves de Groq API:

```env
GROQ_API_KEY=tu_clave_api_principal
GROQ_API_KEY_BACKUP=tu_clave_api_respaldo
```

**Obtener claves API:**
1. Visita [https://console.groq.com/](https://console.groq.com/)
2. Crea una cuenta o inicia sesión
3. Ve a "API Keys"
4. Genera nuevas claves

## Uso

### Uso Básico

```python
from src.clasificador_langchain import clasificar_noticia_con_failover

# Datos de la noticia
datos = {
    "medio": "El País",
    "fecha": "2025-12-07",
    "titulo": "China lanza nuevo satélite",
    "descripcion": "Avance tecnológico espacial",
    "texto_completo": "China ha lanzado con éxito un nuevo satélite..."
}

# Clasificar
resultado = clasificar_noticia_con_failover(datos)

print(resultado)
# {
#   "tema": "Tecnología industrial",
#   "imagen_de_china": "Positiva",
#   "resumen_dos_frases": "China lanza satélite exitosamente. Refuerza posición espacial global.",
#   "medio": "El País",
#   "fecha": "2025-12-07",
#   ...
# }
```

### Integración con Pipeline

```python
import json
from pathlib import Path
from src.clasificador_langchain import clasificar_noticia_con_failover

# Leer artículos procesados
articles_path = Path("data/articles_full.jsonl")

resultados_clasificados = []

with open(articles_path, 'r', encoding='utf-8') as f:
    for line in f:
        article = json.loads(line)
        
        # Preparar datos
        datos = {
            "medio": article['nombre_del_medio'],
            "fecha": article['fecha'],
            "titulo": article['titular'],
            "descripcion": article['descripcion'],
            "texto_completo": article['texto']
        }
        
        # Clasificar
        try:
            clasificacion = clasificar_noticia_con_failover(datos)
            resultados_clasificados.append(clasificacion)
        except Exception as e:
            print(f"Error clasificando {article['titular']}: {e}")

# Guardar resultados
output_path = Path("data/articles_classified.jsonl")
with open(output_path, 'w', encoding='utf-8') as f:
    for resultado in resultados_clasificados:
        f.write(json.dumps(resultado, ensure_ascii=False) + '\n')
```

### Uso con API Key Específica

```python
from src.clasificador_langchain import clasificar_noticia

# Usar una API key específica (sin failover)
resultado = clasificar_noticia(
    datos=datos,
    api_key="tu_api_key_especifica",
    model_name="llama-3.3-70b-versatile"
)
```

## Categorías

### Temas
- Economia
- Política interior China
- Geopolítica
- Política social
- Territorio geografía y medio ambiente
- Cultura y ciencia
- Tecnología industrial
- Tecnología de consumo

### Imagen de China
- Amenaza
- Positiva
- Negativa
- Neutral
- Muy positiva
- Muy negativa
- Imperio de Xi Jinping

## Testing

Ejecuta el script de pruebas:

```bash
python test_clasificador.py
```

El script ejecuta múltiples tests:
1. **Validación JSON**: Verifica parsing y reparación
2. **Clasificación Básica**: Prueba con datos de ejemplo
3. **Clasificación Económica**: Valida clasificación temática
4. **Desde Archivo Real**: Procesa artículos reales del pipeline

## Estructura del Módulo

```
clasificador_langchain.py
├── Configuración
│   ├── CATEGORIAS_TEMA
│   ├── CATEGORIAS_IMAGEN
│   └── PROMPT_TEMPLATE
├── Inicialización
│   ├── init_groq_model()
│   ├── create_classification_prompt()
│   └── create_classification_chain()
├── Validación
│   ├── extract_json_from_text()
│   └── validate_and_repair_json()
└── Clasificación
    ├── clasificar_noticia()
    └── clasificar_noticia_con_failover()
```

## Manejo de Errores

El módulo maneja varios tipos de errores:

- **API Key inválida**: Cambia automáticamente a clave de respaldo
- **JSON mal formado**: Intenta extraer y reparar
- **Categorías inválidas**: Normaliza automáticamente
- **Campos faltantes**: Lanza error descriptivo
- **Timeout de API**: Reintenta con backoff exponencial

## Logging

El módulo usa logging estándar de Python:

```python
import logging

# Configurar nivel de logging
logging.basicConfig(level=logging.INFO)

# Los logs incluyen:
# - Inicio de clasificación
# - Cambios de API key
# - Advertencias de normalización
# - Errores detallados
```

## Consideraciones

- **Costos**: Cada clasificación consume tokens de la API de Groq
- **Rate Limits**: Respeta los límites de la API (usa failover si es necesario)
- **Determinismo**: Temperatura 0.0 para resultados consistentes
- **Idioma**: El prompt está en español, optimizado para noticias en español

## Solución de Problemas

### Error: "No se encontró GROQ_API_KEY"
- Verifica que existe el archivo `.env`
- Confirma que las claves están configuradas correctamente

### Error: "Ambas API keys fallaron"
- Verifica que las claves son válidas
- Comprueba tu cuota de API en console.groq.com
- Revisa tu conexión a internet

### JSON inválido persistente
- Revisa los logs para ver la respuesta del modelo
- Considera ajustar el prompt si es necesario
- Verifica que el texto de entrada no esté vacío

## Próximos Pasos

Posibles mejoras futuras:
- Procesamiento por lotes para mayor eficiencia
- Cache de clasificaciones para evitar duplicados
- Métricas de confianza en las clasificaciones
- Soporte para múltiples idiomas
- Integración directa en la GUI
