from __future__ import annotations

import csv
import io
from datetime import date

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from app.schemas.schemas import ReportRow


def to_csv(rows: list[ReportRow]) -> bytes:
    output = io.StringIO()
    if not rows:
        writer = csv.writer(output)
        writer.writerow(["employee_code", "full_name", "status"])
        return output.getvalue().encode()
    fieldnames = list(rows[0].model_dump(mode="json", by_alias=True).keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row.model_dump(mode="json", by_alias=True))
    return output.getvalue().encode()


def to_excel(rows: list[ReportRow]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    if rows:
        headers = list(rows[0].model_dump(mode="json", by_alias=True).keys())
        ws.append(headers)
        for row in rows:
            ws.append(list(row.model_dump(mode="json", by_alias=True).values()))
    else:
        ws.append(["employee_code", "full_name", "status"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def to_pdf(rows: list[ReportRow], title: str = "Attendance Report") -> bytes:
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    data = [["Code", "Name", "Dept", "Date", "Check In", "Check Out", "Status", "Late", "OT"]]
    if not rows:
        data.append(["—", "No records", "", "", "", "", "", "", ""])
    for r in rows[:500]:
        data.append([
            r.employee_code,
            r.full_name[:28] if r.full_name else "",
            (r.department or "")[:16],
            str(r.attendance_date or ""),
            (r.check_in or "")[:16],
            (r.check_out or "")[:16],
            r.status,
            str(r.late_minutes),
            str(r.overtime_minutes),
        ])
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    story.append(table)
    doc.build(story)
    return buf.getvalue()
