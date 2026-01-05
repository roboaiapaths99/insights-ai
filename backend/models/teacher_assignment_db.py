from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from db.base import Base

class TeacherAssignmentDB(Base):
    __tablename__ = "teacher_assignments"

    id = Column(Integer, primary_key=True, index=True)

    teacher_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    grade = Column(String, nullable=False, index=True)
    section = Column(String, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("teacher_user_id", "grade", "section", name="uq_teacher_assignment"),
    )
