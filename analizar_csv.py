import csv
from collections import Counter

# Leer el archivo CSV (utf-8-sig para manejar el BOM)
with open('data/articles_full.csv', encoding='utf-8-sig') as f:
    data = list(csv.DictReader(f))

total = len(data)
exitosos = sum(1 for row in data if row['scrape_status'] == 'ok')
errores = total - exitosos

print("=" * 60)
print("RESUMEN DE ARTICULOS PROCESADOS")
print("=" * 60)
print(f"\nTotal de articulos: {total}")
print(f"Articulos exitosos (ok): {exitosos}")
print(f"Articulos con errores: {errores}")

# Desglose por medio
print("\n" + "-" * 60)
print("ARTICULOS POR MEDIO DE COMUNICACION:")
print("-" * 60)
medios = Counter(row['nombre_del_medio'] for row in data)
for medio, count in medios.most_common():
    print(f"  {medio}: {count}")

# Métodos de extracción
print("\n" + "-" * 60)
print("METODOS DE EXTRACCION USADOS:")
print("-" * 60)
metodos = Counter(row['extraction_method'] for row in data if row['scrape_status'] == 'ok')
for metodo, count in metodos.most_common():
    print(f"  {metodo}: {count}")

# Estadísticas de errores (si hay)
if errores > 0:
    print("\n" + "-" * 60)
    print("DESGLOSE DE ERRORES:")
    print("-" * 60)
    status_counts = Counter(row['scrape_status'] for row in data if row['scrape_status'] != 'ok')
    for status, count in status_counts.most_common():
        print(f"  {status}: {count}")

# Estadísticas de contenido
print("\n" + "-" * 60)
print("ESTADISTICAS DE CONTENIDO:")
print("-" * 60)
total_palabras = sum(int(row['word_count']) for row in data if row['word_count'])
promedio_palabras = total_palabras / exitosos if exitosos > 0 else 0
print(f"  Total de palabras extraidas: {total_palabras:,}")
print(f"  Promedio de palabras por articulo: {promedio_palabras:.0f}")

print("\n" + "=" * 60)
