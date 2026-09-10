import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db import database as db
from app.core.gdrive import GDriveClient

logger = logging.getLogger(__name__)

DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

_gdrive_client = None


def _execute_upload(file_id):
    global _gdrive_client
    file_data = db.get_file(file_id)
    if not file_data or not file_data["active"]:
        logger.info(f"Archivo {file_id} inactivo, saltando.")
        return

    if not _gdrive_client.is_authenticated:
        logger.warning("Google Drive no autenticado, intentando reconectar...")
        try:
            _gdrive_client.authenticate()
        except Exception as e:
            logger.error(f"No se pudo autenticar con Drive: {e}")
            db.add_history(file_id=file_id, status="error", message=f"No autenticado: {e}")
            return

    try:
        existing_id = file_data.get("last_drive_file_id") or None
        result = _gdrive_client.upload_file(
            file_path=file_data["source_path"],
            folder_id=file_data["drive_folder_id"] or None,
            existing_file_id=existing_id,
        )
        db.set_last_drive_file_id(file_id, result.get("id"))
        db.add_history(
            file_id=file_id,
            status="success",
            message=f"{'Actualizado' if existing_id else 'Subido'}: {result.get('name')} (ID: {result.get('id')})",
            file_size=result.get("size", 0),
        )
        logger.info(f"Upload exitoso: {file_data['name']}")
    except Exception as e:
        db.add_history(file_id=file_id, status="error", message=str(e))
        logger.error(f"Error subiendo {file_data['name']}: {e}")


def _calculate_next_run(days_enabled, hour_start, minute_start):
    now = datetime.now()
    for day_offset in range(8):
        check_date = now + timedelta(days=day_offset)
        if check_date.weekday() in days_enabled:
            if day_offset == 0:
                target = check_date.replace(hour=hour_start, minute=minute_start, second=0, microsecond=0)
                if target > now:
                    return target
                continue
            return check_date.replace(hour=hour_start, minute=minute_start, second=0, microsecond=0)
    return now


class TaskScheduler:
    def __init__(self, gdrive_client: GDriveClient):
        global _gdrive_client
        _gdrive_client = gdrive_client
        self.gdrive = gdrive_client
        self.scheduler = BackgroundScheduler()

    def start(self):
        self.scheduler.start()
        self._reload_all_tasks()

    def shutdown(self):
        self.scheduler.shutdown(wait=False)

    def _reload_all_tasks(self):
        self.scheduler.remove_all_jobs()
        active_files = db.get_active_files()
        for f in active_files:
            self._add_job_for_file(f["id"])

    def _add_job_for_file(self, file_id):
        schedule = db.get_schedule(file_id)
        if not schedule:
            return

        days_enabled = []
        for i, day_key in enumerate(DAY_MAP.values()):
            if schedule[day_key]:
                days_enabled.append(i)

        if not days_enabled:
            return

        hour_start = schedule["hour_start"]
        minute_start = schedule.get("minute_start", 0)
        interval_minutes = schedule.get("interval_minutes", 120)

        job_id = f"upload_file_{file_id}"
        existing = self.scheduler.get_job(job_id)
        if existing:
            existing.remove()

        self.scheduler.add_job(
            _execute_upload,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            args=[file_id],
            replace_existing=True,
            next_run_time=_calculate_next_run(days_enabled, hour_start, minute_start),
        )
        logger.info(f"Tarea programada: archivo_id={file_id}, intervalo={interval_minutes}min, dias={days_enabled}")

    def activate_task(self, file_id):
        db.set_file_active(file_id, True)
        self._add_job_for_file(file_id)

    def deactivate_task(self, file_id):
        db.set_file_active(file_id, False)
        job_id = f"upload_file_{file_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            job.remove()
        logger.info(f"Tarea desactivada: archivo_id={file_id}")

    def update_task(self, file_id):
        schedule = db.get_schedule(file_id)
        file_data = db.get_file(file_id)
        if file_data and file_data["active"] and schedule:
            self._add_job_for_file(file_id)
        else:
            job_id = f"upload_file_{file_id}"
            job = self.scheduler.get_job(job_id)
            if job:
                job.remove()

    def get_task_status(self, file_id):
        job_id = f"upload_file_{file_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                "status": "active",
                "next_run": str(job.next_run_time) if job.next_run_time else "N/A",
            }
        return {"status": "inactive", "next_run": "N/A"}

    def run_now(self, file_id):
        _execute_upload(file_id)
