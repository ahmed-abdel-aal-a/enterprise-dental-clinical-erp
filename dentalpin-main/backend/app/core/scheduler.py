"""APScheduler configuration for background jobs.

Provides a singleton scheduler for running periodic tasks like
appointment reminders, budget expiry checks, etc.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from zoneinfo import ZoneInfo

from app.config import settings
from app.core.plugins.registry import module_registry
from app.core.scheduling import ScheduledJob

logger = logging.getLogger(__name__)

# Singleton scheduler instance
scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the scheduler instance, creating it if needed."""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone=ZoneInfo("Africa/Cairo"))
    return scheduler


def _build_trigger(job: ScheduledJob) -> CronTrigger | IntervalTrigger:
    if job.trigger == "cron":
        return CronTrigger(**job.trigger_args)
    if job.trigger == "interval":
        return IntervalTrigger(**job.trigger_args)
    raise ValueError(f"Unknown trigger '{job.trigger}' for job '{job.id}'")


def init_scheduler() -> None:
    """Initialize and start the scheduler.

    Jobs are collected from the *active* modules (installed and mounted at
    boot, issue #91) via ``BaseModule.get_scheduled_jobs()`` — the
    scheduler no longer imports module task functions directly, so an
    uninstalled module contributes no job (ADR 0014 import-coupling fix).
    """
    global scheduler

    # Don't run scheduler in test mode
    if settings.TESTING:
        logger.info("Skipping scheduler initialization in test mode")
        return

    scheduler = get_scheduler()

    for module in module_registry.list_active():
        for job in module.get_scheduled_jobs():
            if scheduler.get_job(job.id):
                logger.info("Scheduler job '%s' already exists, skipping", job.id)
                continue
            scheduler.add_job(
                job.func,
                _build_trigger(job),
                id=job.id,
                name=job.name,
                max_instances=job.max_instances,
                replace_existing=True,
            )
            logger.info("Registered job '%s' from module '%s'", job.id, module.name)

    # Periodic memory maintenance job for low-end hardware
    async def _periodic_memory_trim():
        import gc
        gc.collect()
        try:
            import ctypes
            import os
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi
            h_proc = kernel32.OpenProcess(0x1F0FFF, False, os.getpid())
            if h_proc:
                psapi.EmptyWorkingSet(h_proc)
                kernel32.CloseHandle(h_proc)
        except Exception:
            pass

    scheduler.add_job(
        _periodic_memory_trim,
        IntervalTrigger(minutes=10),
        id="low_end_memory_trim",
        name="Trim dormant memory pages for low-end hardware",
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully.

    Should be called during application shutdown.
    """
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown complete")
