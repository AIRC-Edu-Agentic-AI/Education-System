from fastapi import APIRouter

# Tạo một router tổng cho thư mục schedule
router = APIRouter()

# 1. Gộp router của giảng viên (Phần việc của bạn)
from .teacher import router as teacher_router
router.include_router(teacher_router)

# 2. Gộp router của sinh viên (Bắt lỗi an toàn)
try:
    from .student import router as student_router
    router.include_router(student_router)
except ImportError:
    # Nếu nhánh của sinh viên chưa có file này, tự động bỏ qua để không sập server
    pass