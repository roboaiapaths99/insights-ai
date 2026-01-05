from fastapi import APIRouter

from .students import router as students_router
from .dashboard import router as dashboard_router
from .parent_dashboard import router as parent_dashboard_router
from .insights import router as insights_router
from .teacher_upload import router as teacher_upload_router
from .admin import router as admin_router
from .teacher_feedback import router as teacher_feedback_router  # ✅ ADD THIS
from auth.auth_api import router as auth_router

api_router = APIRouter()

api_router.include_router(students_router, prefix="/students", tags=["students"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(parent_dashboard_router, prefix="/dashboard", tags=["parent-dashboard"])
api_router.include_router(insights_router, prefix="/insights", tags=["insights"])
api_router.include_router(teacher_upload_router, prefix="/teacher", tags=["teacher"])
api_router.include_router(teacher_feedback_router, prefix="/teacher", tags=["teacher-feedback"])  # ✅ ADD THIS
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
