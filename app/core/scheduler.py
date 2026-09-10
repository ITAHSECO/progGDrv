import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger

from app.db import database as db
from app.core.gdrive import GDriveClient

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "gdrive_scheduler.db")

DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


class TaskScheduler:
    def __init__(self, gdrive_client: GDriveClient):
        self.gdrive = gdrive_client
        jobstores = {"default": SQLAlchemyJobStore(url=f"sqlite:///{DB_PATH}")}
        self.scheduler = BackgroundScheduler(jobstores=jobstores)

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
        hour_end = schedule["hour_end"]
        interval = schedule["interval_hours"]

        if hour_start <= hour_end:
            run_hours = [h for h in range(hour_start, hour_end + 1) if self._should_run_in_window(h, hour_start, hour_end, interval)]
        else:
            run_hours = [h for h in range(hour_start, 24)] + [h for h in range(0, hour_end + 1) if self._should_run_in_window(h, hour_start, hour_end, interval)]

        job_id = f"upload_file_{file_id}"
        existing = self.scheduler.get_job(job_id)
        if existing:
            existing.remove()

        self.scheduler.add_job(
            self._execute_upload,
            trigger=IntervalTrigger(hours=interval),
            id=job_id,
            args=[file_id],
            replace_existing=True,
            next_run_time=self._calculate_next_run(days_enabled, interval),
        )
        logger.info(f"Tarea programada: archivo_id={file_id}, intervalo={interval}h, dias={days_enabled}")

    def _should_run_in_window(self, hour, start, end, interval):
        if start <= end:
            return (hour - start) % max(int(interval), 1) == 0
        return True

    def _calculate_next_run(self, days_enabled, interval_hours):
        now = datetime.now()
        for day_offset in range(8):
            check_date = now
            from datetime import timedelta
            check_date = now + timedelta(days=day_offset)
            if check_date.weekday() in days_enabled:
                if day_offset == 0:
                    return check_date.replace(hour=check_date.hour, minute=0, second=0, microsecond=0)
                return check_date.replace(hour=0, minute=0, second=0, microsecond=0)
        return now

    def _execute_upload(self, file_id):
        file_data = db.get_file(file_id)
        if not file_data or not file_data["active"]:
            logger.info(f"Archivo {file_id} inactivo, saltando.")
            return

        try:
            result = self.gdrive.upload_file(
                file_path=file_data["source_path"],
                folder_id=file_data["drive_folder_id"] or None,
            )
            db.add_history(
                file_id=file_id,
                status="success",
                message=f"Subido: {result.get('name')} (ID: {result.get('id')})",
                file_size=result.get("size", 0),
            )
            logger.info(f"Upload exitoso: {file_data['name']}")
        except Exception as e:
            db.add_history(file_id=file_id, status="error", message=str(e))
            logger.error(f"Error subiendo {file_data['name']}: {e}")

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
        self._execute_upload(file_id)
