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
def turkce_font_hazirla():
    font_url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
    font_bold_url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    try:
        f_reg = requests.get(font_url).content
        f_bold = requests.get(font_bold_url).content
        pdfmetrics.registerFont(TTFont('Roboto', io.BytesIO(f_reg)))
        pdfmetrics.registerFont(TTFont('Roboto-Bold', io.BytesIO(f_bold)))
        return 'Roboto', 'Roboto-Bold'
    except:
        return 'Helvetica', 'Helvetica-Bold'

FONT_NAME, FONT_NAME_BOLD = turkce_font_hazirla()

# --- 2. BİRİM FİYATLAR ---
BIRIM_SU = 3421.76
BIRIM_KANAL = 5974.26
BIRIM_KESIF = 2082.25

st.set_page_config(page_title="Katılım Bedelleri Hesaplama Sistemi", layout="wide")
st.title("🏛️ Katılım Bedelleri Hesaplama Sistemi")

# --- 3. FONKSİYONLAR ---
def satir_hazirla(isim, olcu, birim, secim):
    if secim in ["Meskun", "Tarım Alanı", "Muaf", "Ücretsiz"]:
        return [isim, "", "", secim, ""], 0.0
    oran_kat = 1.0 if secim == "%100" else 0.25 if secim == "%25" else 0.0
    tutar = olcu * birim * oran_kat
    if secim == "Seçiniz...":
        return [isim, f"{olcu}", f"{birim:,.2f}", "-", "0.00 TL"], 0.0
    return [isim, f"{olcu}", f"{birim:,.2f}", secim, f"{tutar:,.2f} TL"], tutar

# --- 4. ADIM: PDF KAYNAĞI SEÇİMİ ---
st.subheader("1. PDF Kaynağını Belirleyin")
kaynak_secimi = st.radio("PDF'i nasıl getireceksiniz?", ["Dosya Yükle", "URL Adresi Yapıştır"], horizontal=True)

pdf_file_content = None

if kaynak_secimi == "Dosya Yükle":
    yuklenen_dosya = st.file_uploader("Bilgisayarınızdan PDF seçin", type="pdf")
    if yuklenen_dosya:
        pdf_file_content = yuklenen_dosya.read()
else:
    url_adresi = st.text_input("Dilekçe PDF URL'sini buraya yapıştırın:")
    if url_adresi:
        try:
            response = requests.get(url_adresi, timeout=45)
            if response.status_code == 200:
                pdf_file_content = response.content
                st.success("✅ PDF başarıyla URL'den çekildi!")
        except:
            st.error("❌ PDF çekilemedi.")

st.divider()

# --- 5. ADIM: PARAMETRELER ---
st.subheader("📊 Hesaplama Parametreleri")
oran_listesi = ["Seçiniz...", "%100", "%25", "Meskun", "Tarım Alanı", "Muaf", "Ücretsiz"]

col1, col2 = st.columns(2)
with col1:
    st.markdown("**💧 Su Satırı**")
    su_olcu = st.number_input("Su Ölçü (m)", min_value=0.0, value=0.0, step=0.1, key="su_m")
    su_oran_secim = st.selectbox("Su Oranı", oran_listesi, key="su_o")
    su_aciklama = "SU ABONESİ OLAMAZ" if su_oran_secim in ["%25", "Tarım Alanı"] else ""
    if su_aciklama: st.markdown(f"**:red[{su_aciklama}]**")

with col2
