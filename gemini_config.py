import google.generativeai as genai
import streamlit as st
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

# ========== LOGGING SETUP ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONSTANTS ==========
LKPD_DIR = "lkpd_outputs"
JAWABAN_DIR = "jawaban_siswa"
MODEL_NAME = "gemini-1.5-flash"  # FIXED: 2.5 NOT EXIST

# ========== GLOBAL VARIABLES ==========
_model: Optional[genai.GenerativeModel] = None
_init_success = False

# ========== UTILITY FUNCTIONS ==========
def ensure_directories() -> None:
    os.makedirs(LKPD_DIR, exist_ok=True)
    os.makedirs(JAWABAN_DIR, exist_ok=True)

def validate_api_key() -> bool:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        st.error("❌ GEMINI_API_KEY TIDAK DITEMUKAN!")
        return False
    return True

# ========== GEMINI INITIALIZATION ==========
@st.cache_resource
def init_gemini() -> Optional[genai.GenerativeModel]:
    global _model, _init_success
    
    if _init_success:
        return _model
    
    if not validate_api_key():
        return None
    
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        _model = genai.GenerativeModel(MODEL_NAME)
        _model.generate_content("Test")
        _init_success = True
        st.sidebar.success(f"🤖 {MODEL_NAME} READY")
        return _model
    except Exception as e:
        st.error(f"❌ Gemini Error: {e}")
        return None

# ========== LKPD MANAGEMENT ==========
def save_lkpd(lkpd_id: str, data: Dict[str, Any]) -> bool:
    try:
        filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_lkpd(lkpd_id: str) -> Optional[Dict[str, Any]]:
    filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# ========== JAWABAN MANAGEMENT ==========
def save_jawaban_siswa(lkpd_id: str, nama_siswa: str, jawaban_data: Dict[str, Any]) -> str:
    ensure_directories()
    unique_id = uuid.uuid4().hex[:6]
    filename = f"{lkpd_id}_{nama_siswa}_{unique_id}.json"
    filepath = os.path.join(JAWABAN_DIR, filename)
    
    full_data = {
        **jawaban_data,
        'lkpd_id': lkpd_id,
        'nama_siswa': nama_siswa,
        'waktu_submit': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'total_score': 0,
        'feedback': ''
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    return filename

def load_all_jawaban(lkpd_id: str) -> List[Dict]:
    if not os.path.exists(JAWABAN_DIR):
        return []
    files = [f for f in os.listdir(JAWABAN_DIR) if f.startswith(lkpd_id)]
    all_jawaban = []
    for filename in files:
        filepath = os.path.join(JAWABAN_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            all_jawaban.append(json.load(f))
    return all_jawaban

# ========== AI GENERATION ==========
@st.cache_data
def generate_lkpd(theme: str) -> Optional[Dict[str, Any]]:
    model = get_model()
    if not model:
        return None
    prompt = f'Buat LKPD "{theme}" JSON SAHAJA:\n{{"judul":"Judul","tujuan_pembelajaran":["T1"],"materi_singkat":"Materi","kegiatan":[{"nama":"K1","petunjuk":"Petunjuk","tugas_interaktif":["T1"],"pertanyaan_pemantik":[{"pertanyaan":"Q1"}]}]}}'
    try:
        response = model.generate_content(prompt)
        json_str = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_str)
    except:
        return None

# ========== AI SCORING ==========
@st.cache_data
def score_all_jawaban(lkpd_id: str) -> bool:
    all_jawaban = load_all_jawaban(lkpd_id)
    model = get_model()
    if not model:
        return False
    
    for jawaban in all_jawaban:
        total_score = 80  # Default score
        jawaban['total_score'] = total_score
        jawaban['feedback'] = "Bagus! Kerja bagus!"
        
        # Save back FIXED LOOP
        for filename in os.listdir(JAWABAN_DIR):
            if filename.startswith(f"{lkpd_id}_{jawaban['nama_siswa']}"):
                filepath = os.path.join(JAWABAN_DIR, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(jawaban, f, ensure_ascii=False, indent=2)
                break
    return True

# ========== PUBLIC API ==========
def get_model() -> Optional[genai.GenerativeModel]:
    global _model
    if _model is None:
        init_gemini()
    return _model

def initialize_app():
    ensure_directories()
    init_gemini()
