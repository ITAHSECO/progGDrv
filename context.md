# Programador de Copias a Google Drive

Aplicación de escritorio en Python que programa subidas automáticas de archivos a Google Drive.

## Tecnologías

- **GUI**: Tkinter
- **Persistencia**: SQLite (`app/gdrive_scheduler.db`)
- **Scheduler**: APScheduler (MemoryJobStore, tareas se re-registran al iniciar)
- **API**: Google Drive API v3 (OAuth 2.0)

## Estructura

```
progGDrv/
├── main.py                     # Entry point
├── requirements.txt            # Dependencias
├── .gitignore
├── credentials.json            # OAuth (usuario descarga de Google Cloud Console)
├── token.json                  # Token de acceso (se genera automáticamente)
├── app/
│   ├── core/
│   │   ├── gdrive.py           # Autenticación y subida/actualización a Drive
│   │   └── scheduler.py        # Gestión de tareas programadas
│   ├── db/
│   │   └── database.py         # SQLite: files, schedules, upload_history
│   └── gui/
│       ├── main_window.py      # Ventana principal con toolbar y pestañas
│       ├── file_panel.py       # Pestaña Tareas + FolderPickerDialog
│       └── history_panel.py    # Pestaña Historial con export CSV
```

## Base de datos

### Tabla `files`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador |
| name | TEXT | Nombre descriptivo |
| source_path | TEXT | Ruta local del archivo |
| drive_folder_id | TEXT | Carpeta destino en Drive |
| last_drive_file_id | TEXT | ID del último archivo subido (para sobreescribir) |
| active | BOOLEAN | Habilitado/deshabilitado |
| created_at | TIMESTAMP | Fecha de creación |

### Tabla `schedules`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador |
| file_id | INTEGER FK | Referencia a archivo |
| hour_start | INTEGER | Hora inicio (0-23) |
| minute_start | INTEGER | Minuto inicio (0-59) |
| hour_end | INTEGER | Hora fin (0-23) |
| minute_end | INTEGER | Minuto fin (0-59) |
| interval_minutes | INTEGER | Intervalo en minutos |
| mon-sun | BOOLEAN | Días activos |

### Tabla `upload_history`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador |
| file_id | INTEGER FK | Referencia a archivo |
| upload_time | TIMESTAMP | Fecha/hora de subida |
| status | TEXT | "success" / "error" |
| message | TEXT | Detalle |
| file_size | INTEGER | Tamaño en bytes |

## Funcionalidades

1. **Conectar a Drive**: OAuth 2.0 con scopes `drive.file` + `drive.readonly`
2. **Agregar archivo**: Seleccionar archivo local, configurar programación
3. **Selector de carpetas**: Lista carpetas de Drive para elegir destino
4. **Programación**: Intervalo en minutos, hora inicio/fin con minutos, días activos
5. **Activar/Desactivar**: Control individual de cada tarea
6. **Subir ahora**: Ejecución manual
7. **Sobreescribir**: Actualiza el mismo archivo en Drive (no crea copias)
8. **Historial**: Log de subidas con filtro, export CSV y vaciado

## Configuración de Google Cloud Console

1. Crear proyecto en Google Cloud Console
2. Habilitar Google Drive API
3. Pantalla de consentimiento: completar nombre, logo, email de soporte
4. Agregar scopes: `drive.file` y `drive.readonly`
5. Agregar email como usuario de prueba
6. Credenciales > OAuth > Tipo: Escritorio
7. Authorized redirect URIs: `http://localhost:8080`
8. Descargar `credentials.json` a la raíz del proyecto

## Ejecución

```bash
pip install -r requirements.txt
python main.py
```

## Crear ejecutable

```bash
pyinstaller --onefile --windowed --icon=icono.ico main.py
```

## Commits

| Hash | Descripción |
|------|-------------|
| 4167d24 | fix: usar scopes drive.file + drive.readonly |
| 0e213d0 | fix: sobreescribir archivo en Drive |
| 2b8eede | fix: scheduler con MemoryJobStore |
| d855c9d | fix: migracion automatica de esquema DB |
| 231fc3b | feat: programacion con minutos y selector de carpetas |
| 5cc2f51 | fix: puerto fijo 8080 para OAuth |
| 52233c7 | feat: implementacion inicial |
