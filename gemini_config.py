import google.generativeai as genai
from dotenv import load_dotenv
import os

# Muat variabel lingkungan dari file .env
load_dotenv()

# Ambil API key dari variabel lingkungan
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("API key tidak ditemukan. Pastikan GEMINI_API_KEY ada di file .env.")

# Konfigurasi API Gemini
genai.configure(api_key=api_key)

# Ganti model ke yang tersedia di 2025: gemini-2.0-flash (stabil dan cepat)
model = genai.GenerativeModel('gemini-2.0-flash')

def generate_lkpd(prompt):
    """
    Menghasilkan konten LKPD berdasarkan prompt yang diberikan.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise Exception(f"Gagal menghasilkan LKPD: {str(e)}")

if __name__ == "__main__":
    # Contoh penggunaan untuk pengujian
    sample_prompt = "Buatkan LKPD untuk Matematika jenjang SMP kelas VIII, tema Geometri, dengan 5 soal."
    try:
        lkpd = generate_lkpd(sample_prompt)
        print("LKPD yang dihasilkan:")
        print(lkpd)
    except Exception as e:
        print(f"Error: {e}")