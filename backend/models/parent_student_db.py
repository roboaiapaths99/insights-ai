from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from db.base import Base

class ParentStudentDB(Base):
    __tablename__ = "parent_students"

    id = Column(Integer, primary_key=True, index=True)

    parent_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("parent_user_id", "student_id", name="uq_parent_student"),
    )
