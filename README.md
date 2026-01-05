academics_insights/
│
├── backend/
│   ├── app.py                          # FastAPI entry point (creates app, includes routers)
│   ├── requirements.txt
│
│   ├── api/                            # 🌐 API ROUTERS (ROLE-BASED)
│   │   ├── __init__.py
│   │   ├── students.py                 # student CRUD / list for UI
│   │   ├── dashboard.py                # legacy dashboard endpoints
│   │   ├── parent_dashboard.py         # parent dashboard analytics endpoints
│   │   ├── insights.py                 # AI insights endpoint (LLM summary)
│   │   ├── teacher_upload.py           # CSV upload + recent uploads + template
│   │   ├── teacher.py                  # teacher endpoints (class-marks, student-exam-marks)
│   │   ├── teacher_feedback.py         # ✅ NEW: save/get feedback (remark + note)
│   │   └── admin.py                    # admin endpoints (students/exams/subjects)
│   │
│   ├── core/
│   │   ├── config.py                   # env settings (OPENAI_API_KEY, OPENAI_MODEL, DB_URL)
│   │   └── db.py                       # (optional legacy) keep if still referenced
│   │
│   ├── db/
│   │   ├── base.py                     # SQLAlchemy Base
│   │   ├── session.py                  # SessionLocal + engine
│   │   ├── init_db.py                  # create tables
│   │   └── migrations/                 # ✅ optional future (Alembic) 
│   │
│   ├── models/
│   │   ├── student.py                  # Student table
│   │   ├── exam.py                     # ✅ NEW/SEPARATE: Exam table (if you have it in repo)
│   │   ├── marks.py                    # ✅ NEW/SEPARATE: Marks table (student_id, exam_id, subject, score)
│   │   ├── assessment.py               # legacy / analytics (if still used)
│   │   └── teacher_feedback.py         # ✅ NEW: remark + note per (student_id, exam_id)
│   │
│   ├── repositories/
│   │   ├── students_repo.py
│   │   ├── exams_repo.py
│   │   ├── marks_repo.py
│   │   └── teacher_feedback_repo.py    # ✅ NEW: upsert/get feedback
│   │
│   ├── schemas/
│   │   ├── student.py
│   │   ├── exam.py
│   │   ├── marks.py
│   │   ├── analytics.py
│   │   └── teacher_feedback.py         # ✅ NEW: request/response models
│   │
│   ├── services/
│   │   ├── analytics_service.py        # core student/class analytics
│   │   ├── llm_service.py              # ✅ improved: crisp + patterns + teacher feedback injection
│   │   ├── teacher_feedback_service.py # ✅ NEW: fetch feedback for exam+student (optional layer)
│   │   ├── marks_store.py              # demo JSON-based marks storage (optional/legacy)
│   │   └── data_store.py               # helper / transitional storage (optional/legacy)
│   │
│   ├── demo_data/
│   │   └── class_6A.json               # demo dataset
│   │
│   └── bac_env/                        # backend venv (local) (optional; not in git)
│
├── frontend/
│   ├── streamlit_app.py                # Parent + Teacher UI (main)
│   ├── pages/                          # future pages
│   ├── requirements.txt
│   ├── .streamlit/
│   └── fro_env/                        # frontend venv (local) (optional; not in git)
│
├── .env
├── README.md
└── run_dev.bat
