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

# --- 1. BİRİM FİYATLAR ---
BIRIM_SU = 3421.76
BIRIM_KANAL = 5974.26
BIRIM_KESIF = 2082.25

# --- FONT AYARI (İnternet/Bulut Uyumlu) ---
# Sunucularda Windows fontları (C:\Windows\Fonts) olmadığı için 
# standart Helvetica fontlarını kullanıyoruz.
FONT_NAME, FONT_NAME_BOLD = 'Helvetica', 'Helvetica-Bold'

st.set_page_config(page_title="Katılım Bedelleri Hesaplama Sistemi", layout="wide")
st.title("🏛️ Katılım Bedelleri Hesaplama Sistemi")

# --- 2. FONKSİYONLAR ---
def satir_hazirla(isim, olcu, birim, secim):
    if secim in ["Meskun", "Tarım Alanı", "Muaf", "Ücretsiz"]:
        return [isim, "", "", secim, ""], 0.0
    oran_kat = 1.0 if secim == "%100" else 0.25 if secim == "%25" else 0.0
    tutar = olcu * birim * oran_kat
    if secim == "Seçiniz...":
        return [isim, f"{olcu}", f"{birim:,.2f}", "-", "0.00 TL"], 0.0
    return [isim, f"{olcu}", f"{birim:,.2f}", secim, f"{tutar:,.2f} TL"], tutar

# --- 3. ADIM: PDF KAYNAĞI SEÇİMİ ---
st.subheader("1. PDF Kaynağını Belirleyin")
kaynak_secimi = st.radio("PDF'i nasıl getireceksiniz?", ["Dosya Yükle", "URL Adresi Yapıştır"], horizontal=True)

pdf_file_content = None

if kaynak_secimi == "Dosya Yükle":
    yuklenen_dosya = st.file_uploader("Bilgisayarınızdan PDF seçin", type="pdf")
    if yuklenen_dosya:
        pdf_file_content = yuklenen_dosya.read()
else:
    url_adresi = st.text_input("Dilekçe PDF URL'sini buraya yapıştırın:", placeholder="https://example.com/dilekce.pdf")
    if url_adresi:
        try:
            response = requests.get(url_adresi, timeout=45)
            if response.status_code == 200:
                pdf_file_content = response.content
                st.success("✅ PDF başarıyla URL'den çekildi!")
            else:
                st.error("❌ PDF çekilemedi. Bağlantıyı kontrol edin.")
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")

st.divider()

# --- 4. ADIM: HESAPLAMA PARAMETRELERİ ---
st.subheader("📊 Hesaplama Parametreleri")
oran_listesi = ["Seçiniz...", "%100", "%25", "Meskun", "Tarım Alanı", "Muaf", "Ücretsiz"]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**💧 Su Satırı**")
    su_olcu = st.number_input("Su Ölçü (m)", min_value=0.0, value=0.0, step=0.1, key="su_m")
    su_oran_secim = st.selectbox("Su Oranı", oran_listesi, key="su_o")
    su_aciklama = "SU ABONESİ OLAMAZ" if su_oran_secim in ["%25", "Tarım Alanı"] else ""
    if su_aciklama: st.markdown(f"**:red[{su_aciklama}]**")

with col2:
    st.markdown("**🚽 Kanal Satırı**")
    kanal_olcu = st.number_input("Kanal Ölçü (m)", min_value=0.0, value=0.0, step=0.1, key="ka_m")
    kanal_oran_secim = st.selectbox("Kanal Oranı", oran_listesi, key="ka_o")

col3, col4 = st.columns(2)
with col3:
    st.markdown("**🔍 Keşif Bilgisi**")
    kesif_adet = st.number_input("Keşif Sayısı (Adet)", min_value=0, value=0, step=1, key="ke_a")

st.markdown("**📝 Genel Notlar ve Açıklama**")
kanal_aciklama = st.text_area("Raporun altına eklenecek detaylı not:", height=100)

# --- 5. ADIM: PDF OLUŞTURMA ---
if st.button("🚀 PDF Raporunu Oluştur"):
    if pdf_file_content is None:
        st.error("Lütfen önce bir PDF dosyası yükleyin veya geçerli bir URL girin!")
    else:
        try:
            su_satiri, su_t = satir_hazirla("Su", su_olcu, BIRIM_SU, su_oran_secim)
            kanal_satiri, kanal_t = satir_hazirla("Kanal", kanal_olcu, BIRIM_KANAL, kanal_oran_secim)
            kesif_t = kesif_adet * BIRIM_KESIF
            
            kesif_