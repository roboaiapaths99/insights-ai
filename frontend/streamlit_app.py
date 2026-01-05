import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Academic Insights",
    page_icon="📘",
    layout="wide",
)

# ─────────────────────────────────────────
# THEME CONFIG (LIGHT ONLY)
# ─────────────────────────────────────────
THEMES = {
    "Light": {
        "bg": "#ffffff",
        "text": "#222222",
        "muted_text": "#555555",
        "accent": "#2196f3",
        "accent_soft": "rgba(33,150,243,0.06)",
        "pill_border": "#ff9800",
        "pill_text": "#ff9800",
        "card_border": "rgba(0,0,0,0.08)",
        "card_bg": "rgba(0,0,0,0.02)",
        "footer_text": "#888888",
    }
}

st.sidebar.title("School View")

# Removed Dark theme toggle (Light only)
st.session_state["theme"] = "Light"
theme_choice = "Light"
theme = THEMES[theme_choice]

# ─────────────────────────────────────────
# AUTH (Streamlit Login + JWT)
# ─────────────────────────────────────────
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None

def _auth_headers() -> dict:
    tok = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

# Keep raw requests methods for /health + for internal use
_RAW_GET = requests.get
_RAW_POST = requests.post
_RAW_PUT = requests.put
_RAW_DELETE = requests.delete

def _merge_headers(existing: dict | None) -> dict:
    base = _auth_headers()
    if not existing:
        return base
    merged = dict(existing)
    # Don't overwrite caller's Authorization if they explicitly set it
    if "Authorization" not in merged and "authorization" not in {k.lower() for k in merged.keys()}:
        merged.update(base)
    else:
        # still allow other default headers if any
        for k, v in base.items():
            if k not in merged:
                merged[k] = v
    return merged

# Monkey-patch requests so ALL existing calls automatically include JWT header.
def _patched_get(url, **kwargs):
    kwargs["headers"] = _merge_headers(kwargs.get("headers"))
    return _RAW_GET(url, **kwargs)

def _patched_post(url, **kwargs):
    kwargs["headers"] = _merge_headers(kwargs.get("headers"))
    return _RAW_POST(url, **kwargs)

def _patched_put(url, **kwargs):
    kwargs["headers"] = _merge_headers(kwargs.get("headers"))
    return _RAW_PUT(url, **kwargs)

def _patched_delete(url, **kwargs):
    kwargs["headers"] = _merge_headers(kwargs.get("headers"))
    return _RAW_DELETE(url, **kwargs)

requests.get = _patched_get
requests.post = _patched_post
requests.put = _patched_put
requests.delete = _patched_delete

def _load_me() -> dict:
    tok = st.session_state.get("access_token")
    if not tok:
        return {}
    try:
        me_r = _RAW_GET(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {tok}"},
            timeout=20,
        )
        if me_r.ok:
            return me_r.json() or {}
        return {}
    except Exception:
        return {}

# Sidebar login/logout
with st.sidebar:
    if st.session_state["access_token"]:
        # ✅ Ensure /auth/me is loaded (role + mappings) after refresh
        if not st.session_state.get("auth_user") or not isinstance(st.session_state.get("auth_user"), dict):
            st.session_state["auth_user"] = _load_me() or st.session_state.get("auth_user") or {}

        u = st.session_state.get("auth_user") or {}
        st.success(f"Logged in: {u.get('email', 'user')}")
        st.caption(f"Role: {u.get('role', '—')}")
        if st.button("Logout"):
            st.session_state["access_token"] = None
            st.session_state["auth_user"] = None
            st.rerun()
    else:
        st.markdown("### 🔐 Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", type="primary"):
            try:
                r = _RAW_POST(
                    f"{API_BASE}/auth/login",
                    json={"email": email, "password": password},
                    timeout=20,
                )
                r.raise_for_status()
                data = r.json() or {}
                st.session_state["access_token"] = data.get("access_token") or data.get("token")

                # ✅ Always prefer /auth/me for role + mappings
                me = _load_me()
                st.session_state["auth_user"] = me or data.get("user") or {
                    "email": data.get("email") or email,
                    "role": data.get("role"),
                }

                if not st.session_state["access_token"]:
                    st.error("Login succeeded but token missing in response.")
                else:
                    st.rerun()
            except Exception as e:
                st.error("Login failed.")
                st.text(str(e))

# Require login
if not st.session_state["access_token"]:
    st.info("Please login to continue.")
    st.stop()

# ✅ Ensure /auth/me is loaded (role + mappings) before routing
if not st.session_state.get("auth_user") or not isinstance(st.session_state.get("auth_user"), dict):
    st.session_state["auth_user"] = _load_me() or st.session_state.get("auth_user") or {}

# Role comes from backend
role = (st.session_state.get("auth_user") or {}).get("role") or "Parent"

# ─────────────────────────────────────────
# Backend health check (REQUIRED: prevents crash when API is down)
# ─────────────────────────────────────────
def _api_is_up() -> bool:
    try:
        r = _RAW_GET(f"{API_BASE}/health", timeout=3)
        return r.ok
    except Exception:
        return False


if not _api_is_up():
    st.error(
        "Backend API is not reachable.\n\n"
        "✅ Start backend first:\n"
        "`uvicorn app:app --reload --host 127.0.0.1 --port 8000`\n\n"
        f"Current API_BASE: {API_BASE}"
    )
    st.stop()

# ─────────────────────────────────────────
# TOP HEADER / BRANDING
# ─────────────────────────────────────────
st.markdown(
    f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
        <div>
            <h1 style="margin-bottom:0;color:{theme["text"]};">📘 Academic Insights</h1>
            <p style="margin-top:0.35rem;margin-bottom:0;color:{theme["muted_text"]};">
                A simple view of your child’s progress across subjects &amp; exams.
            </p>
        </div>
        <div style="
            padding:4px 12px;
            border-radius:999px;
            border:1px solid {theme["pill_border"]};
            font-size:0.8rem;
            color:{theme["pill_text"]};
            font-weight:500;
        ">
            Latest Exam · DB + Upload Ready
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────
# Admin Screen (MERGED: best of both) + SUBJECTS (REQUIRED)
# ─────────────────────────────────────────
if role == "Admin":
    import pandas as pd
    from datetime import date as _date

    st.subheader("🛠️ Admin Panel (MVP)")
    st.caption("Create students, exams, subjects, users, and mappings (demo admin).")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👩‍🎓 Students", "📝 Exams", "📚 Subjects", "👤 Users", "🔗 Mappings"])

    # -------------------------
    # Helpers
    # -------------------------
    def _err_text(resp: requests.Response) -> str:
        try:
            payload = resp.json()
            if isinstance(payload, dict):
                return payload.get("detail") or payload.get("message") or resp.text
            return resp.text
        except Exception:
            return resp.text

    def _api_get(path: str):
        r = requests.get(f"{API_BASE}{path}", timeout=20)
        r.raise_for_status()
        return r.json()

    def _api_post(path: str, payload: dict):
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=20)
        if not r.ok:
            raise RuntimeError(_err_text(r))
        return r.json()

    def _api_put(path: str, payload: dict):
        r = requests.put(f"{API_BASE}{path}", json=payload, timeout=20)
        if not r.ok:
            raise RuntimeError(_err_text(r))
        return r.json()

    def _api_delete(path: str):
        r = requests.delete(f"{API_BASE}{path}", timeout=20)
        if not r.ok:
            raise RuntimeError(_err_text(r))
        try:
            return r.json()
        except Exception:
            return {"status": "ok"}

    # -------------------------
    # Students
    # -------------------------
    with tab1:
        st.subheader("Create Student")

        c1, c2, c3, c4 = st.columns(4)
        name = c1.text_input("Name")
        admission_no = c2.text_input("Admission No")
        grade = c3.text_input("Grade", value="6")
        section = c4.text_input("Section", value="A")

        if st.button("➕ Add Student", type="primary"):
            try:
                _api_post(
                    "/admin/students",
                    {
                        "name": name,
                        "admission_no": admission_no,
                        "grade": grade,
                        "section": section,
                    },
                )
                st.success("Student added ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

        st.markdown("---")
        st.subheader("Students List")

        try:
            rows = _api_get("/admin/students")
            df_students = pd.DataFrame(rows or [])
            if df_students.empty:
                st.info("No students found.")
            else:
                st.dataframe(df_students, width="stretch", hide_index=True)
        except Exception as e:
            st.error(f"Could not load students: {e}")
            rows = []

        st.markdown("---")
        st.subheader("Update / Delete Student")

        if rows:
            options = {
                f'#{s["id"]} · {s.get("name","—")} (Grade {s.get("grade","—")}{s.get("section","")})': s
                for s in rows
            }
            selected_label = st.selectbox("Select student", list(options.keys()))
            selected = options[selected_label]

            u1, u2 = st.columns([2, 1])

            with u1:
                st.markdown("**Edit Student**")
                with st.form("admin_update_student_form"):
                    u_name = st.text_input("Name", value=selected.get("name") or "")
                    u_adm = st.text_input("Admission No", value=selected.get("admission_no") or "")
                    u_grade = st.text_input("Grade", value=selected.get("grade") or "")
                    u_section = st.text_input("Section", value=selected.get("section") or "")

                    upd = st.form_submit_button("Update Student")
                    if upd:
                        try:
                            _api_put(
                                f"/admin/students/{selected['id']}",
                                {
                                    "name": u_name,
                                    "admission_no": u_adm,
                                    "grade": u_grade,
                                    "section": u_section,
                                },
                            )
                            st.success("Student updated ✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")

            with u2:
                st.markdown("**Delete Student**")
                st.warning("This will permanently delete the student.")
                if st.button("🗑️ Delete Student", type="secondary"):
                    try:
                        _api_delete(f"/admin/students/{selected['id']}")
                        st.success("Student deleted ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
        else:
            st.info("No students available yet to update/delete.")

    # -------------------------
    # Exams
    # -------------------------
    with tab2:
        st.subheader("Create Exam")

        c1, c2, c3 = st.columns(3)
        exam_name = c1.text_input("Exam Name", value="Final")
        exam_date = c2.date_input("Exam Date", value=_date.today())
        max_score = c3.number_input("Max Score", min_value=1, value=100, step=1)

        if st.button("➕ Add Exam", type="primary"):
            try:
                _api_post(
                    "/admin/exams",
                    {
                        "exam_name": exam_name,
                        "exam_date": exam_date.isoformat(),
                        "max_score": int(max_score),
                    },
                )
                st.success("Exam added (or updated) ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

        st.markdown("---")
        st.subheader("Exams List")

        try:
            rows = _api_get("/admin/exams")
            df_exams = pd.DataFrame(rows or [])
            if df_exams.empty:
                st.info("No exams found.")
            else:
                st.dataframe(df_exams, width="stretch", hide_index=True)
        except Exception as e:
            st.error(f"Could not load exams: {e}")
            rows = []

        st.markdown("---")
        st.subheader("Delete Exam")

        if rows:
            ex_options = {
                f'#{e["id"]} · {e.get("exam_name","—")} ({e.get("exam_date","—")})': e
                for e in rows
            }
            ex_label = st.selectbox("Select exam", list(ex_options.keys()))
            ex = ex_options[ex_label]

            st.warning("Deleting an exam may affect dashboards if marks are linked to it.")
            if st.button("🗑️ Delete Exam", type="secondary"):
                try:
                    _api_delete(f"/admin/exams/{ex['id']}")
                    st.success("Exam deleted ✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
        else:
            st.info("No exams available yet to delete.")

    # -------------------------
    # Subjects (REQUIRED)
    # -------------------------
    with tab3:
        st.subheader("Create Subject")

        c1, c2 = st.columns([2, 1])
        subject_name = c1.text_input("Subject Name", value="")
        add_subject = c2.button("➕ Add Subject", type="primary")

        if add_subject:
            try:
                _api_post("/admin/subjects", {"name": subject_name})
                st.success("Subject added ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

        st.markdown("---")
        st.subheader("Subjects List")

        try:
            rows = _api_get("/admin/subjects")
            df_sub = pd.DataFrame(rows or [])
            if df_sub.empty:
                st.info("No subjects found.")
            else:
                st.dataframe(df_sub, width="stretch", hide_index=True)
        except Exception as e:
            st.info("Subjects API not available yet. Add backend endpoints: GET/POST/DELETE /admin/subjects")
            rows = []

        st.markdown("---")
        st.subheader("Delete Subject")

        if rows:
            sub_options = {f'#{s["id"]} · {s.get("name","—")}': s for s in rows}
            sub_label = st.selectbox("Select subject", list(sub_options.keys()))
            sub = sub_options[sub_label]

            st.warning("Deleting a subject may affect marks linked to it.")
            if st.button("🗑️ Delete Subject", type="secondary"):
                try:
                    _api_delete(f"/admin/subjects/{sub['id']}")
                    st.success("Subject deleted ✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
        else:
            st.info("No subjects available yet to delete.")

    # -------------------------
    # Users (NEW: Create Parent/Teacher/Admin users from UI)
    # -------------------------
    with tab4:
        st.subheader("Users (Create Parent/Teacher/Admin)")
        st.caption("Create login accounts so mappings can be assigned from the UI (no Swagger needed).")

        with st.form("admin_create_user_form"):
            c1, c2 = st.columns(2)
            u_email = c1.text_input("Email", value="")
            u_full_name = c2.text_input("Full Name (optional)", value="")

            c3, c4 = st.columns(2)
            u_password = c3.text_input("Password", value="", type="password")
            u_role = c4.selectbox("Role", ["Parent", "Teacher", "Admin"], index=0)

            submitted = st.form_submit_button("➕ Create User")
            if submitted:
                try:
                    _api_post(
                        "/admin/users",
                        {
                            "email": u_email,
                            "password": u_password,
                            "full_name": u_full_name,
                            "role": u_role,
                        },
                    )
                    st.success("User created ✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

        st.markdown("---")
        st.subheader("Users List")

        try:
            rows = _api_get("/admin/users")
            df_users = pd.DataFrame(rows or [])
            if df_users.empty:
                st.info("No users found.")
            else:
                st.dataframe(df_users, width="stretch", hide_index=True)
        except Exception as e:
            st.error(f"Could not load users: {e}")

    # -------------------------
    # Mappings (REQUIRED: Parent ↔ Student, Teacher ↔ Grade/Section)
    # -------------------------
    with tab5:
        st.subheader("Mappings (Assignments)")
        st.caption("Assign children to parents and classes to teachers. This enables ownership enforcement.")

        subtab1, subtab2 = st.tabs(["👨‍👩‍👧 Parent ↔ Student", "👩‍🏫 Teacher ↔ Grade/Section"])

        # Shared data
        try:
            _students = _api_get("/admin/students") or []
        except Exception:
            _students = []

        # -------------------------
        # Parent ↔ Student
        # -------------------------
        with subtab1:
            st.markdown("#### Assign Student to Parent")

            parents = []
            try:
                parents = _api_get("/admin/users/parents") or []
            except Exception:
                try:
                    parents = _api_get("/admin/users?role=Parent") or []
                except Exception:
                    parents = []

            if not parents:
                st.info("No Parent users found. Create Parent users first.")
            elif not _students:
                st.info("No students found. Create students first.")
            else:
                p_opts = {f'#{p.get("id")} · {p.get("email","—")}': p for p in parents}
                s_opts = {f'#{s.get("id")} · {s.get("name","—")} (Grade {s.get("grade","—")}{s.get("section","")})': s for s in _students}

                c1, c2, c3 = st.columns([2, 2, 1])
                p_label = c1.selectbox("Parent", list(p_opts.keys()))
                s_label = c2.selectbox("Student", list(s_opts.keys()))
                if c3.button("Assign", type="primary"):
                    try:
                        _api_post(
                            "/admin/mappings/parent-students",
                            {"parent_user_id": int(p_opts[p_label]["id"]), "student_id": int(s_opts[s_label]["id"])},
                        )
                        st.success("Assigned ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")

            st.markdown("---")
            st.markdown("#### Current Parent ↔ Student Links")

            try:
                links = _api_get("/admin/mappings/parent-students") or []
            except Exception as e:
                st.error(f"Could not load links: {e}")
                links = []

            if links:
                df_links = pd.DataFrame(links)

                try:
                    parents_map = {int(p.get("id")): p for p in (parents or []) if p.get("id") is not None}
                except Exception:
                    parents_map = {}

                students_map = {int(s.get("id")): s for s in (_students or []) if s.get("id") is not None}

                def _p_name(pid):
                    p = parents_map.get(int(pid)) if pid is not None else None
                    return p.get("email") if isinstance(p, dict) else None

                def _s_name(sid):
                    s = students_map.get(int(sid)) if sid is not None else None
                    if isinstance(s, dict):
                        return f'{s.get("name","—")} (Grade {s.get("grade","—")}{s.get("section","")})'
                    return None

                if "parent_user_id" in df_links.columns:
                    df_links["parent"] = df_links["parent_user_id"].apply(_p_name)
                if "student_id" in df_links.columns:
                    df_links["student"] = df_links["student_id"].apply(_s_name)

                show_cols = [c for c in ["id", "parent_user_id", "parent", "student_id", "student"] if c in df_links.columns]
                st.dataframe(df_links[show_cols] if show_cols else df_links, width="stretch", hide_index=True)

                st.markdown("##### Delete Link")
                link_opts = {f'#{r.get("id")} · Parent {r.get("parent_user_id")} → Student {r.get("student_id")}': r for r in links}
                del_label = st.selectbox("Select link", list(link_opts.keys()))
                if st.button("Delete Link", type="secondary"):
                    try:
                        _api_delete(f"/admin/mappings/parent-students/{int(link_opts[del_label]['id'])}")
                        st.success("Deleted ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            else:
                st.info("No parent-student links yet.")

        # -------------------------
        # Teacher ↔ Grade/Section
        # -------------------------
        with subtab2:
            st.markdown("#### Assign Grade/Section to Teacher")

            teachers = []
            try:
                teachers = _api_get("/admin/users/teachers") or []
            except Exception:
                try:
                    teachers = _api_get("/admin/users?role=Teacher") or []
                except Exception:
                    teachers = []

            grades = sorted({str(s.get("grade", "")).strip() for s in (_students or []) if str(s.get("grade", "")).strip()})
            sections = sorted({str(s.get("section", "")).strip() for s in (_students or []) if str(s.get("section", "")).strip()})

            if not teachers:
                st.info("No Teacher users found. Create Teacher users first.")
            else:
                t_opts = {f'#{t.get("id")} · {t.get("email","—")}': t for t in teachers}

                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                t_label = c1.selectbox("Teacher", list(t_opts.keys()))
                sel_grade = c2.selectbox("Grade", grades if grades else ["6"], index=0)
                sel_section = c3.selectbox("Section", sections if sections else ["A"], index=0)
                if c4.button("Assign", type="primary", key="assign_teacher_class"):
                    try:
                        _api_post(
                            "/admin/mappings/teacher-assignments",
                            {
                                "teacher_user_id": int(t_opts[t_label]["id"]),
                                "grade": str(sel_grade).strip(),
                                "section": str(sel_section).strip(),
                            },
                        )
                        st.success("Assigned ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")

            st.markdown("---")
            st.markdown("#### Current Teacher Assignments")

            try:
                assigns = _api_get("/admin/mappings/teacher-assignments") or []
            except Exception as e:
                st.error(f"Could not load assignments: {e}")
                assigns = []

            if assigns:
                df_a = pd.DataFrame(assigns)

                try:
                    teachers_map = {int(t.get("id")): t for t in (teachers or []) if t.get("id") is not None}
                except Exception:
                    teachers_map = {}

                def _t_name(tid):
                    t = teachers_map.get(int(tid)) if tid is not None else None
                    return t.get("email") if isinstance(t, dict) else None

                if "teacher_user_id" in df_a.columns:
                    df_a["teacher"] = df_a["teacher_user_id"].apply(_t_name)

                show_cols = [c for c in ["id", "teacher_user_id", "teacher", "grade", "section"] if c in df_a.columns]
                st.dataframe(df_a[show_cols] if show_cols else df_a, width="stretch", hide_index=True)

                st.markdown("##### Delete Assignment")
                a_opts = {f'#{r.get("id")} · Teacher {r.get("teacher_user_id")} → {r.get("grade")}{r.get("section")}': r for r in assigns}
                a_label = st.selectbox("Select assignment", list(a_opts.keys()), key="del_assign_select")
                if st.button("Delete Assignment", type="secondary", key="del_assign_btn"):
                    try:
                        _api_delete(f"/admin/mappings/teacher-assignments/{int(a_opts[a_label]['id'])}")
                        st.success("Deleted ✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            else:
                st.info("No teacher assignments yet.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="text-align:center;font-size:0.8rem;color:{theme["footer_text"]};margin-top:2rem;">
            Powered by <strong>RoboAIAPaths</strong> · Academic Insights MVP<br/>
            Built with FastAPI + Streamlit for school-ready dashboards.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# ─────────────────────────────────────────
# Teacher Upload Screen (UPDATED: uses /teacher/class-marks)
# ─────────────────────────────────────────
if role == "Teacher":
    import pandas as pd
    import io  # ✅ REQUIRED (used below for CSV conversion)

    st.subheader("👩‍🏫 Teacher – Upload Marks (CSV)")
    st.caption("Upload marks for a class exam. This updates the data used by the parent dashboard.")

    # Recent uploads
    st.markdown("### 📌 Recently Uploaded Exams")
    recent_items = []
    try:
        # ✅ FIX: include auth headers
        r = requests.get(f"{API_BASE}/teacher/recent-uploads", headers=_auth_headers(), timeout=20)
        if r.ok:
            recent_items = (r.json() or {}).get("items", [])
            if recent_items:
                df_recent = pd.DataFrame(recent_items)
                st.dataframe(df_recent, width="stretch", hide_index=True)
            else:
                st.info("No uploads yet.")
        else:
            st.info("Could not load recent uploads.")
    except Exception:
        st.info("Could not load recent uploads.")

    st.markdown("---")

    # ✅ REQUIRED: Teacher Marks Table (DB-backed)
    st.markdown("### 📋 Class Marks Table (DB – Pivoted Subject-wise)")
    st.caption("Select grade/section/exam to view the current class marks table.")

    try:
        # Students (for grade/section filters)
        # ✅ FIX: Teacher should NOT call /admin/students → use /students
        # ✅ FIX: include auth headers
        students_r = requests.get(f"{API_BASE}/students", headers=_auth_headers(), timeout=20)
        students_r.raise_for_status()
        admin_students = students_r.json() or []

        # ✅ REQUIRED FIX: support {"items":[...]} shape too
        if isinstance(admin_students, dict):
            admin_students = admin_students.get("items") or admin_students.get("rows") or admin_students.get("data") or []

        if not admin_students:
            st.info("No students in DB yet. Admin must add students first.")
        else:
            df_students = pd.DataFrame(admin_students)

            grades = sorted({str(x).strip() for x in df_students["grade"].astype(str).tolist() if str(x).strip()})
            sections = sorted({str(x).strip() for x in df_students["section"].astype(str).tolist() if str(x).strip()})

            # Exams list from recent uploads (fallback: unique exam_name from recent_items)
            exam_names = []
            for it in recent_items or []:
                nm = str(it.get("exam_name") or "").strip()
                if nm:
                    exam_names.append(nm)
            exam_names = list(dict.fromkeys(exam_names))  # unique keep order
            if not exam_names:
                exam_names = ["Final"]

            c1, c2, c3 = st.columns(3)
            sel_grade = c1.selectbox("Grade", grades, index=0 if grades else 0)
            sel_section = c2.selectbox("Section", sections, index=0 if sections else 0)
            sel_exam = c3.selectbox("Exam", exam_names, index=0)

            # ✅ Call backend class-marks endpoint
            params = {"grade": sel_grade, "section": sel_section, "exam_name": sel_exam}
            # ✅ FIX: include auth headers
            cm_r = requests.get(f"{API_BASE}/teacher/class-marks", params=params, headers=_auth_headers(), timeout=30)

            if not cm_r.ok:
                st.info("Class marks endpoint returned an error.")
                st.text(cm_r.text)
            else:
                payload = cm_r.json()

                # Accept either:
                # - list[rows]
                # - {"items": [...], "subjects": [...]} etc.
                if isinstance(payload, list):
                    items = payload
                    subjects = []
                elif isinstance(payload, dict):
                    items = payload.get("items") or payload.get("rows") or payload.get("data") or []
                    subjects = payload.get("subjects") or []
                else:
                    items = []
                    subjects = []

                if not items:
                    st.info("No marks found for this grade/section/exam yet. Upload marks CSV first.")
                else:
                    df = pd.DataFrame(items)

                    # If backend didn't include subjects list, infer subject columns
                    meta_cols = {
                        "admission_no", "student_id",
                        "student_name", "name",
                        "grade", "section",
                        "exam_name", "exam_id", "exam_date",
                        "max_score", "total", "percentage",
                    }
                    if not subjects:
                        subjects = [c for c in df.columns if c not in meta_cols]

                    # Compute total/percentage if missing
                    if "total" not in df.columns:
                        safe_subjects = [c for c in subjects if c in df.columns]
                        if safe_subjects:
                            df["total"] = df[safe_subjects].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
                    if "percentage" not in df.columns:
                        safe_subjects = [c for c in subjects if c in df.columns]
                        if safe_subjects and "max_score" in df.columns:
                            max_per_row = pd.to_numeric(df["max_score"], errors="coerce").fillna(0)
                            denom = (max_per_row * len(safe_subjects)).replace(0, pd.NA)
                            df["percentage"] = (df["total"] / denom) * 100
                            df["percentage"] = df["percentage"].fillna(0).round(2)

                    # Arrange columns nicely
                    ordered = []
                    for c in ["admission_no", "student_id", "student_name", "name", "grade", "section", "exam_name", "exam_id", "exam_date"]:
                        if c in df.columns:
                            ordered.append(c)
                    for c in subjects:
                        if c in df.columns and c not in ordered:
                            ordered.append(c)
                    for c in ["max_score", "total", "percentage"]:
                        if c in df.columns and c not in ordered:
                            ordered.append(c)

                    # ─────────────────────────────────────────
                    # ✅ Teacher Feedback (persist + reload)
                    # - Shows 2 columns in table: teacher_remark + special_note
                    # - Saves to backend: POST /teacher/feedback
                    # - Loads on selection: GET /teacher/feedback
                    #
                    # ✅ REQUIRED FIX (so it shows in table always):
                    # Load feedback for all students in current table and fill df columns BEFORE rendering.
                    # ─────────────────────────────────────────
                    if "teacher_remark" not in df.columns:
                        df["teacher_remark"] = ""
                    if "special_note" not in df.columns:
                        df["special_note"] = ""

                    # add feedback cols to ordered display
                    if "teacher_remark" not in ordered:
                        ordered.append("teacher_remark")
                    if "special_note" not in ordered:
                        ordered.append("special_note")

                    # Build admission_no -> student_id map (from /students list)
                    adm_to_student_id = {}
                    try:
                        for s in (admin_students or []):
                            s = s or {}
                            adm = str(s.get("admission_no") or "").strip()

                            # ✅ FIX: support multiple possible key names
                            sid = s.get("id")
                            if sid is None:
                                sid = s.get("student_id")
                            if sid is None:
                                sid = s.get("studentId")

                            if adm and sid is not None and str(sid).strip() != "":
                                adm_to_student_id[adm] = int(sid)
                    except Exception:
                        adm_to_student_id = {}


                    # Try to infer exam_id from table (best option without calling /admin/exams)
                    inferred_exam_id = None
                    try:
                        if "exam_id" in df.columns:
                            vals = df["exam_id"].dropna().unique().tolist()
                            if vals:
                                inferred_exam_id = int(vals[0])
                    except Exception:
                        inferred_exam_id = None

                    # ✅ REQUIRED FIX: if table doesn't have exam_id, use backend meta.exam_id
                    if inferred_exam_id is None:
                        try:
                            if isinstance(payload, dict):
                                meta = payload.get("meta") or {}
                                mid = meta.get("exam_id")
                                if mid is not None and str(mid).strip() != "":
                                    inferred_exam_id = int(mid)
                        except Exception:
                            pass

                    # ✅ NEW: fill missing student_id using admission_no map (so feedback can load)
                    if "student_id" not in df.columns:
                        df["student_id"] = None
                    try:
                        def _resolve_student_id(row):
                            try:
                                sid = row.get("student_id")
                                if sid is not None and str(sid).strip() != "":
                                    return int(sid)
                            except Exception:
                                pass
                            adm = str(row.get("admission_no") or "").strip()
                            return adm_to_student_id.get(adm)
                        df["student_id"] = df.apply(_resolve_student_id, axis=1)
                    except Exception:
                        pass
                    # st.write("DEBUG inferred_exam_id:", inferred_exam_id)
                    # st.write("DEBUG student_id null count:", int(df["student_id"].isna().sum()))


                    # ✅ NEW: load feedback for full table and populate columns (persist after logout/login)
                    def _fb_cache_key(exam_id, student_ids):
                        try:
                            ids = ",".join([str(int(x)) for x in sorted({int(i) for i in student_ids if i is not None})])
                        except Exception:
                            ids = ""
                        return f"fb:{exam_id}:{ids}"

                    def _load_feedback_map(exam_id: int, student_ids: list[int]) -> dict:
                        """
                        Returns: {student_id: {"remark": "...", "note": "..."}}
                        Uses session cache to avoid re-calling too much.
                        """
                        if not exam_id:
                            return {}
                        ids_clean = []
                        for sid in (student_ids or []):
                            try:
                                if sid is not None:
                                    ids_clean.append(int(sid))
                            except Exception:
                                pass
                        ids_clean = sorted(list(set(ids_clean)))
                        if not ids_clean:
                            return {}

                        cache_key = _fb_cache_key(exam_id, ids_clean)
                        if "teacher_fb_cache" not in st.session_state:
                            st.session_state["teacher_fb_cache"] = {}

                        if cache_key in st.session_state["teacher_fb_cache"]:
                            return st.session_state["teacher_fb_cache"][cache_key] or {}

                        fb_map = {}
                        for sid in ids_clean:
                            try:
                                fb_r = requests.get(
                                    f"{API_BASE}/teacher/feedback",
                                    params={"student_id": int(sid), "exam_id": int(exam_id)},
                                    headers=_auth_headers(),
                                    timeout=12,
                                )
                                if fb_r.ok:
                                    item = (fb_r.json() or {}).get("item")
                                    if item:
                                        fb_map[int(sid)] = {
                                            "remark": (item.get("remark") or "").strip(),
                                            "note": (item.get("note") or "").strip(),
                                        }
                            except Exception:
                                pass

                        st.session_state["teacher_fb_cache"][cache_key] = fb_map
                        return fb_map

                    # Populate table columns from DB feedback
                    if inferred_exam_id is not None:
                        try:
                            sids = df["student_id"].dropna().tolist() if "student_id" in df.columns else []
                            fb_map = _load_feedback_map(int(inferred_exam_id), sids)

                            def _remark_for_sid(sid):
                                try:
                                    sid = int(sid)
                                    return (fb_map.get(sid) or {}).get("remark", "")
                                except Exception:
                                    return ""

                            def _note_for_sid(sid):
                                try:
                                    sid = int(sid)
                                    return (fb_map.get(sid) or {}).get("note", "")
                                except Exception:
                                    return ""

                            df["teacher_remark"] = df["student_id"].apply(_remark_for_sid)
                            df["special_note"] = df["student_id"].apply(_note_for_sid)
                        except Exception:
                            pass

                    st.dataframe(df[ordered] if ordered else df, width="stretch", hide_index=True)

                    st.markdown("---")
                    st.markdown("### 🧑‍🏫 Teacher Feedback (Remark + Special Note)")
                    st.caption("Select a student from this table and add feedback for the selected exam. Feedback persists after logout/login.")

                    # selector uses admission_no (stable)
                    if "admission_no" in df.columns:
                        name_col = "student_name" if "student_name" in df.columns else ("name" if "name" in df.columns else "admission_no")

                        labels = []
                        label_to_adm = {}
                        for _, row in df.iterrows():
                            adm = str(row.get("admission_no", "")).strip()
                            nm = str(row.get(name_col, "")).strip()
                            if adm:
                                label = f"{nm} (Admission: {adm})" if nm and nm != adm else f"Admission: {adm}"
                                labels.append(label)
                                label_to_adm[label] = adm

                        if labels:
                            # ✅ Add "All Students" default like earlier
                            labels2 = ["All Students"] + labels
                            sel_label = st.selectbox("Select Student", labels2, index=0)

                            sel_adm = None
                            if sel_label != "All Students":
                                sel_adm = label_to_adm.get(sel_label)

                            # ✅ Show only selected student's row (like earlier)
                            df_to_show = df
                            try:
                                if "admission_no" in df.columns and sel_adm:
                                    df_to_show = df[df["admission_no"].astype(str) == str(sel_adm)]
                            except Exception:
                                df_to_show = df

                            st.dataframe(df_to_show[ordered] if ordered else df_to_show, width="stretch", hide_index=True)

                            # Determine student_id: prefer table student_id, else map by admission_no
                            student_id = None
                            try:
                                if sel_adm is not None and "student_id" in df.columns:
                                    sid_vals = df.loc[df["admission_no"].astype(str) == str(sel_adm), "student_id"].dropna().unique().tolist()
                                    if sid_vals:
                                        student_id = int(sid_vals[0])
                            except Exception:
                                student_id = None
                            if student_id is None and sel_adm is not None:
                                student_id = adm_to_student_id.get(str(sel_adm))

                            exam_id = inferred_exam_id

                            # Load saved feedback (backend) to persist across sessions
                            saved_remark = ""
                            saved_note = ""
                            if student_id is not None and exam_id is not None:
                                try:
                                    fb_r = requests.get(
                                        f"{API_BASE}/teacher/feedback",
                                        params={"student_id": int(student_id), "exam_id": int(exam_id)},
                                        headers=_auth_headers(),
                                        timeout=20,
                                    )
                                    if fb_r.ok:
                                        item = (fb_r.json() or {}).get("item")
                                        if item:
                                            saved_remark = (item.get("remark") or "").strip()
                                            saved_note = (item.get("note") or "").strip()
                                except Exception:
                                    pass

                            REMARK_OPTIONS = ["Excellent", "Good", "Average", "Needs Improvement", "Poor"]
                            default_index = REMARK_OPTIONS.index(saved_remark) if saved_remark in REMARK_OPTIONS else 1

                            c1, c2 = st.columns([1, 2])
                            with c1:
                                remark = st.selectbox("Teacher Remark", REMARK_OPTIONS, index=default_index, key=f"remark_{sel_adm}_{sel_exam}")
                            with c2:
                                note = st.text_area(
                                    "Special Note",
                                    value=saved_note,
                                    height=110,
                                    placeholder="Write special note for this student...",
                                    key=f"note_{sel_adm}_{sel_exam}",
                                )

                            if st.button("✅ Save Feedback", type="primary", key=f"save_fb_{sel_adm}_{sel_exam}"):
                                # update table view immediately
                                try:
                                    if sel_adm is not None:
                                        mask = df["admission_no"].astype(str) == str(sel_adm)
                                        df.loc[mask, "teacher_remark"] = remark
                                        df.loc[mask, "special_note"] = (note or "").strip()
                                except Exception:
                                    pass

                                # persist to backend (if ids available)
                                if student_id is not None and exam_id is not None:
                                    try:
                                        fb_post = requests.post(
                                            f"{API_BASE}/teacher/feedback",
                                            json={
                                                "student_id": int(student_id),
                                                "exam_id": int(exam_id),
                                                "remark": remark,
                                                "note": (note or "").strip(),
                                            },
                                            headers=_auth_headers(),
                                            timeout=20,
                                        )
                                        fb_post.raise_for_status()

                                        # ✅ update cache so table shows immediately after rerun
                                        try:
                                            if "teacher_fb_cache" not in st.session_state:
                                                st.session_state["teacher_fb_cache"] = {}
                                            cache_key = _fb_cache_key(int(exam_id), [int(student_id)])
                                            cached = st.session_state["teacher_fb_cache"].get(cache_key) or {}
                                            cached[int(student_id)] = {"remark": remark, "note": (note or "").strip()}
                                            st.session_state["teacher_fb_cache"][cache_key] = cached
                                        except Exception:
                                            pass

                                        st.success("Feedback saved ✅")
                                    except Exception as e:
                                        st.warning("Saved in table view, but could not persist to server.")
                                        st.text(str(e))
                                else:
                                    st.info("Saved in table view. Server persistence not available because student_id/exam_id could not be resolved.")

                                st.rerun()
                        else:
                            st.info("No students found in current table.")


    except Exception as e:
        st.info("Could not load Class Marks Table view.")
        st.text(str(e))

    st.markdown("---")

    # Download template
    st.markdown("### 📥 Download CSV Template")
    try:
        # ✅ FIX: include auth headers
        tmpl = requests.get(f"{API_BASE}/teacher/template", headers=_auth_headers(), timeout=20)
        if tmpl.ok:
            st.download_button(
                label="Download marks_template.csv",
                data=tmpl.text,
                file_name="marks_template.csv",
                mime="text/csv",
            )
            st.caption("Important: exam_date must be in YYYY-MM-DD.")
        else:
            st.info("Template not available.")
    except Exception:
        st.info("Template not available.")

    st.markdown("---")

    # Upload + preview
    st.markdown("### ⬆️ Upload CSV")
    st.caption("If your CSV has exam_date like 05-03-2026, it will be auto-converted to 2026-03-05 for upload.")

    csv_file = st.file_uploader("Choose a CSV file", type=["csv"])

    preview_df = None
    upload_bytes = None

    if csv_file is not None:
        try:
            preview_df = pd.read_csv(csv_file)
            st.markdown("#### Preview (first 20 rows)")
            st.dataframe(preview_df.head(20), width="stretch", hide_index=True)

            # AUTO-FIX exam_date if DD-MM-YYYY detected
            df_fixed = preview_df.copy()
            if "exam_date" in df_fixed.columns:
                def _fix_date(v):
                    try:
                        s = str(v).strip()
                        if len(s) == 10 and s[2] == "-" and s[5] == "-" and s[:2].isdigit() and s[3:5].isdigit() and s[6:].isdigit():
                            # DD-MM-YYYY -> YYYY-MM-DD
                            dd = s[:2]
                            mm = s[3:5]
                            yyyy = s[6:]
                            return f"{yyyy}-{mm}-{dd}"
                        return s
                    except Exception:
                        return v

                df_fixed["exam_date"] = df_fixed["exam_date"].apply(_fix_date)

            upload_buf = io.StringIO()
            df_fixed.to_csv(upload_buf, index=False)
            upload_bytes = upload_buf.getvalue().encode("utf-8")
        except Exception as e:
            st.error("Could not read CSV preview.")
            st.text(str(e))

    if csv_file is not None and st.button("Upload Marks"):
        try:
            data_to_send = upload_bytes if upload_bytes is not None else csv_file.getvalue()
            files = {"file": (csv_file.name, data_to_send, "text/csv")}
            # ✅ FIX: include auth headers
            resp = requests.post(f"{API_BASE}/teacher/upload-marks", files=files, headers=_auth_headers(), timeout=60)

            if resp.ok:
                st.success("Upload successful ✅")
                st.json(resp.json())
                st.rerun()
            else:
                st.error("Upload failed ❌")
                try:
                    payload = resp.json()
                    detail = payload.get("detail")
                    if isinstance(detail, dict) and "errors" in detail:
                        st.markdown("### ⚠️ Validation Errors")
                        err_df = pd.DataFrame(detail["errors"])
                        st.dataframe(err_df, width="stretch", hide_index=True)
                    else:
                        st.text(resp.text)
                except Exception:
                    st.text(resp.text)

        except Exception as e:
            st.error("Upload failed due to an unexpected error.")
            st.text(str(e))

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="text-align:center;font-size:0.8rem;color:{theme["footer_text"]};margin-top:2rem;">
            Powered by <strong>RoboAIAPaths</strong> · Academic Insights MVP<br/>
            Built with FastAPI + Streamlit for school-ready dashboards.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()




# ─────────────────────────────────────────
# 1) Load students
# ─────────────────────────────────────────
@st.cache_data
def fetch_students():
    # ✅ Parent ownership enforcement: use mapped students from /auth/me if present
    auth_user = st.session_state.get("auth_user") or {}
    role_local = (auth_user.get("role") or "").strip().lower()
    mapped_students = auth_user.get("students") if isinstance(auth_user, dict) else None

    if role_local == "parent" and mapped_students:
        return mapped_students

    resp = requests.get(f"{API_BASE}/students", timeout=20)
    resp.raise_for_status()
    return resp.json()


students = fetch_students()
student_map = {f"{s['name']} (Grade {s['grade']}{s['section']})": s["id"] for s in students}

st.sidebar.markdown("**Demo School:** Green Valley Public School")

selected_label = st.sidebar.selectbox("Select Student", list(student_map.keys()))
selected_id = student_map[selected_label]

# ─────────────────────────────────────────
# 2) Fetch dashboard data (UPDATED ROUTE)
# ─────────────────────────────────────────
def fetch_dashboard(student_id: int):
    headers = _auth_headers()

    # ✅ Parent must use parent endpoint (ownership-safe)
    if st.session_state.get("role") == "Parent":
        resp = requests.get(
            f"{API_BASE}/dashboard/parent/{student_id}",
            params={"exam_name": "Final"},
            headers=headers,
            timeout=30,
        )
    else:
        resp = requests.get(
            f"{API_BASE}/dashboard/{student_id}/dashboard-data",
            headers=headers,
            timeout=30,
        )

    resp.raise_for_status()
    return resp.json()



dashboard = fetch_dashboard(selected_id)

student = dashboard.get("student", {})
metrics = dashboard.get("metrics", {}) or {}
subject_bar = dashboard.get("subject_bar", []) or []
overall_trend = dashboard.get("overall_trend", []) or []

# ─────────────────────────────────────────
# Fetch Parent Class Insights BEFORE charts, so class_summary/class_trend exist.
# ─────────────────────────────────────────
def fetch_parent_insights(student_id: int, exam_name: str = "Final"):
    resp = requests.get(f"{API_BASE}/dashboard/parent/{student_id}", params={"exam_name": exam_name}, timeout=20)
    resp.raise_for_status()
    return resp.json()


try:
    parent_dash = fetch_parent_insights(selected_id, exam_name="Final")
    class_summary = parent_dash.get("class_summary", {}) or {}
    student_vs_class = parent_dash.get("student_vs_class_subject_avg", []) or []
    highlights = parent_dash.get("highlights", []) or []
    class_trend = parent_dash.get("class_trend", []) or []
    class_subject_stats = parent_dash.get("class_subject_stats", []) or []
except Exception:
    parent_dash = {}
    class_summary = {}
    student_vs_class = []
    highlights = []
    class_trend = []
    class_subject_stats = []

# ─────────────────────────────────────────
# 3) Header info
# ─────────────────────────────────────────
name = student.get("name", "Unknown")
grade = student.get("grade", "?")
section = student.get("section", "")

st.subheader(f"{name} – Grade {grade}{section}")
st.markdown("---")

# ─────────────────────────────────────────
# 4) Handle case: no metrics / no assessments
# ─────────────────────────────────────────
required_keys = {
    "overall_average",
    "strongest_subject",
    "strongest_percentage",
    "weakest_subject",
    "weakest_percentage",
    "trend_label",
}

if not metrics or not required_keys.issubset(metrics.keys()):
    st.info(
        "No sufficient assessment data is available yet for this student. "
        "Once marks are entered, the dashboard will show metrics, charts and summary."
    )
else:
    # ─────────────────────────────────────────
    # 5) “How is my child doing?” KPI cards
    # ─────────────────────────────────────────
    st.markdown("### ✅ How is my child doing?")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Average", f"{metrics['overall_average']}%")
    col2.metric(
        "Strongest Subject",
        metrics["strongest_subject"],
        f"{metrics['strongest_percentage']}%",
    )
    col3.metric(
        "Needs Attention",
        metrics["weakest_subject"],
        f"{metrics['weakest_percentage']}%",
    )
    col4.metric("Trend", metrics["trend_label"])

    # ✅ Trend explanation (brief)
    trend_expl = (metrics.get("trend_explanation") or "").strip()
    if trend_expl:
        with st.expander("ℹ️ What is Trend Analysis & how is it calculated?", expanded=False):
            st.write(trend_expl)
            if metrics.get("trend_delta_percentage_points") is not None:
                st.caption(f"Change from first exam to latest exam: {metrics.get('trend_delta_percentage_points')} percentage points.")

    # ─────────────────────────────────────────
    # Quick Summary (1 line insight) – rule-based
    # ─────────────────────────────────────────
    strengths_1line = []
    weaknesses_1line = []
    for row in student_vs_class:
        try:
            if float(row.get("delta", 0)) >= 5:
                strengths_1line.append(row.get("subject"))
            elif float(row.get("delta", 0)) <= -5:
                weaknesses_1line.append(row.get("subject"))
        except Exception:
            pass

    parts = []
    if strengths_1line:
        parts.append(f"above class average in <strong>{', '.join(strengths_1line[:3])}</strong>")
    if weaknesses_1line:
        parts.append(f"needs support in <strong>{', '.join(weaknesses_1line[:3])}</strong>")
    parts.append(f"overall trend is <strong>{metrics.get('trend_label','—')}</strong>")

    quick_line = f"{name} is " + ", ".join(parts).strip() + "."

    st.markdown(
        f"""
        <div style="
            padding:10px 12px;
            border-radius:8px;
            border:1px solid {theme["card_border"]};
            background-color:{theme["card_bg"]};
            color:{theme["text"]};
            margin-top:0.75rem;
        ">
            <strong>Quick Summary:</strong> {quick_line}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### 📈 Exam & Subject Analytics")

    # ─────────────────────────────────────────
    # 6) Charts
    # ─────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.markdown("#### Latest Exam – Subject-wise Performance")
        st.caption("Student vs Class Average vs Subject Max vs Subject Min (latest class exam)")

        if subject_bar:
            import pandas as pd
            import plotly.express as px

            # Student % (latest exam for student)
            df_student = pd.DataFrame(subject_bar)[["subject", "percentage"]].rename(
                columns={"percentage": "Student"}
            )

            # Class stats per subject (avg/max/min) - Prefer student_vs_class since it is aligned per subject
            if student_vs_class:
                df_stats = pd.DataFrame(student_vs_class)[
                    ["subject", "class_average_percentage", "subject_max_percentage", "subject_min_percentage"]
                ].rename(
                    columns={
                        "class_average_percentage": "Class Average",
                        "subject_max_percentage": "Subject Max",
                        "subject_min_percentage": "Subject Min",
                    }
                )
            else:
                # Fallback: if backend didn't return student_vs_class, try class_subject_stats
                df_stats = pd.DataFrame(class_subject_stats).rename(
                    columns={
                        "class_average_percentage": "Class Average",
                        "subject_max_percentage": "Subject Max",
                        "subject_min_percentage": "Subject Min",
                    }
                )
                if not df_stats.empty and "subject" in df_stats.columns:
                    df_stats = df_stats[["subject", "Class Average", "Subject Max", "Subject Min"]]

            if df_stats is None or df_stats.empty:
                df = df_student.copy()
                df["Class Average"] = 0
                df["Subject Max"] = 0
                df["Subject Min"] = 0
            else:
                df = df_student.merge(df_stats, on="subject", how="left")

            for col in ["Student", "Class Average", "Subject Max", "Subject Min"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.fillna(0)

            y_cols = ["Student", "Class Average", "Subject Max", "Subject Min"]

            fig = px.bar(
                df,
                x="subject",
                y=y_cols,
                barmode="group",
                text_auto=True,
            )
            # Keep consistent colors (same pattern always)
            color_map = {
                "Student": "#1f77b4",        # Plotly default blue
                "Class Average": "#ff7f0e",  # Plotly default orange
                "Subject Max": "#2ca02c",    # green
                "Subject Min": "#d62728",    # red
            }
            for tr in fig.data:
                if tr.name in color_map:
                    tr.marker.color = color_map[tr.name]

            fig.update_layout(
                yaxis_title="Percentage",
                xaxis_title="Subject",
                legend_title="",
            )

            st.plotly_chart(fig, width="stretch")
            # st.caption("This chart uses the latest exam available for the class.")

            # ✅ Table just below chart (same data)
            st.markdown("**Table (same as bar chart):**")
            st.dataframe(
                df[["subject", "Student", "Class Average", "Subject Max", "Subject Min"]].rename(
                    columns={
                        "subject": "Subject",
                        "Student": "Student %",
                        "Class Average": "Class Avg %",
                        "Subject Max": "Max in Class %",
                        "Subject Min": "Min in Class %",
                    }
                ),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No assessments found for this student yet.")

    with right:
        st.markdown("#### Overall Performance Trend (Across Exams)")
        st.caption("Student vs Class Average vs Topper vs Bottom")

        if overall_trend:
            import pandas as pd
            import plotly.express as px

            df_student = pd.DataFrame(overall_trend).rename(columns={"percentage": "Student"})

            df_class = pd.DataFrame(class_trend)
            if not df_class.empty:
                rename_map = {"class_average": "Class Average", "topper": "Topper"}
                if "bottom" in df_class.columns:
                    rename_map["bottom"] = "Bottom"

                df_class = df_class.rename(columns=rename_map)

                cols_to_merge = ["exam_name"]
                if "Class Average" in df_class.columns:
                    cols_to_merge.append("Class Average")
                if "Topper" in df_class.columns:
                    cols_to_merge.append("Topper")
                if "Bottom" in df_class.columns:
                    cols_to_merge.append("Bottom")

                df = df_student.merge(df_class[cols_to_merge], on="exam_name", how="left")
            else:
                df = df_student

            for col in ["Student", "Class Average", "Topper", "Bottom"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.fillna(0)

            y_cols = ["Student"]
            if "Class Average" in df.columns:
                y_cols.append("Class Average")
            if "Topper" in df.columns:
                y_cols.append("Topper")
            if "Bottom" in df.columns and df["Bottom"].sum() > 0:
                y_cols.append("Bottom")

            fig = px.line(
                df,
                x="exam_name",
                y=y_cols,
                markers=True,
            )
            # Keep consistent colors (same pattern always)
            color_map = {
                "Student": "#1f77b4",        # blue
                "Class Average": "#ff7f0e",  # orange
                "Topper": "#2ca02c",         # green
                "Bottom": "#d62728",         # red
            }
            for tr in fig.data:
                if tr.name in color_map:
                    tr.line.color = color_map[tr.name]
                    tr.marker.color = color_map[tr.name]


            fig.update_layout(
                yaxis_title="Percentage",
                xaxis_title="Exam",
                legend_title="",
            )

            st.plotly_chart(fig, width="stretch")
            # ✅ Table just below line chart (same data)
            st.markdown("**Table (same as line graph):**")

            table_df = df[["exam_name"] + y_cols].copy()

            rename_cols = {"exam_name": "Exam"}
            for c in y_cols:
                rename_cols[c] = f"{c} %"

            st.dataframe(
                table_df.rename(columns=rename_cols),
                width="stretch",
                hide_index=True,
            )

        else:
            st.info("No trend available yet.")

    st.markdown("---")

    # ─────────────────────────────────────────
    # Class Comparison (Current Exam)
    # ─────────────────────────────────────────
    st.markdown("### 🏫 Class Comparison (Current Exam)")
    st.caption("Where does my child stand in the class for the current exam?")

    if class_summary and class_summary.get("class_avg") is not None:
        topper = class_summary.get("topper") or {}
        bottom = class_summary.get("bottom") or {}
        student_pct_current = class_summary.get("student_percentage")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Student (Overall)", f"{student_pct_current if student_pct_current is not None else '—'}%")
        c2.metric("Topper (Overall)", f"{topper.get('percentage', '—')}%")
        c3.metric("Class Average (Overall)", f"{class_summary.get('class_avg')}%")
        c4.metric("Bottom (Overall)", f"{bottom.get('percentage', '—')}%")

        st.markdown("---")

        topper_marks = topper.get("subject_marks") or []
        if topper_marks:
            import pandas as pd

            with st.expander("🥇 Topper Marks (Subject-wise)", expanded=False):
                df_topper = pd.DataFrame(topper_marks)
                cols = [c for c in ["subject", "score", "max_score", "percentage"] if c in df_topper.columns]
                st.dataframe(df_topper[cols] if cols else df_topper, width="stretch", hide_index=True)

        bottom_marks = bottom.get("subject_marks") or []
        if bottom_marks:
            import pandas as pd

            with st.expander("🔻 Bottom Student Marks (Subject-wise)", expanded=False):
                df_bottom = pd.DataFrame(bottom_marks)
                cols = [c for c in ["subject", "score", "max_score", "percentage"] if c in df_bottom.columns]
                st.dataframe(df_bottom[cols] if cols else df_bottom, width="stretch", hide_index=True)

        st.markdown("---")

        st.markdown("### 📌 Student vs Class (Subject-wise)")

        if student_vs_class:
            import pandas as pd

            df_cmp = pd.DataFrame(student_vs_class)

            st.dataframe(
                df_cmp[
                    [
                        "subject",
                        "student_percentage",
                        "class_average_percentage",
                        "subject_max_percentage",
                        "subject_min_percentage",
                        "delta",
                    ]
                ].rename(
                    columns={
                        "subject": "Subject",
                        "student_percentage": "Student %",
                        "class_average_percentage": "Class Avg %",
                        "subject_max_percentage": "Max in Class %",
                        "subject_min_percentage": "Min in Class %",
                        "delta": "Delta (Student - Avg)",
                    }
                ),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No subject comparison data available for this student/class.")

        st.markdown("---")

        st.markdown("### ⭐ Rank Highlights (Top 5 / Bottom 5 in Class)")

        if highlights:
            for h in highlights:
                tag = "Top 5" if h.get("type") == "TOP" else "Bottom 5"

                details = []

                stu_sc = h.get("student_score")
                stu_max = h.get("student_max_score")
                stu_pct = h.get("student_percentage")

                top_sc = h.get("topper_score")
                top_max = h.get("topper_max_score")
                top_pct = h.get("topper_percentage")

                cls_avg = h.get("class_average_percentage")

                if stu_sc is not None and stu_max is not None and stu_pct is not None:
                    details.append(f"Your child: {stu_sc}/{stu_max} ({stu_pct}%)")
                if top_sc is not None and top_max is not None and top_pct is not None:
                    details.append(f"Topper: {top_sc}/{top_max} ({top_pct}%)")
                if cls_avg is not None:
                    details.append(f"Class Avg: {cls_avg}%")

                extra = " • ".join(details)

                st.markdown(
                    f"""
                    <div style="
                        padding:10px 12px;
                        border-radius:8px;
                        border:1px solid {theme["card_border"]};
                        background-color:{theme["card_bg"]};
                        margin-bottom:0.5rem;
                        color:{theme["text"]};
                    ">
                        <strong>{tag}</strong> in <strong>{h.get("subject")}</strong>
                        · Rank <strong>{h.get("rank")}</strong> / {h.get("class_size")}
                        {"<div style='margin-top:6px; opacity:0.9; font-size:0.95rem;'>" + extra + "</div>" if extra else ""}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No Top 5 / Bottom 5 highlights for this student in the current exam.")

    else:
        st.info(
            "Class comparison is not available for this student yet. "
            "Once class marks are available (teacher upload / full class demo), "
            "this section will show topper/average/bottom and rankings."
        )

    st.markdown("---")

    # ✅ Remove "AI" word from UI: rename section
    st.markdown("### 📝 Academic Summary")
    st.caption("Interpretation & next steps (keeps charts/tables as the source of truth).")

    # ─────────────────────────────────────────
    # ✅ Teacher Feedback (Parent Dashboard)
    # - Do NOT use /admin/exams here (Parent usually can't access it)
    # - Resolve exam_id from /teacher/class-marks meta (safe + consistent)
    # ─────────────────────────────────────────
    exam_name_for_feedback = "Final"  # keep as-is (your original)
    exam_id_for_feedback = None

    # 1) Resolve exam_id using teacher/class-marks meta (works after our backend fix)
    try:
        # NOTE: grade/section must be available in your parent dashboard context
        # If you already have student's grade/section, use those variables.
        # Common names in your code are: selected_grade, selected_section.
        cm_r = requests.get(
            f"{API_BASE}/teacher/class-marks",
            params={"grade": selected_grade, "section": selected_section, "exam_name": exam_name_for_feedback},
            headers=_auth_headers(),   # ✅ IMPORTANT
            timeout=20,
        )
        if cm_r.ok:
            cm_payload = cm_r.json() or {}
            meta = (cm_payload or {}).get("meta") or {}
            mid = meta.get("exam_id")
            if mid is not None and str(mid).strip() != "":
                exam_id_for_feedback = int(mid)
    except Exception:
        exam_id_for_feedback = None

    teacher_feedback = None

    # 2) Fetch feedback using exam_id + student_id
    if exam_id_for_feedback is not None:
        try:
            tf_r = requests.get(
                f"{API_BASE}/teacher/feedback",
                params={"student_id": int(selected_id), "exam_id": int(exam_id_for_feedback)},
                headers=_auth_headers(),  # ✅ IMPORTANT
                timeout=20,
            )
            if tf_r.ok:
                teacher_feedback = (tf_r.json() or {}).get("item")
        except Exception:
            teacher_feedback = None

    teacher_remark = (teacher_feedback or {}).get("remark") or "—"
    teacher_note = (teacher_feedback or {}).get("note") or "—"

    teacher_feedback_html = f"""
        <hr style="opacity:0.25;"/>
        <h4>🧑‍🏫 Teacher Feedback</h4>
        <ul style="margin-top:0.35rem;">
            <li><strong>Remark:</strong> {teacher_remark}</li>
            <li><strong>Special Note:</strong> {teacher_note}</li>
        </ul>
    """

    # ✅ Always refresh automatically (no button)
    with st.spinner("Generating summary..."):
        try:
            resp = requests.post(f"{API_BASE}/insights/{selected_id}/ai-insights", timeout=60)
            resp.raise_for_status()
            st.session_state["summary_text"] = resp.json().get("summary", "No summary returned.")
        except Exception:
            st.session_state["summary_text"] = "Could not generate summary at this time."

    strengths = []
    weaknesses = []
    for row in student_vs_class:
        try:
            if float(row.get("delta", 0)) >= 5:
                strengths.append(row)
            elif float(row.get("delta", 0)) <= -5:
                weaknesses.append(row)
        except Exception:
            pass

    highlight_msgs = []
    for h in highlights:
        tag = "Top 5" if h.get("type") == "TOP" else "Bottom 5"
        highlight_msgs.append(f"{tag} in {h.get('subject')} (Rank {h.get('rank')}/{h.get('class_size')})")

    border = theme["card_border"]
    bg = theme["card_bg"]
    text_color = theme["text"]

    if strengths:
        strengths_html = "<ul>" + "".join(
            [f"<li>{s.get('subject')}: +{s.get('delta')}% above class average</li>" for s in strengths]
        ) + "</ul>"
    else:
        strengths_html = "<p>Performing close to class average in all subjects.</p>"

    if weaknesses:
        weaknesses_html = "<ul>" + "".join(
            [f"<li>{w.get('subject')}: {w.get('delta')}% below class average</li>" for w in weaknesses]
        ) + "</ul>"
    else:
        weaknesses_html = "<p>No major weak areas detected in this exam.</p>"

    if highlight_msgs:
        highlights_html = "<ul>" + "".join([f"<li>{msg}</li>" for msg in highlight_msgs]) + "</ul>"
    else:
        highlights_html = "<p>No Top/Bottom 5 positions in this exam.</p>"

    # ✅ Make Guidance UI consistent (clean + sectioned)
    raw_summary = (st.session_state.get("summary_text") or "").strip()

    def _strip_md(s: str) -> str:
        return (s or "").replace("**", "").strip()

    cleaned = _strip_md(raw_summary)

    sections = {
        "Overview": "",
        "Patterns & Strengths": "",
        "Needs Support": "",
        "Actions at Home": "",
        "Next Step": "",
    }

    current = None

    def _set_section_from_line(line: str):
        """Returns (section_name, inline_text_or_empty) or (None, None)"""
        l = _strip_md(line).strip()
        low = l.lower().strip()

        if low in ["overview", "patterns & strengths", "needs support", "actions at home", "next step"]:
            mapping = {
                "overview": "Overview",
                "patterns & strengths": "Patterns & Strengths",
                "needs support": "Needs Support",
                "actions at home": "Actions at Home",
                "next step": "Next Step",
            }
            return (mapping.get(low), "")

        for key in sections.keys():
            if low.startswith(key.lower() + ":"):
                inline = l.split(":", 1)[1].strip()
                return (key, inline)
        return (None, None)

    lines = [ln.rstrip() for ln in cleaned.splitlines()]

    for line in lines:
        l = _strip_md(line)
        if not l:
            continue

        sec, inline = _set_section_from_line(l)
        if sec:
            current = sec
            if inline:
                if current == "Actions at Home":
                    sections[current] += f"<li>{inline}</li>"
                else:
                    sections[current] += inline + " "
            continue

        if current == "Actions at Home":
            if l.startswith("-"):
                item = l[1:].strip()
            else:
                item = l.strip()
            if item:
                sections[current] += f"<li>{item}</li>"
        elif current:
            sections[current] += l.strip() + " "

    overview = sections["Overview"].strip() or "-"
    patterns = sections["Patterns & Strengths"].strip() or "-"
    needs = sections["Needs Support"].strip() or "-"
    actions = sections["Actions at Home"].strip()
    next_step = sections["Next Step"].strip() or "-"

    actions_html = f"<ul style='margin-top:6px;'>{actions}</ul>" if actions else "<p>-</p>"

    st.markdown(
        f"""
        <div style="
            padding:16px;
            border-radius:10px;
            border:1px solid {border};
            background-color:{bg};
            color:{text_color};
        ">

        <h4 style="margin-top:0;">📌 Snapshot</h4>
        <ul style="margin-top:0.35rem;">
            <li><strong>Overall Average:</strong> {metrics.get('overall_average', '—')}%</li>
            <li><strong>Trend:</strong> {metrics.get('trend_label', '—')}</li>
            <li><strong>Strongest Subject:</strong> {metrics.get('strongest_subject', '—')} ({metrics.get('strongest_percentage', '—')}%)</li>
            <li><strong>Needs Attention:</strong> {metrics.get('weakest_subject', '—')} ({metrics.get('weakest_percentage', '—')}%)</li>
        </ul>

        <hr style="opacity:0.25;"/>

        <h4>💪 Strengths (Compared to Class)</h4>
        {strengths_html}

        <hr style="opacity:0.25;"/>

        <h4>⚠️ Areas Needing Support</h4>
        {weaknesses_html}

        <hr style="opacity:0.25;"/>

        <h4>⭐ Class Standing Highlights</h4>
        {highlights_html}

        {teacher_feedback_html}

        <hr style="opacity:0.25;"/>

        <h4>🧠 Guidance for Parents</h4>

        <div style="margin-top:10px;">
            <strong>Overview:</strong>
            <div style="margin-top:6px; line-height:1.6;">{overview}</div>
        </div>

        <hr style="opacity:0.25;"/>

        <div>
            <strong>Patterns &amp; Strengths:</strong>
            <div style="margin-top:6px; line-height:1.6;">{patterns}</div>
        </div>

        <hr style="opacity:0.25;"/>

        <div>
            <strong>Needs Support:</strong>
            <div style="margin-top:6px; line-height:1.6;">{needs}</div>
        </div>

        <hr style="opacity:0.25;"/>

        <div>
            <strong>Actions at Home:</strong>
            {actions_html}
        </div>

        <hr style="opacity:0.25;"/>

        <div>
            <strong>Next Step:</strong>
            <div style="margin-top:6px; line-height:1.6;">{next_step}</div>
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
