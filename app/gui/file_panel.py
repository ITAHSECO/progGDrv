import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.db import database as db


class FolderPickerDialog:
    def __init__(self, parent, gdrive_client):
        self.result = None
        self.gdrive = gdrive_client
        self.top = tk.Toplevel(parent)
        self.top.title("Seleccionar Carpeta de Drive")
        self.top.geometry("500x420")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()
        self._build_ui()

    def _build_ui(self):
        ttk.Label(self.top, text="Selecciona la carpeta destino en Google Drive:").pack(
            padx=10, pady=(10, 5), anchor=tk.W
        )

        ttk.Button(self.top, text="Cargar carpetas", command=self._load_folders).pack(
            fill=tk.X, padx=10, pady=(0, 5)
        )

        frame = ttk.Frame(self.top)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(frame, columns=("id", "name"), show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Nombre")
        self.tree.column("id", width=200)
        self.tree.column("name", width=280)

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scroll.pack(fill=tk.Y, side=tk.RIGHT)

        ttk.Label(self.top, text="O ingresa el ID manualmente:").pack(padx=10, anchor=tk.W)
        self.var_manual = tk.StringVar()
        ttk.Entry(self.top, textvariable=self.var_manual, width=60).pack(padx=10, pady=3, fill=tk.X)

        btn_frame = ttk.Frame(self.top)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="Aceptar", command=self._on_ok).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Cancelar", command=self.top.destroy).pack(side=tk.RIGHT, padx=2)

    def _load_folders(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            folders = self.gdrive.list_folders()
            for f in folders:
                self.tree.insert("", tk.END, iid=f["id"], values=(f["id"], f["name"]))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las carpetas:\n{e}")

    def _on_ok(self):
        sel = self.tree.selection()
        if sel:
            self.result = sel[0]
        elif self.var_manual.get().strip():
            self.result = self.var_manual.get().strip()
        else:
            messagebox.showwarning("Seleccion", "Selecciona una carpeta o ingresa un ID.")
            return
        self.top.destroy()


class FilePanel:
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.frame)
        top.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(top, text="Agregar Archivo", command=self._add_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Editar", command=self._edit_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Eliminar", command=self._delete_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(top, text="Activar", command=self._activate).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Desactivar", command=self._deactivate).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Subir Ahora", command=self._run_now).pack(side=tk.LEFT, padx=2)

        cols = ("id", "nombre", "archivo", "carpeta_drive", "estado", "proxima_ejecucion")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("archivo", text="Archivo Local")
        self.tree.heading("carpeta_drive", text="Carpeta Drive")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("proxima_ejecucion", text="Proxima Ejecucion")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("nombre", width=150)
        self.tree.column("archivo", width=250)
        self.tree.column("carpeta_drive", width=120)
        self.tree.column("estado", width=80, anchor=tk.CENTER)
        self.tree.column("proxima_ejecucion", width=160)

        scroll_y = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(5, 0), pady=5)
        scroll_y.pack(fill=tk.Y, side=tk.RIGHT, padx=(0, 5), pady=5)

        self.tree.bind("<Double-1>", lambda e: self._edit_file())

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        files = db.get_all_files()
        for f in files:
            status_text = "Activa" if f["active"] else "Inactiva"
            task_info = self.main_window.scheduler.get_task_status(f["id"])
            next_run = task_info.get("next_run", "N/A")
            if next_run and len(next_run) > 19:
                next_run = next_run[:19]

            self.tree.insert("", tk.END, iid=str(f["id"]), values=(
                f["id"],
                f["name"],
                f["source_path"],
                f["drive_folder_id"] or "-",
                status_text,
                next_run,
            ))

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seleccion", "Selecciona una tarea de la tabla.")
            return None
        return int(sel[0])

    def _add_file(self):
        dialog = FileDialog(self.main_window.root, title="Agregar Archivo", gdrive=self.main_window.gdrive)
        self.main_window.root.wait_window(dialog.top)
        if dialog.result:
            r = dialog.result
            file_id = db.add_file(r["name"], r["source_path"], r["drive_folder_id"])
            db.update_schedule(
                file_id, r["hour_start"], r["minute_start"], r["hour_end"], r["minute_end"],
                r["interval_minutes"],
                r["mon"], r["tue"], r["wed"], r["thu"], r["fri"], r["sat"], r["sun"],
            )
            if r["active"]:
                self.main_window.scheduler.activate_task(file_id)
            else:
                self.main_window.scheduler.update_task(file_id)
            self.refresh()
            self.main_window.set_status(f"Archivo '{r['name']}' agregado.")

    def _edit_file(self):
        file_id = self._get_selected_id()
        if not file_id:
            return
        file_data = db.get_file(file_id)
        schedule = db.get_schedule(file_id)
        if not file_data or not schedule:
            return

        dialog = FileDialog(
            self.main_window.root, title="Editar Archivo",
            file_data=file_data, schedule_data=schedule, gdrive=self.main_window.gdrive,
        )
        self.main_window.root.wait_window(dialog.top)
        if dialog.result:
            r = dialog.result
            db.update_file(file_id, r["name"], r["source_path"], r["drive_folder_id"])
            db.update_schedule(
                file_id, r["hour_start"], r["minute_start"], r["hour_end"], r["minute_end"],
                r["interval_minutes"],
                r["mon"], r["tue"], r["wed"], r["thu"], r["fri"], r["sat"], r["sun"],
            )
            db.set_file_active(file_id, r["active"])
            self.main_window.scheduler.update_task(file_id)
            self.refresh()
            self.main_window.set_status(f"Archivo '{r['name']}' actualizado.")

    def _delete_file(self):
        file_id = self._get_selected_id()
        if not file_id:
            return
        file_data = db.get_file(file_id)
        if messagebox.askyesno("Confirmar", f"Eliminar '{file_data['name']}' y toda su programacion?"):
            self.main_window.scheduler.deactivate_task(file_id)
            db.delete_file(file_id)
            self.refresh()
            self.main_window.set_status(f"Archivo eliminado.")

    def _activate(self):
        file_id = self._get_selected_id()
        if not file_id:
            return
        if not self.main_window.gdrive.is_authenticated:
            messagebox.showwarning("Drive", "Primero conectate a Google Drive.")
            return
        self.main_window.scheduler.activate_task(file_id)
        self.refresh()
        self.main_window.set_status(f"Tarea {file_id} activada.")

    def _deactivate(self):
        file_id = self._get_selected_id()
        if not file_id:
            return
        self.main_window.scheduler.deactivate_task(file_id)
        self.refresh()
        self.main_window.set_status(f"Tarea {file_id} desactivada.")

    def _run_now(self):
        file_id = self._get_selected_id()
        if not file_id:
            return
        if not self.main_window.gdrive.is_authenticated:
            messagebox.showwarning("Drive", "Primero conectate a Google Drive.")
            return
        self.main_window.set_status(f"Ejecutando subida manual para tarea {file_id}...")
        try:
            self.main_window.scheduler.run_now(file_id)
            self.main_window.set_status(f"Subida manual completada para tarea {file_id}.")
            self.main_window.history_panel.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Error en subida manual:\n{e}")
            self.main_window.set_status(f"Error en subida manual: {e}")


class FileDialog:
    def __init__(self, parent, title="Dialogo", file_data=None, schedule_data=None, gdrive=None):
        self.result = None
        self.gdrive = gdrive
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("520x520")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        self._build_form(file_data, schedule_data)

    def _build_form(self, file_data, schedule_data):
        notebook = ttk.Notebook(self.top)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab: Archivo
        tab_file = ttk.Frame(notebook, padding=10)
        notebook.add(tab_file, text="Archivo")

        ttk.Label(tab_file, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.var_name = tk.StringVar(value=file_data["name"] if file_data else "")
        ttk.Entry(tab_file, textvariable=self.var_name, width=45).grid(row=0, column=1, pady=3)

        ttk.Label(tab_file, text="Archivo local:").grid(row=1, column=0, sticky=tk.W, pady=3)
        frame_path = ttk.Frame(tab_file)
        frame_path.grid(row=1, column=1, pady=3, sticky=tk.EW)
        self.var_path = tk.StringVar(value=file_data["source_path"] if file_data else "")
        ttk.Entry(frame_path, textvariable=self.var_path, width=35).pack(side=tk.LEFT)
        ttk.Button(frame_path, text="...", width=3, command=self._browse_file).pack(side=tk.LEFT, padx=3)

        ttk.Label(tab_file, text="Carpeta Drive:").grid(row=2, column=0, sticky=tk.W, pady=3)
        frame_folder = ttk.Frame(tab_file)
        frame_folder.grid(row=2, column=1, pady=3, sticky=tk.EW)
        self.var_folder = tk.StringVar(value=file_data["drive_folder_id"] if file_data else "")
        ttk.Entry(frame_folder, textvariable=self.var_folder, width=35).pack(side=tk.LEFT)
        ttk.Button(frame_folder, text="...", width=3, command=self._pick_folder).pack(side=tk.LEFT, padx=3)

        self.var_active = tk.BooleanVar(value=bool(file_data["active"]) if file_data else False)
        ttk.Checkbutton(tab_file, text="Activo (ejecutar subidas)", variable=self.var_active).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=8
        )

        # Tab: Programacion
        tab_sched = ttk.Frame(notebook, padding=10)
        notebook.add(tab_sched, text="Programacion")

        ttk.Label(tab_sched, text="Intervalo:").grid(row=0, column=0, sticky=tk.W, pady=3)
        interval_frame = ttk.Frame(tab_sched)
        interval_frame.grid(row=0, column=1, sticky=tk.W, pady=3)

        default_minutes = 120
        if schedule_data:
            default_minutes = schedule_data.get("interval_minutes", 120)
        self.var_interval = tk.IntVar(value=default_minutes)
        ttk.Spinbox(interval_frame, from_=1, to=1440, textvariable=self.var_interval, width=6).pack(side=tk.LEFT)
        ttk.Label(interval_frame, text=" minutos").pack(side=tk.LEFT)

        ttk.Label(tab_sched, text="Hora inicio:").grid(row=1, column=0, sticky=tk.W, pady=3)
        start_frame = ttk.Frame(tab_sched)
        start_frame.grid(row=1, column=1, sticky=tk.W, pady=3)

        default_hstart = schedule_data["hour_start"] if schedule_data else 0
        default_mstart = schedule_data.get("minute_start", 0) if schedule_data else 0
        self.var_hstart = tk.IntVar(value=default_hstart)
        self.var_mstart = tk.IntVar(value=default_mstart)
        ttk.Spinbox(start_frame, from_=0, to=23, textvariable=self.var_hstart, width=3).pack(side=tk.LEFT)
        ttk.Label(start_frame, text=" : ").pack(side=tk.LEFT)
        ttk.Spinbox(start_frame, from_=0, to=59, textvariable=self.var_mstart, width=3).pack(side=tk.LEFT)

        ttk.Label(tab_sched, text="Hora fin:").grid(row=2, column=0, sticky=tk.W, pady=3)
        end_frame = ttk.Frame(tab_sched)
        end_frame.grid(row=2, column=1, sticky=tk.W, pady=3)

        default_hend = schedule_data["hour_end"] if schedule_data else 23
        default_mend = schedule_data.get("minute_end", 59) if schedule_data else 59
        self.var_hend = tk.IntVar(value=default_hend)
        self.var_mend = tk.IntVar(value=default_mend)
        ttk.Spinbox(end_frame, from_=0, to=23, textvariable=self.var_hend, width=3).pack(side=tk.LEFT)
        ttk.Label(end_frame, text=" : ").pack(side=tk.LEFT)
        ttk.Spinbox(end_frame, from_=0, to=59, textvariable=self.var_mend, width=3).pack(side=tk.LEFT)

        ttk.Label(tab_sched, text="Dias activos:").grid(row=3, column=0, sticky=tk.W, pady=(10, 3))

        days_frame = ttk.Frame(tab_sched)
        days_frame.grid(row=3, column=1, sticky=tk.W, pady=(10, 3))

        day_labels = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        day_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        self.day_vars = {}
        for i, (label, key) in enumerate(zip(day_labels, day_keys)):
            val = schedule_data[key] if schedule_data else (0 if key in ("sat", "sun") else 1)
            var = tk.BooleanVar(value=bool(val))
            self.day_vars[key] = var
            ttk.Checkbutton(days_frame, text=label, variable=var).grid(row=0, column=i, padx=3)

        # Botones
        btn_frame = ttk.Frame(self.top)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Aceptar", command=self._on_ok).pack(side=tk.RIGHT, padx=3)
        ttk.Button(btn_frame, text="Cancelar", command=self.top.destroy).pack(side=tk.RIGHT, padx=3)

    def _browse_file(self):
        path = filedialog.askopenfilename(title="Seleccionar archivo")
        if path:
            self.var_path.set(path)

    def _pick_folder(self):
        if not self.gdrive or not self.gdrive.is_authenticated:
            messagebox.showwarning("Drive", "Primero conectate a Google Drive para ver las carpetas.")
            return
        dialog = FolderPickerDialog(self.top, self.gdrive)
        self.top.wait_window(dialog.top)
        if dialog.result:
            self.var_folder.set(dialog.result)

    def _on_ok(self):
        name = self.var_name.get().strip()
        path = self.var_path.get().strip()
        if not name:
            messagebox.showwarning("Validacion", "El nombre es obligatorio.")
            return
        if not path or not os.path.exists(path):
            messagebox.showwarning("Validacion", "Selecciona un archivo local valido.")
            return
        interval = self.var_interval.get()
        if interval <= 0:
            messagebox.showwarning("Validacion", "El intervalo debe ser mayor a 0.")
            return

        self.result = {
            "name": name,
            "source_path": path,
            "drive_folder_id": self.var_folder.get().strip(),
            "active": self.var_active.get(),
            "hour_start": self.var_hstart.get(),
            "minute_start": self.var_mstart.get(),
            "hour_end": self.var_hend.get(),
            "minute_end": self.var_mend.get(),
            "interval_minutes": interval,
            "mon": self.day_vars["mon"].get(),
            "tue": self.day_vars["tue"].get(),
            "wed": self.day_vars["wed"].get(),
            "thu": self.day_vars["thu"].get(),
            "fri": self.day_vars["fri"].get(),
            "sat": self.day_vars["sat"].get(),
            "sun": self.day_vars["sun"].get(),
        }
        self.top.destroy()
