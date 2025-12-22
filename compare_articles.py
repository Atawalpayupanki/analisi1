import csv
import os

def compare_articles():
    """Compare articles_full.csv and articles_classified.csv to find missing articles."""
    
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    full_file = os.path.join(data_dir, 'articles_full.csv')
    classified_file = os.path.join(data_dir, 'articles_classified.csv')
    
    # Read classified articles and store their links
    classified_links = set()
    with open(classified_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            classified_links.add(row['enlace'])
    
    # Read full articles and find missing ones
    missing_articles = []
    with open(full_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['enlace'] not in classified_links:
                missing_articles.append({
                    'medio': row['nombre_del_medio'],
                    'fecha': row['fecha'],
                    'titulo': row['titular'],
                    'enlace': row['enlace'],
                    'scrape_status': row['scrape_status']
                })
    
    # Print results
    print(f"Total articles in articles_full.csv: {len(classified_links) + len(missing_articles)}")
    print(f"Total articles in articles_classified.csv: {len(classified_links)}")
    print(f"Missing articles: {len(missing_articles)}\n")
    
    if missing_articles:
        print("=" * 100)
        print("MISSING ARTICLES:")
        print("=" * 100)
        for i, article in enumerate(missing_articles, 1):
            print(f"\n{i}. {article['titulo']}")
            print(f"   Medio: {article['medio']}")
            print(f"   Fecha: {article['fecha']}")
            print(f"   Status: {article['scrape_status']}")
            print(f"   Link: {article['enlace']}")
    else:
        print("No missing articles found. All articles from articles_full.csv are in articles_classified.csv")
    
    # Save to file
    output_file = os.path.join(data_dir, 'missing_articles.csv')
    if missing_articles:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['medio', 'fecha', 'titulo', 'enlace', 'scrape_status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(missing_articles)
        print(f"\n\nMissing articles saved to: {output_file}")

if __name__ == '__main__':
    compare_articles()
