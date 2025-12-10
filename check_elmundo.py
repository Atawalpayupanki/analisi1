import json

# Leer artículos completos
with open('data/articles_full.jsonl', 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f if line.strip()]

# Filtrar El Mundo
elmundo = [a for a in data if 'mundo' in a.get('nombre_del_medio', '').lower()]

print(f'Total El Mundo articles: {len(elmundo)}')
print('\nPrimeros 5 titulares de El Mundo:')
for i, a in enumerate(elmundo[:5], 1):
    titular = a.get('titular', 'NO TITLE')
    print(f'{i}. {titular[:100]}...')
    
# Verificar si tienen texto
print('\n¿Tienen texto extraído?')
for i, a in enumerate(elmundo[:5], 1):
    texto = a.get('texto', '')
    tiene_texto = len(texto) > 100 if texto else False
    print(f'{i}. Texto: {"SÍ" if tiene_texto else "NO"} ({len(texto) if texto else 0} caracteres)')
