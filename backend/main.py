from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from routers import student, chat, schedule, notifications, auth, admin, teacher_dashboard, teacher_schedule, teacher_notification, realtime_chat
from routers import study_groups
from routers import teacher_risk, teacher_classrooms
from routers.assignment import student as assignment_student, teacher as assignment_teacher
from db.mongodb import connect_db, close_db, db_state
from scheduler import setup_scheduler, teardown_scheduler
from agent.llm_pool import init_pool, get_pool
from routers.course_communication import router as course_communication_router
from db.event_logging import log_event


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    import notify_schedule
    await notify_schedule.load_settings()
    init_pool()
    import asyncio
    asyncio.create_task(realtime_chat.listen_to_change_stream())

    print("\n" + "="*60)
    print("REGISTERED ROUTES:")
    print("="*60)
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"  {route.path}")
        elif hasattr(route, "routes"):
            for r in route.routes:
                if hasattr(r, "path"):
                    print(f"  {r.path}")
    print("="*60 + "\n")

    yield

    # Shutdown
    teardown_scheduler()
    await close_db()


app = FastAPI(
    title="Education System API",
    version="2.0.0",
    description="API cho he thong giao duc tich hop AI -- Student + Teacher + AI Agent",
    lifespan=lifespan,
)

@app.middleware("http")
async def auto_event_logging_middleware(request, call_next):
    path = request.url.path
    if path in {"/docs", "/openapi.json", "/redoc", "/health", "/uploads"}:
        return await call_next(request)

    payload = {
        "method": request.method,
        "path": path,
        "query_params": dict(request.query_params),
        "user_agent": request.headers.get("user-agent"),
        "client_ip": request.headers.get("x-forwarded-for") or request.client.host if request.client else None,
    }

    try:
        response = await call_next(request)
    except Exception as exc:
        await log_event(
            None,
            "http_error",
            target_id=path,
            payload={**payload, "error": str(exc)},
            source="http_middleware",
        )
        raise

    await log_event(
        None,
        "http_request",
        target_id=path,
        payload={**payload, "status_code": response.status_code},
        source="http_middleware",
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads/submissions", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Authentication
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Teacher: Notifications (BR26-27, BR32-33, BR38-39)
app.include_router(teacher_notification.router, prefix="/notify", tags=["teacher-notification"])

# Student endpoints (BR01-BR18)
app.include_router(student.router, prefix="/student", tags=["student"])
app.include_router(schedule.student_router, prefix="/schedule", tags=["schedule-student"])
app.include_router(assignment_student.router, prefix="/student", tags=["student-assignments"])
app.include_router(assignment_teacher.router, prefix="/assignments", tags=["assignments"])
app.include_router(assignment_teacher.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(notifications.router, prefix="/notify", tags=["notifications"])

# Course Communication (channels, messages, courses)
app.include_router(course_communication_router, prefix="/course")

# Chat (AI agent chat for students)
app.include_router(chat.router, prefix="/chat", tags=["chat"])

# Real-time WebSocket chat
app.include_router(realtime_chat.router, prefix="/realtime-chat", tags=["realtime-chat"])

# Study Groups
app.include_router(study_groups.router, tags=["study-groups"])



# Teacher: Dashboard & Analytics (BR34-35)
app.include_router(teacher_dashboard.router, prefix="/api", tags=["teacher-dashboard"])
app.include_router(teacher_schedule.router, prefix="/api", tags=["teacher-schedule"])

# Teacher: Risk Management (BR36-37, BR40-42)
app.include_router(teacher_risk.router, prefix="/api/risk", tags=["teacher-risk"])

# Teacher: Classroom Management (BR28-29)
app.include_router(teacher_classrooms.router, prefix="/api/classrooms", tags=["teacher-classrooms"])

# Admin
app.include_router(admin.router, prefix="/admin", tags=["admin"])

# Static files (teacher dashboard UI)
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/dashboard", NoCacheStaticFiles(directory=_STATIC_DIR, html=True), name="dashboard")


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard/")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "db": "connected" if db_state["connected"] else "mock",
        "environment": os.getenv("ENVIRONMENT", "demo"),
        "version": "2.0.0",
    }


@app.post("/debug/trigger/{job_id}")
async def debug_trigger(job_id: str):
    from scheduler import scheduler
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    job.modify(next_run_time=__import__("datetime").datetime.now())
    return {"triggered": job_id}