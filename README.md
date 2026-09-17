# Programador de Copias a Google Drive

Aplicación de escritorio en Python que programa subidas automáticas de archivos a Google Drive.

---

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Generar credenciales de Google Drive (`credentials.json`)

### Paso 1: Crear proyecto en Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Menú superior → "Seleccionar proyecto" → **Nuevo proyecto**
3. Nombre: cualquier nombre (ej: `progGDrv`)
4. Click **Crear**

### Paso 2: Habilitar la API de Google Drive

1. Menú → **APIs y servicios** → **Biblioteca**
2. Buscar "Google Drive API"
3. Click **Habilitar**

### Paso 3: Configurar la Pantalla de consentimiento

1. Menú → **APIs y servicios** → **Pantalla de consentimiento de OAuth**
2. Seleccionar **Externo** → Click **Crear**
3. Completar información obligatoria:
   - **Nombre de la app**: `progGDrv`
   - **Correo electrónico de soporte**: tu email
   - **Logo**: subir cualquier imagen (puede ser un PNG de 100x100px)
   - **Enlace de privacidad**: `http://localhost`
   - **Enlace de soporte**: `http://localhost`
4. Click **Guardar y continuar**
5. En **Alcances** → Click **Agregar o quitar alcances** → Buscar y agregar:
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/drive.readonly`
6. Click **Guardar y continuar**
7. En **Usuarios de prueba** → Agregar tu email de Google
8. Click **Guardar y continuar** → **Volver al panel**

### Paso 4: Crear credenciales OAuth

1. Menú → **APIs y servicios** → **Credenciales**
2. Click **+ Crear credenciales** → **ID de cliente de OAuth**
3. Configurar:
   - **Nombre**: `progGDrv`
   - **Tipo de app**: **Escritorio**
4. Click **Crear**
5. Se genera el `client_id` y `client_secret`
6. Click en el **ícono de descarga** junto a tu cliente OAuth
7. Se descarga un JSON → **renombrarlo a `credentials.json`**
8. Colocarlo en la **raíz del proyecto** (junto a `main.py`)

### Paso 5: Configurar redirect URI

1. En **Credenciales**, click en tu cliente OAuth
2. En **URIs de redireccionamiento autorizados**, agregar:
   ```
   http://localhost:8080
   ```
3. Click **Guardar**

> **Nota**: Si el botón "Guardar" no aparece, es porque la Pantalla de consentimiento no está completa. Verifica que tengas nombre, logo, email y scopes configurados.

---

## Manual de uso

### Conectar a Google Drive

1. Ejecutar `python main.py`
2. Click en **"Conectar a Drive"** en la barra superior
3. Se abre el navegador pidiendo autorización
4. Seleccionar tu cuenta de Google → Click **Permitir**
5. El estado cambia a **"Conectado"** (verde)

### Agregar un archivo para subir

1. Click en **"Agregar Archivo"**
2. Pestaña **Archivo**:
   - **Nombre**: nombre descriptivo (ej: "Backup Documents")
   - **Archivo local**: click en `...` y seleccionar el archivo
   - **Carpeta Drive**: click en `...` para ver tus carpetas de Drive, o ingresa el ID manualmente
   - **Activo**: marcar para que se ejecute automáticamente
3. Pestaña **Programacion**:
   - **Intervalo**: cada cuántos minutos se ejecuta (ej: 120 = cada 2 horas)
   - **Hora inicio**: hora de inicio (ej: 08:00)
   - **Hora fin**: hora de fin (ej: 18:00)
   - **Días activos**: marcar Lun-Vie (Sab y Dom desactivados por defecto)
4. Click **Aceptar**

### Selector de carpetas de Drive

Al hacer click en `...` junto a "Carpeta Drive":

1. Click **"Cargar carpetas"** para ver tus carpetas
2. Seleccionar una de la lista
3. Click **Aceptar**

> Si no aparecen las carpetas, verifica que estés conectado a Drive.

### Activar / Desactivar tareas

1. Seleccionar una tarea en la tabla
2. Click **"Activar"** o **"Desactivar"**
3. El estado cambia en la tabla

### Ejecutar subida manual

1. Seleccionar una tarea
2. Click **"Subir Ahora"**
3. Se sube inmediatamente a Drive

### Editar tarea

1. Doble click en la tarea **o** seleccionar y click **"Editar"**
2. Modificar los campos necesarios
3. Click **Aceptar**

### Eliminar tarea

1. Seleccionar la tarea
2. Click **"Eliminar"**
3. Confirmar

### Ver historial de subidas

1. Click en la pestaña **"Historial"**
2. Ver todas las subidas realizadas con fecha, estado y detalle
3. **Filtrar por archivo**: seleccionar un archivo en el dropdown
4. **Exportar CSV**: guarda el historial en un archivo Excel
5. **Vaciar Historial**: elimina todo el registro

---

## Crear ejecutable

```bash
pyinstaller --onefile --windowed --icon=icono.ico main.py
```

El `.exe` se genera en la carpeta `dist/`.

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| "No se encontro credentials.json" | Descargar de Google Cloud Console y colocar en la raíz |
| "invalid scope: bad request" | Eliminar `token.json` y reconectar |
| Error 403 al conectar | Verificar que tu email esté como usuario de prueba |
| Carpetas no se cargan | Verificar scopes `drive.file` y `drive.readonly` |
| Tarea no ejecuta | Verificar que esté activa y que Drive esté conectado |
