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

# --- 1. TÜRKÇE FONT DESTEĞİ (KESİN ÇÖZÜM) ---
@st.cache_resource
def turkce_font_yukle():
    # Fontları güvenli bir kaynaktan çekiyoruz
    url_reg = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
    url_bold = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    try:
        reg_content = requests.get(url_reg).content
        bold_content = requests.get(url_bold).content
        pdfmetrics.registerFont(TTFont('Roboto-Regular', io.BytesIO(reg_content)))
        pdfmetrics.registerFont(TTFont('Roboto-Bold', io.BytesIO(bold_content)))
        return 'Roboto-Regular', 'Roboto-Bold'
    except:
        # İnternet hatası olursa standart fonta döner (ama karakter bozulabilir)
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

    if st.button("Raporu Hazırla"):
        try:
            # Hesaplamalar
            s_satir, s_t = satir_olustur("Su", s_olcu, BIRIM_SU, s_oran)
            k_satir, k_t = satir_olustur("Kanal", k_olcu, BIRIM_KANAL, k_oran)
            kes_t = kesif_sayi * BIRIM_KESIF
            kes_satir = ["Keşif", f"{kesif_sayi}", f"{BIRIM_KESIF:,.2f}", "-", f"{kes_t:,.2f} TL"]
            toplam = s
