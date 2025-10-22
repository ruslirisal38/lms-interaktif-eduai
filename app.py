import streamlit as st
import google.generativeai as genai
import os
import json
import uuid

# ========== API SETUP - GEMINI 2.5 FLASH (2025 UPDATE) ==========
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")  # FIXED: 2.5 (1.5 retired)
except Exception as e:
    st.error(f"❌ API Error: {e}")
    st.stop()

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="LMS Interaktif EduAI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SESSION STATE ==========
if 'role' not in st.session_state:
    st.session_state.role = none

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("🎓 Pilih Peran Anda")
    selected_role = st.radio("Saya adalah:", ["👨‍🏫 Guru", "👩‍🎓 Siswa"], key="role_radio")
    
    if selected_role and selected_role != st.session_state.role:
        st.session_state.role = selected_role
        st.rerun()

# ========== MAIN PAGE ==========
st.title("🚀 LMS Interaktif dengan Gemini AI")
st.markdown("Platform untuk membuat dan mengisi Lembar Kerja Peserta Didik (LKPD) secara otomatis.")

if not st.session_state.role:
    st.warning("👈 Silakan pilih peran Anda di sidebar untuk memulai.")
    st.stop()

if st.session_state.role == "👨‍🏫 Guru":
    st.header("👨‍🏫 Mode Guru: Buat LKPD Baru")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        theme = st.text_input("Masukkan Tema / Topik Pembelajaran (Contoh: Gerak Lurus, Rantai Makanan)")
    
    with col2:
        if st.button("🚀 Generate LKPD", use_container_width=True):
            if theme:
                with st.spinner("🤖 AI sedang merancang LKPD Anda..."):
                    # Generate LKPD with Gemini 2.5
                    prompt = f"""
                    Buat LKPD interaktif untuk tema "{theme}" dalam format JSON sahaja:
                    {{
                      "judul": "Judul LKPD Menarik",
                      "tujuan_pembelajaran": ["Tujuan 1", "Tujuan 2"],
                      "materi_singkat": "Penjelasan singkat 1 paragraf",
                      "kegiatan": [
                        {{
                          "nama": "Kegiatan 1",
                          "petunjuk": "Petunjuk langkah",
                          "tugas_interaktif": ["Tugas 1", "Tugas 2"],
                          "pertanyaan_pemantik": [
                            {{"pertanyaan": "Pertanyaan 1"}},
                            {{"pertanyaan": "Pertanyaan 2"}}
                          ]
                        }},
                        {{
                          "nama": "Kegiatan 2",
                          "petunjuk": "Petunjuk langkah",
                          "tugas_interaktif": ["Tugas 1"],
                          "pertanyaan_pemantik": [
                            {{"pertanyaan": "Pertanyaan 1"}}
                          ]
                        }}
                      ]
                    }}
                    """
                    try:
                        response = model.generate_content(prompt)
                        json_str = response.text.strip().replace("```json", "").replace("```", "")
                        lkpd_data = json.loads(json_str)
                        
                        # Save LKPD
                        lkpd_id = str(uuid.uuid4())[:8]
                        os.makedirs("lkpd_outputs", exist_ok=True)
                        filepath = os.path.join("lkpd_outputs", f"{lkpd_id}.json")
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(lkpd_data, f, ensure_ascii=False, indent=2)
                        
                        st.session_state.lkpd_data = lkpd_data
                        st.session_state.lkpd_id = lkpd_id
                        st.success(f"✅ LKPD berhasil dibuat! ID: `{lkpd_id}` - Bagikan ke siswa!")
                        
                        # Display LKPD
                        st.markdown("---")
                        st.subheader(f"📋 {lkpd_data['judul']}")
                        st.info(lkpd_data['materi_singkat'])
                        
                        for i, kegiatan in enumerate(lkpd_data['kegiatan'], 1):
                            with st.expander(f"Kegiatan {i}: {kegiatan['nama']}"):
                                st.markdown(f"**Petunjuk:** {kegiatan['petunjuk']}")
                                st.markdown("**Tugas Interaktif:**")
                                for tugas in kegiatan['tugas_interaktif']:
                                    st.markdown(f"• {tugas}")
                                st.markdown("**Pertanyaan Pemantik:**")
                                for q in kegiatan['pertanyaan_pemantik']:
                                    st.markdown(f"❓ {q['pertanyaan']}")
                        
                    except json.JSONDecodeError:
                        st.error("❌ JSON parsing error - AI response invalid.")
                    except Exception as e:
                        st.error(f"❌ Gagal generate LKPD: {e}")
            else:
                st.warning("Mohon masukkan tema terlebih dahulu.")
    
    if 'lkpd_data' in st.session_state:
        st.markdown("---")
        st.subheader("📂 LKPD Saya")
        st.info(f"ID: {st.session_state.lkpd_id}")

elif st.session_state.role == "👩‍🎓 Siswa":
    st.header("👩‍🎓 Mode Siswa: Isi LKPD")
    lkpd_id = st.text_input("Masukkan ID LKPD dari Guru:")
    
    if lkpd_id:
        filepath = os.path.join("lkpd_outputs", f"{lkpd_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                lkpd_data = json.load(f)
            
            st.success(f"✅ LKPD '{lkpd_data['judul']}' dimuat!")
            
            st.markdown("---")
            st.subheader(lkpd_data['judul'])
            st.info(lkpd_data['materi_singkat'])
            
            for i, kegiatan in enumerate(lkpd_data['kegiatan'], 1):
                with st.expander(f"Kegiatan {i}: {kegiatan['nama']}"):
                    st.markdown(f"**Petunjuk:** {kegiatan['petunjuk']}")
                    st.markdown("**Tugas Interaktif:**")
                    for tugas in kegiatan['tugas_interaktif']:
                        st.markdown(f"• {tugas}")
                    
                    st.markdown("**Pertanyaan Pemantik - Isi Jawaban Anda:**")
                    for j, q in enumerate(kegiatan['pertanyaan_pemantik']):
                        key = f"ans_{i}_{j}"
                        st.text_area(f"{j+1}. {q['pertanyaan']}", key=key, height=80)
            
            if st.button("✨ Kirim Jawaban & Minta Feedback", use_container_width=True):
                st.info("Feedback akan segera hadir! 🎉")
        else:
            st.error("❌ ID LKPD tidak ditemukan. Periksa kembali.")
    else:
        st.info("Masukkan ID LKPD dari guru Anda untuk memulai.")

st.markdown("---")
st.markdown("**Powered by Google Gemini AI 2.5**")
