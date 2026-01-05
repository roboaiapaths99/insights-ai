from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.exam import Exam
from models.marks import Mark
from models.subject import Subject
from models.student_db import StudentDB


def load_uploaded_marks() -> List[Dict[str, Any]]:
    """
    Keeps the SAME output structure as the old JSON store.
    This is consumed by analytics_service._apply_uploaded_marks_once().
    """
    db: Session = SessionLocal()
    try:
        try:
            rows = (
                db.query(Mark, Exam, Subject, StudentDB)
                .join(Exam, Mark.exam_id == Exam.id)
                .join(Subject, Mark.subject_id == Subject.id)
                .join(StudentDB, Mark.student_id == StudentDB.id)
                .all()
            )
        except OperationalError:
            # Tables not created yet
            return []

        out_map: Dict[tuple, Dict[str, Any]] = {}

        for m, e, sub, stu in rows:
            key = (
                stu.admission_no,
                e.exam_name,
                e.exam_date.isoformat(),
                e.max_score,
            )

            if key not in out_map:
                out_map[key] = {
                    "admission_no": stu.admission_no,
                    "exam_name": e.exam_name,
                    "exam_date": e.exam_date.isoformat(),
                    "max_score": e.max_score,
                    "scores": {},
                }

            # subject_name -> marks_obtained
            out_map[key]["scores"][sub.name] = m.marks_obtained

        return list(out_map.values())

    finally:
        db.close()


def save_uploaded_marks(rows: List[Dict[str, Any]]) -> None:
    """
    Takes the SAME input structure as before and upserts into DB.

    IMPORTANT (Option A):
    - Subjects must already exist in DB (admin-managed).
    - If a subject name is not found, we SKIP it (teacher_upload should reject earlier anyway).
    """
    db: Session = SessionLocal()
    try:
        for r in rows:
            admission_no = r["admission_no"]
            exam_name = r["exam_name"]
            exam_date_str = r["exam_date"]
            max_score = int(r.get("max_score", 100))
            scores = r.get("scores", {}) or {}

            exam_date = date.fromisoformat(exam_date_str)

            # Resolve student
            student = (
                db.query(StudentDB)
                .filter(StudentDB.admission_no == admission_no)
                .first()
            )
            if not student:
                # Skip unknown students
                continue

            # Upsert exam (unique by exam_name + exam_date)
            exam = (
                db.query(Exam)
                .filter(Exam.exam_name == exam_name, Exam.exam_date == exam_date)
                .first()
            )
            if not exam:
                exam = Exam(
                    exam_name=exam_name,
                    exam_date=exam_date,
                    max_score=max_score,
                )
                db.add(exam)
                db.flush()
            else:
                exam.max_score = max_score
                db.add(exam)
                db.flush()

            # Upsert marks (unique by exam_id + student_id + subject_id)
            for subject_name, score in scores.items():
                score_val = float(score)

                # ✅ Option A: Subject must already exist (admin-managed)
                subject = (
                    db.query(Subject)
                    .filter(Subject.name == subject_name)
                    .first()
                )
                if not subject:
                    # Teacher upload should have rejected earlier;
                    # keep safe behavior here (skip) to avoid crashing.
                    continue

                mark = (
                    db.query(Mark)
                    .filter(
                        Mark.exam_id == exam.id,
                        Mark.student_id == student.id,
                        Mark.subject_id == subject.id,
                    )
                    .first()
                )

                if not mark:
                    mark = Mark(
                        exam_id=exam.id,
                        student_id=student.id,
                        subject_id=subject.id,
                        marks_obtained=score_val,
                        max_marks=max_score,
                    )
                else:
                    mark.marks_obtained = score_val
                    mark.max_marks = max_score

                db.add(mark)

        db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
