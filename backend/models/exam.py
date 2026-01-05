from sqlalchemy import Column, Integer, String, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from db.base import Base

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String, index=True, nullable=False)
    exam_date = Column(Date, index=True, nullable=False)
    max_score = Column(Integer, nullable=False, default=100)

    __table_args__ = (
        UniqueConstraint("exam_name", "exam_date", name="uq_exam_name_date"),
    )

    marks = relationship("Mark", back_populates="exam", cascade="all, delete-orphan")
