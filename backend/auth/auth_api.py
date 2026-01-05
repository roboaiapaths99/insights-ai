from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db.session import SessionLocal
from models.user_db import UserDB
from models.parent_student_db import ParentStudentDB
from models.teacher_assignment_db import TeacherAssignmentDB
from models.student_db import StudentDB
from auth.auth_service import verify_password, create_access_token
from auth.dependencies import get_current_user

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(payload: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.email == payload.email).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"sub": str(user.id), "role": user.role})

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            },
        }
    finally:
        db.close()


@router.get("/me")
def me(user: UserDB = Depends(get_current_user)):
    db = SessionLocal()
    try:
        payload = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
        }

        # Parent → mapped students
        if (user.role or "").lower() == "parent":
            q = (
                db.query(StudentDB)
                .join(ParentStudentDB, ParentStudentDB.student_id == StudentDB.id)
                .filter(ParentStudentDB.parent_user_id == user.id)
                .order_by(StudentDB.grade.asc(), StudentDB.section.asc(), StudentDB.name.asc())
            )
            payload["students"] = [
                {
                    "id": s.id,
                    "name": s.name,
                    "admission_no": s.admission_no,
                    "grade": s.grade,
                    "section": s.section,
                }
                for s in q.all()
            ]

        # Teacher → assigned grade/section(s)
        if (user.role or "").lower() == "teacher":
            rows = (
                db.query(TeacherAssignmentDB)
                .filter(TeacherAssignmentDB.teacher_user_id == user.id)
                .order_by(TeacherAssignmentDB.grade.asc(), TeacherAssignmentDB.section.asc())
                .all()
            )
            payload["assignments"] = [{"grade": r.grade, "section": r.section} for r in rows]

        return payload
    finally:
        db.close()
