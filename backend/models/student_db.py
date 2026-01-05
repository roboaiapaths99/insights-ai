from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from db.base import Base

class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    admission_no = Column(String, nullable=False)
    grade = Column(String, nullable=False)
    section = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("admission_no", name="uq_students_admission_no"),
    )

    marks = relationship("Mark", back_populates="student", cascade="all, delete-orphan")
