import streamlit as st
from gemini_config import generate_lkpd, check_lkpd_existence, load_lkpd, is_api_key_set
import os

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="LMS Interaktif EduAI",
    page_icon="🧠",
    layout="wide"
)

# Judul dan Deskripsi
st.title("🧠 LMS Interaktif Bertenaga Gemini AI")
st.markdown("Aplikasi untuk guru (pembuat LKPD) dan siswa (pengerja LKPD) yang dapat berinteraksi secara real-time.")

# --- Pengecekan API Key ---
if not is_api_key_set():
    st.error("API Key Gemini belum diatur di 'Secrets'. Aplikasi tidak dapat berfungsi. Silakan atur GEMINI_API_KEY di Streamlit Secrets.")
    st.stop()

# --- Fungsi Pilihan Peran ---
role = st.sidebar.selectbox("Pilih Peran Anda", ["Guru", "Siswa"])

if role == "Guru":
    st.sidebar.header("Mode Guru (Pembuat LKPD)")

    # Form Pembuatan LKPD
    st.header("1. Buat LKPD Baru")
    with st.form("lkpd_form"):
        tema = st.text_input("Tema / Topik Pembelajaran", help="Contoh: Gerak Lurus Beraturan, Hukum Newton I, Siklus Air")
        kelas = st.selectbox("Tingkat Kelas", ["SD", "SMP", "SMA"])
        materi = st.text_area("Materi Tambahan (Opsional)", help="Berikan konteks atau batasan spesifik jika diperlukan.")
        
        submitted = st.form_submit_button("🚀 Generate LKPD")

        if submitted and tema:
            # Panggil generate_lkpd dengan safety check untuk API Key
            if is_api_key_set():
                with st.spinner(f"Sedang membuat LKPD untuk topik '{tema}'..."):
                    lkpd_id, lkpd_content = generate_lkpd(tema, kelas, materi)
                    
                if lkpd_id:
                    st.success("LKPD berhasil dibuat!")
                    st.markdown(f"**Bagikan ID ini kepada siswa:** `<span style='color:#FF4B4B; font-weight:bold;'>{lkpd_id}</span>`", unsafe_allow_html=True)
                    st.info("Siswa perlu memilih peran 'Siswa' dan memasukkan ID di atas.")
                    
                    # Menampilkan LKPD yang baru dibuat (hanya preview)
                    st.subheader("Preview LKPD yang Dibuat:")
                    st.markdown(lkpd_content)
                else:
                    st.error("Gagal membuat LKPD. Periksa log atau koneksi Gemini API Anda.")
            # else: sudah dihandle oleh st.stop() di awal

elif role == "Siswa":
    st.sidebar.header("Mode Siswa (Pengerja LKPD)")

    st.header("2. Kerjakan LKPD")
    
    lkpd_id_input = st.text_input("Masukkan ID LKPD dari Guru", max_chars=8)
    
    if lkpd_id_input:
        lkpd_content = check_lkpd_existence(lkpd_id_input)
        
        if lkpd_content:
            st.success(f"LKPD ID '{lkpd_id_input}' berhasil dimuat!")
            st.subheader("Lembar Kerja Peserta Didik (LKPD)")
            st.markdown(lkpd_content)
            
            # Form Jawaban Siswa
            with st.form("answer_form"):
                jawaban_siswa = st.text_area("Tuliskan Jawaban Anda di Sini", height=300)
                submit_answer = st.form_submit_button("Kirim Jawaban")
                
                if submit_answer and jawaban_siswa:
                    st.session_state[f'answer_{lkpd_id_input}'] = jawaban_siswa
                    st.success("Jawaban Anda telah tersimpan. Guru Anda dapat memeriksanya.")
                    
                    # Tambahkan fitur interaktif dari Gemini (koreksi sederhana)
                    # NOTE: Koreksi ini menggunakan Gemini, pastikan API Key sudah ada
                    if is_api_key_set():
                        with st.spinner("Memproses jawaban dan memberikan umpan balik instan..."):
                            feedback = load_lkpd(
                                lkpd_id_input, 
                                mode="feedback", 
                                user_answer=jawaban_siswa
                            )
                            st.subheader("Umpan Balik Instan (Eksperimental)")
                            st.info(feedback)
                    else:
                        st.warning("Tidak dapat memberikan umpan balik instan karena Gemini API Key belum diatur.")
        else:
            st.error(f"LKPD dengan ID '{lkpd_id_input}' tidak ditemukan. Pastikan ID sudah benar.")
