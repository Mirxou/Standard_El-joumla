"""
خدمة الجدولة العامة للمهام الخلفية
Task Scheduler Service

تدير حلقة لتشغيل مهام مجدولة مثل إرسال التذكيرات والنسخ الاحتياطي.
"""

from __future__ import annotations
import logging

import os
import threading
import time
from datetime import datetime
from datetime import time as dt_time
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QSettings

from src.services.reminder_service import ReminderService, get_reminder_service

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(
        self,
        db_manager,
        reminder_service: Optional[ReminderService] = None,
        interval_seconds: int = 60,
    ):
        self.db_manager = db_manager
        self.reminder_service = reminder_service
        self.interval = interval_seconds
        self.enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        self._jobs: List[Dict[str, Any]] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False

        self.setup_jobs()

    def setup_jobs(self):
        """Sets up the jobs to be run by the scheduler."""
        # Reminder Job
        if self.reminder_service:
            self.add_job(self.run_reminder_job, interval=300)  # Every 5 minutes

        # Backup Job
        self.add_job(self.run_backup_job, interval=3600)  # Check every hour

        # Scheduled Reports Job
        self.add_job(self.run_scheduled_reports_job, interval=300)  # Every 5 minutes

    def add_job(self, job_func: Callable, interval: int):
        """Adds a job to the scheduler."""
        self._jobs.append({"func": job_func, "interval": interval, "last_run": 0})

    def start(self) -> bool:
        if not self.enabled:
            logger.info("TaskScheduler disabled by environment variable")
            return False
        if self._running:
            return True
        logger.info(f"Starting TaskScheduler with check interval={self.interval}s")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="TaskScheduler", daemon=True)
        self._thread.start()
        self._running = True
        return True

    def _run_loop(self):
        while not self._stop_event.is_set():
            current_time = time.time()
            for job in self._jobs:
                if current_time - job["last_run"] > job["interval"]:
                    try:
                        job["func"]()
                        job["last_run"] = current_time
                    except Exception as e:
                        logger.log(logging.ERROR, f"Scheduler job {job['func'].__name__} failed: {e}")

            self._stop_event.wait(self.interval)

    def stop(self) -> None:
        if not self._running:
            return
        logger.info("Stopping TaskScheduler")
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._running = False

    def is_running(self) -> bool:
        return self._running and not self._stop_event.is_set()

    # --- Job Implementations ---

    def run_reminder_job(self):
        """Job to send due reminders."""
        if self.reminder_service:
            result = self.reminder_service.send_due_reminders()
            if result.get("total_sent", 0) > 0:
                logger.info(f"Sent reminders: {result}")

    def run_backup_job(self):
        """Job to perform automated backups based on settings."""
        s = QSettings("LogicalVersion", "ERP")
        is_enabled = s.value("backup/auto_enabled", False, type=bool)
        if not is_enabled:
            return

        backup_time_str = s.value("backup/time", "02:00")
        backup_time = dt_time.fromisoformat(backup_time_str)
        now = datetime.now().time()

        # Check if it's time to run the backup (within a 1-hour window)
        if backup_time.hour == now.hour:
            # Check if a backup for today has already been made
            last_backup_key = "backup/last_auto_backup_date"
            last_backup_date_str = s.value(last_backup_key)
            today_str = datetime.now().date().isoformat()

            if last_backup_date_str != today_str:
                logger.info("Running scheduled daily backup...")
                if hasattr(self.db_manager, "backup_database_encrypted"):
                    metadata = {"type": "automated"}
                    backup_file = self.db_manager.backup_database_encrypted(metadata=metadata)
                    if backup_file:
                        logger.info(f"Scheduled backup created: {backup_file}")
                        s.setValue(last_backup_key, today_str)
                        # Cleanup old backups
                        keep = s.value("backup/keep", 7, type=int)
                        if hasattr(self.db_manager, "cleanup_old_backups"):
                            self.db_manager.cleanup_old_backups(max_backups=keep)
                    else:
                        logger.log(logging.ERROR, "Scheduled backup failed.")
                else:
                    logger.warning("Encrypted backup method not found on db_manager.")

    def run_scheduled_reports_job(self):
        """Job to run scheduled reports."""
        try:
            from src.services.scheduled_reports_service import ScheduledReportsService

            scheduled_reports_service = ScheduledReportsService(self.db_manager, logger)
            results = scheduled_reports_service.check_and_run_due_reports()

            if results:
                logger.info(f"Ran {len(results)} scheduled reports")
                for result in results:
                    if result.get("success"):
                        logger.info(f"Report {result.get('report_id')} generated successfully")
                    else:
                        logger.log(logging.ERROR, f"Report failed: {result.get('error')}")
        except Exception as e:
            logger.log(logging.ERROR, f"Error running scheduled reports job: {e}", exc_info=True)


# Global instance
_scheduler_global: Optional[TaskScheduler] = None


def init_task_scheduler(db_manager, reminder_service: Optional[ReminderService] = None) -> TaskScheduler:
    global _scheduler_global
    if _scheduler_global is None:
        if reminder_service is None:
            reminder_service = get_reminder_service()
        _scheduler_global = TaskScheduler(db_manager, reminder_service)
        _scheduler_global.start()
    return _scheduler_global


def get_task_scheduler() -> Optional[TaskScheduler]:
    return _scheduler_global
