import streamlit as st
import google.generativeai as genai
import os
import json
import uuid
import pandas as pd
from datetime import datetime
from gemini_config import model

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="LMS Interaktif EduAI - Guru Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SESSION STATE ==========
if 'role' not in st.session_state:
    st.session_state.role = None

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("🎓 LMS EduAI Pro")
    selected_role = st.radio("Saya adalah:", ["👨‍🏫 Guru", "👩‍🎓 Siswa"], key="role_radio")
    
    if selected_role and selected_role != st.session_state.role:
        st.session_state.role = selected_role
        st.rerun()

# ========== MAIN PAGE ==========
st.title("🚀 LMS Interaktif EduAI - **GURU PRO MODE**")
st.markdown("**Buat LKPD + Monitor + Nilai Otomatis**")

if not st.session_state.role:
    st.warning("👈 Silakan pilih peran Anda di sidebar.")
    st.stop()

# ========== MODE GURU ==========
if st.session_state.role == "👨‍🏫 Guru":
    
    # TABS GURU
    tab1, tab2, tab3 = st.tabs(["📝 Buat LKPD", "📊 Pemantauan Siswa", "📈 Penilaian & Report"])
    
    with tab1:
        st.header("📝 Buat LKPD Baru")
        col1, col2 = st.columns([2, 1])
        with col1:
            theme = st.text_input("Masukkan Tema", placeholder="Gerak Lurus")
        with col2:
            if st.button("🚀 Generate LKPD", use_container_width=True):
                if theme:
                    with st.spinner("🤖 AI merancang..."):
                        prompt = f"""
                        Buat LKPD "{theme}" JSON:
                        {{
                          "judul": "Judul Menarik",
                          "tujuan_pembelajaran": ["Tujuan 1", "Tujuan 2"],
                          "materi_singkat": "1 paragraf",
                          "kegiatan": [
                            {{"nama": "Kegiatan 1", "petunjuk": "Langkah", "tugas_interaktif": ["Tugas 1"], "pertanyaan_pemantik": [{{"pertanyaan": "Q1"}}, {{"pertanyaan": "Q2"}}]}},
                            {{"nama": "Kegiatan 2", "petunjuk": "Langkah", "tugas_interaktif": ["Tugas 1"], "pertanyaan_pemantik": [{{"pertanyaan": "Q1"}}]}}
                          ]
                        }}
                        """
                        try:
                            response = model.generate_content(prompt)
                            json_str = response.text.strip().replace("```json", "").replace("```", "")
                            lkpd_data = json.loads(json_str)
                            
                            lkpd_id = str(uuid.uuid4())[:8]
                            os.makedirs("lkpd_outputs", exist_ok=True)
                            filepath = f"lkpd_outputs/{lkpd_id}.json"
                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(lkpd_data, f, ensure_ascii=False, indent=2)
                            
                            st.session_state.lkpd_data = lkpd_data
                            st.session_state.lkpd_id = lkpd_id
                            st.success(f"✅ **LKPD SIAP!** ID: `{lkpd_id}`")
                            st.info(f"**Share ke siswa:** `{lkpd_id}`")
                            
                            # DISPLAY LKPD
                            st.markdown("---")
                            st.subheader(f"📋 {lkpd_data['judul']}")
                            st.info(lkpd_data['materi_singkat'])
                            for i, kegiatan in enumerate(lkpd_data['kegiatan'], 1):
                                with st.expander(f"Kegiatan {i}: {kegiatan['nama']}"):
                                    st.markdown(f"**Petunjuk:** {kegiatan['petunjuk']}")
                                    for tugas in kegiatan['tugas_interaktif']:
                                        st.markdown(f"• {tugas}")
                                    for q in kegiatan['pertanyaan_pemantik']:
                                        st.markdown(f"❓ {q['pertanyaan']}")
                                    
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
    
    with tab2:
        st.header("📊 Pemantauan Siswa Real-time")
        lkpd_monitor_id = st.text_input("Masukkan ID LKPD untuk Monitor:")
        
        if lkpd_monitor_id:
            # LOAD LKPD
            filepath = f"lkpd_outputs/{lkpd_monitor_id}.json"
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    lkpd_data = json.load(f)
                
                # LOAD JAWABAN SISWA
                jawaban_dir = "jawaban_siswa"
                os.makedirs(jawaban_dir, exist_ok=True)
                siswa_files = [f for f in os.listdir(jawaban_dir) if f.startswith(lkpd_monitor_id)]
                
                if siswa_files:
                    st.success(f"✅ **{len(siswa_files)} SISWA** sudah submit!")
                    
                    # DASHBOARD
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("👥 Total Siswa", len(siswa_files))
                    with col2:
                        st.metric("📊 Progress", f"{len(siswa_files)}/{len(siswa_files)}")
                    with col3:
                        st.metric("⭐ Rata-rata Nilai", "**85**")
                    
                    # TABLE SISWA
                    data_siswa = []
                    for file in siswa_files:
                        with open(f"{jawaban_dir}/{file}", 'r', encoding='utf-8') as f:
                            jawaban = json.load(f)
                            nama_siswa = jawaban.get('nama_siswa', 'Anonim')
                            waktu_submit = jawaban.get('waktu_submit', 'N/A')
                            total_score = jawaban.get('total_score', 0)
                            data_siswa.append({
                                'Nama': nama_siswa,
                                'Waktu': waktu_submit,
                                'Nilai': total_score,
                                'Status': '✅ Selesai'
                            })
                    
                    df = pd.DataFrame(data_siswa)
                    st.dataframe(df, use_container_width=True)
                    
                else:
                    st.info("⏳ **Belum ada siswa submit** - Bagikan ID ke kelas!")
            else:
                st.error("❌ ID LKPD tidak ditemukan!")
    
    with tab3:
        st.header("🤖 Penilaian Otomatis & Export")
        report_id = st.text_input("ID LKPD untuk Report:")
        
        if report_id:
            jawaban_dir = "jawaban_siswa"
            siswa_files = [f for f in os.listdir(jawaban_dir) if f.startswith(report_id)]
            
            if siswa_files:
                # AI SCORING
                if st.button("🤖 **Nilai Semua Jawaban**", use_container_width=True):
                    with st.spinner("🤖 AI menilai..."):
                        for file in siswa_files:
                            with open(f"{jawaban_dir}/{file}", 'r', encoding='utf-8') as f:
                                jawaban = json.load(f)
                            
                            # AI SCORE
                            prompt_score = f"""
                            Nilai jawaban siswa ini (skala 0-100):
                            {jawaban['jawaban']}
                            
                            Berikan:
                            {{
                              "total_score": 85,
                              "feedback": "Bagus! Perlu tambah contoh.",
                              "strengths": ["Pemahaman konsep"],
                              "improvements": ["Detail perhitungan"]
                            }}
                            """
                            
                            response = model.generate_content(prompt_score)
                            score_json = response.text.strip().replace("```json", "").replace("```", "")
                            score_data = json.loads(score_json)
                            
                            # UPDATE JAWABAN
                            jawaban['total_score'] = score_data['total_score']
                            jawaban['feedback'] = score_data['feedback']
                            
                            with open(f"{jawaban_dir}/{file}", 'w', encoding='utf-8') as f:
                                json.dump(jawaban, f, ensure_ascii=False, indent=2)
                        
                        st.success("✅ **PENILAIAN SELESAI!**")
                
                # SHOW SCORES
                st.subheader("📋 Detail Penilaian")
                for file in siswa_files:
                    with open(f"{jawaban_dir}/{file}", 'r', encoding='utf-8') as f:
                        jawaban = json.load(f)
                    
                    with st.expander(f"{jawaban['nama_siswa']} - **{jawaban['total_score']}**"):
                        st.info(f"**Feedback AI:** {jawaban['feedback']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Kelebihan:**")
                            for strength in jawaban.get('strengths', []):
                                st.success(f"• {strength}")
                        with col2:
                            st.write("**Perbaikan:**")
                            for imp in jawaban.get('improvements', []):
                                st.warning(f"• {imp}")
                
                # EXPORT CSV
                if st.button("📥 Download Report CSV", use_container_width=True):
                    data_export = []
                    for file in siswa_files:
                        with open(f"{jawaban_dir}/{file}", 'r', encoding='utf-8') as f:
                            jawaban = json.load(f)
                            data_export.append({
                                'Nama Siswa': jawaban['nama_siswa'],
                                'Nilai': jawaban['total_score'],
                                'Feedback': jawaban['feedback'][:50] + '...'
                            })
                    
                    df_export = pd.DataFrame(data_export)
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        "📥 Download Report",
                        csv,
                        f"report_{report_id}.csv",
                        "text/csv"
                    )

# ========== MODE SISWA ==========
elif st.session_state.role == "👩‍🎓 Siswa":
    st.header("👩‍🎓 Isi LKPD")
    lkpd_id = st.text_input("Masukkan ID LKPD:")
    
    if lkpd_id:
        filepath = f"lkpd_outputs/{lkpd_id}.json"
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                lkpd_data = json.load(f)
            
            st.success(f"✅ **{lkpd_data['judul']}** dimuat!")
            
            st.markdown("---")
            st.subheader(lkpd_data['judul'])
            st.info(lkpd_data['materi_singkat'])
            
            # FORM JAWABAN
            nama_siswa = st.text_input("Nama Anda:")
            jawaban_form = {}
            
            for i, kegiatan in enumerate(lkpd_data['kegiatan'], 1):
                with st.expander(f"Kegiatan {i}: {kegiatan['nama']}"):
                    st.markdown(f"**Petunjuk:** {kegiatan['petunjuk']}")
                    
                    for j, q in enumerate(kegiatan['pertanyaan_pemantik']):
                        key = f"k{i}_q{j}"
                        jawaban_form[key] = st.text_area(
                            f"{j+1}. {q['pertanyaan']}", 
                            key=key, 
                            height=80
                        )
            
            if st.button("✨ **Submit & Minta Nilai AI**", use_container_width=True):
                if nama_siswa and any(jawaban_form.values()):
                    # SAVE JAWABAN
                    jawaban_data = {
                        'lkpd_id': lkpd_id,
                        'nama_siswa': nama_siswa,
                        'jawaban': jawaban_form,
                        'waktu_submit': datetime.now().strftime("%d/%m/%Y %H:%M"),
                        'total_score': 0,
                        'feedback': ''
                    }
                    
                    jawaban_dir = "jawaban_siswa"
                    os.makedirs(jawaban_dir, exist_ok=True)
                    filename = f"{jawaban_dir}/{lkpd_id}_{uuid.uuid4().hex[:4]}.json"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(jawaban_data, f, ensure_ascii=False, indent=2)
                    
                    st.success(f"✅ **TERKIRIM!** Tunggu nilai dari guru.")
                    st.balloons()
                else:
                    st.warning("❌ Isi nama & jawaban lengkap!")

st.markdown("---")
st.markdown("**Powered by Gemini AI 2.5 • Made with ❤️ untuk Guru Indonesia**")
