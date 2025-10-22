import google.generativeai as genai
import streamlit as st
import os
import json

# ========== API SETUP ==========
@st.cache_resource
def init_gemini():
    """Initialize Gemini dengan error handling"""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except Exception as e:
        st.error(f"❌ API Error: {e}")
        st.stop()

# Global model (cached)
model = init_gemini()

# ========== FILE MANAGEMENT ==========
LKPD_DIR = "lkpd_outputs"

def check_lkpd_existence():
    """Pastikan folder ada"""
    os.makedirs(LKPD_DIR, exist_ok=True)

def save_lkpd(lkpd_id, data):
    """Simpan LKPD ke JSON"""
    check_lkpd_existence()
    filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

def load_lkpd(lkpd_id):
    """Load LKPD dari JSON"""
    filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Load Error: {e}")
    return None

# ========== AI GENERATION ==========
@st.cache_data
def generate_lkpd(theme):
    """Generate LKPD menggunakan Gemini"""
    st.info("🤖 AI sedang membuat LKPD...")
    
    prompt = f"""
    Buat LKPD interaktif untuk tema "{theme}". 
    Output **HANYA JSON** (tanpa markdown):
    {{
      "judul": "Judul LKPD",
      "tujuan_pembelajaran": ["Tujuan 1", "Tujuan 2"],
      "materi_singkat": "Penjelasan singkat 1-2 paragraf",
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
        json_str = response.text.strip()
        
        # Clean JSON
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        
        # Validate & Parse
        data = json.loads(json_str)
        return data
        
    except json.JSONDecodeError:
        st.error("❌ JSON Error - AI response tidak valid")
        return None
    except Exception as e:
        st.error(f"❌ AI Error: {e}")
        return None
