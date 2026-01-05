from __future__ import annotations

import csv
import io
from datetime import date
from typing import Dict, Any, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from services.marks_store import load_uploaded_marks, save_uploaded_marks
from services.analytics_service import DEMO_SUBJECTS, CLASS_6A_ADMISSION
from auth.dependencies import require_role

router = APIRouter()

@router.post("/upload-marks", summary="Teacher uploads marks CSV for an exam")
async def upload_marks_csv(
    file: UploadFile = File(...),
    user=Depends(require_role(["Teacher", "Admin"])),
) -> Dict[str, Any]:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))

    required = {"admission_no", "exam_name", "exam_date", "max_score"}
    missing = [c for c in required if c not in (reader.fieldnames or [])]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    # Validate subject columns exist
    for sub in DEMO_SUBJECTS:
        if sub not in (reader.fieldnames or []):
            raise HTTPException(status_code=400, detail=f"Missing subject column: {sub}")

    # Only allow known admission_no in this demo phase
    allowed_adm = set(CLASS_6A_ADMISSION.values())

    rows_to_store: List[Dict[str, Any]] = []
    for row in reader:
        admission_no = (row.get("admission_no") or "").strip()
        if admission_no not in allowed_adm:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown admission_no for demo: {admission_no}. (Add via admin later)"
            )

        exam_name = (row.get("exam_name") or "").strip()
        exam_date_str = (row.get("exam_date") or "").strip()
        try:
            _ = date.fromisoformat(exam_date_str)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid exam_date: {exam_date_str} (use YYYY-MM-DD)")

        try:
            max_score = int(float(row.get("max_score") or 100))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid max_score")

        scores = {}
        for sub in DEMO_SUBJECTS:
            try:
                scores[sub] = float(row.get(sub) or 0)
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid score for {sub} in admission_no {admission_no}")

        rows_to_store.append({
            "admission_no": admission_no,
            "exam_name": exam_name,
            "exam_date": exam_date_str,
            "max_score": max_score,
            "scores": scores,
        })

    # UPSERT behavior: if same admission_no + exam_name + exam_date exists, replace it
    existing = load_uploaded_marks()
    def k(r): return (r["admission_no"], r["exam_name"], r["exam_date"])
    existing_map = {k(r): r for r in existing}
    for r in rows_to_store:
        existing_map[k(r)] = r

    merged = list(existing_map.values())
    save_uploaded_marks(merged)

    return {
        "status": "ok",
        "uploaded_rows": len(rows_to_store),
        "stored_total_rows": len(merged),
        "note": "Restart backend OR reload module to see updates reflected in analytics immediately. (Next step: live apply)"
    }
