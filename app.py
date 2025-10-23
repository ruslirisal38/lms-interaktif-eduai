import streamlit as st
import os
import json
import uuid
import pandas as pd
from datetime import datetime

# FAKE DATA GENERATOR (OFFLINE)
SAMPLE_LKPD = {
    "judul": "LKPD Gerak Lurus Interaktif",
    "tujuan_pembelajaran": ["Memahami konsep gerak lurus", "Menghitung kecepatan benda"],
    "materi_singkat": "Gerak lurus adalah pergerakan benda pada garis lurus dengan kecepatan tetap. Rumus: v = s/t.",
    "kegiatan": [
        {
            "nama": "Pengukuran Kecepatan",
            "petunjuk": "Ukur jarak dan waktu mobil mainan.",
            "tugas_interaktif": ["Catat jarak 2 meter", "Hitung waktu"],
            "pertanyaan_pemantik": [
                {"pertanyaan": "Apa rumus kecepatan? Jelaskan!"},
                {"pertanyaan": "Contoh benda gerak lurus di kehidupan?"}
            ]
        },
        {
            "nama": "Analisis Grafik",
            "petunjuk": "Buat grafik s-t dari data.",
            "tugas_interaktif": ["Plot 5 titik data"],
            "pertanyaan_pemantik": [
                {"pertanyaan": "Apa kesimpulan dari grafik?"}
            ]
        }
    ]
}

# PAGE CONFIG
st.set_page_config(page_title="LMS EduAI Pro", page_icon="🎓", layout="wide")

# SESSION STATE
if 'role' not in st.session_state:
    st.session_state.role = None

# SIDEBAR
with st.sidebar:
    st.title("🎓 LMS EduAI **OFFLINE PRO**")
    st.info("🤖 **FAKE AI MODE** - No API Limits!")
    selected_role = st.radio("Saya adalah:", ["👨‍🏫 Guru", "👩‍🎓 Siswa"])

if selected_role != st.session_state.role:
    st.session_state.role = selected_role
    st.rerun()

st.title("🚀 LMS Interaktif EduAI **OFFLINE PRO**")
st.info("**API Gemini sementara off** - Full features working!")

if not st.session_state.role:
    st.stop()

# ========== GURU MODE ==========
if st.session_state.role == "👨‍🏫 Guru":
    tab1, tab2, tab3 = st.tabs(["📝 Buat LKPD", "📊 Monitor", "🎯 Nilai"])
    
    with tab1:
        st.header("📝 Buat LKPD (FAKE AI)")
        col1, col2 = st.columns([2, 1])
        with col1:
            theme = st.text_input("Tema:", "Gerak Lurus")
        with col2:
            if st.button("🚀 Generate (2s)", use_container_width=True):
                # FAKE GENERATE
                lkpd_data = SAMPLE_LKPD.copy()
                lkpd_data["judul"] = f"LKPD {theme} Interaktif"
                
                lkpd_id = str(uuid.uuid4())[:8]
                os.makedirs("lkpd_outputs", exist_ok=True)
                filepath = f"lkpd_outputs/{lkpd_id}.json"
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(lkpd_data, f, ensure_ascii=False, indent=2)
                
                st.session_state.lkpd_data = lkpd_data
                st.session_state.lkpd_id = lkpd_id
                st.success(f"✅ **ID: `{lkpd_id}`** - Share ke siswa!")
                
                # DISPLAY
                st.subheader(lkpd_data['judul'])
                st.info(lkpd_data['materi_singkat'])
                for i, keg in enumerate(lkpd_data['kegiatan'], 1):
                    with st.expander(f"Kegiatan {i}: {keg['nama']}"):
                        st.write(f"**Petunjuk:** {keg['petunjuk']}")
                        for q in keg['pertanyaan_pemantik']:
                            st.write(f"❓ {q['pertanyaan']}")
    
    with tab2:
        st.header("📊 Monitor Siswa")
        lkpd_id = st.text_input("ID LKPD:")
        if lkpd_id:
            jawaban_dir = "jawaban_siswa"
            os.makedirs(jawaban_dir, exist_ok=True)
            files = [f for f in os.listdir(jawaban_dir) if f.startswith(lkpd_id)]
            if files:
                st.success(f"✅ **{len(files)} SISWA**")
                data = []
                for f in files:
                    with open(f"{jawaban_dir}/{f}", 'r') as file:
                        j = json.load(file)
                        data.append({
                            'Nama': j['nama_siswa'],
                            'Waktu': j['waktu_submit'],
                            'Status': '✅'
                        })
                st.dataframe(pd.DataFrame(data))
            else:
                st.info("⏳ Belum ada siswa")
    
    with tab3:
        st.header("🎯 Penilaian (FAKE)")
        lkpd_id = st.text_input("ID LKPD:")
        if lkpd_id and st.button("🤖 Nilai Semua", use_container_width=True):
            jawaban_dir = "jawaban_siswa"
            files = [f for f in os.listdir(jawaban_dir) if f.startswith(lkpd_id)]
            for f in files:
                with open(f"{jawaban_dir}/{f}", 'r') as file:
                    j = json.load(file)
                j['total_score'] = 85
                j['feedback'] = "Bagus! Pemahaman konsep baik."
                with open(f"{jawaban_dir}/{f}", 'w') as file:
                    json.dump(j, file)
            st.success("✅ **PENILAIAN SELESAI!**")
            
            files = [f for f in os.listdir(jawaban_dir) if f.startswith(lkpd_id)]
            for f in files:
                with open(f"{jawaban_dir}/{f}", 'r') as file:
                    j = json.load(file)
                with st.expander(f"{j['nama_siswa']} - **{j['total_score']}**"):
                    st.info(j['feedback'])

# ========== SISWA MODE ==========
elif st.session_state.role == "👩‍🎓 Siswa":
    st.header("👩‍🎓 Isi LKPD")
    lkpd_id = st.text_input("ID LKPD:")
    
    if lkpd_id:
        filepath = f"lkpd_outputs/{lkpd_id}.json"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                lkpd_data = json.load(f)
            
            st.success(f"✅ **{lkpd_data['judul']}**")
            
            nama = st.text_input("Nama Anda:")
            jawaban = {}
            
            for i, keg in enumerate(lkpd_data['kegiatan'], 1):
                with st.expander(f"Kegiatan {i}"):
                    for j, q in enumerate(keg['pertanyaan_pemantik']):
                        jawaban[f"k{i}q{j}"] = st.text_area(
                            f"{j+1}. {q['pertanyaan']}", 
                            key=f"q{i}{j}"
                        )
            
            if st.button("✨ Submit", use_container_width=True):
                if nama and any(jawaban.values()):
                    os.makedirs("jawaban_siswa", exist_ok=True)
                    filename = f"jawaban_siswa/{lkpd_id}_{nama}_{uuid.uuid4().hex[:4]}.json"
                    data = {
                        'jawaban': jawaban,
                        'nama_siswa': nama,
                        'waktu_submit': datetime.now().strftime("%d/%m/%Y %H:%M")
                    }
                    with open(filename, 'w') as f:
                        json.dump(data, f)
                    st.success("✅ **TERKIRIM!**")
                    st.balloons()
                else:
                    st.warning("Isi nama & jawaban!")

st.markdown("---")
st.markdown("**Made for 🇮🇩 • Offline Pro Mode**")
