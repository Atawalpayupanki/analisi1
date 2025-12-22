"""
Módulo de clasificación de noticias usando LangChain y Groq API.

Este módulo recibe noticias ya procesadas (con texto completo) y las clasifica
usando un modelo LLM de Groq, devolviendo un JSON estructurado con:
- tema
- imagen_de_china


Incluye failover automático entre dos API keys y validación estricta de JSON.
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_groq import ChatGroq

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================

CATEGORIAS_TEMA = [
    "Economia",
    "Política interior China",
    "Geopolítica",
    "Política social",
    "Territorio geografía y medio ambiente",
    "Cultura y ciencia",
    "Tecnología industrial",
    "Tecnología de consumo"
]

CATEGORIAS_IMAGEN = [
    "Amenaza",
    "Positiva",
    "Negativa",
    "Neutral",
    "Muy positiva",
    "Muy negativa",
    "Imperio de Xi Jinping"
]

# Prompt actualizado para clasificación multilingüe
PROMPT_TEMPLATE = """Instrucciones:
Clasifica la siguiente noticia únicamente a partir del contenido proporcionado. No inventes información ni interpretes más allá de lo explícito. Evalúa la imagen de China tal como es presentada por el medio, teniendo en cuenta su procedencia y contexto editorial.

Si el texto original no está en español, genera el resumen final en español igualmente, sin traducir literalmente, sino resumiendo el contenido en dos frases claras y concisas.

Si un artículo toca múltiples áreas, elige únicamente la que sea dominante en el texto.

Tu salida debe ser exclusivamente un objeto JSON válido. No añadas comentarios, explicaciones ni texto fuera del JSON.

Categorías de "tema":

Economia

Política interior China

Geopolítica

Política social

Territorio geografía y medio ambiente

Cultura y ciencia

Tecnología industrial

Tecnología de consumo

Categorías de "imagen_de_china":

Amenaza

Positiva

Negativa

Neutral

Muy positiva

Muy negativa

Imperio de Xi Jinping

Contenido a analizar:

Medio: {medio}

Procedencia del medio: {procedencia}

Idioma del texto: {idioma}

Fecha: {fecha}

Título: {titulo}

Descripción breve: {descripcion}

Texto completo: {texto_completo}

Tu salida debe seguir este formato exacto en JSON:

{{
  "tema": "",
  "imagen_de_china": "",
  "resumen_dos_frases": ""
}}"""


# ============================================================
# INICIALIZACIÓN DE COMPONENTES
# ============================================================

def init_groq_model(api_key: str, model_name: str = "llama-3.3-70b-versatile") -> ChatGroq:
    """
    Inicializa el modelo Groq LLM.
    
    Args:
        api_key: Clave API de Groq
        model_name: Nombre del modelo a usar
        
    Returns:
        Instancia de ChatGroq configurada
    """
    return ChatGroq(
        api_key=api_key,
        model_name=model_name,
        temperature=0.0,  # Determinístico para clasificación
        max_tokens=500,   # Suficiente para respuesta estructurada
        timeout=30,
        max_retries=2
    )


def create_classification_prompt() -> PromptTemplate:
    """
    Crea el prompt template para clasificación.
    
    Returns:
        PromptTemplate configurado con las variables necesarias
    """
    return PromptTemplate(
        input_variables=["medio", "procedencia", "idioma", "fecha", "titulo", "descripcion", "texto_completo"],
        template=PROMPT_TEMPLATE
    )


def create_classification_chain(llm: ChatGroq) -> RunnableSequence:
    """
    Crea la cadena de clasificación completa.
    
    Args:
        llm: Instancia del modelo Groq
        
    Returns:
        RunnableSequence que procesa la entrada y devuelve clasificación
    """
    prompt = create_classification_prompt()
    chain = prompt | llm
    return chain


# ============================================================
# VALIDACIÓN Y REPARACIÓN DE JSON
# ============================================================

def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extrae JSON de un texto que puede contener contenido adicional.
    
    Args:
        text: Texto que puede contener JSON
        
    Returns:
        String JSON extraído o None
    """
    # Buscar bloques JSON con llaves
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    if matches:
        # Retornar el match más largo (probablemente el JSON completo)
        return max(matches, key=len)
    
    return None


def validate_and_repair_json(json_str: str) -> Dict[str, Any]:
    """
    Valida y repara JSON de respuesta del modelo.
    
    Args:
        json_str: String JSON a validar
        
    Returns:
        Diccionario con los datos validados
        
    Raises:
        ValueError: Si el JSON no puede ser reparado o validado
    """
    # Intentar parsear directamente
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # Intentar extraer JSON del texto
        logger.warning("JSON mal formado, intentando extraer...")
        extracted = extract_json_from_text(json_str)
        
        if not extracted:
            raise ValueError(f"No se pudo extraer JSON válido de: {json_str[:200]}")
        
        try:
            data = json.loads(extracted)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON extraído sigue siendo inválido: {e}")
    
    # Validar campos requeridos
    required_fields = ["tema", "imagen_de_china"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValueError(f"Campos faltantes en JSON: {missing_fields}")
    
    # Validar categorías
    tema = data["tema"]
    imagen = data["imagen_de_china"]
    
    if tema not in CATEGORIAS_TEMA:
        logger.warning(f"Tema '{tema}' no está en categorías válidas. Intentando normalizar...")
        # Intentar encontrar coincidencia parcial
        tema_lower = tema.lower()
        for cat in CATEGORIAS_TEMA:
            if cat.lower() in tema_lower or tema_lower in cat.lower():
                data["tema"] = cat
                logger.info(f"Tema normalizado a: {cat}")
                break
        else:
            raise ValueError(f"Tema '{tema}' no válido. Debe ser uno de: {CATEGORIAS_TEMA}")
    
    if imagen not in CATEGORIAS_IMAGEN:
        logger.warning(f"Imagen '{imagen}' no está en categorías válidas. Intentando normalizar...")
        imagen_lower = imagen.lower()
        for cat in CATEGORIAS_IMAGEN:
            if cat.lower() in imagen_lower or imagen_lower in cat.lower():
                data["imagen_de_china"] = cat
                logger.info(f"Imagen normalizada a: {cat}")
                break
        else:
            raise ValueError(f"Imagen '{imagen}' no válida. Debe ser uno de: {CATEGORIAS_IMAGEN}")
    
    return data


# ============================================================
# FUNCIONES DE CLASIFICACIÓN
# ============================================================

def clasificar_noticia(
    datos: Dict[str, str],
    api_key: Optional[str] = None,
    model_name: str = "llama-3.3-70b-versatile"
) -> Dict[str, Any]:
    """
    Clasifica una noticia usando Groq API.
    
    Args:
        datos: Diccionario con las claves:
            - medio: Nombre del medio
            - procedencia: Procedencia del medio (Occidental | China), opcional
            - idioma: Idioma del texto (es, zh, etc.), opcional
            - fecha: Fecha de publicación
            - titulo: Título de la noticia
            - descripcion: Descripción breve
            - texto_completo: Texto completo del artículo
        api_key: Clave API de Groq (opcional, usa variable de entorno si no se proporciona)
        model_name: Nombre del modelo a usar
        
    Returns:
        Diccionario con:
            - tema: Categoría temática
            - imagen_de_china: Categoría de imagen
            - resumen_dos_frases: Resumen en español (2 frases)
            - metadatos originales (medio, fecha, titulo, etc.)
            
    Raises:
        ValueError: Si faltan datos requeridos o la clasificación falla
        Exception: Si hay error en la API
    """
    # Validar datos de entrada
    required_keys = ["medio", "fecha", "titulo", "descripcion", "texto_completo"]
    missing_keys = [key for key in required_keys if key not in datos]
    
    if missing_keys:
        raise ValueError(f"Faltan campos requeridos: {missing_keys}")
    
    # Obtener API key
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("No se encontró GROQ_API_KEY en variables de entorno")
    
    # Inicializar modelo y cadena
    logger.info(f"Clasificando noticia: {datos['titulo'][:50]}...")
    
    try:
        llm = init_groq_model(api_key, model_name)
        chain = create_classification_chain(llm)
        
        # Ejecutar clasificación (con procedencia e idioma opcionales)
        response = chain.invoke({
            "medio": datos["medio"],
            "procedencia": datos.get("procedencia", "Occidental"),
            "idioma": datos.get("idioma", "es"),
            "fecha": datos["fecha"],
            "titulo": datos["titulo"],
            "descripcion": datos["descripcion"],
            "texto_completo": datos["texto_completo"]
        })
        
        # Extraer contenido de la respuesta
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Validar y parsear JSON
        clasificacion = validate_and_repair_json(response_text)
        
        # Agregar metadatos originales
        resultado = {
            **clasificacion,
            "medio": datos["medio"],
            "procedencia": datos.get("procedencia", "Occidental"),
            "idioma": datos.get("idioma", "es"),
            "fecha": datos["fecha"],
            "titulo": datos["titulo"],
            "descripcion": datos["descripcion"],
            "enlace": datos.get("enlace", "")
        }
        
        resumen = clasificacion.get('resumen_dos_frases', '')
        logger.info(f"Clasificación exitosa: tema={clasificacion['tema']}, imagen={clasificacion['imagen_de_china']}")
        return resultado
        
    except Exception as e:
        logger.error(f"Error en clasificación: {e}")
        raise


def clasificar_noticia_con_failover(
    datos: Dict[str, str],
    model_name: str = "llama-3.3-70b-versatile"
) -> Dict[str, Any]:
    """
    Clasifica una noticia con failover automático entre múltiples API keys.
    
    Intenta con GROQ_API_KEY, luego GROQ_API_KEY_BACKUP, GROQ_API_KEY_3, etc.
    
    Args:
        datos: Diccionario con datos de la noticia
        model_name: Nombre del modelo a usar
        
    Returns:
        Diccionario con la clasificación y metadatos
        
    Raises:
        Exception: Si todas las API keys fallan
    """
    # Lista de claves a intentar en orden de prioridad
    keys_to_try = []
    
    # Recolectar claves disponibles
    env_vars = [
        "GROQ_API_KEY", 
        "GROQ_API_KEY_BACKUP", 
        "GROQ_API_KEY_3", 
        "GROQ_API_KEY_4"
    ]
    
    for var_name in env_vars:
        key = os.getenv(var_name)
        if key:
            keys_to_try.append((var_name, key))
    
    if not keys_to_try:
        raise ValueError(
            "No se encontraron claves API. Define GROQ_API_KEY, GROQ_API_KEY_BACKUP, "
            "GROQ_API_KEY_3 o GROQ_API_KEY_4 en el archivo .env"
        )
    
    last_exception = None
    
    for i, (var_name, api_key) in enumerate(keys_to_try):
        try:
            logger.info(f"Intentando clasificación con API key #{i+1} ({var_name})...")
            return clasificar_noticia(datos, api_key=api_key, model_name=model_name)
        except Exception as e:
            logger.warning(f"Falló API key #{i+1} ({var_name}): {e}")
            last_exception = e
            
    raise Exception(f"Todas las API keys ({len(keys_to_try)}) fallaron. Último error: {last_exception}")


# ============================================================
# PUNTO DE ENTRADA PARA TESTING
# ============================================================

if __name__ == "__main__":
    # Configurar logging para testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Datos de prueba
    datos_prueba = {
        "medio": "El País",
        "fecha": "2025-12-07",
        "titulo": "China lanza nuevo satélite de comunicaciones",
        "descripcion": "Avance tecnológico en el programa espacial chino",
        "texto_completo": """China ha lanzado con éxito un nuevo satélite de comunicaciones 
        desde el Centro de Lanzamiento de Satélites de Xichang. El satélite, denominado 
        ChinaSat-9B, forma parte del programa de expansión de telecomunicaciones del país. 
        Este lanzamiento representa un avance significativo en la capacidad tecnológica china 
        en el sector espacial y refuerza su posición como potencia espacial global.""",
        "enlace": "https://ejemplo.com/noticia"
    }
    
    try:
        print("=" * 60)
        print("PRUEBA DE CLASIFICACIÓN DE NOTICIAS")
        print("=" * 60)
        print(f"\nNoticia: {datos_prueba['titulo']}")
        print(f"Medio: {datos_prueba['medio']}")
        print(f"Fecha: {datos_prueba['fecha']}")
        print("\nClasificando...")
        
        resultado = clasificar_noticia_con_failover(datos_prueba)
        
        print("\n" + "=" * 60)
        print("RESULTADO DE CLASIFICACIÓN")
        print("=" * 60)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
