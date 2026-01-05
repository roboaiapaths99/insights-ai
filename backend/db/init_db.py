from db.base import Base
from db.session import engine

# Import ALL models so SQLAlchemy registry is complete
from models.student_db import StudentDB
from models.subject import Subject
from models.exam import Exam
from models.marks import Mark  # noqa: F401
from models.student_db import StudentDB
from models.user_db import UserDB
from models.parent_student_db import ParentStudentDB
from models.teacher_assignment_db import TeacherAssignmentDB


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
