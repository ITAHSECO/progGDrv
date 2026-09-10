import sys
import os
import logging
import tkinter as tk

sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import init_db
from app.core.gdrive import GDriveClient
from app.core.scheduler import TaskScheduler
from app.gui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gdrive_scheduler.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Iniciando aplicacion...")
    init_db()

    gdrive = GDriveClient()
    scheduler = TaskScheduler(gdrive)

    root = tk.Tk()
    app = MainWindow(root, scheduler, gdrive)

    scheduler.start()

    def on_close():
        logger.info("Cerrando aplicacion...")
        scheduler.shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
