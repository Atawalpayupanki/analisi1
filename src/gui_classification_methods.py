"""
Métodos de clasificación para la GUI.
Este archivo contiene los métodos que se agregarán a la clase RSSChinaGUI.

Ahora usa el CSV maestro centralizado para leer artículos pendientes
y actualizar su estado tras la clasificación.
"""

def start_classification(self):
    """Inicia el proceso de clasificación de noticias."""
    from pathlib import Path
    from tkinter import messagebox
    import os
    import threading
    from noticias_db import obtener_db
    
    if not hasattr(self, 'CLASIFICADOR_DISPONIBLE') or not self.CLASIFICADOR_DISPONIBLE:
        messagebox.showerror("Error", "El módulo de clasificación no está disponible.\nInstala las dependencias: pip install langchain langchain-groq python-dotenv")
        return
    
    # Verificar que existe el CSV maestro
    csv_path = Path(self.output_dir.get()) / "noticias_china.csv"
    if not csv_path.exists():
        messagebox.showerror("Error", "No se encontró el CSV maestro.\nEjecuta primero el proceso RSS para crear la base de datos.")
        return
    
    # Verificar artículos pendientes
    db = obtener_db(str(csv_path))
    pendientes = db.obtener_por_estado('extraido') + db.obtener_por_estado('por_clasificar') + db.obtener_por_estado('error')
    
    if not pendientes:
        messagebox.showinfo("Info", "No hay artículos pendientes de clasificar.\n\nEstados actuales:\n" + 
                           "\n".join([f"- {k}: {v}" for k, v in db.contar_por_estado().items()]))
        return
    
    if self.is_running:
        messagebox.showwarning("Advertencia", "Ya hay un proceso en ejecución")
        return
    
    if not os.getenv("GROQ_API_KEY") and not os.getenv("GROQ_API_KEY_BACKUP"):
        messagebox.showerror("Error", "No se encontraron claves API de Groq.\n\nConfigura tus claves en el archivo .env")
        return
    
    self.is_running = True
    if hasattr(self, 'classify_button'):
        self.classify_button.config(state='disabled')
    
    # Enable Stop button
    if hasattr(self, 'stop_button'):
        self.stop_button.config(state='normal')
        
    self.status_label.config(text="● Clasificando...", fg='#8b5cf6')
    
    self.classification_stats = {'total': len(pendientes), 'classified': 0, 'failed': 0, 'temas': {}, 'imagenes': {}}
    thread = threading.Thread(target=self.run_classification, args=(str(csv_path),), daemon=True)
    thread.start()


def run_classification(self, csv_path):
    """Ejecuta la clasificación en un thread separado."""
    import logging
    from tkinter import messagebox
    from clasificador_langchain import clasificar_noticia_con_failover
    from noticias_db import obtener_db
    from activity_logger import (
        log_classification_success, log_classification_failed,
        log_process_started, log_process_completed, log_error
    )
    
    try:
        logger = logging.getLogger(__name__)
        logger.info("Iniciando clasificación de noticias...")
        log_process_started("Clasificación LLM")
        
        # Obtener artículos pendientes del CSV maestro
        db = obtener_db(csv_path)
        articles = db.obtener_por_estado('extraido') + db.obtener_por_estado('por_clasificar') + db.obtener_por_estado('error')
        
        total = len(articles)
        self.classification_stats['total'] = total
        logger.info(f"Clasificando {total} artículos pendientes...")
        
        classified_count = 0
        
        for i, article in enumerate(articles, 1):
            if not self.is_running:
                break
            
            url = article.get('url', '')
            if not url:
                continue
            
            try:
                datos = {
                    "medio": article.get('medio', 'Desconocido'),
                    "procedencia": article.get('procedencia', 'Occidental'),
                    "idioma": article.get('idioma', 'es'),
                    "fecha": article.get('fecha', ''),
                    "titulo": article.get('titular', ''),
                    "descripcion": article.get('descripcion', ''),
                    "texto_completo": article.get('texto_completo', article.get('descripcion', '')),
                    "enlace": url
                }
                
                resultado = clasificar_noticia_con_failover(datos)
                
                tema_detectado = resultado.get('tema', '')
                
                if tema_detectado == 'Noticia no extraida correctamente':
                     # Marcar como 'nuevo' para reintentar extracción (limpiando texto)
                    db.actualizar_articulo(url, {
                        'texto_completo': '',
                        'tema': '',
                        'imagen_de_china': '',
                        'resumen': '',
                        'estado': 'nuevo',
                        'error_msg': 'Reiniciado por mala extracción detectada en clasificación'
                    })
                    logger.warning(f"Artículo reiniciado por mala extracción: {datos['titulo'][:50]}...")
                    self.classification_stats['failed'] += 1
                
                elif tema_detectado == 'Deportes':
                    # Eliminar noticia de deportes
                    db.eliminar_articulo(url)
                    logger.info(f"Artículo de deportes eliminado: {datos['titulo'][:50]}...")
                    # No contamos como clasificado ni fallido, simplemente desaparece
                    # Ajustamos el total para que no parezca que falta uno al final
                    self.classification_stats['total'] -= 1
                    
                else:
                    # Actualizar en la DB como clasificado exitoso
                    db.actualizar_articulo(url, {
                        'tema': tema_detectado,
                        'imagen_de_china': resultado.get('imagen_de_china', ''),
                        'resumen': resultado.get('resumen_dos_frases', ''),
                        'estado': 'clasificado'
                    })
                    
                    classified_count += 1
                    self.classification_stats['classified'] += 1
                    
                    self.classification_stats['temas'][tema_detectado] = self.classification_stats['temas'].get(tema_detectado, 0) + 1
                    imagen = resultado.get('imagen_de_china', 'Desconocido')
                    self.classification_stats['imagenes'][imagen] = self.classification_stats['imagenes'].get(imagen, 0) + 1
                    
                    logger.info(f"Clasificado {i}/{total}: {datos['titulo'][:50]}... -> {tema_detectado}")
                    log_classification_success(datos['titulo'], tema_detectado, imagen)
                
            except Exception as e:
                logger.error(f"Error clasificando artículo {i}: {e}")
                self.classification_stats['failed'] += 1
                log_classification_failed(datos.get('titulo', 'Sin título'), str(e))
                # Marcar como error
                db.actualizar_estado(url, 'error', str(e))
                
            # Guardar periódicamente (cada 10 artículos)
            if i % 10 == 0:
                db.guardar()
                logger.info(f"Guardado parcial (progreso: {i}/{total})")
        
        # Guardar todos los cambios
        db.guardar()
        
        log_process_completed("Clasificación LLM", self.classification_stats)
        
        logger.info("=== Clasificación completada ===")
        self.root.after(0, lambda: messagebox.showinfo("Éxito", 
            f"Clasificación completada\n{self.classification_stats['classified']} artículos clasificados\n{self.classification_stats['failed']} fallos"))
        
    except Exception as e:
        import traceback
        logger.error(f"Error en clasificación: {e}", exc_info=True)
        log_error("Error en clasificación LLM", str(e))
        self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    finally:
        self.is_running = False
        if hasattr(self, 'classify_button'):
            self.root.after(0, lambda: self.classify_button.config(state='normal'))
        if hasattr(self, 'stop_button'):
            self.root.after(0, lambda: self.stop_button.config(state='disabled'))
        self.root.after(0, lambda: self.status_label.config(text="● Listo", fg=self.colors['text_light']))


def load_classifications(self):
    """Carga las clasificaciones desde el CSV maestro."""
    import logging
    from pathlib import Path
    from noticias_db import obtener_db
    
    csv_path = Path(self.output_dir.get()) / "noticias_china.csv"
    if not csv_path.exists():
        return
    
    try:
        db = obtener_db(str(csv_path))
        
        # Cargar todos los clasificados
        self.classified_data = db.obtener_por_estado('clasificado')
        
        self.classification_stats = {
            'total': db.total(),
            'classified': len(self.classified_data),
            'failed': len(db.obtener_por_estado('error')),
            'temas': {},
            'imagenes': {}
        }
        
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
            if (search_term in item.get('titular', '').lower() or 
                search_term in item.get('medio', '').lower() or 
                search_term in item.get('tema', '').lower() or 
                search_term in item.get('imagen_de_china', '').lower()):
                filtered.append(item)
        else:
            filtered.append(item)
    
    for item in filtered:
        self.classifications_tree.insert('', 'end', values=(
            item.get('medio', ''), 
            item.get('titular', ''), 
            item.get('tema', ''), 
            item.get('imagen_de_china', '')
        ))
    
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
        self.temas_text.insert(tk.END, f"{tema}: {count}\n")
    self.temas_text.config(state='disabled')
    
    imagenes_sorted = sorted(self.classification_stats['imagenes'].items(), key=lambda x: x[1], reverse=True)
    self.imagen_text.config(state='normal')
    self.imagen_text.delete('1.0', tk.END)
    for imagen, count in imagenes_sorted[:5]:
        self.imagen_text.insert(tk.END, f"{imagen}: {count}\n")
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
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
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
