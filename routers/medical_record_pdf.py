"""
medical_record_pdf.py  –  FastAPI endpoint to export a patient's full medical record as PDF.

Dependencies (add to requirements.txt):
    reportlab>=4.0.0

Usage:
    GET /records/me/export-pdf          → patient exports their own record
    GET /records/user/{user_id}/export-pdf  → doctor / admin exports a patient's record
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from database import get_db
from models import (
    Booking,
    AppointmentNotes,
    Diagnostic,
    DiagnosticResult,
    MedicalRecord,
    Radiology,
    RadiologyFinding,
    RoleEnum,
    User,
)
from utils import get_current_user

router = APIRouter(prefix="/records", tags=["medical-records"])

# ──────────────────────────────────────────────
# Colour palette (easy to change in one place)
# ──────────────────────────────────────────────
PRIMARY   = colors.HexColor("#1a6ea8")   # header / accent blue
SECONDARY = colors.HexColor("#2e9b8f")   # section bar teal
LIGHT_BG  = colors.HexColor("#f0f6fb")   # alternating row / box bg
DARK_TEXT = colors.HexColor("#1e2430")
MUTED     = colors.HexColor("#6b7a8d")
WHITE     = colors.white
RED       = colors.HexColor("#d94f4f")
GREEN     = colors.HexColor("#2e9b5a")

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm


# ══════════════════════════════════════════════
#  Style helpers
# ══════════════════════════════════════════════
def _styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "title":    s("title",    fontSize=22, textColor=WHITE,     leading=28, alignment=TA_CENTER, fontName="Helvetica-Bold"),
        "subtitle": s("subtitle", fontSize=11, textColor=WHITE,     leading=16, alignment=TA_CENTER),
        "section":  s("section",  fontSize=13, textColor=WHITE,     leading=18, fontName="Helvetica-Bold"),
        "label":    s("label",    fontSize=9,  textColor=MUTED,     leading=14, fontName="Helvetica-Bold"),
        "value":    s("value",    fontSize=10, textColor=DARK_TEXT, leading=14),
        "normal":   s("normal",   fontSize=10, textColor=DARK_TEXT, leading=14),
        "small":    s("small",    fontSize=8,  textColor=MUTED,     leading=12),
        "bold":     s("bold",     fontSize=10, textColor=DARK_TEXT, leading=14, fontName="Helvetica-Bold"),
        "risk_high":s("risk_high",fontSize=10, textColor=RED,       leading=14, fontName="Helvetica-Bold"),
        "risk_low": s("risk_low", fontSize=10, textColor=GREEN,     leading=14, fontName="Helvetica-Bold"),
    }


# ══════════════════════════════════════════════
#  Page template (header / footer on every page)
# ══════════════════════════════════════════════
class _HeaderFooter:
    def __init__(self, patient_name: str, patient_id: str):
        self.patient_name = patient_name
        self.patient_id   = patient_id

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        # ── top bar ──────────────────────────────
        canvas.setFillColor(PRIMARY)
        canvas.rect(0, h - 1.2 * cm, w, 1.2 * cm, fill=True, stroke=False)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN, h - 0.8 * cm, "SMART MEDICAL ASSISTANT")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(w - MARGIN, h - 0.8 * cm,
                               f"Patient: {self.patient_name}  |  ID: {self.patient_id}")

        # ── bottom bar ───────────────────────────
        canvas.setFillColor(LIGHT_BG)
        canvas.rect(0, 0, w, 0.9 * cm, fill=True, stroke=False)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(MARGIN, 0.3 * cm,
                          f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        canvas.drawRightString(w - MARGIN, 0.3 * cm, f"Page {doc.page}")

        canvas.restoreState()


def _build_doc(buffer: io.BytesIO, patient_name: str, patient_id: str) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=2.0 * cm,
        bottomMargin=1.6 * cm,
    )
    hf = _HeaderFooter(patient_name, patient_id)
    frame = Frame(MARGIN, 1.6 * cm, PAGE_W - 2 * MARGIN, PAGE_H - 3.6 * cm, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=hf)])
    return doc


# ══════════════════════════════════════════════
#  Reusable building blocks
# ══════════════════════════════════════════════
def _section_bar(title: str, st: dict) -> List:
    tbl = Table(
        [[Paragraph(title.upper(), st["section"])]],
        colWidths=[PAGE_W - 2 * MARGIN],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SECONDARY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [SECONDARY]),
    ]))
    return [Spacer(1, 10), tbl, Spacer(1, 6)]


def _kv_table(rows: List[tuple], st: dict, cols=(5 * cm, 10.6 * cm)) -> Table:
    """Two-column label/value table."""
    data = [[Paragraph(k, st["label"]), Paragraph(str(v or "—"), st["value"])]
            for k, v in rows]
    tbl = Table(data, colWidths=list(cols))
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_BG]),
    ]))
    return tbl


def _generic_table(headers: List[str], rows: List[List], st: dict) -> Table:
    col_w = (PAGE_W - 2 * MARGIN) / len(headers)
    header_row = [Paragraph(h, st["bold"]) for h in headers]
    body_rows  = [[Paragraph(str(cell or "—"), st["normal"]) for cell in row]
                  for row in rows]
    tbl = Table([header_row] + body_rows, colWidths=[col_w] * len(headers))
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0), PRIMARY),
        ("TEXTCOLOR",     (0, 0), (-1,  0), WHITE),
        ("FONTNAME",      (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d8e4")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    return tbl


# ══════════════════════════════════════════════
#  Cover page
# ══════════════════════════════════════════════
def _cover_page(user: User, st: dict) -> List:
    story = []

    # Big banner
    banner = Table(
        [
            [Paragraph("Medical Record Report", st["title"])],
            [Paragraph("Smart Medical Assistant Platform", st["subtitle"])],
            [Paragraph(datetime.utcnow().strftime("%B %d, %Y"), st["subtitle"])],
        ],
        colWidths=[PAGE_W - 2 * MARGIN],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(Spacer(1, 1 * cm))
    story.append(banner)
    story.append(Spacer(1, 0.8 * cm))

    # Patient info box
    full_name = getattr(user, 'full_name', None) or getattr(user, 'email', str(user.uuid))
    rows = [
        ("Patient Name",  full_name),
        ("Patient ID",    str(user.uuid)),
        ("Email",         getattr(user, "email", "—")),
        ("Date of Birth", str(getattr(user, "date_of_birth", "—"))),
        ("Gender",        str(getattr(user, "gender", "—"))),
        ("Phone",         str(getattr(user, "phone", "—"))),
        ("Report Date",   datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
    ]
    story.append(_kv_table(rows, st))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "This document contains confidential patient health information. "
        "Unauthorised disclosure is strictly prohibited.",
        st["small"],
    ))
    story.append(PageBreak())
    return story


# ══════════════════════════════════════════════
#  Section builders
# ══════════════════════════════════════════════
def _medical_record_section(record: Optional[MedicalRecord], st: dict) -> List:
    story = _section_bar("📋  Medical Record Summary", st)
    if not record or not record.record:
        story.append(Paragraph("No medical record data on file.", st["normal"]))
        return story

    data = record.record if isinstance(record.record, dict) else {}
    rows = [(k.replace("_", " ").title(), v) for k, v in data.items()]
    if rows:
        story.append(_kv_table(rows, st))
    else:
        story.append(Paragraph("Record exists but contains no fields.", st["normal"]))
    return story


def _diabetes_section(diagnostics: List[Diagnostic], st: dict) -> List:
    story = _section_bar("🩸  Diabetes Analysis Results", st)
    if not diagnostics:
        story.append(Paragraph("No diabetes analyses recorded.", st["normal"]))
        return story

    headers = ["Date", "Glucose", "BMI", "Blood Pressure", "Age", "Risk", "Confidence"]
    rows = []
    for d in diagnostics:
        result: Optional[DiagnosticResult] = d.result
        risk       = getattr(result, "risk_level", "—") if result else "—"
        confidence = f"{float(getattr(result, 'confidence', 0)) * 100:.0f}%" if result else "—"
        rows.append([
            d.created_at.strftime("%Y-%m-%d") if hasattr(d, "created_at") and d.created_at else "—",
            getattr(d, "Glucose",          "—"),
            getattr(d, "BMI",              "—"),
            getattr(d, "BloodPressure",    "—"),
            getattr(d, "Age",              "—"),
            "HIGH RISK" if str(risk) == "1" else "LOW RISK",
            confidence,
        ])
    story.append(_generic_table(headers, rows, st))
    return story


def _xray_section(radiology_list: List[Radiology], st: dict, upload_dir: str) -> List:
    story = _section_bar("🩻  Radiology / X-Ray Reports", st)
    if not radiology_list:
        story.append(Paragraph("No radiology studies on file.", st["normal"]))
        return story

    available_w = PAGE_W - 2 * MARGIN
    img_w = min(10 * cm, available_w * 0.55)

    for rad in radiology_list:
        date_str = rad.created_at.strftime("%Y-%m-%d") if hasattr(rad, "created_at") and rad.created_at else "—"
        story.append(Paragraph(f"Study — {date_str}  |  Body part: {rad.body_part or '—'}", st["bold"]))
        story.append(Spacer(1, 4))

        # Findings table
        findings: List[RadiologyFinding] = rad.findings or []
        if findings:
            f_headers = ["Finding", "Confidence"]
            f_rows    = [
                [f.finding_name, f"{float(f.confidence_score)*100:.1f}%"]
                for f in findings
            ]
            story.append(_generic_table(f_headers, f_rows, st))
        else:
            story.append(Paragraph("No findings recorded.", st["normal"]))

        # Embed image if it exists
        img_path = rad.image_path
        if img_path and os.path.isfile(img_path):
            try:
                img = Image(img_path, width=img_w, height=img_w * 0.85)
                img.hAlign = "LEFT"
                story.append(Spacer(1, 6))
                story.append(img)
            except Exception:
                story.append(Paragraph("[Image could not be rendered]", st["small"]))

        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d0d8e4")))
        story.append(Spacer(1, 4))

    return story


def _appointments_section(bookings: List[Booking], st: dict) -> List:
    story = _section_bar("📅  Appointments", st)
    if not bookings:
        story.append(Paragraph("No appointment records found.", st["normal"]))
        return story

    headers = ["Date", "Time", "Doctor", "Clinic", "Status", "Notes"]
    rows = []
    for b in bookings:
        slot      = getattr(b, "slot", None)
        doctor    = getattr(b, "doctor", None)
        clinic    = getattr(b, "clinic", None)
        notes_obj = getattr(b, "appointment_notes", None)

        slot_date   = str(getattr(slot, "slot_date",       "—")) if slot else "—"
        slot_time   = str(getattr(slot, "slot_start_time", "—")) if slot else "—"
        doctor_name = getattr(doctor, "full_name", "—") if doctor else "—"
        clinic_name = getattr(clinic, "name", "Independent") if clinic else "Independent"
        status      = str(getattr(b, "booking_status", "—"))
        notes       = (getattr(notes_obj, "notes", None) or "—") if notes_obj else "—"

        rows.append([slot_date, slot_time, doctor_name, clinic_name, status, notes])

    story.append(_generic_table(headers, rows, st))
    return story


# ══════════════════════════════════════════════
#  Master builder
# ══════════════════════════════════════════════
def build_patient_pdf(
    user: User,
    record: Optional[MedicalRecord],
    diagnostics: List[Diagnostic],
    radiology_list: List[Radiology],
    appointments: List[Booking],
    upload_dir: str = "uploads",
) -> bytes:
    buffer = io.BytesIO()
    full_name = getattr(user, 'full_name', None) or getattr(user, 'email', str(user.uuid))
    doc   = _build_doc(buffer, full_name, str(user.uuid))
    st    = _styles()
    story: List = []

    story += _cover_page(user, st)
    story += _medical_record_section(record, st)
    story.append(Spacer(1, 12))
    story += _diabetes_section(diagnostics, st)
    story.append(Spacer(1, 12))
    story += _xray_section(radiology_list, st, upload_dir)
    story.append(Spacer(1, 12))
    story += _appointments_section(appointments, st)

    doc.build(story)
    return buffer.getvalue()


# ══════════════════════════════════════════════
#  Endpoints
# ══════════════════════════════════════════════
def _stream(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _fetch_patient_data(user: User, db: Session):
    """Return (record, diagnostics, radiology_list, appointments) for a user."""
    record      = db.query(MedicalRecord).filter(MedicalRecord.user_id == user.uuid).first()
    diagnostics = db.query(Diagnostic).filter(Diagnostic.user_id == user.uuid).order_by(Diagnostic.id.desc()).all()
    radiology   = (
        db.query(Radiology)
        .filter(Radiology.user_id == user.uuid)
        .order_by(Radiology.id.desc())
        .all()
    )
    appointments = (
        db.query(Booking)
        .filter(Booking.user_id == user.uuid)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return record, diagnostics, radiology, appointments


@router.get("/me/export-pdf", summary="Export my medical record as PDF")
def export_my_pdf(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record, diagnostics, radiology, appointments = _fetch_patient_data(current_user, db)
    pdf_bytes = build_patient_pdf(current_user, record, diagnostics, radiology, appointments)
    filename  = f"medical_record_{current_user.uuid}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return _stream(pdf_bytes, filename)


@router.get("/user/{user_id}/export-pdf", summary="Export a patient's record (doctor/admin)")
def export_user_pdf(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ── authorisation ──────────────────────────
    if current_user.role == RoleEnum.doctor or current_user.role == RoleEnum.clinic:
        # TODO: verify an active booking exists between doctor and patient
        pass
    elif current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorised to export this record")

    patient = db.query(User).filter(User.uuid == user_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    record, diagnostics, radiology, appointments = _fetch_patient_data(patient, db)
    pdf_bytes = build_patient_pdf(patient, record, diagnostics, radiology, appointments)
    filename  = f"medical_record_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return _stream(pdf_bytes, filename)