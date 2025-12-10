import json

# Leer artículos clasificados
try:
    with open('data/articles_classified.jsonl', 'r', encoding='utf-8') as f:
        classified = [json.loads(line) for line in f if line.strip()]
    
    # Filtrar El Mundo
    elmundo_classified = [a for a in classified if 'mundo' in a.get('nombre_del_medio', '').lower() or 'mundo' in a.get('medio', '').lower()]
    
    print(f'Total El Mundo articles CLASIFICADOS: {len(elmundo_classified)}')
    print('\nPrimeros 5 titulares de El Mundo clasificados:')
    for i, a in enumerate(elmundo_classified[:5], 1):
        titular = a.get('titulo', 'NO TITLE')
        tema = a.get('tema', 'NO TEMA')
        print(f'{i}. [{tema}] {titular[:80]}...')
        
except FileNotFoundError:
    print('No se encontró el archivo articles_classified.jsonl')
    print('Esto significa que aún no se ha ejecutado la clasificación.')
