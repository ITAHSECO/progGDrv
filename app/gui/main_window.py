import tkinter as tk
from tkinter import ttk, messagebox
from app.gui.file_panel import FilePanel
from app.gui.history_panel import HistoryPanel
from app.db import database as db


class MainWindow:
    def __init__(self, root, task_scheduler, gdrive_client):
        self.root = root
        self.scheduler = task_scheduler
        self.gdrive = gdrive_client

        self.root.title("Programador de Copias a Google Drive")
        self.root.geometry("1000x650")
        self.root.minsize(800, 500)

        self._build_menu()
        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()

        self.refresh_all()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self._show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill=tk.X)

        ttk.Label(toolbar, text="Estado de Google Drive: ").pack(side=tk.LEFT)
        self.lbl_gdrive_status = ttk.Label(toolbar, text="No conectado", foreground="red")
        self.lbl_gdrive_status.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="Conectar a Drive", command=self._connect_drive).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refrescar", command=self.refresh_all).pack(side=tk.LEFT, padx=2)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.file_panel = FilePanel(self.notebook, self)
        self.history_panel = HistoryPanel(self.notebook, self)

        self.notebook.add(self.file_panel.frame, text="  Tareas  ")
        self.notebook.add(self.history_panel.frame, text="  Historial  ")

    def _build_statusbar(self):
        self.statusbar = ttk.Frame(self.root, padding=(5, 2))
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.lbl_status = ttk.Label(self.statusbar, text="Listo")
        self.lbl_status.pack(side=tk.LEFT)

    def _connect_drive(self):
        try:
            self.gdrive.authenticate()
            self.lbl_gdrive_status.config(text="Conectado", foreground="green")
            self.lbl_status.config(text="Conectado a Google Drive exitosamente.")
            messagebox.showinfo("Conexion", "Conectado a Google Drive exitosamente.")
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error de conexion", str(e))

    def refresh_all(self):
        self.file_panel.refresh()
        self.history_panel.refresh()

    def set_status(self, text):
        self.lbl_status.config(text=text)

    def _show_about(self):
        messagebox.showinfo(
            "Acerca de",
            "Programador de Copias a Google Drive\n\n"
            "Permite programar subidas automaticas de archivos a Google Drive.\n"
            "Desarrollado en Python con Tkinter, SQLite y APScheduler.",
        )
