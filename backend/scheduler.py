from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from db.mock_data import MOCK_STUDENT

scheduler = AsyncIOScheduler()


async def _event_check_job() -> None:
    from agent.event_checker import run_event_check
    await run_event_check(MOCK_STUDENT["student_id"])


async def _daily_plan_job() -> None:
    from agent.daily_planner import run_daily_planning
    await run_daily_planning(MOCK_STUDENT["student_id"])


async def _weekly_plan_job() -> None:
    from agent.weekly_planner import run_weekly_planning
    await run_weekly_planning(MOCK_STUDENT["student_id"], trigger="cron")


async def _progress_report_job() -> None:
    from agent.progress_report import run_progress_report
    await run_progress_report(MOCK_STUDENT["student_id"])


async def _progress_check_job() -> None:
    from agent.event_checker import run_progress_check
    await run_progress_check(MOCK_STUDENT["student_id"])


def setup_scheduler() -> None:
    scheduler.add_job(
        _event_check_job,
        IntervalTrigger(minutes=15),
        id="event_check",
        replace_existing=True,
    )
    scheduler.add_job(
        _daily_plan_job,
        CronTrigger(hour=8, minute=0),
        id="daily_plan",
        replace_existing=True,
    )
    scheduler.add_job(
        _weekly_plan_job,
        CronTrigger(day_of_week="mon", hour=8, minute=5),
        id="weekly_plan",
        replace_existing=True,
    )
    scheduler.add_job(
        _progress_report_job,
        CronTrigger(day_of_week="sun", hour=20, minute=0),
        id="progress_report",
        replace_existing=True,
    )
    scheduler.add_job(
        _progress_check_job,
        CronTrigger(hour=12, minute=0),
        id="progress_check",
        replace_existing=True,
    )
    scheduler.start()
    print("[scheduler] Started — event_check/15min, daily_plan/08:00, weekly_plan/Mon 08:05, "
          "progress_report/Sun 20:00, progress_check/12:00")


def teardown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
        print("[scheduler] Stopped")
