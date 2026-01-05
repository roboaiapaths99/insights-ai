from sqlalchemy import Column, Integer, String
from db.base import Base

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)

    # "Parent" | "Teacher" | "Admin"
    role = Column(String, nullable=False, index=True)
