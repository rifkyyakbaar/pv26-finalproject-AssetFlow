import csv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


def export_csv(rows, path, report_name):
    if not rows:
        rows = []
    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        if rows:
            fieldnames = list(rows[0].keys())
        else:
            fieldnames = ["empty"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def export_pdf(rows, path, title):
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    if not rows:
        story.append(Paragraph("Tidak ada data untuk diekspor.", styles["Normal"]))
        doc.build(story)
        return

    headers = list(rows[0].keys())
    data = [headers]
    for row in rows:
        data.append([str(row.get(key, "")) for key in headers])

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B7BEC")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )
    story.append(table)
    doc.build(story)
