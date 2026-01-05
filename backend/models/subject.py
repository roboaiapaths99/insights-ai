from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from db.base import Base

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint("name", name="uq_subjects_name"),
    )

    marks = relationship("Mark", back_populates="subject", cascade="all, delete-orphan")
