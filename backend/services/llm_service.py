from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple

import json
from openai import OpenAI
from core.config import settings


client = None
if settings.OPENAI_API_KEY:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _compute_patterns(metrics: Dict[str, Any], overall_trend: List[Dict[str, Any]], student_vs_class: List[Dict[str, Any]], highlights: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute crisp, useful signals (patterns) to help LLM generate better insights.
    """
    # Trend direction signal
    trend_points: List[Tuple[str, Optional[float]]] = []
    for t in overall_trend:
        trend_points.append((str(t.get("exam_name") or ""), _safe_float(t.get("percentage"))))

    valid_pcts = [p for _, p in trend_points if p is not None]
    direction = None
    delta = None
    volatility = None

    if len(valid_pcts) >= 2:
        first = valid_pcts[0]
        last = valid_pcts[-1]
        delta = round(last - first, 2)

        if delta >= 2:
            direction = "Improving"
        elif delta <= -2:
            direction = "Declining"
        else:
            direction = "Stable"

        # volatility: max-min range
        volatility = round(max(valid_pcts) - min(valid_pcts), 2)

    # Subject spread (strong vs weak gap)
    strongest = _safe_float(metrics.get("strongest_percentage"))
    weakest = _safe_float(metrics.get("weakest_percentage"))
    spread = None
    if strongest is not None and weakest is not None:
        spread = round(strongest - weakest, 2)

    # Above / below class avg counts (subject-wise)
    above = 0
    below = 0
    focus_subjects = []
    for row in student_vs_class:
        d = _safe_float(row.get("delta"))
        sub = row.get("subject")
        if d is None or not sub:
            continue
        if d > 0:
            above += 1
        elif d < 0:
            below += 1
            focus_subjects.append(sub)

    # Top/Bottom 5 flags
    top5 = []
    bottom5 = []
    for h in highlights:
        sub = h.get("subject")
        if not sub:
            continue
        if h.get("type") == "TOP":
            top5.append(sub)
        elif h.get("type") == "BOTTOM":
            bottom5.append(sub)

    # Convert volatility into label
    volatility_label = None
    if volatility is not None:
        if volatility <= 5:
            volatility_label = "Consistent"
        elif volatility <= 12:
            volatility_label = "Some ups and downs"
        else:
            volatility_label = "Highly variable"

    # Focus shortlist (max 3)
    focus_short = focus_subjects[:3]

    return {
        "trend_direction": direction,
        "trend_delta_pct_points": delta,
        "trend_volatility_range": volatility,
        "trend_consistency_label": volatility_label,
        "subject_spread_pct_points": spread,
        "above_class_subjects_count": above,
        "below_class_subjects_count": below,
        "below_class_focus_subjects": focus_short,
        "top5_subjects": top5[:3],
        "bottom5_subjects": bottom5[:3],
    }


def _extract_teacher_feedback(dashboard_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Supports multiple future shapes. Return None if not present.
    Expected (future): dashboard_data["teacher_feedback"] = {"remark": "...", "note": "...", "exam_name": "...", ...}
    """
    tf = dashboard_data.get("teacher_feedback")
    if isinstance(tf, dict):
        remark = (tf.get("remark") or "").strip()
        note = (tf.get("note") or "").strip()
        if remark or note:
            return {
                "remark": remark or None,
                "note": note or None,
                "exam_name": tf.get("exam_name"),
                "exam_id": tf.get("exam_id"),
            }

    # Optional fallback keys if you use other naming later
    tf2 = dashboard_data.get("teacher_note")
    if isinstance(tf2, dict):
        remark = (tf2.get("remark") or "").strip()
        note = (tf2.get("note") or "").strip()
        if remark or note:
            return {
                "remark": remark or None,
                "note": note or None,
                "exam_name": tf2.get("exam_name"),
                "exam_id": tf2.get("exam_id"),
            }

    return None


def _build_academic_prompt(dashboard_data: Dict[str, Any]) -> str:
    """
    Build a crisp, insight-rich prompt for the LLM using the student's dashboard data.
    """

    student = dashboard_data.get("student", {}) or {}
    metrics = dashboard_data.get("metrics", {}) or {}
    subject_bar = dashboard_data.get("subject_bar", []) or []
    overall_trend = dashboard_data.get("overall_trend", []) or []

    class_summary = dashboard_data.get("class_summary", {}) or {}
    student_vs_class = dashboard_data.get("student_vs_class_subject_avg", []) or []
    highlights = dashboard_data.get("highlights", []) or []
    class_trend = dashboard_data.get("class_trend", []) or []

    name = student.get("name", "the student")
    grade = student.get("grade", "?")
    section = student.get("section", "")

    # Compact facts: latest subjects
    latest_subjects = []
    for s in subject_bar:
        latest_subjects.append(
            {
                "subject": s.get("subject"),
                "student_pct": s.get("percentage"),
            }
        )

    # Compact trend points
    trend_points = []
    for t in overall_trend:
        trend_points.append(
            {
                "exam": t.get("exam_name"),
                "pct": t.get("percentage"),
            }
        )

    # Subject comparison compact (keep min/max too)
    svc_points = []
    for row in student_vs_class:
        svc_points.append(
            {
                "subject": row.get("subject"),
                "student_pct": row.get("student_percentage"),
                "class_avg_pct": row.get("class_average_percentage"),
                "delta": row.get("delta"),
                "max_in_class": row.get("subject_max_percentage"),
                "min_in_class": row.get("subject_min_percentage"),
            }
        )

    # Highlights compact
    hl_points = []
    for h in highlights:
        hl_points.append(
            {
                "subject": h.get("subject"),
                "type": h.get("type"),  # TOP / BOTTOM
                "rank": h.get("rank"),
                "class_size": h.get("class_size"),
            }
        )

    # Class summary compact
    topper = (class_summary.get("topper") or {}) if isinstance(class_summary, dict) else {}
    bottom = (class_summary.get("bottom") or {}) if isinstance(class_summary, dict) else {}

    # NEW: derived patterns
    patterns = _compute_patterns(metrics, overall_trend, student_vs_class, highlights)

    # ✅ NEW: teacher feedback (clean + optional)
    teacher_feedback = _extract_teacher_feedback(dashboard_data)

    facts = {
        "student": {"name": name, "grade": f"{grade}{section}"},
        "overall": {
            "overall_average_pct": metrics.get("overall_average"),
            "trend_label": metrics.get("trend_label"),
            "strongest_subject": metrics.get("strongest_subject"),
            "strongest_pct": metrics.get("strongest_percentage"),
            "weakest_subject": metrics.get("weakest_subject"),
            "weakest_pct": metrics.get("weakest_percentage"),
        },
        "latest_subjects": latest_subjects,
        "trend_points": trend_points,
        "class_summary": {
            "exam_name": class_summary.get("exam_name") if isinstance(class_summary, dict) else None,
            "class_avg_pct": class_summary.get("class_avg") if isinstance(class_summary, dict) else None,
            "topper_pct": topper.get("percentage"),
            "bottom_pct": bottom.get("percentage"),
            "student_pct_current_exam": class_summary.get("student_percentage") if isinstance(class_summary, dict) else None,
        },
        "student_vs_class": svc_points,
        "highlights": hl_points,
        "class_trend": class_trend,  # optional
        "derived_patterns": patterns,  # ✅ pattern recognition
        "teacher_feedback": teacher_feedback,  # ✅ remark + note (optional, cleaned)
    }

    facts_json = json.dumps(facts, ensure_ascii=False)

    prompt = f"""
You are an experienced school counselor writing a parent note.

Rules (must follow):
- Be warm, supportive, and practical. No jargon.
- Do NOT mention systems, models, prompts, prototypes, or AI.
- Use insights from "derived_patterns" to recognize consistency, direction, and focus areas.
- If teacher_feedback is present, incorporate it especially in Needs Support / Next Step.
- Avoid repeating percentages: use at most THREE numbers in the whole response.
- If class comparison facts are missing, do not invent them.

Use exactly this structure and limits:
1) Overview (max 40 words)
2) Patterns & Strengths (max 80 words)  ← mention consistency / improving / top areas
3) Needs Support (max 80 words)         ← mention focus subjects / below class avg signals
4) Actions at Home: exactly 6 bullets, each max 11 words
5) Next Step (4 sentence, max 40 words)

FACTS (JSON):
{facts_json}
""".strip()

    return prompt


def _fallback_summary(dashboard_data: Dict[str, Any]) -> str:
    student = dashboard_data.get("student", {}) or {}
    metrics = dashboard_data.get("metrics", {}) or {}

    name = student.get("name", "The student")
    grade = student.get("grade", "?")

    overall = metrics.get("overall_average", "?")
    strongest = metrics.get("strongest_subject", "their stronger subjects")
    strongest_perc = metrics.get("strongest_percentage", "?")
    weakest = metrics.get("weakest_subject", "their weaker subjects")
    weakest_perc = metrics.get("weakest_percentage", "?")
    trend_label = metrics.get("trend_label", "stable")

    return (
        f"{name} (Grade {grade}) is currently performing at an overall average of around {overall}%. "
        f"The strongest subject at the moment appears to be {strongest} (about {strongest_perc}%), while "
        f"{weakest} (about {weakest_perc}%) needs more consistent focus.\n\n"
        f"The overall performance trend looks **{trend_label}** over the recent exams. "
        f"We recommend regular revision in weaker subjects, short daily practice, and open "
        f"communication between parents and teachers to maintain progress."
    )


def generate_academic_summary(dashboard_data: Dict[str, Any]) -> str:
    """
    Main function used by the API.

    - If OPENAI_API_KEY is present and the call succeeds -> returns LLM summary.
    - Otherwise -> returns safe fallback summary.

    DEBUG: prints reason in backend logs only (never in UI).
    """
    key_present = bool(getattr(settings, "OPENAI_API_KEY", None))
    model = getattr(settings, "OPENAI_MODEL", None)

    print("[LLM] OPENAI_API_KEY present:", key_present)
    print("[LLM] OPENAI_MODEL:", model)

    # If no key or client, use fallback directly
    if client is None or not settings.OPENAI_API_KEY:
        print("[LLM] Using fallback because client/key missing.")
        return _fallback_summary(dashboard_data)

    prompt = _build_academic_prompt(dashboard_data)

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an academic counselor writing progress notes for parents. "
                        "Be clear, kind, and supportive. Avoid technical jargon."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
            max_tokens=520,
        )
        content = response.choices[0].message.content
        if not content:
            print("[LLM] Empty content returned, using fallback.")
            return _fallback_summary(dashboard_data)
        return content.strip()

    except Exception as e:
        print("[LLM] OpenAI exception:", repr(e))
        return _fallback_summary(dashboard_data)
