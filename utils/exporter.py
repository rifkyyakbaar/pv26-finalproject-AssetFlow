import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
    doc = SimpleDocTemplate(
        path, 
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#073B3A"),
        spaceAfter=15
    )
    
    story = [Paragraph(title, title_style), Spacer(1, 10)]

    if not rows:
        story.append(Paragraph("Tidak ada data untuk diekspor.", styles["Normal"]))
        doc.build(story)
        return

    raw_headers = list(rows[0].keys())
    
    col_widths_map = {
        "id": 30,
        "item_id": 50,
        "name": 110,
        "item_name": 110,
        "category": 85,
        "quantity": 40,
        "condition": 65,
        "location": 90,
        "description": 130,
        "status": 60,
        "created_at": 100,
        "borrower_name": 115,
        "borrower_id": 85,
        "borrow_date": 70,
        "return_date": 70,
        "notes": 120
    }
    
    header_translations = {
        "id": "ID",
        "item_id": "ID Barang",
        "name": "Nama Barang",
        "item_name": "Nama Barang",
        "category": "Kategori",
        "quantity": "Jumlah",
        "condition": "Kondisi",
        "location": "Lokasi",
        "description": "Keterangan",
        "status": "Status",
        "created_at": "Tgl Dibuat",
        "borrower_name": "Nama Peminjam",
        "borrower_id": "NIM/ID Peminjam",
        "borrow_date": "Tgl Pinjam",
        "return_date": "Tgl Kembali",
        "notes": "Catatan"
    }

    header_para_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1 
    )
    
    cell_para_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1A3038")
    )

    headers_row = []
    for h in raw_headers:
        display_name = header_translations.get(h, h.replace("_", " ").title())
        headers_row.append(Paragraph(display_name, header_para_style))
        
    data = [headers_row]
    
    for row in rows:
        content_row = []
        for key in raw_headers:
            val = str(row.get(key, ""))
            if key == "created_at" and "T" in val:
                try:
                    dt = datetime.fromisoformat(val)
                    val = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            content_row.append(Paragraph(val, cell_para_style))
        data.append(content_row)

    col_widths = []
    for h in raw_headers:
        col_widths.append(col_widths_map.get(h, 80))
        
    printable_width = 769.89
    total_width = sum(col_widths)
    if total_width > printable_width:
        scale_factor = printable_width / total_width
        col_widths = [w * scale_factor for w in col_widths]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#008080")), 
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    
    story.append(table)
    doc.build(story)
