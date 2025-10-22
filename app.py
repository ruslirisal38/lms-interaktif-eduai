import streamlit as st
from gemini_config import generate_lkpd, check_lkpd_existence, load_lkpd, client, MODEL_QA, save_lkpd
import uuid
import json

# Pastikan direktori lkpd_outputs ada saat aplikasi dimulai
check_lkpd_existence()

# --- Pengaturan Halaman ---
st.set_page_config(
    page_title="LMS Interaktif Berbasis AI (Gemini)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- State Management Sederhana ---
if 'role' not in st.session_state:
    st.session_state.role = None
if 'lkpd_data' not in st.session_state:
    st.session_state.lkpd_data = None
if 'lkpd_id' not in st.session_state:
    st.session_state.lkpd_id = None
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# --- Sidebar (Pemilihan Peran) ---
with st.sidebar:
    st.title("Pilih Peran Anda")
    selected_role = st.radio(
        "Saya adalah:",
        ["Guru", "Siswa"],
        index=None
    )
    if selected_role:
        st.session_state.role = selected_role
        # Menggunakan st.experimental_rerun() untuk memuat ulang berdasarkan peran
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("Powered by Google Gemini AI")

# --- Halaman Utama ---
st.title("🚀 LMS Interaktif dengan Gemini AI")
st.markdown("Platform untuk membuat dan mengisi Lembar Kerja Peserta Didik (LKPD) secara otomatis.")

if not st.session_state.role:
    st.warning("Silakan pilih peran Anda di sidebar untuk memulai.")

elif st.session_state.role == "Guru":
    st.header("👨‍🏫 Mode Guru: Buat LKPD Baru")

    col1, col2 = st.columns([2, 1])

    with col1:
        theme = st.text_input("Masukkan Tema / Topik Pembelajaran (Contoh: Gerak Lurus, Rantai Makanan)", key="theme_input")
    
    with col2:
        # Tombol Generate
        st.markdown("<br>", unsafe_allow_html=True) 
        if st.button("🚀 Generate LKPD", use_container_width=True):
            if theme:
                # 1. Generasi LKPD
                lkpd_content = generate_lkpd(theme)
                
                if lkpd_content:
                    # 2. Simpan LKPD
                    new_id = str(uuid.uuid4()).split('-')[0] # ID LKPD unik
                    # Mencoba menyimpan LKPD. Save harus berhasil jika check_lkpd_existence() berhasil
                    if save_lkpd(new_id, lkpd_content):
                        st.session_state.lkpd_data = lkpd_content
                        st.session_state.lkpd_id = new_id
                        st.success("✅ LKPD berhasil dibuat dan disimpan!")
                    else:
                        st.error("Gagal menyimpan LKPD. Periksa folder dan izin file.")
            else:
                st.warning("Mohon masukkan Tema/Topik terlebih dahulu.")

    if st.session_state.lkpd_data:
        st.markdown("---")
        st.subheader(f"LKPD yang Baru Dibuat (ID: `{st.session_state.lkpd_id}`)")
        st.info(f"**Bagikan ID ini kepada siswa:** `{st.session_state.lkpd_id}`")
        
        # Tampilkan hasil LKPD
        data = st.session_state.lkpd_data
        st.write(f"## {data.get('judul', 'Judul Tidak Ditemukan')}")
        st.markdown(f"**Tujuan Pembelajaran:**")
        for tujuan in data.get('tujuan_pembelajaran', []):
            st.markdown(f"- {tujuan}")
        
        st.markdown("---")
        st.markdown("### Materi Singkat")
        st.info(data.get('materi_singkat', ''))
        
        st.markdown("---")
        st.markdown("### Kegiatan Siswa")
        for i, kegiatan in enumerate(data.get('kegiatan', [])):
            with st.expander(f"Kegiatan {i+1}: {kegiatan.get('nama', 'Kegiatan')}"):
                st.markdown(f"**Petunjuk:** {kegiatan.get('petunjuk', '-')}")
                
                st.markdown("**Tugas Interaktif:**")
                for tugas in kegiatan.get('tugas_interaktif', []):
                    st.markdown(f"• {tugas}")

                st.markdown("**Pertanyaan Pemantik:**")
                for j, pertanyaan in enumerate(kegiatan.get('pertanyaan_pemantik', [])):
                    st.markdown(f"*{j+1}. {pertanyaan.get('pertanyaan', '-')}")
                    # Area teks hanya untuk tampilan guru, tidak menyimpan jawaban
                    st.text_area("Jawaban (Contoh Isian Guru)", value="", height=50, key=f"guru_ans_{i}_{j}", disabled=True)


elif st.session_state.role == "Siswa":
    st.header("📝 Mode Siswa: Isi LKPD")

    lkpd_input = st.text_input("Masukkan ID LKPD dari Guru Anda:", key="lkpd_id_input")

    if lkpd_input:
        # Memuat LKPD dari ID yang dimasukkan
        lkpd_data = load_lkpd(lkpd_input)
        
        if lkpd_data:
            # Menyimpan data LKPD dan ID ke session state
            st.session_state.lkpd_data = lkpd_data
            st.session_state.lkpd_id = lkpd_input
            
            # Inisialisasi dictionary jawaban jika belum ada
            if lkpd_input not in st.session_state.answers:
                 st.session_state.answers[lkpd_input] = {}

            st.success(f"LKPD **{lkpd_data.get('judul', 'Ditemukan')}** berhasil dimuat.")
            st.markdown("---")

            data = st.session_state.lkpd_data
            st.write(f"## {data.get('judul', 'Judul Tidak Ditemukan')}")
            
            st.markdown("### Materi Singkat")
            st.info(data.get('materi_singkat', ''))
            
            st.markdown("---")
            st.markdown("### Kegiatan Siswa")

            all_answers_filled = True
            
            # Loop untuk menampilkan kegiatan dan pertanyaan
            for i, kegiatan in enumerate(data.get('kegiatan', [])):
                with st.expander(f"Kegiatan {i+1}: {kegiatan.get('nama', 'Kegiatan')}"):
                    st.markdown(f"**Petunjuk:** {kegiatan.get('petunjuk', '-')}")
                    
                    st.markdown("**Tugas Interaktif:**")
                    for tugas in kegiatan.get('tugas_interaktif', []):
                        st.markdown(f"• {tugas}")

                    st.markdown("**Pertanyaan Pemantik (Isi Jawaban Anda):**")
                    for j, pertanyaan in enumerate(kegiatan.get('pertanyaan_pemantik', [])):
                        unique_key = f"siswa_ans_{i}_{j}"
                        
                        # Ambil jawaban sebelumnya dari session state
                        current_answer = st.session_state.answers[lkpd_input].get(unique_key, "")

                        st.markdown(f"*{j+1}. {pertanyaan.get('pertanyaan', '-')}")
                        
                        new_answer = st.text_area(
                            "Jawaban Anda:", 
                            value=current_answer, 
                            height=80, 
                            key=unique_key
                        )
                        
                        # Update session state jika ada perubahan
                        st.session_state.answers[lkpd_input][unique_key] = new_answer
                        
                        # Cek apakah jawaban sudah diisi
                        if not new_answer:
                             all_answers_filled = False

            st.markdown("---")
            
            if st.button("Kirim Jawaban & Minta Feedback Otomatis", use_container_width=True):
                if not all_answers_filled:
                    st.warning("Mohon isi semua kolom jawaban terlebih dahulu.")
                else:
                    with st.spinner("Sedang menganalisis jawaban Anda dan menghasilkan feedback..."):
                        # 1. Kumpulkan semua pertanyaan dan jawaban
                        feedback_prompt_parts = [
                            f"Tema LKPD: {data.get('judul', 'Tidak Diketahui')}",
                            "--- Pertanyaan dan Jawaban Siswa ---"
                        ]
                        
                        for i, kegiatan in enumerate(data.get('kegiatan', [])):
                            for j, pertanyaan in enumerate(kegiatan.get('pertanyaan_pemantik', [])):
                                unique_key = f"siswa_ans_{i}_{j}"
                                jawaban = st.session_state.answers[lkpd_input].get(unique_key, "Tidak dijawab")
                                
                                feedback_prompt_parts.append(
                                    f"Q: {pertanyaan.get('pertanyaan', 'Pertanyaan')}\nA: {jawaban}\n"
                                )
                        
                        full_prompt = (
                            "Anda adalah seorang guru yang memberikan feedback konstruktif dan memotivasi untuk pekerjaan siswa. "
                            "Analisis jawaban siswa (diberikan di bawah) berdasarkan pertanyaan yang diajukan. "
                            "Berikan poin-poin umpan balik yang ringkas: pertama, apresiasi atas jawaban yang benar/relevan. Kedua, berikan saran perbaikan atau koreksi untuk bagian yang kurang tepat. "
                            "Gunakan bahasa Indonesia yang ramah dan memotivasi."
                            "\n\n" + "\n".join(feedback_prompt_parts)
                        )

                        # 2. Panggil Gemini untuk Feedback
                        try:
                            feedback_response = client.models.generate_content(
                                model=MODEL_QA,
                                contents=full_prompt
                            )
                            st.success("✨ Feedback Otomatis Berhasil Dibuat!")
                            st.markdown("### Umpan Balik dari AI Tutor")
                            st.markdown(feedback_response.text)
                        except Exception as e:
                            st.error(f"❌ Gagal mendapatkan feedback: {e}")
                            st.error("Periksa koneksi API atau coba lagi.")


        else:
            st.error("❌ ID LKPD tidak valid atau tidak ditemukan. Mohon periksa kembali ID yang Anda masukkan.")
