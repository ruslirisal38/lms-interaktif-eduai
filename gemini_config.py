import google.generativeai as genai
import streamlit as st
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# ========== LOGGING SETUP ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONSTANTS ==========
LKPD_DIR = "lkpd_outputs"
JAWABAN_DIR = "jawaban_siswa"
MODEL_NAME = "gemini-2.5-flash"

# ========== GLOBAL VARIABLES ==========
_model: Optional[genai.GenerativeModel] = None
_init_success = False

# ========== UTILITY FUNCTIONS ==========
def ensure_directories() -> None:
    """Create all required directories"""
    os.makedirs(LKPD_DIR, exist_ok=True)
    os.makedirs(JAWABAN_DIR, exist_ok=True)
    logger.info("✅ Directories created")

def validate_api_key() -> bool:
    """Validate GEMINI_API_KEY exists"""
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        st.error("❌ **GEMINI_API_KEY** tidak ditemukan!")
        st.info("**Fix:** Settings → Secrets → Tambah `GEMINI_API_KEY`")
        return False
    return True

# ========== GEMINI INITIALIZATION ==========
@st.cache_resource
def init_gemini() -> Optional[genai.GenerativeModel]:
    """Initialize Gemini model with full error handling"""
    global _model, _init_success
    
    if _init_success:
        return _model
    
    if not validate_api_key():
        return None
    
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        _model = genai.GenerativeModel(MODEL_NAME)
        
        # Test connection
        _model.generate_content("Test")
        _init_success = True
        st.sidebar.success(f"🤖 **{MODEL_NAME} READY**")
        logger.info(f"✅ {MODEL_NAME} connected")
        return _model
        
    except Exception as e:
        st.error(f"❌ Gemini Error: {str(e)}")
        logger.error(f"Gemini init error: {e}")
        return None

# ========== LKPD MANAGEMENT ==========
def save_lkpd(lkpd_id: str, data: Dict[str, Any]) -> bool:
    """Save LKPD to JSON"""
    try:
        filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 LKPD saved: {lkpd_id}")
        return True
    except Exception as e:
        st.error(f"❌ Save Error: {e}")
        return False

def load_lkpd(lkpd_id: str) -> Optional[Dict[str, Any]]:
    """Load LKPD from JSON"""
    filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            st.error(f"❌ Load Error: {e}")
    return None

# ========== JAWABAN SISWA MANAGEMENT ==========
def save_jawaban_siswa(lkpd_id: str, nama_siswa: str, jawaban_data: Dict[str, Any]) -> str:
    """Save student answer"""
    try:
        unique_id = uuid.uuid4().hex[:6]
        filename = f"{lkpd_id}_{nama_siswa}_{unique_id}.json"
        filepath = os.path.join(JAWABAN_DIR, filename)
        
        full_data = {
            **jawaban_data,
            'lkpd_id': lkpd_id,
            'nama_siswa': nama_siswa,
            'waktu_submit': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'total_score': 0,
            'feedback': '',
            'strengths': [],
            'improvements': []
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        return filename
    except Exception as e:
        st.error(f"❌ Save Jawaban Error: {e}")
        return ""

def load_all_jawaban(lkpd_id: str) -> list:
    """Load all answers for LKPD"""
    if not os.path.exists(JAWABAN_DIR):
        return []
    
    jawaban_files = [f for f in os.listdir(JAWABAN_DIR) if f.startswith(lkpd_id)]
    all_jawaban = []
    
    for filename in jawaban_files:
        filepath = os.path.join(JAWABAN_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                all_jawaban.append(json.load(f))
        except Exception:
            continue
    
    return all_jawaban

# ========== AI GENERATION ==========
@st.cache_data
def generate_lkpd(theme: str) -> Optional[Dict[str, Any]]:
    """Generate LKPD using Gemini"""
    model = get_model()
    if not model:
        return None
    
    st.info("🤖 AI merancang LKPD...")
    
    prompt = f'''Buat LKPD "{theme}" JSON SAHAJA:
{{
  "judul": "Judul LKPD",
  "tujuan_pembelajaran": ["Tujuan 1", "Tujuan 2"],
  "materi_singkat": "Penjelasan 1 paragraf",
  "kegiatan": [
    {{"nama": "Kegiatan 1", "petunjuk": "Petunjuk", "tugas_interaktif": ["Tugas 1"], "pertanyaan_pemantik": [{{"pertanyaan": "Q1"}}, {{"pertanyaan": "Q2"}}]}},
    {{"nama": "Kegiatan 2", "petunjuk": "Petunjuk", "tugas_interaktif": ["Tugas 1"], "pertanyaan_pemantik": [{{"pertanyaan": "Q1"}}]}}
  ]
}}'''
    
    try:
        response = model.generate_content(prompt)
        json_str = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_str)
        return data
    except Exception as e:
        st.error(f"❌ Generate Error: {e}")
        return None

# ========== AI SCORING ==========
@st.cache_data
def score_jawaban(jawaban_text: str, pertanyaan: str) -> Dict[str, Any]:
    """AI Auto-Scoring"""
    model = get_model()
    if not model:
        return {"total_score": 0, "feedback": "Error"}
    
    prompt = f'''Nilai jawaban (0-100):
Pertanyaan: {pertanyaan}
Jawaban: {jawaban_text}

JSON:
{{
  "total_score": 85,
  "feedback": "Feedback singkat",
  "strengths": ["Kelebihan"],
  "improvements": ["Perbaikan"]
}}'''
    
    try:
        response = model.generate_content(prompt)
        json_str = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_str)
    except:
        return {"total_score": 0, "feedback": "Error"}

def score_all_jawaban(lkpd_id: str) -> bool:
    """Bulk scoring all answers"""
    all_jawaban = load_all_jawaban(lkpd_id)
    
    for jawaban in all_jawaban:
        total_score = 0
        feedbacks = []
        
        for key, answer_text in jawaban['jawaban'].items():
            if answer_text.strip():
                score = score_jawaban(answer_text, "Jawab lengkap")
                total_score += score['total_score']
                feedbacks.append(score['feedback'])
        
        jawaban['total_score'] = total_score // max(len(jawaban['jawaban']), 1)
        jawaban['feedback'] = " | ".join(feedbacks[:2])
        
        # Save back
        filename = next(f for f in os.listdir(JAWABAN_DIR) if f.startswith(f"{lkpd_id}_{jawaban['nama_siswa']}"))
        filepath = os.path.join(JAWABAN_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(jawaban, f, ensure_ascii=False, indent=2)
    
    return True

# ========== PUBLIC API ==========
def get_model() -> Optional[genai.GenerativeModel]:
    """Get cached model"""
    global _model
    if _model is None:
        init_gemini()
    return _model

def initialize_app():
    """Init all components"""
    ensure_directories()
    return init_gemini() is not None

def get_stats() -> Dict[str, int]:
    """App statistics"""
    lkpd_count = len(os.listdir(LKPD_DIR)) if os.path.exists(LKPD_DIR) else 0
    jawaban_count = len(os.listdir(JAWABAN_DIR)) if os.path.exists(JAWABAN_DIR) else 0
    return {"lkpd": lkpd_count, "jawaban": jawaban_count}

# ========== AUTO-INIT ==========
if __name__ == "__main__":
    initialize_app()
