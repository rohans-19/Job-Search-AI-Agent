"""
exporters.py
------------
Export helpers for the Job Search AI Agent.

Produces downloadable artifacts:
  - PDF job list           : a formatted report of recommended jobs.
  - PDF resume profile     : a one-page skills / profile summary ("resume version").
  - CSV                    : raw tabular export of any list-of-dicts.

PDF generation uses ReportLab. If ReportLab is not installed the PDF helpers
return ``None`` so callers can fall back gracefully (e.g. offer CSV only).
"""

from __future__ import annotations

import io
import csv
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )
    _REPORTLAB = True
except ImportError:  # pragma: no cover - optional dependency
    _REPORTLAB = False

_BRAND = "#3b82f6"
_DARK = "#1e293b"
_MUTED = "#64748b"


def is_pdf_available() -> bool:
    """True if ReportLab is installed and PDF export is possible."""
    return _REPORTLAB


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def jobs_to_csv(jobs: list[dict]) -> bytes:
    """Serialise a list of job dicts to UTF-8 CSV bytes (BOM for Excel)."""
    if not jobs:
        return "No data".encode("utf-8-sig")
    fieldnames = list({k for job in jobs for k in job.keys()})
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for job in jobs:
        writer.writerow({k: job.get(k, "") for k in fieldnames})
    return buf.getvalue().encode("utf-8-sig")


# ---------------------------------------------------------------------------
# Shared PDF styles
# ---------------------------------------------------------------------------

def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="HeroTitle", fontName="Helvetica-Bold", fontSize=20,
        textColor=colors.HexColor(_DARK), spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="Sub", fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor(_MUTED), spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="SectionH", fontName="Helvetica-Bold", fontSize=12,
        textColor=colors.HexColor(_BRAND), spaceBefore=12, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="JobTitle", fontName="Helvetica-Bold", fontSize=11,
        textColor=colors.HexColor(_DARK), spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="Meta", fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor(_MUTED), spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="Body9", fontName="Helvetica", fontSize=9,
        textColor=colors.HexColor("#334155"), spaceAfter=4, leading=12,
    ))
    return styles


# ---------------------------------------------------------------------------
# Job-list PDF
# ---------------------------------------------------------------------------

def jobs_to_pdf(jobs: list[dict], role: str = "", location: str = "") -> bytes | None:
    """
    Build a polished PDF report of recommended jobs.

    Returns PDF bytes, or None if ReportLab is unavailable.
    """
    if not _REPORTLAB:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title="Job Search AI — Recommendations",
    )
    s = _styles()
    flow = []

    flow.append(Paragraph("Job Search AI — Recommendations", s["HeroTitle"]))
    subtitle = "Generated " + datetime.now().strftime("%d %b %Y, %H:%M")
    if role:
        subtitle = f"Role: {role}" + (f"  |  Location: {location}" if location else "") + "  |  " + subtitle
    flow.append(Paragraph(subtitle, s["Sub"]))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    flow.append(Spacer(1, 6))

    if not jobs:
        flow.append(Paragraph("No jobs to display.", s["Body9"]))
        doc.build(flow)
        return buf.getvalue()

    for i, job in enumerate(jobs, 1):
        title = f"#{i}  {job.get('title', 'N/A')}"
        flow.append(Paragraph(_esc(title), s["JobTitle"]))
        flow.append(Paragraph(
            _esc(f"{job.get('company', 'Unknown')}  ·  {job.get('location', 'Unknown')}"),
            s["Meta"],
        ))

        meta_bits = []
        if job.get("salary_label"):
            meta_bits.append(f"Salary: {job['salary_label']}")
        if job.get("recommendation_score") is not None:
            meta_bits.append(f"Rec score: {job['recommendation_score']}")
        if job.get("source"):
            meta_bits.append(f"Source: {job['source']}")
        if meta_bits:
            flow.append(Paragraph(_esc("  |  ".join(meta_bits)), s["Meta"]))

        matched = job.get("matched_skills") or []
        if matched:
            flow.append(Paragraph(
                _esc("Matched skills: " + ", ".join(matched[:10])), s["Body9"],
            ))

        culture = (
            f"WLB: {job.get('culture_wlb', 'N/A')}  ·  "
            f"Growth: {job.get('culture_growth', 'N/A')}  ·  "
            f"Remote: {job.get('culture_remote', 'N/A')}"
        )
        flow.append(Paragraph(_esc(culture), s["Body9"]))
        flow.append(Spacer(1, 4))
        flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#eef2f7")))
        flow.append(Spacer(1, 4))

    doc.build(flow)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Resume / profile PDF ("resume version")
# ---------------------------------------------------------------------------

def resume_profile_to_pdf(
    skills: list[str],
    target_role: str = "",
    summary: str = "",
    categorized: dict[str, list[str]] | None = None,
    highlights: list[str] | None = None,
) -> bytes | None:
    """
    Build a one-page candidate profile / tailored "resume version" PDF from the
    skills extracted by the pipeline.

    Returns PDF bytes, or None if ReportLab is unavailable.
    """
    if not _REPORTLAB:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title="Candidate Skills Profile",
    )
    s = _styles()
    flow = []

    heading = "Candidate Skills Profile"
    if target_role:
        heading += f" — {target_role}"
    flow.append(Paragraph(_esc(heading), s["HeroTitle"]))
    flow.append(Paragraph("Generated by Job Search AI · " + datetime.now().strftime("%d %b %Y"), s["Sub"]))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))

    if summary:
        flow.append(Paragraph("Professional Summary", s["SectionH"]))
        flow.append(Paragraph(_esc(summary), s["Body9"]))

    if highlights:
        flow.append(Paragraph("Key Highlights", s["SectionH"]))
        for h in highlights:
            flow.append(Paragraph("• " + _esc(h), s["Body9"]))

    if categorized:
        flow.append(Paragraph("Skills by Category", s["SectionH"]))
        rows = [[Paragraph(f"<b>{_esc(cat)}</b>", s["Body9"]),
                 Paragraph(_esc(", ".join(items)), s["Body9"])]
                for cat, items in categorized.items() if items]
        if rows:
            tbl = Table(rows, colWidths=[45 * mm, 120 * mm])
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#eef2f7")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            flow.append(tbl)
    elif skills:
        flow.append(Paragraph("Detected Skills", s["SectionH"]))
        flow.append(Paragraph(_esc(", ".join(skills)), s["Body9"]))

    if not skills and not summary:
        flow.append(Paragraph("No skills detected from the resume.", s["Body9"]))

    doc.build(flow)
    return buf.getvalue()


def _esc(text: str) -> str:
    """Escape characters that break ReportLab's mini-HTML paragraph parser."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))
