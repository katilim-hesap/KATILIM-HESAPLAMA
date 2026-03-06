import streamlit as st
import io
import requests
import base64
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 1. TÜRKÇE FONT DESTEĞİ (Roboto Fontu) ---
@st.cache_resource
def turkce_font_yukle():
    url_reg = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
    url_bold = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    try:
        reg_content = requests.get(url_reg).content
        bold_content = requests.get(url_bold).content
        pdfmetrics.registerFont(TTFont('Roboto-Regular', io.BytesIO(reg_content)))
        pdfmetrics.registerFont(TTFont('Roboto-Bold', io.BytesIO(bold_content)))
        return 'Roboto-Regular', 'Roboto-Bold'
    except:
        return 'Helvetica', 'Helvetica-Bold'

FONT_REG, FONT_BOLD = turkce_font_yukle()

# --- 2. AYARLAR ---
BIRIM_SU = 3421.76
BIRIM_KANAL = 5974.26
BIRIM_KESIF = 2082.25

st.set_page_config(page_title="Katılım Bedelleri", layout="wide")
st.title("🏛️ Katılım Bedelleri Hesaplama")

def satir_olustur(isim, olcu, birim, secim):
    if secim in ["Meskun", "Tarım Alanı", "Muaf", "Ücretsiz"]:
        return [isim, "", "", secim, ""], 0.0
    oran = 1.0 if secim == "%100" else 0.25 if secim == "%25" else 0.0
    tutar = olcu * birim * oran
    if secim == "Seçiniz...":
        return [isim, f"{olcu}", f"{birim:,.2f}", "-", "0.00 TL"], 0.0
    return [isim, f"{olcu}", f"{birim:,.2f}", secim, f"{tutar:,.2f} TL"], tutar

# --- 3. PDF KAYNAĞI ---
yuklenen_dosya = st.file_uploader("Dilekçe PDF'ini yükleyin", type="pdf")

if yuklenen_dosya:
    pdf_bytes = yuklenen_dosya.read()
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        s_olcu = st.number_input("Su Ölçü (m)", value=0.0)
        s_oran = st.selectbox("Su Oranı", ["Seçiniz...", "%100", "%25", "Meskun", "Muaf"])
    with col2:
        k_olcu = st.number_input("Kanal Ölçü (m)", value=0.0)
        k_oran = st.selectbox("Kanal Oranı", ["Seçiniz...", "%100", "%25", "Meskun", "Muaf"])
    
    kesif_sayi = st.number_input("Keşif Adedi", value=0, step=1)
    notlar = st.text_area("Ek Notlar")

    if st.button("🚀 Raporu Hazırla"):
        try:
            # Hesaplamalar
            s_satir, s_t = satir_olustur("Su", s_olcu, BIRIM_SU, s_oran)
            k_satir, k_t = satir_olustur("Kanal", k_olcu, BIRIM_KANAL, k_oran)
            kes_t = kesif_sayi * BIRIM_KESIF
            kes_satir = ["Keşif", f"{kesif_sayi}", f"{BIRIM_KESIF:,.2f}", "-", f"{kes_t:,.2f} TL"]
            toplam = s_t + k_t + kes_t

            # PDF Çizimi
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            
            # Maskeleme (Eski yazıların üstünü kapatma)
            can.setFillColor(colors.white)
            can.rect(50, 420, 500, 150, fill=1, stroke=0) 

            # Tablo Verisi
            data = [
                ["Tahakkuk Kalemi", "Ölçü", "Birim Fiyat", "Oran", "Tutar"],
                s_satir, k_satir, kes_satir,
                ["GENEL TOPLAM", "", "", "", f"{toplam:,.2f} TL"]
            ]

            # Tablo Stili ve Genişlikleri (Satır uzunluğu buraya sabitlendi)
            table = Table(data, colWidths=[120, 60, 100, 80, 100])
            table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), FONT_REG),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
                ('FONTNAME', (0,-1), (-1,-1), FONT_BOLD),
                ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
                ('ALIGN', (0,-1), (-1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 5),
                ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ]))

            table.wrapOn(can, 400, 200)
            table.drawOn(can, 70, 160)

            # Notlar
            if notlar:
                can.setFont(FONT_REG, 9)
                can.setFillColor(colors.black)
                can.drawString(70, 140, f"Not: {notlar}")

            can.save()
            packet.seek(0)

            # Birleştirme
            yeni_pdf = PdfReader(packet)
            eski_pdf = PdfReader(io.BytesIO(pdf_bytes))
            output = PdfWriter()

            sayfa = eski_pdf.pages[0]
            sayfa.merge_page(yeni_pdf.pages[0])
            output.add_page(sayfa)

            final_pdf = io.BytesIO()
            output.write(final_pdf)
            
            st.success("✅ Rapor Hazır!")
            st.download_button("📥 PDF İndir", final_pdf.getvalue(), "Rapor.pdf")
            
            # Önizleme
            b64 = base64.b64encode(final_pdf.getvalue()).decode()
            pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"⚠️ Hata: {e}")
else:
    st.info("Lütfen hesaplama yapmak için bir PDF dosyası yükleyin.")
