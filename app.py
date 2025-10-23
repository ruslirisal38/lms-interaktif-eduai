import streamlit as st
from gemini_config import generate_lkpd, save_lkpd, load_lkpd, save_jawaban_siswa, load_all_jawaban, score_all_jawaban, get_model, initialize_app
import os
import json
import uuid
import pandas as pd

# INIT
initialize_app()

# PAGE CONFIG
st.set_page_config(page_title="LMS EduAI Pro", page_icon="🎓", layout="wide")

# SESSION STATE
if 'role' not in st.session_state:
    st.session_state.role = None

# SIDEBAR
with st.sidebar:
    st.title("🎓 LMS EduAI Pro")
    selected_role = st.radio("Saya adalah:", ["👨‍🏫 Guru", "👩‍🎓 Siswa"])
    if selected_role != st.session_state.role:
        st.session_state.role = selected_role
        st.rerun()

st.title("🚀 LMS Interaktif EduAI **PRO**")

if not st.session_state.role:
    st.warning("👈 Pilih peran Anda!")
    st.stop()

# ========== GURU MODE ==========
if st.session_state.role == "👨‍🏫 Guru":
    tab1, tab2, tab3 = st.tabs(["📝 Buat LKPD", "📊 Monitor", "🎯 Nilai"])
    
    with tab1:
        st.header("📝 Buat LKPD")
        col1, col2 = st.columns([2, 1])
        with col1:
            theme = st.text_input("Tema:", "Gerak Lurus")
        with col2:
            if st.button("🚀 Generate", use_container_width=True):
                if theme:
                    with st.spinner("🤖 AI..."):
                        lkpd_data = generate_lkpd(theme)
                        if lkpd_data:
                            lkpd_id = str(uuid.uuid4())[:8]
                            if save_lkpd(lkpd_id, lkpd_data):
                                st.session_state.lkpd_data = lkpd_data
                                st.session_state.lkpd_id = lkpd_id
                                st.success(f"✅ **ID: `{lkpd_id}`** - Share ke siswa!")
                                st.info(f"**Copy:** `{lkpd_id}`")
                                
                                st.subheader(lkpd_data['judul'])
                                st.info(lkpd_data['materi_singkat'])
                                for i, keg in enumerate(lkpd_data['kegiatan'], 1):
                                    with st.expander(f"Kegiatan {i}"):
                                        st.write(keg['petunjuk'])
                                        for q in keg['pertanyaan_pemantik']:
                                            st.write(f"❓ {q['pertanyaan']}")
    
    with tab2:
        st.header("📊 Monitor Siswa")
        lkpd_id = st.text_input("ID LKPD:")
        if lkpd_id:
            jawaban_list = load_all_jawaban(lkpd_id)
            if jawaban_list:
                st.success(f"✅ **{len(jawaban_list)} SISWA**")
                df = pd.DataFrame([{
                    'Nama': j['nama_siswa'],
                    'Waktu': j['waktu_submit'],
                    'Status': '✅'
                } for j in jawaban_list])
                st.dataframe(df)
            else:
                st.info("⏳ Belum ada siswa")
    
    with tab3:
        st.header("🎯 Penilaian")
        lkpd_id = st.text_input("ID LKPD:")
        if lkpd_id and st.button("🤖 Nilai Semua", use_container_width=True):
            with st.spinner("AI Scoring..."):
                if score_all_jawaban(lkpd_id):
                    st.success("✅ **PENILAIAN SELESAI!**")
                    jawaban_list = load_all_jawaban(lkpd_id)
                    for j in jawaban_list:
                        with st.expander(f"{j['nama_siswa']} - **{j['total_score']}**"):
                            st.info(j['feedback'])

# ========== SISWA MODE ==========
elif st.session_state.role == "👩‍🎓 Siswa":
    st.header("👩‍🎓 Isi LKPD")
    lkpd_id = st.text_input("ID LKPD:")
    
    if lkpd_id:
        lkpd_data = load_lkpd(lkpd_id)
        if lkpd_data:
            st.success(f"✅ **{lkpd_data['judul']}**")
            
            nama = st.text_input("Nama Anda:")
            jawaban = {}
            
            for i, keg in enumerate(lkpd_data['kegiatan'], 1):
                with st.expander(f"Kegiatan {i}"):
                    for j, q in enumerate(keg['pertanyaan_pemantik']):
                        jawaban[f"k{i}q{j}"] = st.text_area(f"{j+1}. {q['pertanyaan']}", height=80)
            
            if st.button("✨ Submit", use_container_width=True):
                if nama and any(jawaban.values()):
                    save_jawaban_siswa(lkpd_id, nama, jawaban)
                    st.success("✅ **TERKIRIM!**")
                    st.balloons()
                else:
                    st.warning("Isi nama & jawaban!")

st.markdown("---")
st.markdown("**Powered by Gemini AI • Made for 🇮🇩**")
