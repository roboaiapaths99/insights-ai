from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, func
from db.base import Base


class TeacherFeedback(Base):
    __tablename__ = "teacher_feedback"

    id = Column(Integer, primary_key=True, index=True)

    # NEW: who wrote the feedback (NULL for legacy rows)
    teacher_user_id = Column(Integer, index=True, nullable=True)

    student_id = Column(Integer, index=True, nullable=False)
    exam_id = Column(Integer, index=True, nullable=False)

    remark = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "student_id", "exam_id", "teacher_user_id",
            name="uq_teacher_feedback_student_exam_teacher"
        ),
    )
