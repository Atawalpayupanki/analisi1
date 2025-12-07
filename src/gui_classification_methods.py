"""
Métodos de clasificación para la GUI.
Este archivo contiene los métodos que se agregarán a la clase RSSChinaGUI.
"""

def start_classification(self):
    """Inicia el proceso de clasificación de noticias."""
    from pathlib import Path
    from tkinter import messagebox
    import os
    import threading
    
    if not hasattr(self, 'CLASIFICADOR_DISPONIBLE') or not self.CLASIFICADOR_DISPONIBLE:
        messagebox.showerror("Error", "El módulo de clasificación no está disponible.\\nInstala las dependencias: pip install langchain langchain-groq python-dotenv")
        return
    
    articles_path = Path(self.output_dir.get()) / "articles_full.jsonl"
    if not articles_path.exists():
        messagebox.showerror("Error", "No se encontraron artículos para clasificar.\\nEjecuta primero la extracción de texto completo.")
        return
    
    if self.is_running:
        messagebox.showwarning("Advertencia", "Ya hay un proceso en ejecución")
        return
    
    if not os.getenv("GROQ_API_KEY") and not os.getenv("GROQ_API_KEY_BACKUP"):
        messagebox.showerror("Error", "No se encontraron claves API de Groq.\\n\\nConfigura tus claves en el archivo .env")
        return
    
    self.is_running = True
    if hasattr(self, 'classify_button'):
        self.classify_button.config(state='disabled')
    self.status_label.config(text="● Clasificando...", fg='#8b5cf6')
    
    self.classification_stats = {'total': 0, 'classified': 0, 'failed': 0, 'temas': {}, 'imagenes': {}}
    thread = threading.Thread(target=self.run_classification, args=(str(articles_path),), daemon=True)
    thread.start()


def run_classification(self, input_file):
    """Ejecuta la clasificación en un thread separado."""
    import json
    import logging
    import csv
    from pathlib import Path
    from tkinter import messagebox
    from clasificador_langchain import clasificar_noticia_con_failover
    
    try:
        logger = logging.getLogger(__name__)
        logger.info("Iniciando clasificación de noticias...")
        
        articles = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    articles.append(json.loads(line))
        
        total = len(articles)
        self.classification_stats['total'] = total
        logger.info(f"Clasificando {total} artículos...")
        
        classified_results = []
        
        for i, article in enumerate(articles, 1):
            if not self.is_running:
                break
            
            try:
                datos = {
                    "medio": article.get('nombre_del_medio', 'Desconocido'),
                    "fecha": article.get('fecha', ''),
                    "titulo": article.get('titular', ''),
                    "descripcion": article.get('descripcion', ''),
                    "texto_completo": article.get('texto', article.get('descripcion', '')),
                    "enlace": article.get('enlace', '')
                }
                
                resultado = clasificar_noticia_con_failover(datos)
                resultado['nombre_del_medio'] = datos['medio']
                resultado['enlace'] = datos['enlace']
                classified_results.append(resultado)
                
                self.classification_stats['classified'] += 1
                tema = resultado.get('tema', 'Desconocido')
                imagen = resultado.get('imagen_de_china', 'Desconocido')
                self.classification_stats['temas'][tema] = self.classification_stats['temas'].get(tema, 0) + 1
                self.classification_stats['imagenes'][imagen] = self.classification_stats['imagenes'].get(imagen, 0) + 1
                logger.info(f"Clasificado {i}/{total}: {datos['titulo'][:50]}... -> {tema}")
                
            except Exception as e:
                logger.error(f"Error clasificando artículo {i}: {e}")
                self.classification_stats['failed'] += 1
        
        if classified_results:
            output_dir = Path(self.output_dir.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            jsonl_path = output_dir / "articles_classified.jsonl"
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for result in classified_results:
                    f.write(json.dumps(result, ensure_ascii=False) + '\\n')
            
            csv_path = output_dir / "articles_classified.csv"
            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                if classified_results:
                    fieldnames = list(classified_results[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for result in classified_results:
                        writer.writerow(result)
            
            logger.info(f"Guardados {len(classified_results)} artículos clasificados")
        
        logger.info("=== Clasificación completada ===")
        self.root.after(0, lambda: messagebox.showinfo("Éxito", f"Clasificación completada\\n{self.classification_stats['classified']} artículos clasificados\\n{self.classification_stats['failed']} fallos"))
        
    except Exception as e:
        logger.error(f"Error en clasificación: {e}", exc_info=True)
        self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    finally:
        self.is_running = False
        if hasattr(self, 'classify_button'):
            self.root.after(0, lambda: self.classify_button.config(state='normal'))
        self.root.after(0, lambda: self.status_label.config(text="● Listo", fg=self.colors['text_light']))


def load_classifications(self):
    """Carga las clasificaciones desde el archivo."""
    import csv
    import logging
    from pathlib import Path
    
    # Intentar cargar desde CSV primero
    classified_path = Path(self.output_dir.get()) / "articles_classified.csv"
    if not classified_path.exists():
        classified_path = Path("data") / "articles_classified.csv"
    
    # Si no existe CSV, intentar JSONL
    if not classified_path.exists():
        classified_path = Path(self.output_dir.get()) / "articles_classified.jsonl"
        if not classified_path.exists():
            classified_path = Path("data") / "articles_classified.jsonl"
    
    if not classified_path.exists():
        return
    
    try:
        self.classified_data = []
        
        # Cargar según la extensión del archivo
        if classified_path.suffix == '.csv':
            with open(classified_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.classified_data.append(row)
        else:  # JSONL
            import json
            with open(classified_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.classified_data.append(json.loads(line))
        
        self.classification_stats = {'total': len(self.classified_data), 'classified': len(self.classified_data), 'failed': 0, 'temas': {}, 'imagenes': {}}
        
        for item in self.classified_data:
            tema = item.get('tema', 'Desconocido')
            imagen = item.get('imagen_de_china', 'Desconocido')
            self.classification_stats['temas'][tema] = self.classification_stats['temas'].get(tema, 0) + 1
            self.classification_stats['imagenes'][imagen] = self.classification_stats['imagenes'].get(imagen, 0) + 1
        
        self.update_classification_stats()
        self.filter_classifications()
        
    except Exception as e:
        logging.error(f"Error cargando clasificaciones: {e}")


def filter_classifications(self, event=None):
    """Filtra y muestra las clasificaciones en la tabla."""
    for item in self.classifications_tree.get_children():
        self.classifications_tree.delete(item)
    
    search_term = self.classification_search_var.get().lower() if hasattr(self, 'classification_search_var') else ""
    filtered = []
    
    for item in self.classified_data:
        if search_term:
            if (search_term in item.get('titulo', '').lower() or search_term in item.get('medio', '').lower() or search_term in item.get('tema', '').lower() or search_term in item.get('imagen_de_china', '').lower()):
                filtered.append(item)
        else:
            filtered.append(item)
    
    for item in filtered:
        resumen = item.get('resumen_dos_frases', '')
        resumen_short = resumen[:100] + '...' if len(resumen) > 100 else resumen
        self.classifications_tree.insert('', 'end', values=(item.get('medio', ''), item.get('titulo', ''), item.get('tema', ''), item.get('imagen_de_china', ''), resumen_short))
    
    self.classifications_count_label.config(text=f"{len(filtered)} clasificaciones")


def update_classification_stats(self):
    """Actualiza las estadísticas de clasificación en la UI."""
    import tkinter as tk
    
    for key in ['total', 'classified', 'failed']:
        if key in self.classification_stats_labels:
            self.classification_stats_labels[key].config(text=str(self.classification_stats.get(key, 0)))
    
    temas_sorted = sorted(self.classification_stats['temas'].items(), key=lambda x: x[1], reverse=True)
    self.temas_text.config(state='normal')
    self.temas_text.delete('1.0', tk.END)
    for tema, count in temas_sorted[:5]:
        self.temas_text.insert(tk.END, f"{tema}: {count}\\n")
    self.temas_text.config(state='disabled')
    
    imagenes_sorted = sorted(self.classification_stats['imagenes'].items(), key=lambda x: x[1], reverse=True)
    self.imagen_text.config(state='normal')
    self.imagen_text.delete('1.0', tk.END)
    for imagen, count in imagenes_sorted[:5]:
        self.imagen_text.insert(tk.END, f"{imagen}: {count}\\n")
    self.imagen_text.config(state='disabled')


def export_classifications_json(self):
    """Exporta clasificaciones a JSON."""
    import json
    from tkinter import messagebox, filedialog
    
    if not self.classified_data:
        messagebox.showinfo("Info", "No hay clasificaciones para exportar")
        return
    
    filename = filedialog.asksaveasfilename(defaultextension=".jsonl", filetypes=[("JSONL files", "*.jsonl"), ("All files", "*.*")])
    
    if filename:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for item in self.classified_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\\n')
            messagebox.showinfo("Éxito", f"Exportado a {filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


def export_classifications_csv(self):
    """Exporta clasificaciones a CSV."""
    import csv
    from tkinter import messagebox, filedialog
    
    if not self.classified_data:
        messagebox.showinfo("Info", "No hay clasificaciones para exportar")
        return
    
    filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    
    if filename:
        try:
            with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                fieldnames = list(self.classified_data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in self.classified_data:
                    writer.writerow(item)
            messagebox.showinfo("Éxito", f"Exportado a {filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# Agregar estos métodos a la clase RSSChinaGUI
def add_classification_methods_to_gui(gui_class):
    """Agrega los métodos de clasificación a la clase GUI."""
    gui_class.start_classification = start_classification
    gui_class.run_classification = run_classification
    gui_class.load_classifications = load_classifications
    gui_class.filter_classifications = filter_classifications
    gui_class.update_classification_stats = update_classification_stats
    gui_class.export_classifications_json = export_classifications_json
    gui_class.export_classifications_csv = export_classifications_csv
    gui_class.CLASIFICADOR_DISPONIBLE = True
