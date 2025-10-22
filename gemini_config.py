import google.generativeai as genai
import streamlit as st
import os
import json
import uuid # Menggunakan uuid untuk ID yang unik dan stabil

# --- PENTING: PENGATURAN API KEY ---
# API Key diambil dari Streamlit Secrets, yang telah Anda atur di Advanced Settings.
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    # Error ini muncul jika Secret Key tidak diatur
    st.error("❌ GEMINI_API_KEY tidak ditemukan di Streamlit Secrets. Harap atur kunci Anda di Advanced Settings.")
    st.stop()

# Inisialisasi Klien Gemini
try:
    genai.configure(api_key=API_KEY)
    client = genai.Client()
except Exception as e:
    st.error(f"❌ Gagal menginisialisasi Gemini Client: {e}")
    st.stop()

# Model yang digunakan
MODEL_LKPD = "gemini-2.5-flash"
MODEL_QA = "gemini-2.5-flash"

# --- Fungsi Manajemen File LKPD ---
LKPD_DIR = "lkpd_outputs" # Nama folder untuk menyimpan output LKPD

def check_lkpd_existence():
    """Memastikan folder LKPD_DIR ada. Sangat penting untuk deployment."""
    if not os.path.exists(LKPD_DIR):
        try:
            # os.makedirs membuat folder secara rekursif jika belum ada
            os.makedirs(LKPD_DIR)
            print(f"Direktori '{LKPD_DIR}' berhasil dibuat.")
            return True
        except OSError as e:
            # Streamlit Cloud memiliki izin terbatas, ini menangani error jika gagal
            print(f"ERROR: Gagal membuat direktori '{LKPD_DIR}': {e}")
            return False
    return True

def save_lkpd(lkpd_id, data):
    """Menyimpan data LKPD ke file JSON."""
    if check_lkpd_existence():
        filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"ERROR: Gagal menyimpan file LKPD: {e}")
            return False
    return False

def load_lkpd(lkpd_id):
    """Memuat data LKPD dari file JSON."""
    filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: Gagal memuat file LKPD: {e}")
            return None
    return None

# --- Fungsi Generasi LKPD menggunakan Gemini ---
def generate_lkpd(theme):
    """Membuat struktur LKPD interaktif menggunakan Gemini AI."""
    st.info("AI sedang merancang LKPD Anda... Harap tunggu sebentar.")
    
    prompt = f"""
    Anda adalah ahli kurikulum dan guru fisika/sains yang berpengalaman.
    Tugas Anda adalah membuat kerangka (outline) untuk Lembar Kerja Peserta Didik (LKPD) yang interaktif, menarik, dan terstruktur dengan baik.
    LKPD ini harus berfokus pada tema/topik: "{theme}".

    Hasilkan output dalam format JSON MURNI (tidak ada teks atau komentar di luar kurung kurawal) yang mengikuti skema berikut:

    {{
      "judul": "Judul LKPD yang Menarik dan Relevan",
      "tujuan_pembelajaran": ["Daftar tujuan pembelajaran yang jelas dan terukur"],
      "materi_singkat": "Penjelasan singkat (1-2 paragraf) tentang konsep dasar tema",
      "kegiatan": [
        {{
          "nama": "Nama Kegiatan (misalnya: Eksplorasi Konsep)",
          "petunjuk": "Petunjuk langkah-langkah yang harus dilakukan siswa",
          "pertanyaan_pemantik": [
            {{
              "pertanyaan": "Pertanyaan yang memancing diskusi atau pemikiran",
              "tipe": "essay"
            }}
          ],
          "tugas_interaktif": [
            "Tugas praktikum sederhana/observasi yang dapat dilakukan siswa (maksimal 2)"
          ]
        }}
      ]
    }}

    Tambahkan minimal 2-3 objek kegiatan serupa (di dalam array "kegiatan") untuk membuat LKPD yang komprehensif. Pastikan output Anda adalah JSON yang valid.
    """
    
    try:
        # Panggil Gemini API
        response = client.models.generate_content(
            model=MODEL_LKPD,
            contents=prompt
        )
        
        # Membersihkan respons untuk memastikan JSON valid
        json_string = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_string)
    
    except Exception as e:
        st.error(f"❌ Gagal menghasilkan LKPD dari AI. Error: {e}")
        st.error("Pastikan format prompt dan kunci API Gemini Anda benar.")
        return None
