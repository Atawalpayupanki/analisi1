# Clasificador de Noticias - Guía Rápida

## Instalación Rápida

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar claves API
cp .env.example .env
# Editar .env y agregar tus claves de Groq
```

## Uso Básico

```python
from src.clasificador_langchain import clasificar_noticia_con_failover

datos = {
    "medio": "El País",
    "fecha": "2025-12-07",
    "titulo": "China lanza nuevo satélite",
    "descripcion": "Avance tecnológico",
    "texto_completo": "Texto completo del artículo..."
}

resultado = clasificar_noticia_con_failover(datos)
# Retorna: {"tema": "...", "imagen_de_china": "...", "resumen_dos_frases": "..."}
```

## Testing

```bash
python test_clasificador.py
```

## Categorías

**Temas:** Economia | Política interior China | Geopolítica | Política social | Territorio geografía y medio ambiente | Cultura y ciencia | Tecnología industrial | Tecnología de consumo

**Imagen:** Amenaza | Positiva | Negativa | Neutral | Muy positiva | Muy negativa | Imperio de Xi Jinping

## Documentación Completa

Ver: `docs/clasificador_langchain.md`
