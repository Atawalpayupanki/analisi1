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
from pathlib import Path
from queue import Queue
import asyncio
from typing import Optional, List

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
        self.root.title("🇨🇳 RSS China News Filter")
        self.root.geometry("1200x800")
        
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
        self.failed_feeds: List[tuple] = []  # Lista de (nombre, url, razón)
        
        # Variables de configuración
        self.config_file = tk.StringVar(value="config/feeds.json")
        self.keywords_file = tk.StringVar(value="config/keywords.json")
        self.output_dir = tk.StringVar(value="data")
        self.use_async = tk.BooleanVar(value=False)
        self.log_level = tk.StringVar(value="INFO")
        
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
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        
        # Frame principal con padding
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=15, pady=15)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # === TÍTULO ===
        title_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        title_label = tk.Label(title_frame, 
                              text="🇨🇳 RSS China News Filter",
                              font=('Segoe UI', 20, 'bold'),
                              bg=self.colors['bg'],
                              fg=self.colors['primary'])
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(title_frame,
                                 text="Monitoreo de noticias sobre China en medios españoles",
                                 font=('Segoe UI', 10),
                                 bg=self.colors['bg'],
                                 fg=self.colors['text_light'])
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # === PANEL DE CONFIGURACIÓN ===
        config_card = tk.Frame(main_frame, bg=self.colors['card_bg'], 
                              relief='solid', borderwidth=1, 
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        config_card.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        config_inner = tk.Frame(config_card, bg=self.colors['card_bg'], padx=20, pady=15)
        config_inner.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(config_inner, text="⚙️ Configuración", 
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.colors['text']).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        config_inner.columnconfigure(1, weight=1)
        
        # Archivo de feeds
        tk.Label(config_inner, text="Feeds:", bg=self.colors['card_bg'], 
                fg=self.colors['text']).grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        entry_feeds = ttk.Entry(config_inner, textvariable=self.config_file, width=60)
        entry_feeds.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(config_inner, text="📁", width=3, 
                  command=lambda: self.browse_file(self.config_file)).grid(row=1, column=2, pady=5)
        
        # Archivo de keywords
        tk.Label(config_inner, text="Keywords:", bg=self.colors['card_bg'],
                fg=self.colors['text']).grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        entry_keywords = ttk.Entry(config_inner, textvariable=self.keywords_file, width=60)
        entry_keywords.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(config_inner, text="📁", width=3,
                  command=lambda: self.browse_file(self.keywords_file)).grid(row=2, column=2, pady=5)
        
        # Directorio de salida
        tk.Label(config_inner, text="Salida:", bg=self.colors['card_bg'],
                fg=self.colors['text']).grid(row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        entry_output = ttk.Entry(config_inner, textvariable=self.output_dir, width=60)
        entry_output.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(config_inner, text="📁", width=3,
                  command=lambda: self.browse_directory(self.output_dir)).grid(row=3, column=2, pady=5)
        
        # Opciones
        options_frame = tk.Frame(config_inner, bg=self.colors['card_bg'])
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        
        ttk.Checkbutton(options_frame, text="⚡ Modo asíncrono (más rápido)", 
                       variable=self.use_async).pack(side=tk.LEFT, padx=5)
        
        tk.Label(options_frame, text="Log level:", bg=self.colors['card_bg'],
                fg=self.colors['text']).pack(side=tk.LEFT, padx=(30, 5))
        log_combo = ttk.Combobox(options_frame, textvariable=self.log_level, 
                                values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                state="readonly", width=12)
        log_combo.pack(side=tk.LEFT)
        
        # === PANEL DE CONTROL Y ESTADÍSTICAS ===
        control_stats_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        control_stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_stats_frame.columnconfigure(1, weight=1)
        
        # Controles
        control_card = tk.Frame(control_stats_frame, bg=self.colors['card_bg'],
                               relief='solid', borderwidth=1,
                               highlightbackground=self.colors['border'],
                               highlightthickness=1)
        control_card.grid(row=0, column=0, sticky=(tk.W, tk.N, tk.S), padx=(0, 10))
        
        control_inner = tk.Frame(control_card, bg=self.colors['card_bg'], padx=20, pady=15)
        control_inner.pack()
        
        self.start_button = tk.Button(control_inner, text="▶ INICIAR", 
                                      command=self.start_process,
                                      bg=self.colors['success'],
                                      fg='white',
                                      font=('Segoe UI', 11, 'bold'),
                                      relief='flat',
                                      padx=30, pady=12,
                                      cursor='hand2',
                                      activebackground='#059669')
        self.start_button.pack(pady=5, fill=tk.X)
        
        self.stop_button = tk.Button(control_inner, text="⬛ DETENER",
                                     command=self.stop_process,
                                     bg=self.colors['error'],
                                     fg='white',
                                     font=('Segoe UI', 11, 'bold'),
                                     relief='flat',
                                     padx=30, pady=12,
                                     cursor='hand2',
                                     state=tk.DISABLED,
                                     activebackground='#dc2626')
        self.stop_button.pack(pady=5, fill=tk.X)
        
        # Separador
        ttk.Separator(control_inner, orient='horizontal').pack(fill='x', pady=10)
        
        # Botón de Extracción
        self.extract_button = tk.Button(control_inner, text="📝 EXTRAER TEXTO",
                                      command=self.start_extraction,
                                      bg=self.colors['secondary'],
                                      fg='white',
                                      font=('Segoe UI', 11, 'bold'),
                                      relief='flat',
                                      padx=30, pady=10,
                                      cursor='hand2',
                                      activebackground=self.colors['secondary_dark'])
        self.extract_button.pack(pady=5, fill=tk.X)
        
        self.status_label = tk.Label(control_inner, text="● Listo",
                                     font=('Segoe UI', 10, 'bold'),
                                     bg=self.colors['card_bg'],
                                     fg=self.colors['success'])
        self.status_label.pack(pady=(10, 0))
        
        # Estadísticas
        stats_card = tk.Frame(control_stats_frame, bg=self.colors['card_bg'],
                             relief='solid', borderwidth=1,
                             highlightbackground=self.colors['border'],
                             highlightthickness=1)
        stats_card.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        stats_inner = tk.Frame(stats_card, bg=self.colors['card_bg'], padx=20, pady=15)
        stats_inner.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(stats_inner, text="📊 Estadísticas",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.colors['text']).grid(row=0, column=0, columnspan=4, 
                                             sticky=tk.W, pady=(0, 15))
        
        # Grid para estadísticas
        self.stats_labels = {}
        stats_info = [
            ("feeds_total", "📡 Feeds consultados:", self.colors['primary']),
            ("feeds_ok", "  ✓ Exitosos:", self.colors['success']),
            ("feeds_error", "  ✗ Fallidos:", self.colors['error']),
            ("items_total", "📰 Ítems analizados:", self.colors['primary']),
            ("items_china", "🇨🇳 Sobre China:", self.colors['warning']),
            ("items_unique", "⭐ Únicos guardados:", self.colors['success'])
        ]
        
        for i, (key, label, color) in enumerate(stats_info):
            row = (i // 2) + 1
            col = (i % 2) * 2
            
            # Para feeds fallidos, hacer el label clickeable
            if key == "feeds_error":
                label_widget = tk.Label(stats_inner, text=label, bg=self.colors['card_bg'],
                                       fg=self.colors['text'], font=('Segoe UI', 9),
                                       cursor='hand2')
                label_widget.grid(row=row, column=col, sticky=tk.W, padx=(0, 5), pady=3)
                label_widget.bind('<Button-1>', lambda e: self.show_failed_feeds())
                
                # Añadir efecto hover
                label_widget.bind('<Enter>', lambda e: label_widget.config(fg=self.colors['error'], font=('Segoe UI', 9, 'bold')))
                label_widget.bind('<Leave>', lambda e: label_widget.config(fg=self.colors['text'], font=('Segoe UI', 9)))
            else:
                tk.Label(stats_inner, text=label, bg=self.colors['card_bg'],
                        fg=self.colors['text'], font=('Segoe UI', 9)).grid(
                            row=row, column=col, sticky=tk.W, padx=(0, 5), pady=3)
            
            value_label = tk.Label(stats_inner, text="0", bg=self.colors['card_bg'],
                                  fg=color, font=('Segoe UI', 11, 'bold'))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 5), pady=3)
            self.stats_labels[key] = value_label
        
        # === NOTEBOOK PARA LOGS Y RESULTADOS ===
        notebook_frame = tk.Frame(main_frame, bg=self.colors['card_bg'],
                                 relief='solid', borderwidth=1,
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=1)
        notebook_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Tab 1: Logs
        logs_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(logs_frame, text='📋 Logs de Ejecución')
        
        self.output_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD,
                                                     font=("Consolas", 9),
                                                     bg='#1e1e1e', fg='#d4d4d4',
                                                     insertbackground='white',
                                                     relief='flat')
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 2: Resultados
        results_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(results_frame, text='📊 Resultados')
        
        # Toolbar para resultados
        results_toolbar = tk.Frame(results_frame, bg=self.colors['card_bg'], pady=10)
        results_toolbar.pack(fill=tk.X, padx=5)
        
        tk.Button(results_toolbar, text="🔄 Cargar Resultados",
                 command=self.load_results,
                 bg=self.colors['primary'], fg='white',
                 font=('Segoe UI', 9, 'bold'),
                 relief='flat', padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(results_toolbar, text="📄 Abrir JSONL",
                 command=self.open_jsonl,
                 bg=self.colors['text_light'], fg='white',
                 font=('Segoe UI', 9),
                 relief='flat', padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(results_toolbar, text="📊 Abrir CSV",
                 command=self.open_csv,
                 bg=self.colors['text_light'], fg='white',
                 font=('Segoe UI', 9),
                 relief='flat', padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=5)
                 
        tk.Button(results_toolbar, text="📂 Abrir Full JSONL",
                 command=self.open_full_jsonl,
                 bg=self.colors['secondary'], fg='white',
                 font=('Segoe UI', 9),
                 relief='flat', padx=15, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        self.results_count_label = tk.Label(results_toolbar,
                                           text="No hay resultados cargados",
                                           bg=self.colors['card_bg'],
                                           fg=self.colors['text_light'],
                                           font=('Segoe UI', 9))
        self.results_count_label.pack(side=tk.RIGHT, padx=10)
        
        # Treeview para resultados
        tree_frame = tk.Frame(results_frame, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        self.results_tree = ttk.Treeview(tree_frame,
                                        columns=('medio', 'titular', 'fecha'),
                                        show='tree headings',
                                        yscrollcommand=tree_scroll_y.set,
                                        xscrollcommand=tree_scroll_x.set)
        
        tree_scroll_y.config(command=self.results_tree.yview)
        tree_scroll_x.config(command=self.results_tree.xview)
        
        # Configurar columnas
        self.results_tree.heading('#0', text='#')
        self.results_tree.heading('medio', text='Medio')
        self.results_tree.heading('titular', text='Titular')
        self.results_tree.heading('fecha', text='Fecha')
        
        self.results_tree.column('#0', width=50, anchor='center')
        self.results_tree.column('medio', width=150)
        self.results_tree.column('titular', width=600)
        self.results_tree.column('fecha', width=180)
        
        # Grid
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Doble click para abrir enlace
        self.results_tree.bind('<Double-1>', self.on_result_double_click)
    
    def setup_logging(self):
        """Configura el sistema de logging."""
        # Crear directorio de logs
        Path("logs").mkdir(exist_ok=True)
        
        # Configurar logging
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%H:%M:%S'
        
        # Handler para archivo
        file_handler = logging.FileHandler("logs/rss_china_gui.log", encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Handler para GUI
        self.text_handler = TextHandler(self.output_text, self.log_queue)
        self.text_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Configurar root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(self.text_handler)
    
    def check_log_queue(self):
        """Revisa la cola de logs y actualiza el widget de texto."""
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.output_text.insert(tk.END, msg + '\n')
            self.output_text.see(tk.END)
        
        # Programar siguiente revisión
        self.root.after(100, self.check_log_queue)
    
    def browse_file(self, var):
        """Abre diálogo para seleccionar archivo."""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            var.set(filename)
    
    def browse_directory(self, var):
        """Abre diálogo para seleccionar directorio."""
        directory = filedialog.askdirectory(title="Seleccionar directorio")
        if directory:
            var.set(directory)
    
    def update_status(self, text, color="black"):
        """Actualiza el label de estado."""
        self.status_label.config(text=text, fg=color)
    
    def update_stats(self):
        """Actualiza las estadísticas en la UI."""
        for key, label in self.stats_labels.items():
            label.config(text=str(self.stats[key]))
    
    def clear_output(self):
        """Limpia el área de salida."""
        self.output_text.delete(1.0, tk.END)
    
    def reset_stats(self):
        """Resetea las estadísticas."""
        for key in self.stats:
            self.stats[key] = 0
        self.update_stats()
        self.failed_feeds = []
    
    def load_results(self):
        """Carga los resultados desde el archivo JSONL."""
        filepath = Path(self.output_dir.get()) / "output.jsonl"
        
        if not filepath.exists():
            messagebox.showwarning("Archivo no encontrado",
                                 "No se encontró el archivo de resultados.\n"
                                 "Ejecuta el proceso primero.")
            return
        
        # Limpiar tabla
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Cargar datos
        try:
            self.results_data = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    data = json.loads(line)
                    self.results_tree.insert('', 'end', text=str(i),
                                           values=(data.get('nombre_del_medio', ''),
                                                  data.get('titular', ''),
                                                  data.get('fecha', '')))
                    self.results_data.append(data)
            
            self.results_count_label.config(
                text=f"✓ {len(self.results_data)} resultados cargados",
                fg=self.colors['success'])
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar resultados:\n{e}")
    
    def on_result_double_click(self, event):
        """Maneja el doble click en un resultado."""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        item = self.results_tree.item(selection[0])
        index = int(item['text']) - 1
        
        if 0 <= index < len(self.results_data):
            url = self.results_data[index].get('enlace', '')
            if url:
                import webbrowser
                webbrowser.open(url)
    
    def show_failed_feeds(self):
        """Muestra un diálogo con los feeds que fallaron."""
        import webbrowser
        
        if not self.failed_feeds:
            messagebox.showinfo(
                "Feeds Fallidos",
                "No hay feeds fallidos en la última ejecución.\n\n"
                "Los feeds fallidos son aquellos que no se pudieron descargar por:\n"
                "  • Servidor no responde\n"
                "  • URL no existe (404)\n"
                "  • Timeout de conexión\n"
                "  • Problemas de red\n"
                "  • Feed bloqueado o requiere autenticación"
            )
            return
        
        # Crear ventana personalizada
        dialog = tk.Toplevel(self.root)
        dialog.title("⚠️ Feeds Fallidos - Detalles")
        dialog.geometry("850x600")
        dialog.configure(bg=self.colors['bg'])
        
        # Frame principal
        main = tk.Frame(dialog, bg=self.colors['bg'], padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title = tk.Label(main,
                        text=f"⚠️ {len(self.failed_feeds)} Feed(s) Fallido(s)",
                        font=('Segoe UI', 14, 'bold'),
                        bg=self.colors['bg'],
                        fg=self.colors['error'])
        title.pack(pady=(0, 10))
        
        # Subtítulo con instrucciones
        subtitle = tk.Label(main,
                           text="Haz clic en '🌐 Abrir URL' para verificar el feed en tu navegador",
                           font=('Segoe UI', 9),
                           bg=self.colors['bg'],
                           fg=self.colors['text_light'])
        subtitle.pack(pady=(0, 15))
        
        # Frame con scroll para la lista de feeds
        list_frame = tk.Frame(main, bg='white', relief='solid', borderwidth=1)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas y scrollbar para scroll vertical
        canvas = tk.Canvas(list_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Crear una tarjeta para cada feed fallido
        for i, (nombre, url, razon) in enumerate(self.failed_feeds, 1):
            # Frame para cada feed
            feed_card = tk.Frame(scrollable_frame, bg='white', 
                                relief='solid', borderwidth=1,
                                highlightbackground=self.colors['border'],
                                highlightthickness=1)
            feed_card.pack(fill=tk.X, padx=10, pady=8)
            
            # Contenido interno
            feed_inner = tk.Frame(feed_card, bg='white', padx=15, pady=12)
            feed_inner.pack(fill=tk.BOTH, expand=True)
            
            # Número y nombre del medio
            header_frame = tk.Frame(feed_inner, bg='white')
            header_frame.pack(fill=tk.X, pady=(0, 8))
            
            tk.Label(header_frame, 
                    text=f"{i}.",
                    font=('Segoe UI', 11, 'bold'),
                    bg='white',
                    fg=self.colors['error']).pack(side=tk.LEFT, padx=(0, 8))
            
            tk.Label(header_frame,
                    text=nombre,
                    font=('Segoe UI', 11, 'bold'),
                    bg='white',
                    fg=self.colors['text']).pack(side=tk.LEFT)
            
            # URL (truncada si es muy larga)
            url_display = url if len(url) <= 80 else url[:77] + "..."
            tk.Label(feed_inner,
                    text=f"URL: {url_display}",
                    font=('Consolas', 9),
                    bg='white',
                    fg=self.colors['text_light'],
                    anchor='w').pack(fill=tk.X, pady=(0, 5))
            
            # Razón del fallo
            tk.Label(feed_inner,
                    text=f"Razón: {razon}",
                    font=('Segoe UI', 9),
                    bg='white',
                    fg=self.colors['error'],
                    anchor='w').pack(fill=tk.X, pady=(0, 10))
            
            # Botón para abrir URL
            open_btn = tk.Button(feed_inner,
                                text="🌐 Abrir URL en navegador",
                                command=lambda u=url: webbrowser.open(u),
                                bg=self.colors['primary'],
                                fg='white',
                                font=('Segoe UI', 9, 'bold'),
                                relief='flat',
                                cursor='hand2',
                                padx=15, pady=6,
                                activebackground=self.colors['primary_dark'])
            open_btn.pack(anchor='w')
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Información adicional
        info_frame = tk.Frame(main, bg=self.colors['bg'])
        info_frame.pack(fill=tk.X, pady=(15, 0))
        
        info_text = ("💡 Posibles causas: Servidor caído temporalmente • URL cambió o no existe • "
                    "Problemas de conexión • Feed requiere autenticación • Timeout")
        tk.Label(info_frame,
                text=info_text,
                font=('Segoe UI', 8),
                bg=self.colors['bg'],
                fg=self.colors['text_light'],
                wraplength=800,
                justify=tk.LEFT).pack(side=tk.LEFT)
        
        # Botón cerrar
        close_btn = tk.Button(main, text="Cerrar",
                             command=dialog.destroy,
                             bg=self.colors['primary'],
                             fg='white',
                             font=('Segoe UI', 10, 'bold'),
                             relief='flat',
                             padx=30, pady=10,
                             cursor='hand2',
                             activebackground=self.colors['primary_dark'])
        close_btn.pack(pady=(15, 0))
    
    def start_process(self):
        """Inicia el proceso de descarga y filtrado."""
        if self.is_running:
            return
        
        # Validar archivos
        if not Path(self.config_file.get()).exists():
            messagebox.showerror("Error", f"Archivo de feeds no encontrado: {self.config_file.get()}")
            return
        
        if not Path(self.keywords_file.get()).exists():
            messagebox.showerror("Error", f"Archivo de keywords no encontrado: {self.keywords_file.get()}")
            return
        
        # Preparar UI
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.extract_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("● Ejecutando...", self.colors['warning'])
        self.clear_output()
        self.reset_stats()
        
        # Cambiar a tab de logs
        self.notebook.select(0)
        
        # Actualizar nivel de logging
        logging.getLogger().setLevel(getattr(logging, self.log_level.get()))
        
        # Iniciar thread
        self.worker_thread = threading.Thread(target=self.run_process, daemon=True)
        self.worker_thread.start()
    
    def stop_process(self):
        """Detiene el proceso (simplemente marca como detenido)."""
        if self.is_running:
            self.is_running = False
            self.update_status("● Deteniendo...", self.colors['error'])
            logging.warning("Proceso detenido por el usuario")
    
    def run_process(self):
        """Ejecuta el proceso principal (en thread separado)."""
        logger = logging.getLogger(__name__)
        
        try:
            if self.use_async.get():
                # Modo asíncrono
                asyncio.run(self.run_async())
            else:
                # Modo síncrono
                self.run_sync()
            
            if self.is_running:
                self.root.after(0, lambda: self.update_status("● Completado", self.colors['success']))
                self.root.after(0, lambda: messagebox.showinfo("Éxito",
                    f"Proceso completado.\n\n{self.stats['items_unique']} noticias únicas guardadas."))
                # Auto-cargar resultados
                self.root.after(500, self.load_results)
            
        except Exception as e:
            logger.error(f"Error en el proceso: {e}", exc_info=True)
            self.root.after(0, lambda: self.update_status("● Error", self.colors['error']))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error durante la ejecución:\n{str(e)}"))
        
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            # Restaurar estado del botón de extracción si no está corriendo
            if not self.is_running:
                self.root.after(0, lambda: self.extract_button.config(state=tk.NORMAL))

    def start_extraction(self):
        """Inicia el proceso de extracción de texto completo."""
        if self.is_running:
            return
            
        # Verificar que existe el archivo de entrada
        input_file = Path(self.output_dir.get()) / "output.jsonl"
        if not input_file.exists():
            messagebox.showerror("Error", 
                               f"No se encontró el archivo de noticias filtradas: {input_file}\n"
                               "Ejecuta primero el filtro de noticias.")
            return
            
        # Preparar UI
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.extract_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("● Extrayendo texto...", self.colors['secondary'])
        self.clear_output()
        
        # Cambiar a tab de logs
        self.notebook.select(0)
        
        # Actualizar nivel de logging
        logging.getLogger().setLevel(getattr(logging, self.log_level.get()))
        
        # Iniciar thread de extracción
        self.worker_thread = threading.Thread(target=self.run_extraction, daemon=True)
        self.worker_thread.start()

    def run_extraction(self):
        """Ejecuta la extracción de texto (en thread separado)."""
        logger = logging.getLogger(__name__)
        logger.info("=== Iniciando Extracción de Texto Completo ===")
        
        try:
            input_file = str(Path(self.output_dir.get()) / "output.jsonl")
            
            # Configuración básica para el extractor
            config = {
                'output': {
                    'jsonl_path': str(Path(self.output_dir.get()) / "articles_full.jsonl"),
                    'csv_path': str(Path(self.output_dir.get()) / "articles_full.csv")
                },
                'processing': {
                    'concurrency': 5
                }
            }
            
            # Ejecutar proceso
            report = process_articles(input_file, config=config)
            
            if self.is_running:
                self.root.after(0, lambda: self.update_status("● Extracción Completada", self.colors['success']))
                
                msg = (f"Extracción completada.\n\n"
                       f"Total procesado: {report.total_articles}\n"
                       f"✅ Exitosos: {report.successful}\n"
                       f"❌ Fallos: {report.failed_download + report.failed_extraction}\n"
                       f"⚠️ Sin contenido: {report.no_content}")
                
                self.root.after(0, lambda: messagebox.showinfo("Éxito", msg))
                
        except Exception as e:
            logger.error(f"Error en la extracción: {e}", exc_info=True)
            self.root.after(0, lambda: self.update_status("● Error", self.colors['error']))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error durante la extracción:\n{str(e)}"))
            
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.extract_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))

    def open_full_jsonl(self):
        """Abre el archivo JSONL de artículos completos."""
        filepath = Path(self.output_dir.get()) / "articles_full.jsonl"
        self.open_file(filepath)
    
    async def run_async(self):
        """Ejecuta el proceso en modo asíncrono."""
        logger = logging.getLogger(__name__)
        logger.info("=== Iniciando RSS China News Filter (modo asíncrono) ===")
        
        # 1. Cargar feeds
        logger.info(f"Cargando feeds desde {self.config_file.get()}")
        feeds = load_feeds(self.config_file.get())
        self.stats['feeds_total'] = len(feeds)
        self.root.after(0, self.update_stats)
        
        if not feeds or not self.is_running:
            return
        
        # 2. Cargar keywords
        logger.info(f"Cargando keywords desde {self.keywords_file.get()}")
        keywords = load_keywords(self.keywords_file.get())
        
        if not keywords or not self.is_running:
            return
        
        # 3. Descargar feeds
        logger.info(f"Descargando {len(feeds)} feeds...")
        download_results = await download_feeds_async(feeds)
        
        if not self.is_running:
            return
        
        # 4. Parsear feeds
        logger.info("Parseando feeds...")
        all_items = []
        
        # Mapear feeds por URL para obtener nombres
        feeds_map = {f['url']: f['nombre'] for f in feeds}
        
        for url, nombre, content in download_results:
            if not self.is_running:
                return
            
            if content:
                items = parse_feed(content, url, nombre)
                all_items.extend(items)
                self.stats['feeds_ok'] += 1
            else:
                self.stats['feeds_error'] += 1
                # Registrar feed fallido
                feed_nombre = feeds_map.get(url, nombre or 'Desconocido')
                self.failed_feeds.append((feed_nombre, url, "No se pudo descargar"))
            
            self.root.after(0, self.update_stats)
        
        self.stats['items_total'] = len(all_items)
        self.root.after(0, self.update_stats)
        logger.info(f"Total de ítems parseados: {self.stats['items_total']}")
        
        # 5. Filtrar por China
        logger.info("Filtrando noticias sobre China...")
        china_items = filter_china_news(all_items, keywords)
        self.stats['items_china'] = len(china_items)
        self.root.after(0, self.update_stats)
        
        # 6. Deduplicar
        logger.info("Eliminando duplicados...")
        unique_items = deduplicate(china_items)
        self.stats['items_unique'] = len(unique_items)
        self.root.after(0, self.update_stats)
        
        # 7. Guardar resultados
        if unique_items and self.is_running:
            logger.info(f"Guardando {len(unique_items)} noticias únicas...")
            save_results(unique_items, self.output_dir.get())
        else:
            logger.warning("No se encontraron noticias sobre China")
        
        logger.info("=== Proceso completado ===")
    
    def run_sync(self):
        """Ejecuta el proceso en modo síncrono."""
        logger = logging.getLogger(__name__)
        logger.info("=== Iniciando RSS China News Filter (modo síncrono) ===")
        
        # 1. Cargar feeds
        logger.info(f"Cargando feeds desde {self.config_file.get()}")
        feeds = load_feeds(self.config_file.get())
        self.stats['feeds_total'] = len(feeds)
        self.root.after(0, self.update_stats)
        
        if not feeds or not self.is_running:
            return
        
        # 2. Cargar keywords
        logger.info(f"Cargando keywords desde {self.keywords_file.get()}")
        keywords = load_keywords(self.keywords_file.get())
        
        if not keywords or not self.is_running:
            return
        
        # 3. Descargar feeds
        logger.info(f"Descargando {len(feeds)} feeds...")
        download_results = download_feeds_sync(feeds)
        
        if not self.is_running:
            return
        
        # 4. Parsear feeds
        logger.info("Parseando feeds...")
        all_items = []
        
        # Mapear feeds por URL para obtener nombres
        feeds_map = {f['url']: f['nombre'] for f in feeds}
        
        for url, nombre, content in download_results:
            if not self.is_running:
                return
            
            if content:
                items = parse_feed(content, url, nombre)
                all_items.extend(items)
                self.stats['feeds_ok'] += 1
            else:
                self.stats['feeds_error'] += 1
                # Registrar feed fallido
                feed_nombre = feeds_map.get(url, nombre or 'Desconocido')
                self.failed_feeds.append((feed_nombre, url, "No se pudo descargar"))
            
            self.root.after(0, self.update_stats)
        
        self.stats['items_total'] = len(all_items)
        self.root.after(0, self.update_stats)
        logger.info(f"Total de ítems parseados: {self.stats['items_total']}")
        
        # 5. Filtrar por China
        logger.info("Filtrando noticias sobre China...")
        china_items = filter_china_news(all_items, keywords)
        self.stats['items_china'] = len(china_items)
        self.root.after(0, self.update_stats)
        
        # 6. Deduplicar
        logger.info("Eliminando duplicados...")
        unique_items = deduplicate(china_items)
        self.stats['items_unique'] = len(unique_items)
        self.root.after(0, self.update_stats)
        
        # 7. Guardar resultados
        if unique_items and self.is_running:
            logger.info(f"Guardando {len(unique_items)} noticias únicas...")
            save_results(unique_items, self.output_dir.get())
        else:
            logger.warning("No se encontraron noticias sobre China")
        
        logger.info("=== Proceso completado ===")
    
    def open_jsonl(self):
        """Abre el archivo JSONL de resultados."""
        filepath = Path(self.output_dir.get()) / "output.jsonl"
        self.open_file(filepath)
    
    def open_csv(self):
        """Abre el archivo CSV de resultados."""
        filepath = Path(self.output_dir.get()) / "output.csv"
        self.open_file(filepath)
    
    def open_file(self, filepath):
        """Abre un archivo con la aplicación predeterminada del sistema."""
        if not filepath.exists():
            messagebox.showwarning("Archivo no encontrado",
                                   f"El archivo no existe:\n{filepath}")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.run(["open", filepath])
            else:
                subprocess.run(["xdg-open", filepath])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")


def main():
    """Función principal para ejecutar la GUI."""
    root = tk.Tk()
    app = RSSChinaGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
