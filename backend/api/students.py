from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from services.analytics_service import list_students, get_student

from auth.dependencies import require_role, get_db
from models.parent_student_db import ParentStudentDB
from models.teacher_assignment_db import TeacherAssignmentDB

router = APIRouter()


@router.get("", summary="List students")
def list_students_endpoint(
    user=Depends(require_role(["Parent", "Teacher", "Admin"])),
    db: Session = Depends(get_db),
):
    role = (getattr(user, "role", "") or "").lower()
    all_students = list_students()

    if role == "admin":
        return [s.dict() for s in all_students]

    if role == "parent":
        mapped_ids = {
            r.student_id
            for r in db.query(ParentStudentDB)
            .filter(ParentStudentDB.parent_user_id == user.id)
            .all()
        }
        return [s.dict() for s in all_students if s.id in mapped_ids]

    if role == "teacher":
        assigns = db.query(TeacherAssignmentDB).filter(
            TeacherAssignmentDB.teacher_user_id == user.id
        ).all()
        allowed = {(str(a.grade), str(a.section)) for a in assigns}
        return [
            s.dict()
            for s in all_students
            if (str(getattr(s, "grade", "")), str(getattr(s, "section", ""))) in allowed
        ]

    return []


@router.get("/{student_id}", summary="Get student details")
def get_student_endpoint(
    student_id: int,
    user=Depends(require_role(["Parent", "Teacher", "Admin"])),
    db: Session = Depends(get_db),
):
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    role = (getattr(user, "role", "") or "").lower()
    if role == "admin":
        return student.dict()

    if role == "parent":
        ok = db.query(ParentStudentDB).filter(
            ParentStudentDB.parent_user_id == user.id,
            ParentStudentDB.student_id == student.id,
        ).first()
        if not ok:
            raise HTTPException(status_code=403, detail="Forbidden")
        return student.dict()

    if role == "teacher":
        ok = db.query(TeacherAssignmentDB).filter(
            TeacherAssignmentDB.teacher_user_id == user.id,
            TeacherAssignmentDB.grade == str(student.grade),
            TeacherAssignmentDB.section == str(student.section),
        ).first()
        if not ok:
            raise HTTPException(status_code=403, detail="Forbidden")
        return student.dict()

    raise HTTPException(status_code=403, detail="Forbidden")
