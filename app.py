import streamlit as st
import uuid
from datetime import datetime
import sqlite3
from gemini_config import generate_lkpd
import re

# === Inisialisasi Database (Akan bersifat sementara di cloud) ===
conn = sqlite3.connect('lms.db', check_same_thread=False) # check_same_thread=False penting untuk Streamlit
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS lkpd 
             (id TEXT PRIMARY KEY, title TEXT, content TEXT, teacher TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS submissions 
             (id TEXT PRIMARY KEY, lkpd_id TEXT, student TEXT, answer TEXT, score REAL, feedback TEXT, submitted_at TEXT)''')
conn.commit()

# === Styling (Tidak Berubah) ===
st.markdown("""
    <style>
    /* ... (CSS Anda dari file sebelumnya tetap di sini) ... */
    .main-title {text-align:center; font-family: 'Roboto', sans-serif; font-size: 2.5em; color: #202124; font-weight: 500; margin-bottom: 20px;}
    .content {max-width: 700px; margin: 0 auto; padding: 20px; background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    .stButton>button {background-color: #34A853; color: white; border: none; border-radius: 4px; padding: 10px 20px; font-family: 'Roboto', sans-serif; font-weight: 500; cursor: pointer; width: 100%; max-width: 200px; margin-top: 20px;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>EduAI LMS</div>", unsafe_allow_html=True)

# === Simulasi Login Sederhana ===
# Di aplikasi nyata, gunakan sistem login yang lebih aman.
user_role = st.sidebar.radio("Login sebagai:", ["Guru", "Siswa"], key="user_role_selector")
username = st.sidebar.text_input("Masukkan Nama Anda", key="username_input")

# === Routing Aplikasi Berdasarkan Peran dan URL ===
query_params = st.query_params
lkpd_id = query_params.get("lkpd_id", [None])[0]

# --- HALAMAN GURU ---
if user_role == "Guru" and not lkpd_id:
    if not username:
        st.warning("Silakan masukkan nama Anda di sidebar untuk melanjutkan.")
        st.stop()
    
    st.sidebar.title("Navigasi Guru")
    page = st.sidebar.radio("Pilih Halaman", ["Buat LKPD Baru", "Monitor Jawaban"])

    if page == "Buat LKPD Baru":
        st.header("📝 Buat LKPD Baru")
        with st.form("lkpd_form"):
            # ... (Form input guru tidak berubah) ...
            jenjang = st.selectbox("Jenjang", ["SMP", "SMA", "SMK"])
            kelas = st.text_input("Kelas", placeholder="Misalnya: X, XI")
            mapel = st.text_input("Mata Pelajaran", placeholder="Misalnya: Biologi")
            jumlah_soal = st.number_input("Jumlah Soal", 1, 10, 3)
            tema = st.text_input("Tema / Topik", placeholder="Misalnya: Keanekaragaman Makhluk Hidup")
            submitted = st.form_submit_button("🚀 Generate LKPD")

        if submitted:
            if not all([jenjang, kelas, mapel, tema]):
                st.error("Mohon lengkapi semua kolom.")
            else:
                with st.spinner("AI sedang membuat LKPD..."):
                    unique_id = str(uuid.uuid4())[:8]
                    # Prompt tetap sama...
                    prompt = f"Buatkan LKPD {mapel} untuk jenjang {jenjang} kelas {kelas} dengan tema {tema} dan {jumlah_soal} soal essay singkat. Struktur: Judul LKPD, Tujuan Pembelajaran, Materi Singkat, Soal-Soal."
                    try:
                        ai_output = generate_lkpd(prompt)
                        c.execute("INSERT INTO lkpd (id, title, content, teacher, created_at) VALUES (?, ?, ?, ?, ?)",
                                  (unique_id, tema, ai_output, username, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        st.session_state.new_lkpd_id = unique_id
                    except Exception as e:
                        st.error(f"Error saat generate: {e}")
        
        if 'new_lkpd_id' in st.session_state:
            st.success("LKPD berhasil dibuat!")
            # Tampilkan link dengan query parameter
            shareable_link = f"?lkpd_id={st.session_state.new_lkpd_id}"
            st.markdown(f"**Bagikan ID ini kepada siswa:** `{st.session_state.new_lkpd_id}`")
            st.info("Siswa perlu memilih peran 'Siswa' dan memasukkan ID di atas.")


    elif page == "Monitor Jawaban":
        st.header("📊 Monitor Jawaban Siswa")
        # ... (Logika monitoring tidak berubah) ...
        c.execute("SELECT s.id, l.title, s.student, s.answer, s.score, s.feedback, s.submitted_at FROM submissions s JOIN lkpd l ON s.lkpd_id = l.id WHERE l.teacher = ?", (username,))
        submissions = c.fetchall()
        if not submissions:
            st.info("Belum ada jawaban yang masuk.")
        for sub in submissions:
            with st.expander(f"Jawaban dari **{sub[2]}** untuk LKPD '{sub[1]}'"):
                st.write(f"**Jawaban:**\n\n{sub[3]}")
                score = st.number_input("Nilai", min_value=0.0, max_value=100.0, value=float(sub[4]), key=f"score_{sub[0]}")
                feedback = st.text_area("Umpan Balik", value=sub[5], key=f"feedback_{sub[0]}")
                if st.button("Simpan Nilai", key=f"save_{sub[0]}"):
                    c.execute("UPDATE submissions SET score = ?, feedback = ? WHERE id = ?", (score, feedback, sub[0]))
                    conn.commit()
                    st.success(f"Nilai untuk {sub[2]} disimpan!")
                    st.rerun()

# --- HALAMAN SISWA ---
elif user_role == "Siswa":
    if not username:
        st.warning("Silakan masukkan nama Anda di sidebar untuk melanjutkan.")
        st.stop()
    
    lkpd_id_input = st.text_input("Masukkan ID LKPD dari guru Anda:")
    
    if lkpd_id_input:
        c.execute("SELECT content FROM lkpd WHERE id = ?", (lkpd_id_input,))
        lkpd_data = c.fetchone()
        
        if lkpd_data:
            lkpd_content = lkpd_data[0]
            st.markdown("<div class='content'>", unsafe_allow_html=True)
            # ... (Logika parsing dan menampilkan soal siswa tidak berubah) ...
            # Regex untuk memisahkan soal
            questions_list = re.split(r'\d+\.\s', lkpd_content)
            soal_section = next((s for s in questions_list if "Soal-Soal" in s), lkpd_content)
            
            # Tampilkan header
            st.markdown(lkpd_content.split("Soal-Soal")[0])
            st.markdown("---")
            st.subheader("Jawab Pertanyaan Berikut:")

            # Ambil hanya bagian soal
            soal_texts = re.findall(r'(\d+\.\s.*)', lkpd_content)

            answers = {}
            for i, q_text in enumerate(soal_texts, 1):
                st.markdown(f"**{q_text}**")
                answers[f"q{i}"] = st.text_area(label=f"Jawaban Soal {i}", height=100, key=f"ans_{i}", label_visibility="collapsed")

            if st.button("Kumpulkan Jawaban"):
                # ... (Logika submit tidak berubah) ...
                submission_text = "\n\n".join([f"Soal {i}: {a}" for i, a in enumerate(answers.values(), 1) if a.strip()])
                if submission_text:
                    sub_id = str(uuid.uuid4())
                    c.execute("INSERT INTO submissions (id, lkpd_id, student, answer, score, feedback, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (sub_id, lkpd_id_input, username, submission_text, 0.0, "", datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    st.success("Jawaban berhasil dikirim!")
                else:
                    st.warning("Harap isi setidaknya satu jawaban.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("LKPD dengan ID tersebut tidak ditemukan.")

elif lkpd_id:
    st.info("Silakan pilih peran Anda (Guru/Siswa) di sidebar untuk melihat konten ini.")

else:
    st.info("Selamat datang di EduAI LMS. Silakan pilih peran Anda di sidebar untuk memulai.")

