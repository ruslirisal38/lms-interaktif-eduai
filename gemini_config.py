import google.generativeai as genai
import streamlit as st
import os
import time

# --- Pengecekan dan Inisialisasi API Key ---
# API Key harus diatur di Secrets Streamlit
def is_api_key_set():
    # Menggunakan st.secrets.get() untuk menghindari KeyError jika GEMINI_API_KEY tidak ada
    return st.secrets.get('GEMINI_API_KEY') is not None

def initialize_gemini():
    if is_api_key_set():
        try:
            # Gunakan st.secrets.get() untuk mengambil nilai API Key
            api_key = st.secrets.get('GEMINI_API_KEY')
            genai.configure(api_key=api_key)
            return genai.Client()
        except Exception as e:
            # Jika inisialisasi gagal, tampilkan error di log Streamlit
            print(f"ERROR: Gagal menginisialisasi Gemini Client: {e}")
            return None
    return None

# Panggil inisialisasi hanya sekali
client = initialize_gemini()

# --- Fungsi untuk Membuat LKPD (Mode Guru) ---
def generate_lkpd(tema: str, kelas: str, materi_tambahan: str):
    if not client:
        return None, None

    # Menggunakan ID berbasis timestamp untuk keunikan
    lkpd_id = hex(int(time.time()))[2:10] # ID 8 karakter heksadesimal
    
    # Memastikan LKPD disimpan di session state (bukan di disk, karena Streamlit Cloud read-only)
    if 'lkpd_storage' not in st.session_state:
        st.session_state['lkpd_storage'] = {}

    system_prompt = (
        f"Anda adalah seorang pengembang konten pendidikan yang ahli dalam membuat Lembar Kerja Peserta Didik (LKPD) yang menarik dan berstandar {kelas}. "
        "Tugas Anda adalah membuat satu set LKPD interaktif untuk topik yang diberikan. "
        "Output harus berupa teks format Markdown, BUKAN JSON, yang mencakup Judul, Tujuan Pembelajaran, Instruksi, dan Pertanyaan Kritis."
    )

    user_prompt = (
        f"Buatkan LKPD interaktif untuk tingkat {kelas} dengan topik utama: **{tema}**. "
        f"Materi tambahan/konteks spesifik: {materi_tambahan if materi_tambahan else 'Tidak ada.'}. "
        "Format LKPD harus sebagai berikut:\n"
        "1. Judul (H1)\n"
        "2. Tujuan Pembelajaran (Daftar berpoin)\n"
        "3. Pertanyaan Pemanasan/Apersepsi\n"
        "4. Inti Pertanyaan Kritis (Minimal 3 pertanyaan terbuka yang memicu analisis siswa).\n"
        "Jawab hanya konten LKPD dalam format Markdown, tanpa penjelasan pendahuluan atau penutup."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
            )
        )
        
        lkpd_content = response.text
        
        # Simpan konten di Streamlit session state
        st.session_state['lkpd_storage'][lkpd_id] = {
            'content': lkpd_content,
            'tema': tema,
            'kelas': kelas
        }
        
        return lkpd_id, lkpd_content

    except Exception as e:
        # Tampilkan pesan error yang lebih informatif
        print(f"ERROR: Terjadi error saat memanggil Gemini API: {e}")
        st.error(f"Terjadi error saat memanggil Gemini API. Cek log Streamlit untuk detail.")
        return None, None

# --- Fungsi untuk Memuat LKPD (Mode Siswa) ---
def check_lkpd_existence(lkpd_id: str):
    if 'lkpd_storage' in st.session_state and lkpd_id in st.session_state['lkpd_storage']:
        return st.session_state['lkpd_storage'][lkpd_id]['content']
    return None

def load_lkpd(lkpd_id: str, mode: str, user_answer: str = ""):
    if not client:
        return "Gemini Client tidak terinisialisasi. Cek API Key Anda."
        
    if mode == "feedback":
        lkpd_data = st.session_state['lkpd_storage'].get(lkpd_id)
        if not lkpd_data:
            return "Data LKPD tidak ditemukan di sesi ini."
            
        lkpd_content = lkpd_data['content']
        tema = lkpd_data['tema']

        system_prompt = (
            "Anda adalah asisten koreksi otomatis yang ramah. Berikan umpan balik yang konstruktif dan suportif "
            "terhadap jawaban siswa. Fokus pada elemen yang benar dan berikan saran singkat untuk perbaikan. "
            "Jangan memberikan nilai, cukup umpan balik kualitatif dalam 3-4 kalimat."
        )
        
        user_prompt = (
            f"Berikut adalah LKPD dengan topik '{tema}' dan Jawaban Siswa:\n\n"
            f"--- LKPD ---\n{lkpd_content}\n\n"
            f"--- Jawaban Siswa ---\n{user_answer}\n\n"
            "Berikan umpan balik kualitatif yang membangun dan ringkas untuk jawaban siswa ini."
        )
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                )
            )
            return response.text
        except Exception as e:
            return f"Gagal mendapatkan umpan balik dari Gemini: {e}. Cek log Streamlit untuk detail."

    return "Mode pemuatan tidak dikenal."
