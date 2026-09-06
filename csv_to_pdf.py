import io
import zipfile
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Sayfa Yapılandırması
st.set_page_config(page_title="Daily Order PDF Generator", layout="wide")

st.title("📦 Daily Order Processing & PDF Generator")
st.write("Upload your daily CSV file to clean data, perform calculations, and export PDFs.")

# 1. Dosya Yükleme Alanı
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

def generate_pdf_bytes(row):
    """Tek bir satır için bellekte (in-memory) PDF üretir."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=12
    )
    
    story = []
    order_id = str(row.get('Order_ID', 'N/A')).strip()
    
    # Başlık ve Müşteri Bilgisi
    story.append(Paragraph(f"ORDER SUMMARY - #{order_id}", title_style))
    story.append(Spacer(1, 10))
    customer_info = f"<b>Customer:</b> {row['Customer_Name']}<br/><b>Date:</b> {pd.Timestamp.now().strftime('%Y-%m-%d')}"
    story.append(Paragraph(customer_info, styles['Normal']))
    story.append(Spacer(1, 15))

    # Tablo
    table_data = [
        ["Description", "Quantity", "Unit Price", "Subtotal"],
        [
            str(row.get('Item_Description', 'Standard Product')),
            str(row['Quantity']),
            f"${row['Unit_Price']:.2f}",
            f"${row['Subtotal']:.2f}"
        ],
        ["", "", "Tax (20%):", f"${row['Tax']:.2f}"],
        ["", "", "Total Amount:", f"${row['Total_Amount']:.2f}"]
    ]

    t = Table(table_data, colWidths=[200, 80, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#EDF2F7")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('FONTNAME', (2, 2), (-1, -1), 'Helvetica-Bold'),
    ]))

    story.append(t)
    doc.build(story)
    
    buffer.seek(0)
    return buffer

if uploaded_file is not None:
    # 2. CSV Okuma ve Veri Temizleme (Pandas)
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    
    df['Customer_Name'] = df['Customer_Name'].fillna('Unknown Customer').astype(str).str.strip()
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0).astype(int)
    df['Unit_Price'] = pd.to_numeric(df['Unit_Price'], errors='coerce').fillna(0.0)

    # 3. İkincil Hesaplamalar
    df['Subtotal'] = df['Quantity'] * df['Unit_Price']
    df['Tax'] = df['Subtotal'] * 0.20
    df['Total_Amount'] = df['Subtotal'] + df['Tax']

    # Ekranda Gösterim
    st.subheader("Data Preview & Calculated Totals")
    st.dataframe(df, use_container_width=True)

    # 4. Tüm PDF'leri ZIP Dosyasına Paketleme
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, row in df.iterrows():
            order_id = str(row.get('Order_ID', f"ORD-{idx+1}")).strip()
            pdf_data = generate_pdf_bytes(row)
            zip_file.writestr(f"Order_{order_id}.pdf", pdf_data.getvalue())

    zip_buffer.seek(0)

    # 5. İndirme Butonu
    st.success("All order PDFs generated successfully!")
    st.download_button(
        label="📥 Download All PDFs (ZIP)",
        data=zip_buffer,
        file_name="Daily_Orders_PDFs.zip",
        mime="application/zip"
    )