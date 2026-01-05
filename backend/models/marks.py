from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.base import Base

class Mark(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True)

    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    marks_obtained = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", "subject_id", name="uq_marks_exam_student_subject"),
    )

    exam = relationship("Exam", back_populates="marks")
    student = relationship("StudentDB", back_populates="marks")
    subject = relationship("Subject", back_populates="marks")
