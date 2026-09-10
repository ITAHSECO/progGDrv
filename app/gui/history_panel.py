import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.db import database as db


class HistoryPanel:
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.frame)
        top.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(top, text="Filtrar por archivo:").pack(side=tk.LEFT, padx=(0, 5))
        self.var_filter = tk.StringVar(value="Todos")
        self.combo_filter = ttk.Combobox(
            top, textvariable=self.var_filter, state="readonly", width=25
        )
        self.combo_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.combo_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(top, text="Exportar CSV", command=self._export_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Vaciar Historial", command=self._clear_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Refrescar", command=self.refresh).pack(side=tk.LEFT, padx=2)

        cols = ("id", "archivo", "fecha", "estado", "mensaje", "tamano")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("archivo", text="Archivo")
        self.tree.heading("fecha", text="Fecha/Hora")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("mensaje", text="Mensaje")
        self.tree.heading("tamano", text="Tamaño")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("archivo", width=150)
        self.tree.column("fecha", width=140)
        self.tree.column("estado", width=70, anchor=tk.CENTER)
        self.tree.column("mensaje", width=280)
        self.tree.column("tamano", width=80, anchor=tk.E)

        scroll_y = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(5, 0), pady=5)
        scroll_y.pack(fill=tk.Y, side=tk.RIGHT, padx=(0, 5), pady=5)

    def _refresh_filter(self):
        files = db.get_all_files()
        names = ["Todos"] + [f["name"] for f in files]
        self.combo_filter["values"] = names
        if self.var_filter.get() not in names:
            self.var_filter.set("Todos")

    def refresh(self):
        self._refresh_filter()
        for item in self.tree.get_children():
            self.tree.delete(item)

        filter_name = self.var_filter.get()
        file_id = None
        if filter_name != "Todos":
            files = db.get_all_files()
            for f in files:
                if f["name"] == filter_name:
                    file_id = f["id"]
                    break

        history = db.get_history(file_id=file_id)
        for h in history:
            status_display = "OK" if h["status"] == "success" else "ERROR"
            size = h["file_size"] if h["file_size"] else 0
            size_str = self._format_size(size) if size else "-"
            self.tree.insert("", tk.END, iid=str(h["id"]), values=(
                h["id"],
                h["file_name"],
                h["upload_time"],
                status_display,
                h["message"],
                size_str,
            ))

    @staticmethod
    def _format_size(size_bytes):
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Exportar historial",
        )
        if not path:
            return

        history = db.get_history()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Archivo", "Fecha/Hora", "Estado", "Mensaje", "Tamano (bytes)"])
                for h in history:
                    writer.writerow([
                        h["id"], h["file_name"], h["upload_time"],
                        h["status"], h["message"], h["file_size"],
                    ])
            messagebox.showinfo("Exportar", f"Historial exportado a:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar:\n{e}")

    def _clear_history(self):
        if messagebox.askyesno("Confirmar", "Vacias todo el historial de subidas?"):
            db.clear_history()
            self.refresh()
            self.main_window.set_status("Historial vaciado.")
