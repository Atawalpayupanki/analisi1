"""
Script de prueba para el módulo de clasificación de noticias.

Este script demuestra cómo usar el clasificador con datos de ejemplo
y valida que todas las funcionalidades trabajen correctamente.
"""

import json
import sys
from pathlib import Path

# Agregar src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.clasificador_langchain import (
    clasificar_noticia_con_failover,
    validate_and_repair_json,
    CATEGORIAS_TEMA,
    CATEGORIAS_IMAGEN
)


def test_clasificacion_basica():
    """Prueba clasificación básica con datos de ejemplo."""
    print("\n" + "=" * 70)
    print("TEST 1: CLASIFICACIÓN BÁSICA")
    print("=" * 70)
    
    datos = {
        "medio": "El País",
        "fecha": "2025-12-07",
        "titulo": "China lanza nuevo satélite de comunicaciones",
        "descripcion": "Avance tecnológico en el programa espacial chino",
        "texto_completo": """China ha lanzado con éxito un nuevo satélite de comunicaciones 
        desde el Centro de Lanzamiento de Satélites de Xichang. El satélite, denominado 
        ChinaSat-9B, forma parte del programa de expansión de telecomunicaciones del país. 
        Este lanzamiento representa un avance significativo en la capacidad tecnológica china 
        en el sector espacial y refuerza su posición como potencia espacial global. El gobierno 
        chino ha invertido miles de millones en su programa espacial en los últimos años.""",
        "enlace": "https://ejemplo.com/noticia1"
    }
    
    print(f"\n📰 Noticia: {datos['titulo']}")
    print(f"📡 Medio: {datos['medio']}")
    print(f"📅 Fecha: {datos['fecha']}")
    print("\n🔄 Clasificando...")
    
    try:
        resultado = clasificar_noticia_con_failover(datos)
        
        print("\n✅ CLASIFICACIÓN EXITOSA")
        print(f"\n📊 Tema: {resultado['tema']}")
        print(f"🖼️  Imagen de China: {resultado['imagen_de_china']}")
        print(f"📝 Resumen: {resultado['resumen_dos_frases']}")
        
        # Validar categorías
        assert resultado['tema'] in CATEGORIAS_TEMA, f"Tema inválido: {resultado['tema']}"
        assert resultado['imagen_de_china'] in CATEGORIAS_IMAGEN, f"Imagen inválida: {resultado['imagen_de_china']}"
        
        print("\n✅ Todas las validaciones pasaron")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validacion_json():
    """Prueba validación y reparación de JSON."""
    print("\n" + "=" * 70)
    print("TEST 2: VALIDACIÓN DE JSON")
    print("=" * 70)
    
    # JSON válido
    json_valido = '''{
        "tema": "Economia",
        "imagen_de_china": "Positiva",
        "resumen_dos_frases": "China crece económicamente. Las inversiones aumentan."
    }'''
    
    print("\n🔍 Probando JSON válido...")
    try:
        resultado = validate_and_repair_json(json_valido)
        print(f"✅ JSON válido parseado correctamente")
        print(f"   Tema: {resultado['tema']}")
        print(f"   Imagen: {resultado['imagen_de_china']}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    # JSON con texto adicional
    json_con_texto = '''Aquí está el resultado:
    {
        "tema": "Geopolítica",
        "imagen_de_china": "Amenaza",
        "resumen_dos_frases": "Tensiones geopolíticas aumentan. Relaciones internacionales complejas."
    }
    Espero que esto ayude.'''
    
    print("\n🔍 Probando JSON con texto adicional...")
    try:
        resultado = validate_and_repair_json(json_con_texto)
        print(f"✅ JSON extraído y parseado correctamente")
        print(f"   Tema: {resultado['tema']}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    print("\n✅ Todas las validaciones de JSON pasaron")
    return True


def test_clasificacion_economia():
    """Prueba clasificación de noticia económica."""
    print("\n" + "=" * 70)
    print("TEST 3: CLASIFICACIÓN ECONÓMICA")
    print("=" * 70)
    
    datos = {
        "medio": "Financial Times",
        "fecha": "2025-12-07",
        "titulo": "El PIB de China supera expectativas en el tercer trimestre",
        "descripcion": "Crecimiento económico robusto impulsado por exportaciones",
        "texto_completo": """La economía china creció un 5.2% en el tercer trimestre del año,
        superando las expectativas de los analistas que proyectaban un 4.8%. El crecimiento
        fue impulsado principalmente por un aumento en las exportaciones y la inversión en
        infraestructura. Los sectores manufacturero y tecnológico mostraron particular fortaleza.
        El Banco Popular de China mantuvo su política monetaria acomodaticia para sostener
        el crecimiento. Los mercados financieros respondieron positivamente a estos datos.""",
        "enlace": "https://ejemplo.com/noticia2"
    }
    
    print(f"\n📰 Noticia: {datos['titulo']}")
    print("\n🔄 Clasificando...")
    
    try:
        resultado = clasificar_noticia_con_failover(datos)
        
        print("\n✅ CLASIFICACIÓN EXITOSA")
        print(f"\n📊 Tema: {resultado['tema']}")
        print(f"🖼️  Imagen de China: {resultado['imagen_de_china']}")
        print(f"📝 Resumen: {resultado['resumen_dos_frases']}")
        
        # Esta noticia debería clasificarse como Economía
        if resultado['tema'] == "Economia":
            print("\n✅ Tema clasificado correctamente como Economía")
        else:
            print(f"\n⚠️  Tema clasificado como '{resultado['tema']}' (esperado: Economia)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_desde_archivo():
    """Prueba clasificación desde archivo real si existe."""
    print("\n" + "=" * 70)
    print("TEST 4: CLASIFICACIÓN DESDE ARCHIVO REAL")
    print("=" * 70)
    
    articles_path = Path("data/articles_full.jsonl")
    
    if not articles_path.exists():
        print("\n⚠️  No se encontró data/articles_full.jsonl")
        print("   Ejecuta primero el pipeline principal para generar datos")
        return None
    
    print(f"\n📂 Cargando artículo desde {articles_path}")
    
    try:
        with open(articles_path, 'r', encoding='utf-8') as f:
            # Leer primera línea
            line = f.readline()
            if not line.strip():
                print("❌ Archivo vacío")
                return False
            
            article = json.loads(line)
        
        # Preparar datos
        datos = {
            "medio": article.get('nombre_del_medio', 'Desconocido'),
            "fecha": article.get('fecha', ''),
            "titulo": article.get('titular', ''),
            "descripcion": article.get('descripcion', ''),
            "texto_completo": article.get('texto', article.get('descripcion', '')),
            "enlace": article.get('enlace', '')
        }
        
        print(f"\n📰 Noticia: {datos['titulo'][:80]}...")
        print(f"📡 Medio: {datos['medio']}")
        print("\n🔄 Clasificando...")
        
        resultado = clasificar_noticia_con_failover(datos)
        
        print("\n✅ CLASIFICACIÓN EXITOSA")
        print(f"\n📊 Tema: {resultado['tema']}")
        print(f"🖼️  Imagen de China: {resultado['imagen_de_china']}")
        print(f"📝 Resumen: {resultado['resumen_dos_frases']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los tests."""
    print("\n" + "=" * 70)
    print("🧪 SUITE DE PRUEBAS - CLASIFICADOR DE NOTICIAS")
    print("=" * 70)
    
    # Verificar que exista .env
    env_path = Path(".env")
    if not env_path.exists():
        print("\n⚠️  ADVERTENCIA: No se encontró archivo .env")
        print("   Copia .env.example a .env y configura tus API keys:")
        print("   cp .env.example .env")
        print("\n   Luego edita .env y agrega tus claves de Groq API")
        return
    
    resultados = []
    
    # Test 1: Validación JSON
    resultados.append(("Validación JSON", test_validacion_json()))
    
    # Test 2: Clasificación básica
    resultados.append(("Clasificación Básica", test_clasificacion_basica()))
    
    # Test 3: Clasificación económica
    resultados.append(("Clasificación Económica", test_clasificacion_economia()))
    
    # Test 4: Desde archivo real
    resultado_archivo = test_desde_archivo()
    if resultado_archivo is not None:
        resultados.append(("Clasificación desde Archivo", resultado_archivo))
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 70)
    
    for nombre, resultado in resultados:
        estado = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{estado} - {nombre}")
    
    total = len(resultados)
    exitosos = sum(1 for _, r in resultados if r)
    
    print(f"\n🎯 Total: {exitosos}/{total} pruebas exitosas")
    
    if exitosos == total:
        print("\n🎉 ¡Todas las pruebas pasaron!")
    else:
        print(f"\n⚠️  {total - exitosos} prueba(s) fallaron")


if __name__ == "__main__":
    main()
