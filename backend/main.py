from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from routers import student, chat, schedule, notifications, auth, assignments, admin, dashboard
from routers import study_groups
from db.mongodb import connect_db, close_db, db_state
from scheduler import setup_scheduler, teardown_scheduler
from agent.llm_pool import init_pool, get_pool
from routers.course_communication import router as course_communication_router


load_dotenv()

app = FastAPI()

os.makedirs("uploads/submissions", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
    await get_pool().healthcheck()
    setup_scheduler()
    
    # ⭐ THÊM DEBUG VÀO ĐÂY
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
    title="Student Agent API",
    version="1.0.0-demo",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# backend/main.py
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(course_communication_router, prefix="/course")
app.include_router(student.router, prefix="/student", tags=["student"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
app.include_router(notifications.router, prefix="/notify", tags=["notifications"])
app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(study_groups.router, tags=["study-groups"])  # ✅ Bỏ prefix
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])  # Teacher Dashboard API

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/dashboard", NoCacheStaticFiles(directory=_STATIC_DIR, html=True), name="dashboard")


@app.on_event("startup")
async def show_routes():
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


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard/")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "db": "connected" if db_state["connected"] else "mock",
        "environment": os.getenv("ENVIRONMENT", "demo"),
    }


@app.post("/debug/trigger/{job_id}")
async def debug_trigger(job_id: str):
    from scheduler import scheduler
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    job.modify(next_run_time=__import__("datetime").datetime.now())
    return {"triggered": job_id}