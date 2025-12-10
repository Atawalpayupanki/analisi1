"""
Script para regenerar el archivo Excel con hiperenlaces nativos.
Esto eliminará el error "Registros quitados: Fórmula".
"""
import json
import os
from pathlib import Path

# Importar el módulo de Excel actualizado
import sys
sys.path.insert(0, 'src')
from excel_storage import guardar_noticia_en_excel

# Leer artículos clasificados
classified_path = Path('data/articles_classified.jsonl')

if not classified_path.exists():
    print("No se encontró el archivo articles_classified.jsonl")
    print("Primero debes clasificar los artículos.")
    exit(1)

# Leer todos los artículos clasificados
with open(classified_path, 'r', encoding='utf-8') as f:
    classified_data = []
    for line in f:
        if line.strip():
            try:
                classified_data.append(json.loads(line))
            except json.JSONDecodeError:
                continue

print(f"Artículos clasificados encontrados: {len(classified_data)}")

# Eliminar el Excel antiguo si existe
excel_path = Path('data/noticias_historico.xlsx')
if excel_path.exists():
    backup_path = Path('data/noticias_historico_backup.xlsx')
    print(f"\nCreando backup en: {backup_path}")
    import shutil
    shutil.copy(excel_path, backup_path)
    os.remove(excel_path)
    print(f"Excel antiguo eliminado")

# Regenerar el Excel con hiperenlaces nativos
print(f"\nRegenerando Excel con {len(classified_data)} artículos...")
print("Esto puede tardar un momento...\n")

exitos = 0
fallos = 0

for i, article in enumerate(classified_data, 1):
    try:
        # Preparar datos de la noticia
        datos_noticia = {
            'medio': article.get('nombre_del_medio', article.get('medio', 'Desconocido')),
            'fecha': article.get('fecha', ''),
            'titulo': article.get('titulo', ''),
            'enlace': article.get('enlace', ''),
            'descripcion': article.get('descripcion', ''),
            'texto_completo': article.get('texto_completo', article.get('texto', ''))
        }
        
        # Preparar datos de clasificación
        datos_clasificacion = {
            'tema': article.get('tema', ''),
            'imagen_de_china': article.get('imagen_de_china', ''),
            'resumen_dos_frases': article.get('resumen_dos_frases', '')
        }
        
        # Guardar en Excel (sin mostrar todos los mensajes)
        import io
        import contextlib
        
        # Suprimir salida para no saturar la consola
        with contextlib.redirect_stdout(io.StringIO()):
            exito = guardar_noticia_en_excel(
                datos_noticia,
                datos_clasificacion,
                str(excel_path)
            )
        
        if exito:
            exitos += 1
            if i % 10 == 0:
                print(f"Procesados {i}/{len(classified_data)} artículos...")
        else:
            fallos += 1
            
    except Exception as e:
        print(f"Error en artículo {i}: {e}")
        fallos += 1

print(f"\n{'='*60}")
print(f"REGENERACIÓN COMPLETADA")
print(f"{'='*60}")
print(f"Artículos guardados: {exitos}")
print(f"Errores: {fallos}")
print(f"\nArchivo Excel regenerado: {excel_path}")
print(f"Backup del anterior: data/noticias_historico_backup.xlsx")
print(f"\nAhora al abrir el Excel NO deberías ver el mensaje de error.")
print(f"Los titulares serán enlaces clicables nativos de Excel.")
