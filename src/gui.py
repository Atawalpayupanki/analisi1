"""
GUI para RSS China News Filter usando tkinter.

Interfaz gráfica moderna para ejecutar el programa y visualizar resultados.
"""
import sys
import subprocess
try:
    from importlib.metadata import distributions
except ImportError:
    # Fallback para Python < 3.8
    from importlib_metadata import distributions

# Verificar dependencias críticas antes de importar nada más
required = {'trafilatura', 'beautifulsoup4', 'requests', 'tenacity'}
installed = {dist.metadata['Name'].lower().replace('-', '_') for dist in distributions()}
# Normalizar nombres (beautifulsoup4 puede aparecer como beautifulsoup4)
installed.update({dist.metadata['Name'].lower() for dist in distributions()})
missing = required - installed

if missing:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error de Dependencias", 
        f"Faltan librerías necesarias:\n{', '.join(missing)}\n\n"
        "Por favor, ejecuta:\npip install -r requirements.txt")
    sys.exit(1)

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import logging
import os
import json
import csv
import webbrowser
from pathlib import Path
from queue import Queue
import asyncio
from typing import Optional, List, Dict, Any

# Importar módulos del proyecto
from feeds_list import load_feeds
from downloader import download_feeds_async, download_feeds_sync
from parser import parse_feed, NewsItem
from filtro_china import load_keywords, filter_china_news
from deduplicador import deduplicate
from almacenamiento import save_results
from article_processor import process_articles


class TextHandler(logging.Handler):
    """Handler personalizado para redirigir logs a un widget de texto."""
    
    def __init__(self, text_widget, queue):
        super().__init__()
        self.text_widget = text_widget
        self.queue = queue
    
    def emit(self, record):
        msg = self.format(record)
        self.queue.put(msg)


class RSSChinaGUI:
    """Interfaz gráfica para RSS China News Filter."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🇨🇳 RSS China News Filter v2.0")
        self.root.geometry("1280x850")
        
        # Colores modernos
        self.colors = {
            'bg': '#f0f4f8',
            'primary': '#2563eb',
            'primary_dark': '#1e40af',
            'secondary': '#6366f1',
            'secondary_dark': '#4f46e5',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'text': '#1f2937',
            'text_light': '#6b7280',
            'card_bg': '#ffffff',
            'border': '#e5e7eb'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Variables
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.log_queue = Queue()
        self.results_data: List[NewsItem] = []
        self.full_articles_data: List[Dict] = []
        self.failed_feeds: List[tuple] = []
        
        # Variables de configuración
        self.config_file = tk.StringVar(value="config/feeds.json")
        self.keywords_file = tk.StringVar(value="config/keywords.json")
        self.output_dir = tk.StringVar(value="data")
        self.use_async = tk.BooleanVar(value=False)
        self.log_level = tk.StringVar(value="INFO")
        self.search_var = tk.StringVar()
        self.article_search_var = tk.StringVar()
        
        # Estadísticas
        self.stats = {
            'feeds_total': 0,
            'feeds_ok': 0,
            'feeds_error': 0,
            'items_total': 0,
            'items_china': 0,
            'items_unique': 0
        }
        
        self.setup_styles()
        self.setup_ui()
        self.setup_logging()
        self.check_log_queue()
    
    def setup_styles(self):
        """Configura estilos personalizados."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame con bordes redondeados (simulado con relief)
        style.configure('Card.TFrame', 
                       background=self.colors['card_bg'],
                       relief='flat',
                       borderwidth=0)
        
        style.configure('TLabel', 
                       background=self.colors['card_bg'],
                       foreground=self.colors['text'])
        
        style.configure('Title.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['primary'],
                       font=('Segoe UI', 11, 'bold'))
        
        # Botones con estilo moderno
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10),
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_dark'])])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=0,
                       padding=(15, 8),
                       font=('Segoe UI', 9))
        
        style.configure('TEntry',
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid')
        
        style.configure('TCheckbutton',
                       background=self.colors['card_bg'])
        
        # Treeview moderno
        style.configure('Treeview',
                       background='white',
                       foreground=self.colors['text'],
                       fieldbackground='white',
                       borderwidth=0,
                       font=('Segoe UI', 9))
        
        style.configure('Treeview.Heading',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       font=('Segoe UI', 10, 'bold'))
        
        style.map('Treeview.Heading',
                 background=[('active', self.colors['primary_dark'])])
                 
        # Notebook (Pestañas)
        style.configure('TNotebook', background=self.colors['bg'])
        style.configure('TNotebook.Tab', 
                       padding=[15, 5], 
                       font=('Segoe UI', 10),
                       background='#e0e0e0')
        style.map('TNotebook.Tab', 
                 background=[('selected', self.colors['card_bg'])],
                 foreground=[('selected', self.colors['primary'])])

    def setup_ui(self):
        """Configura la interfaz de usuario con pestañas."""
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título superior
        title_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(title_frame, 
                text="🇨🇳 RSS China News Filter",
                font=('Segoe UI', 18, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['primary']).pack(side=tk.LEFT)
                
        self.status_label = tk.Label(title_frame, text="● Listo",
                                     font=('Segoe UI', 10, 'bold'),
                                     bg=self.colors['bg'],
                                     fg=self.colors['text_light'])
        self.status_label.pack(side=tk.RIGHT)

        # Notebook principal
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Crear pestañas
        self.tab_control = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_logs = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_results = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_articles = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.tab_reports = tk.Frame(self.notebook, bg=self.colors['bg'])
        
        self.notebook.add(self.tab_control, text='🎛️ Control')
        self.notebook.add(self.tab_logs, text='📋 Logs')
        self.notebook.add(self.tab_results, text='📰 Resultados RSS')
        self.notebook.add(self.tab_articles, text='📄 Artículos Completos')
        self.notebook.add(self.tab_reports, text='📊 Reportes')
        
        # Configurar contenido de cada pestaña
        self.setup_control_tab()
        self.setup_logs_tab()
        self.setup_results_tab()
        self.setup_full_articles_tab()
        self.setup_reports_tab()
        
        # Bind para cargar datos al cambiar de pestaña
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

    def setup_control_tab(self):
        """Configura la pestaña de Control."""
        # Dividir en dos columnas
        left_panel = tk.Frame(self.tab_control, bg=self.colors['bg'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        right_panel = tk.Frame(self.tab_control, bg=self.colors['bg'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === CONFIGURACIÓN (Izquierda) ===
        config_card = tk.LabelFrame(left_panel, text="Configuración", bg=self.colors['card_bg'],
                                   font=('Segoe UI', 11, 'bold'), fg=self.colors['text'],
                                   padx=15, pady=15, relief='flat')
        config_card.pack(fill=tk.X, pady=(0, 15))
        
        # Grid para inputs
        tk.Label(config_card, text="Feeds:", bg=self.colors['card_bg']).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_card, textvariable=self.config_file).grid(row=0, column=1, sticky='ew', padx=5)
        ttk.Button(config_card, text="📂", width=3, 
                  command=lambda: self.browse_file(self.config_file)).grid(row=0, column=2)
        
        tk.Label(config_card, text="Keywords:", bg=self.colors['card_bg']).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_card, textvariable=self.keywords_file).grid(row=1, column=1, sticky='ew', padx=5)
        ttk.Button(config_card, text="📂", width=3,
                  command=lambda: self.browse_file(self.keywords_file)).grid(row=1, column=2)
        
        tk.Label(config_card, text="Salida:", bg=self.colors['card_bg']).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_card, textvariable=self.output_dir).grid(row=2, column=1, sticky='ew', padx=5)
        ttk.Button(config_card, text="📂", width=3,
                  command=lambda: self.browse_directory(self.output_dir)).grid(row=2, column=2)
        
        config_card.columnconfigure(1, weight=1)
        
        # Opciones extra
        opts_frame = tk.Frame(config_card, bg=self.colors['card_bg'])
        opts_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=(10, 0))
        ttk.Checkbutton(opts_frame, text="Modo Asíncrono", variable=self.use_async).pack(side=tk.LEFT)
        
        # === ACCIONES (Izquierda) ===
        actions_card = tk.LabelFrame(left_panel, text="Acciones", bg=self.colors['card_bg'],
                                    font=('Segoe UI', 11, 'bold'), fg=self.colors['text'],
                                    padx=15, pady=15, relief='flat')
        actions_card.pack(fill=tk.X)
        
        self.start_button = tk.Button(actions_card, text="▶ INICIAR PROCESO", 
                                      command=self.start_process,
                                      bg=self.colors['success'], fg='white',
                                      font=('Segoe UI', 10, 'bold'), relief='flat',
                                      padx=20, pady=10, cursor='hand2')
        self.start_button.pack(fill=tk.X, pady=5)
        
        self.stop_button = tk.Button(actions_card, text="⬛ DETENER",
                                     command=self.stop_process,
                                     bg=self.colors['error'], fg='white',
                                     font=('Segoe UI', 10, 'bold'), relief='flat',
                                     padx=20, pady=10, cursor='hand2', state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X, pady=5)
        
        ttk.Separator(actions_card, orient='horizontal').pack(fill='x', pady=10)
        
        self.extract_button = tk.Button(actions_card, text="📝 EXTRAER TEXTO COMPLETO",
                                      command=self.start_extraction,
                                      bg=self.colors['secondary'], fg='white',
                                      font=('Segoe UI', 10, 'bold'), relief='flat',
                                      padx=20, pady=10, cursor='hand2')
        self.extract_button.pack(fill=tk.X, pady=5)

        # === ESTADÍSTICAS (Derecha) ===
        stats_card = tk.LabelFrame(right_panel, text="Estadísticas en Vivo", bg=self.colors['card_bg'],
                                  font=('Segoe UI', 11, 'bold'), fg=self.colors['text'],
                                  padx=15, pady=15, relief='flat')
        stats_card.pack(fill=tk.X, pady=(0, 15))
        
        self.stats_labels = {}
        stats_info = [
            ("feeds_total", "📡 Feeds Total", self.colors['primary']),
            ("feeds_ok", "✅ Feeds OK", self.colors['success']),
            ("feeds_error", "❌ Feeds Error", self.colors['error']),
            ("items_total", "📥 Ítems Total", self.colors['text']),
            ("items_china", "🇨🇳 Ítems China", self.colors['warning']),
            ("items_unique", "⭐ Ítems Únicos", self.colors['success'])
        ]
        
        for i, (key, label, color) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2
            
            lbl = tk.Label(stats_card, text=label, bg=self.colors['card_bg'], fg=self.colors['text_light'])
            lbl.grid(row=row, column=col, sticky='w', padx=(0, 10), pady=5)
            
            val = tk.Label(stats_card, text="0", bg=self.colors['card_bg'], fg=color,
                          font=('Segoe UI', 14, 'bold'))
            val.grid(row=row, column=col+1, sticky='w', padx=(0, 20), pady=5)
            self.stats_labels[key] = val
            
            if key == "feeds_error":
                lbl.bind('<Button-1>', lambda e: self.show_failed_feeds())
                lbl.config(cursor='hand2')

        # === LOG PREVIEW (Derecha) ===
        log_card = tk.LabelFrame(right_panel, text="Vista Previa de Logs", bg=self.colors['card_bg'],
                                font=('Segoe UI', 11, 'bold'), fg=self.colors['text'],
                                padx=10, pady=10, relief='flat')
        log_card.pack(fill=tk.BOTH, expand=True)
        
        self.log_preview = scrolledtext.ScrolledText(log_card, height=10, font=("Consolas", 9),
                                                    bg='#1e1e1e', fg='#d4d4d4', relief='flat')
        self.log_preview.pack(fill=tk.BOTH, expand=True)

    def setup_logs_tab(self):
        """Configura la pestaña de Logs."""
        toolbar = tk.Frame(self.tab_logs, bg=self.colors['bg'], pady=5)
        toolbar.pack(fill=tk.X)
        
        tk.Label(toolbar, text="Nivel:", bg=self.colors['bg']).pack(side=tk.LEFT, padx=5)
        ttk.Combobox(toolbar, textvariable=self.log_level, 
                    values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                    state="readonly", width=10).pack(side=tk.LEFT, padx=5)
                    
        tk.Button(toolbar, text="Limpiar", command=self.clear_logs,
                 bg='white', relief='solid', borderwidth=1).pack(side=tk.LEFT, padx=10)
                 
        self.full_log_text = scrolledtext.ScrolledText(self.tab_logs, font=("Consolas", 10),
                                                      bg='#1e1e1e', fg='#d4d4d4',
                                                      insertbackground='white')
        self.full_log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_results_tab(self):
        """Configura la pestaña de Resultados RSS."""
        # Toolbar
        toolbar = tk.Frame(self.tab_results, bg=self.colors['bg'], pady=10)
        toolbar.pack(fill=tk.X, padx=10)
        
        tk.Button(toolbar, text="🔄 Recargar", command=self.load_results,
                 bg=self.colors['primary'], fg='white', relief='flat', padx=10).pack(side=tk.LEFT, padx=5)
                 
        tk.Button(toolbar, text="📂 Abrir JSONL", command=self.open_jsonl,
                 bg='white', relief='solid', borderwidth=1, padx=10).pack(side=tk.LEFT, padx=5)
                 
        tk.Button(toolbar, text="📊 Abrir CSV", command=self.open_csv,
                 bg='white', relief='solid', borderwidth=1, padx=10).pack(side=tk.LEFT, padx=5)
        
        # Búsqueda
        tk.Label(toolbar, text="Buscar:", bg=self.colors['bg']).pack(side=tk.LEFT, padx=(20, 5))
        entry_search = ttk.Entry(toolbar, textvariable=self.search_var)
        entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        entry_search.bind('<KeyRelease>', self.filter_results)
        
        self.results_count_label = tk.Label(toolbar, text="0 resultados", bg=self.colors['bg'])
        self.results_count_label.pack(side=tk.RIGHT, padx=10)
        
        # Tabla
        columns = ('medio', 'titular', 'fecha', 'enlace')
        self.results_tree = ttk.Treeview(self.tab_results, columns=columns, show='headings')
        
        self.results_tree.heading('medio', text='Medio')
        self.results_tree.heading('titular', text='Titular')
        self.results_tree.heading('fecha', text='Fecha')
        self.results_tree.heading('enlace', text='Enlace')
        
        self.results_tree.column('medio', width=150)
        self.results_tree.column('titular', width=500)
        self.results_tree.column('fecha', width=150)
        self.results_tree.column('enlace', width=300)
        
        # Scrollbars
        sb_y = ttk.Scrollbar(self.tab_results, orient=tk.VERTICAL, command=self.results_tree.yview)
        sb_x = ttk.Scrollbar(self.tab_results, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscroll=sb_y.set, xscroll=sb_x.set)
        
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.results_tree.pack(fill=tk.BOTH, expand=True, padx=10)
        
        self.results_tree.bind('<Double-1>', self.on_result_double_click)

    def setup_full_articles_tab(self):
        """Configura la pestaña de Artículos Completos."""
        # Split container
        paned = tk.PanedWindow(self.tab_articles, orient=tk.HORIZONTAL, bg=self.colors['bg'], sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel Izquierdo: Lista
        left_frame = tk.Frame(paned, bg='white')
        paned.add(left_frame, width=400)
        
        # Toolbar búsqueda
        search_frame = tk.Frame(left_frame, bg='white', pady=5)
        search_frame.pack(fill=tk.X, padx=5)
        tk.Label(search_frame, text="Buscar:", bg='white').pack(side=tk.LEFT, padx=5)
        ttk.Entry(search_frame, textvariable=self.article_search_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Lista de artículos
        self.articles_list = ttk.Treeview(left_frame, columns=('titular',), show='tree headings', selectmode='browse')
        self.articles_list.heading('#0', text='#')
        self.articles_list.heading('titular', text='Titular')
        self.articles_list.column('#0', width=50)
        self.articles_list.column('titular', width=350)
        
        sb = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.articles_list.yview)
        self.articles_list.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.articles_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.articles_list.bind('<<TreeviewSelect>>', self.on_article_select)
        
        # Panel Derecho: Contenido
        right_frame = tk.Frame(paned, bg='white')
        paned.add(right_frame)
        
        # Header del artículo
        header_frame = tk.Frame(right_frame, bg='white', pady=10, padx=10)
        header_frame.pack(fill=tk.X)
        
        self.article_header = tk.Label(header_frame, text="Selecciona un artículo", 
                                       font=('Segoe UI', 14, 'bold'), bg='white', 
                                       wraplength=600, justify=tk.LEFT)
        self.article_header.pack(anchor='w')
        
        self.article_meta = tk.Label(header_frame, text="", 
                                     font=('Segoe UI', 9), bg='white', 
                                     fg=self.colors['text_light'])
        self.article_meta.pack(anchor='w', pady=(5, 0))
        
        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', padx=10)
        
        # Contenido del artículo
        self.article_content = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, 
                                                         font=('Segoe UI', 10), 
                                                         padx=15, pady=15)
        self.article_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def on_article_select(self, event):
        """Maneja la selección de un artículo."""
        selection = self.articles_list.selection()
        if not selection: return
        
        idx = int(self.articles_list.item(selection[0])['text'])
        if idx >= len(self.full_articles_data): return
        
        data = self.full_articles_data[idx]
        
        self.article_header.config(text=data.get('titular', ''))
        self.article_meta.config(text=f"{data.get('nombre_del_medio')} | {data.get('fecha')}")
        
        self.article_content.delete('1.0', tk.END)
        self.article_content.insert('1.0', data.get('texto') or data.get('descripcion', ''))
    
    def setup_reports_tab(self):
        """Configura la pestaña de Reportes."""
        # Estadísticas de extracción
        stats_card = tk.LabelFrame(self.tab_reports, text="Estadísticas de Extracción", 
                                  bg=self.colors['card_bg'], font=('Segoe UI', 11, 'bold'),
                                  padx=15, pady=15)
        stats_card.pack(fill=tk.X, padx=10, pady=10)
        
        self.report_labels = {}
        report_stats = [
            ('total_articles', '📊 Total Artículos'),
            ('successful', '✅ Exitosos'),
            ('failed_download', '❌ Fallos Descarga'),
            ('failed_extraction', '⚠️ Fallos Extracción'),
            ('no_content', '📭 Sin Contenido'),
            ('blocked', '🚫 Bloqueados')
        ]
        
        for i, (key, label) in enumerate(report_stats):
            row = i // 3
            col = (i % 3) * 2
            
            tk.Label(stats_card, text=label, bg=self.colors['card_bg']).grid(
                row=row, column=col, sticky='w', padx=(0, 10), pady=5)
            
            val = tk.Label(stats_card, text="0", bg=self.colors['card_bg'], 
                          font=('Segoe UI', 12, 'bold'))
            val.grid(row=row, column=col+1, sticky='w', padx=(0, 20), pady=5)
            self.report_labels[key] = val
        
        # Tabla de errores
        errors_card = tk.LabelFrame(self.tab_reports, text="Errores de Extracción",
                                   bg=self.colors['card_bg'], font=('Segoe UI', 11, 'bold'),
                                   padx=10, pady=10)
        errors_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('url', 'error', 'timestamp')
        self.errors_tree = ttk.Treeview(errors_card, columns=columns, show='headings', height=10)
        
        self.errors_tree.heading('url', text='URL')
        self.errors_tree.heading('error', text='Error')
        self.errors_tree.heading('timestamp', text='Timestamp')
        
        self.errors_tree.column('url', width=400)
        self.errors_tree.column('error', width=300)
        self.errors_tree.column('timestamp', width=150)
        
        sb = ttk.Scrollbar(errors_card, orient=tk.VERTICAL, command=self.errors_tree.yview)
        self.errors_tree.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.errors_tree.pack(fill=tk.BOTH, expand=True)
    
    def setup_logging(self):
        """Configura el sistema de logging."""
        # Handler para el widget de texto
        text_handler = TextHandler(self.log_preview, self.log_queue)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Configurar root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(text_handler)
    
    def check_log_queue(self):
        """Revisa la cola de logs y actualiza los widgets."""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                # Agregar a preview
                self.log_preview.insert(tk.END, msg + '\n')
                self.log_preview.see(tk.END)
                # Agregar a log completo
                self.full_log_text.insert(tk.END, msg + '\n')
                self.full_log_text.see(tk.END)
        except:
            pass
        
        # Programar siguiente revisión
        self.root.after(100, self.check_log_queue)
    
    def start_process(self):
        """Inicia el proceso de descarga y filtrado."""
        if self.is_running:
            messagebox.showwarning("Advertencia", "Ya hay un proceso en ejecución")
            return
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="● Ejecutando...", fg=self.colors['success'])
        
        # Resetear estadísticas
        for key in self.stats:
            self.stats[key] = 0
            if key in self.stats_labels:
                self.stats_labels[key].config(text="0")
        
        # Limpiar datos previos
        self.failed_feeds = []
        
        # Ejecutar en thread separado
        self.worker_thread = threading.Thread(target=self.run_process, daemon=True)
        self.worker_thread.start()
    
    def stop_process(self):
        """Detiene el proceso en ejecución."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="● Detenido", fg=self.colors['error'])
        logging.info("Proceso detenido por el usuario")
    
    def run_process(self):
        """Ejecuta el proceso principal en un thread separado."""
        try:
            logger = logging.getLogger(__name__)
            logger.info("=== Iniciando proceso ===")
            
            # 1. Cargar feeds
            feeds = load_feeds(self.config_file.get())
            self.stats['feeds_total'] = len(feeds)
            self.update_stats()
            
            # 2. Cargar keywords
            keywords = load_keywords(self.keywords_file.get())
            
            # 3. Descargar feeds
            if self.use_async.get():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                download_results = loop.run_until_complete(download_feeds_async(feeds))
                loop.close()
            else:
                download_results = download_feeds_sync(feeds)
            
            # 4. Parsear
            all_items = []
            for url, nombre, content in download_results:
                if not self.is_running:
                    break
                if content:
                    items = parse_feed(content, url, nombre)
                    all_items.extend(items)
                    self.stats['feeds_ok'] += 1
                else:
                    self.stats['feeds_error'] += 1
                    self.failed_feeds.append((nombre, url, "Sin contenido"))
                self.update_stats()
            
            self.stats['items_total'] = len(all_items)
            self.update_stats()
            
            # 5. Filtrar
            china_items = filter_china_news(all_items, keywords)
            self.stats['items_china'] = len(china_items)
            self.update_stats()
            
            # 6. Deduplicar
            unique_items = deduplicate(china_items)
            self.stats['items_unique'] = len(unique_items)
            self.update_stats()
            
            # 7. Guardar
            if unique_items:
                save_results(unique_items, self.output_dir.get())
                logger.info(f"Guardados {len(unique_items)} resultados")
            
            logger.info("=== Proceso completado ===")
            self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                f"Proceso completado\n{self.stats['items_unique']} noticias guardadas"))
            
        except Exception as e:
            logger.error(f"Error en proceso: {e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_label.config(text="● Listo", 
                                                                fg=self.colors['text_light']))
    
    def update_stats(self):
        """Actualiza las etiquetas de estadísticas."""
        for key, value in self.stats.items():
            if key in self.stats_labels:
                self.root.after(0, lambda k=key, v=value: self.stats_labels[k].config(text=str(v)))
    
    def start_extraction(self):
        """Inicia la extracción de texto completo."""
        input_file = Path(self.output_dir.get()) / "output.jsonl"
        if not input_file.exists():
            messagebox.showerror("Error", "No se encontró output.jsonl. Ejecuta primero el proceso principal.")
            return
        
        if self.is_running:
            messagebox.showwarning("Advertencia", "Ya hay un proceso en ejecución")
            return
        
        self.is_running = True
        self.extract_button.config(state=tk.DISABLED)
        self.status_label.config(text="● Extrayendo...", fg=self.colors['secondary'])
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=self.run_extraction, args=(str(input_file),), daemon=True)
        thread.start()
    
    def run_extraction(self, input_file):
        """Ejecuta la extracción en un thread separado."""
        try:
            logger = logging.getLogger(__name__)
            logger.info("Iniciando extracción de texto completo...")
            
            report = process_articles(input_file)
            
            logger.info(f"Extracción completada: {report.successful} exitosos, {report.failed_download + report.failed_extraction} fallos")
            self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                f"Extracción completada\n{report.successful} artículos procesados"))
            
        except Exception as e:
            logger.error(f"Error en extracción: {e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.extract_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_label.config(text="● Listo", 
                                                                fg=self.colors['text_light']))
    
    def load_results(self):
        """Carga los resultados desde el archivo JSONL."""
        jsonl_path = Path(self.output_dir.get()) / "output.jsonl"
        if not jsonl_path.exists():
            return
        
        try:
            self.results_data = []
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.results_data.append(json.loads(line))
            
            self.filter_results()
        except Exception as e:
            logging.error(f"Error cargando resultados: {e}")
    
    def filter_results(self, event=None):
        """Filtra y muestra los resultados en la tabla."""
        # Limpiar tabla
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        search_term = self.search_var.get().lower()
        filtered = []
        
        for item in self.results_data:
            if search_term:
                if (search_term in item.get('titular', '').lower() or
                    search_term in item.get('nombre_del_medio', '').lower()):
                    filtered.append(item)
            else:
                filtered.append(item)
        
        # Insertar en tabla
        for item in filtered:
            self.results_tree.insert('', 'end', values=(
                item.get('nombre_del_medio', ''),
                item.get('titular', ''),
                item.get('fecha', ''),
                item.get('enlace', '')
            ))
        
        self.results_count_label.config(text=f"{len(filtered)} resultados")
    
    def load_full_articles(self):
        """Carga los artículos completos desde el archivo JSONL."""
        articles_path = Path(self.output_dir.get()) / "articles_full.jsonl"
        if not articles_path.exists():
            articles_path = Path("data") / "articles_full.jsonl"
        
        if not articles_path.exists():
            return
        
        try:
            self.full_articles_data = []
            with open(articles_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.full_articles_data.append(json.loads(line))
            
            # Limpiar lista
            for item in self.articles_list.get_children():
                self.articles_list.delete(item)
            
            # Insertar artículos
            for i, article in enumerate(self.full_articles_data):
                self.articles_list.insert('', 'end', text=str(i), 
                                         values=(article.get('titular', ''),))
        except Exception as e:
            logging.error(f"Error cargando artículos: {e}")

    def load_reports(self):
        """Carga reportes y errores."""
        # Cargar extraction_report.json
        try:
            report_path = Path("extraction_report.json")
            if report_path.exists():
                with open(report_path, 'r') as f:
                    data = json.load(f)
                    for key, label in self.report_labels.items():
                        label.config(text=str(data.get(key, 0)))
        except Exception: pass
        
        # Cargar errores
        try:
            error_path = Path("failed_extractions.jsonl")
            if error_path.exists():
                for item in self.errors_tree.get_children():
                    self.errors_tree.delete(item)
                with open(error_path, 'r') as f:
                    for line in f:
                        data = json.loads(line)
                        self.errors_tree.insert('', 'end', values=(
                            data.get('url', ''),
                            data.get('error', ''),
                            data.get('timestamp', '')
                        ))
        except Exception: pass

    def on_tab_changed(self, event):
        """Maneja el cambio de pestañas."""
        tab_name = self.notebook.tab(self.notebook.select(), "text")
        if "Resultados" in tab_name:
            self.load_results()
        elif "Artículos" in tab_name:
            self.load_full_articles()
        elif "Reportes" in tab_name:
            self.load_reports()

    def browse_file(self, var):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if filename: var.set(filename)

    def browse_directory(self, var):
        directory = filedialog.askdirectory()
        if directory: var.set(directory)

    def clear_logs(self):
        self.full_log_text.delete('1.0', tk.END)

    def open_jsonl(self):
        self.open_file(Path(self.output_dir.get()) / "output.jsonl")

    def open_csv(self):
        self.open_file(Path(self.output_dir.get()) / "output.csv")

    def open_file(self, filepath):
        if not filepath.exists(): return
        try:
            if sys.platform == "win32": os.startfile(filepath)
            elif sys.platform == "darwin": subprocess.run(["open", filepath])
            else: subprocess.run(["xdg-open", filepath])
        except Exception as e: messagebox.showerror("Error", str(e))

    def on_result_double_click(self, event):
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            url = item['values'][3]
            if url: webbrowser.open(url)

    def show_failed_feeds(self):
        if not self.failed_feeds:
            messagebox.showinfo("Info", "No hay feeds fallidos recientes")
            return
        
        top = tk.Toplevel(self.root)
        top.title("Feeds Fallidos")
        top.geometry("600x400")
        
        text = scrolledtext.ScrolledText(top, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        
        for name, url, reason in self.failed_feeds:
            text.insert(tk.END, f"Nombre: {name}\nURL: {url}\nError: {reason}\n{'-'*40}\n")


def main():
    root = tk.Tk()
    app = RSSChinaGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
