from __future__ import annotations

from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.student_db import StudentDB
from models.exam import Exam
from models.subject import Subject
from models.user_db import UserDB
from models.parent_student_db import ParentStudentDB
from models.teacher_assignment_db import TeacherAssignmentDB

# 🔐 AUTH
from auth.dependencies import require_role
from auth.auth_service import create_user

router = APIRouter()


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def _db() -> Session:
    return SessionLocal()


# ─────────────────────────────────────────
# Users (Admin helpers for mapping dropdowns)
# ─────────────────────────────────────────
@router.get("/users", summary="List users (optionally filter by role)")
def admin_list_users(
    role: str | None = None,
    user=Depends(require_role(["Admin"])),
) -> List[dict]:
    db = _db()
    try:
        q = db.query(UserDB).order_by(UserDB.id.asc())
        if role:
            q = q.filter(UserDB.role == role)
        rows = q.all()
        return [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": getattr(u, "is_active", True),
            }
            for u in rows
        ]
    finally:
        db.close()


@router.get("/users/parents", summary="List Parent users")
def admin_list_parents(
    user=Depends(require_role(["Admin"])),
) -> List[dict]:
    db = _db()
    try:
        rows = db.query(UserDB).filter(UserDB.role == "Parent").order_by(UserDB.id.asc()).all()
        return [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": getattr(u, "is_active", True),
            }
            for u in rows
        ]
    finally:
        db.close()


@router.get("/users/teachers", summary="List Teacher users")
def admin_list_teachers(
    user=Depends(require_role(["Admin"])),
) -> List[dict]:
    db = _db()
    try:
        rows = db.query(UserDB).filter(UserDB.role == "Teacher").order_by(UserDB.id.asc()).all()
        return [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": getattr(u, "is_active", True),
            }
            for u in rows
        ]
    finally:
        db.close()



@router.post("/users", summary="Create user (Admin)")
def admin_create_user(payload: dict, user=Depends(require_role(["Admin"]))) -> dict:
    db = _db()
    try:
        u = create_user(
            db=db,
            email=payload.get("email"),
            password=payload.get("password"),
            role=payload.get("role"),
            full_name=payload.get("full_name"),
        )
        return {
            "status": "ok",
            "user": {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
            },
        }
    finally:
        db.close()


# ─────────────────────────────────────────
# Students CRUD
# ─────────────────────────────────────────
@router.get("/students", summary="List students")
def admin_list_students(
    user=Depends(require_role(["Admin"])),
) -> List[dict]:
    db = _db()
    try:
        rows = db.query(StudentDB).order_by(StudentDB.id.asc()).all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "admission_no": s.admission_no,
                "grade": s.grade,
                "section": s.section,
            }
            for s in rows
        ]
    finally:
        db.close()


@router.post("/students", summary="Create student")
def admin_create_student(
    payload: dict,
    user=Depends(require_role(["Admin"])),
) -> dict:
    """
    Expected payload:
    {
      "name": "...",
      "admission_no": "...",
      "grade": "6",
      "section": "A"
    }
    """
    name = (payload.get("name") or "").strip()
    admission_no = (payload.get("admission_no") or "").strip()
    grade = (payload.get("grade") or "").strip()
    section = (payload.get("section") or "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not admission_no:
        raise HTTPException(status_code=400, detail="admission_no is required")
    if not grade:
        raise HTTPException(status_code=400, detail="grade is required")
    if not section:
        raise HTTPException(status_code=400, detail="section is required")

    db = _db()
    try:
        exists = db.query(StudentDB).filter(StudentDB.admission_no == admission_no).first()
        if exists:
            raise HTTPException(status_code=400, detail="admission_no already exists")

        s = StudentDB(name=name, admission_no=admission_no, grade=grade, section=section)
        db.add(s)
        db.commit()
        db.refresh(s)
        return {
            "status": "ok",
            "student": {
                "id": s.id,
                "name": s.name,
                "admission_no": s.admission_no,
                "grade": s.grade,
                "section": s.section,
            },
        }
    finally:
        db.close()


@router.put("/students/{student_id}", summary="Update student")
def admin_update_student(
    student_id: int,
    payload: dict,
    user=Depends(require_role(["Admin"])),
) -> dict:
    db = _db()
    try:
        s = db.query(StudentDB).filter(StudentDB.id == student_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Student not found")

        if "name" in payload:
            s.name = (payload.get("name") or "").strip() or s.name
        if "grade" in payload:
            s.grade = (payload.get("grade") or "").strip() or s.grade
        if "section" in payload:
            s.section = (payload.get("section") or "").strip() or s.section

        if "admission_no" in payload:
            new_adm = (payload.get("admission_no") or "").strip()
            if new_adm and new_adm != s.admission_no:
                exists = db.query(StudentDB).filter(StudentDB.admission_no == new_adm).first()
                if exists:
                    raise HTTPException(status_code=400, detail="admission_no already exists")
                s.admission_no = new_adm

        db.add(s)
        db.commit()
        db.refresh(s)
        return {
            "status": "ok",
            "student": {
                "id": s.id,
                "name": s.name,
                "admission_no": s.admission_no,
                "grade": s.grade,
                "section": s.section,
            },
        }
    finally:
        db.close()


@router.delete("/students/{student_id}", summary="Delete student")
def admin_delete_student(
    student_id: int,
    user=Depends(require_role(["Admin"])),
) -> dict:
    db = _db()
    try:
        s = db.query(StudentDB).filter(StudentDB.id == student_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Student not found")

        db.delete(s)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


# ─────────────────────────────────────────
# Exams CRUD
# ─────────────────────────────────────────
@router.get("/exams", summary="List exams")
def admin_list_exams(
    user=Depends(require_role(["Admin"])),
) -> List[dict]:
    db = _db()
    try:
        rows = db.query(Exam).order_by(Exam.exam_date.asc(), Exam.id.asc()).all()
        return [
            {
                "id": e.id,
                "exam_name": e.exam_name,
                "exam_date": e.exam_date.isoformat() if e.exam_date else None,
                "max_score": e.max_score,
            }
            for e in rows
        ]
    finally:
        db.close()


@router.post("/exams", summary="Create exam")
def admin_create_exam(
    payload: dict,
    user=Depends(require_role(["Admin"])),
) -> dict:
    """
    Expected payload:
    {
      "exam_name": "Mid Term",
      "exam_date": "2025-08-20",
      "max_score": 100
    }
    """
    exam_name = (payload.get("exam_name") or "").strip()
    exam_date_str = (payload.get("exam_date") or "").strip()
    max_score = payload.get("max_score", 100)

    if not exam_name:
        raise HTTPException(status_code=400, detail="exam_name is required")
    if not exam_date_str:
        raise HTTPException(status_code=400, detail="exam_date is required (YYYY-MM-DD)")

    try:
        d = date.fromisoformat(exam_date_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid exam_date (use YYYY-MM-DD)")

    try:
        max_score_int = int(float(max_score))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid max_score")

    db = _db()
    try:
        exists = db.query(Exam).filter(Exam.exam_name == exam_name, Exam.exam_date == d).first()
        if exists:
            exists.max_score = max_score_int
            db.add(exists)
            db.commit()
            db.refresh(exists)
            return {
                "status": "ok",
                "exam": {
                    "id": exists.id,
                    "exam_name": exists.exam_name,
                    "exam_date": exists.exam_date.isoformat(),
                    "max_score": exists.max_score,
                },
            }

        e = Exam(exam_name=exam_name, exam_date=d, max_score=max_score_int)
        db.add(e)
        db.commit()
        db.refresh(e)
        return {
            "status": "ok",
            "exam": {
                "id": e.id,
                "exam_name": e.exam_name,
                "exam_date": e.exam_date.isoformat(),
                "max_score": e.max_score,
            },
        }
    finally:
        db.close()


@router.delete("/exams/{exam_id}", summary="Delete exam")
def admin_delete_exam(
    exam_id: int,
    user=Depends(require_role(["Admin"])),
) -> dict:
    db = _db()
    try:
        e = db.query(Exam).filter(Exam.id == exam_id).first()
        if not e:
            raise HTTPException(status_code=404, detail="Exam not found")

        db.delete(e)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


# ─────────────────────────────────────────
# Subjects CRUD
# ─────────────────────────────────────────
@router.get("/subjects", summary="List subjects")
def admin_list_subjects(
    user=Depends(require_role(["Admin"])),
) -> List[dict]:
    db = _db()
    try:
        rows = db.query(Subject).order_by(Subject.name.asc(), Subject.id.asc()).all()
        return [{"id": s.id, "name": s.name} for s in rows]
    finally:
        db.close()


@router.post("/subjects", summary="Create subject")
def admin_create_subject(
    payload: dict,
    user=Depends(require_role(["Admin"])),
) -> dict:
    """
    Expected payload:
    {
      "name": "Maths"
    }
    """
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    db = _db()
    try:
        exists = db.query(Subject).filter(Subject.name == name).first()
        if exists:
            return {"status": "ok", "subject": {"id": exists.id, "name": exists.name}}

        s = Subject(name=name)
        db.add(s)
        db.commit()
        db.refresh(s)
        return {"status": "ok", "subject": {"id": s.id, "name": s.name}}
    finally:
        db.close()


@router.delete("/subjects/{subject_id}", summary="Delete subject")
def admin_delete_subject(
    subject_id: int,
    user=Depends(require_role(["Admin"])),
) -> dict:
    db = _db()
    try:
        s = db.query(Subject).filter(Subject.id == subject_id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Subject not found")

        db.delete(s)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


# ─────────────────────────────────────────
# Parent ↔ Student Mapping (Admin)
# ─────────────────────────────────────────
@router.get("/mappings/parent-students", summary="List parent-student links")
def admin_list_parent_student_links(user=Depends(require_role(["Admin"]))) -> list[dict]:
    db = _db()
    try:
        rows = db.query(ParentStudentDB).order_by(ParentStudentDB.id.asc()).all()
        return [{"id": r.id, "parent_user_id": r.parent_user_id, "student_id": r.student_id} for r in rows]
    finally:
        db.close()


@router.post("/mappings/parent-students", summary="Create parent-student link")
def admin_create_parent_student_link(payload: dict, user=Depends(require_role(["Admin"]))) -> dict:
    parent_user_id = payload.get("parent_user_id")
    student_id = payload.get("student_id")

    if not parent_user_id or not student_id:
        raise HTTPException(status_code=400, detail="parent_user_id and student_id are required")

    db = _db()
    try:
        parent = db.query(UserDB).filter(UserDB.id == int(parent_user_id)).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent user not found")
        if parent.role != "Parent":
            raise HTTPException(status_code=400, detail="User is not a Parent")

        student = db.query(StudentDB).filter(StudentDB.id == int(student_id)).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        exists = (
            db.query(ParentStudentDB)
            .filter(
                ParentStudentDB.parent_user_id == int(parent_user_id),
                ParentStudentDB.student_id == int(student_id),
            )
            .first()
        )
        if exists:
            return {"status": "ok", "link": {"id": exists.id, "parent_user_id": exists.parent_user_id, "student_id": exists.student_id}}

        link = ParentStudentDB(parent_user_id=int(parent_user_id), student_id=int(student_id))
        db.add(link)
        db.commit()
        db.refresh(link)
        return {"status": "ok", "link": {"id": link.id, "parent_user_id": link.parent_user_id, "student_id": link.student_id}}
    finally:
        db.close()


@router.delete("/mappings/parent-students/{link_id}", summary="Delete parent-student link")
def admin_delete_parent_student_link(link_id: int, user=Depends(require_role(["Admin"]))) -> dict:
    db = _db()
    try:
        link = db.query(ParentStudentDB).filter(ParentStudentDB.id == link_id).first()
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")
        db.delete(link)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


# ─────────────────────────────────────────
# Teacher ↔ Grade/Section Assignment (Admin)
# ─────────────────────────────────────────
@router.get("/mappings/teacher-assignments", summary="List teacher assignments")
def admin_list_teacher_assignments(user=Depends(require_role(["Admin"]))) -> list[dict]:
    db = _db()
    try:
        rows = db.query(TeacherAssignmentDB).order_by(TeacherAssignmentDB.id.asc()).all()
        return [{"id": r.id, "teacher_user_id": r.teacher_user_id, "grade": r.grade, "section": r.section} for r in rows]
    finally:
        db.close()


@router.post("/mappings/teacher-assignments", summary="Create teacher assignment")
def admin_create_teacher_assignment(payload: dict, user=Depends(require_role(["Admin"]))) -> dict:
    teacher_user_id = payload.get("teacher_user_id")
    grade = (payload.get("grade") or "").strip()
    section = (payload.get("section") or "").strip()

    if not teacher_user_id or not grade or not section:
        raise HTTPException(status_code=400, detail="teacher_user_id, grade and section are required")

    db = _db()
    try:
        teacher = db.query(UserDB).filter(UserDB.id == int(teacher_user_id)).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher user not found")
        if teacher.role != "Teacher":
            raise HTTPException(status_code=400, detail="User is not a Teacher")

        exists = (
            db.query(TeacherAssignmentDB)
            .filter(
                TeacherAssignmentDB.teacher_user_id == int(teacher_user_id),
                TeacherAssignmentDB.grade == grade,
                TeacherAssignmentDB.section == section,
            )
            .first()
        )
        if exists:
            return {"status": "ok", "assignment": {"id": exists.id, "teacher_user_id": exists.teacher_user_id, "grade": exists.grade, "section": exists.section}}

        a = TeacherAssignmentDB(teacher_user_id=int(teacher_user_id), grade=grade, section=section)
        db.add(a)
        db.commit()
        db.refresh(a)
        return {"status": "ok", "assignment": {"id": a.id, "teacher_user_id": a.teacher_user_id, "grade": a.grade, "section": a.section}}
    finally:
        db.close()


@router.delete("/mappings/teacher-assignments/{assignment_id}", summary="Delete teacher assignment")
def admin_delete_teacher_assignment(assignment_id: int, user=Depends(require_role(["Admin"]))) -> dict:
    db = _db()
    try:
        a = db.query(TeacherAssignmentDB).filter(TeacherAssignmentDB.id == assignment_id).first()
        if not a:
            raise HTTPException(status_code=404, detail="Assignment not found")
        db.delete(a)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()
