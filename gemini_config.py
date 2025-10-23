import google.generativeai as genai
import streamlit as st
import os
import json
from datetime import datetime
import logging
from typing import Optional, Dict, Any

# ========== LOGGING SETUP ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONSTANTS ==========
LKPD_DIR = "lkpd_outputs"
JAWABAN_DIR = "jawaban_siswa"
API_KEY = st.secrets.get("GEMINI_API_KEY", None)
MODEL_NAME = "gemini-2.5-flash"

# ========== GLOBAL VARIABLES ==========
_model = None
_init_success = False

# ========== UTILITY FUNCTIONS ==========
def ensure_directories() -> None:
    """Create all required directories"""
    os.makedirs(LKPD_DIR, exist_ok=True)
    os.makedirs(JAWABAN_DIR, exist_ok=True)
    logger.info("✅ Directories created: lkpd_outputs, jawaban_siswa")

def validate_api_key() -> bool:
    """Validate GEMINI_API_KEY exists"""
    global API_KEY
    if not API_KEY:
        st.error("❌ **GEMINI_API_KEY** tidak ditemukan di Streamlit Secrets!")
        st.info("**Cara fix:** Settings → Secrets → Tambah `GEMINI_API_KEY`")
        logger.error("API Key missing")
        return False
    return True

# ========== GEMINI INITIALIZATION ==========
@st.cache_resource
def init_gemini() -> Optional[genai.GenerativeModel]:
    """
    Initialize Gemini model with full error handling
    Returns: GenerativeModel or None
    """
    global _model, _init_success
    
    if _init_success:
        logger.info("✅ Gemini already initialized")
        return _model
    
    # Validate API Key
    if not validate_api_key():
        return None
    
    try:
        # Configure API
        genai.configure(api_key=API_KEY)
        logger.info(f"🔑 API configured with {MODEL_NAME}")
        
        # Initialize Model
        _model = genai.GenerativeModel(MODEL_NAME)
        
        # Test connection
        test_response = _model.generate_content("Test")
        logger.info(f"✅ Gemini {MODEL_NAME} connected successfully!")
        
        _init_success = True
        st.sidebar.success(f"🤖 **Gemini {MODEL_NAME} READY**")
        
        return _model
        
    except Exception as e:
        error_msg = f"❌ Gemini Init Error: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg)
        _model = None
        _init_success = False
        return None

# ========== LKPD MANAGEMENT ==========
def save_lkpd(lkpd_id: str, data: Dict[str, Any]) -> bool:
    """Save LKPD to JSON file"""
    try:
        filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 LKPD saved: {lkpd_id}")
        return True
    except Exception as e:
        st.error(f"❌ Save LKPD Error: {e}")
        logger.error(f"Save error: {e}")
        return False

def load_lkpd(lkpd_id: str) -> Optional[Dict[str, Any]]:
    """Load LKPD from JSON file"""
    filepath = os.path.join(LKPD_DIR, f"{lkpd_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"📂 LKPD loaded: {lkpd_id}")
            return data
        except Exception as e:
            st.error(f"❌ Load LKPD Error: {e}")
            logger.error(f"Load error: {e}")
    return None

# ========== JAWABAN SISWA MANAGEMENT ==========
def save_jawaban_siswa(lkpd_id: str, nama_siswa: str, jawaban_data: Dict[str, Any]) -> str:
    """Save student answer with unique filename"""
    try:
        # Create unique filename
        unique_id = uuid.uuid4().hex[:6]
        filename = f"{lkpd_id}_{nama_siswa}_{unique_id}.json"
        filepath = os.path.join(JAWABAN_DIR, filename)
        
        # Add metadata
        full_data = {
            **jawaban_data,
            'lkpd_id': lkpd_id,
            'nama_siswa': nama_siswa,
            'waktu_submit': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'total_score': 0,
            'feedback': "",
            'strengths': [],
            'improvements': []
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📝 Jawaban saved: {nama_siswa} - {lkpd_id}")
        return filename
        
    except Exception as e:
        st.error(f"❌ Save Jawaban Error: {e}")
        logger.error(f"Jawaban save error: {e}")
        return ""

def load_all_jawaban(lkpd_id: str) -> list:
    """Load all student answers for LKPD"""
    jawaban_files = [f for f in os.listdir(JAWABAN_DIR) if f.startswith(lkpd_id)]
    all_jawaban = []
    
    for filename in jawaban_files:
        filepath = os.path.join(JAWABAN_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_jawaban.append(data)
        except Exception as e:
            logger.error(f"Load jawaban error {filename}: {e}")
    
    logger.info(f"📋 Loaded {len(all_jawaban)} jawaban for {lkpd_id}")
    return all_jawaban

# ========== AI GENERATION ==========
@st.cache_data
def generate_lkpd(theme: str) -> Optional[Dict[str, Any]]:
    """Generate LKPD using Gemini AI"""
    if not _model:
        st.error("❌ Model not initialized!")
        return None
    
    st.info("🤖 **AI merancang LKPD**...")
    
    prompt = f"""
    Buat LKPD INTERAKTIF untuk tema "{theme}" SMP/SMA.
    **OUTPUT HANYA JSON VALID** (tanpa markdown/kode):
    
    {{
      "judul": "Judul LKPD Menarik (10 kata max)",
      "tujuan_pembelajaran": [
        "Tujuan pembelajaran 1", 
        "Tujuan pembelajaran 2"
      ],
      "materi_singkat": "Penjelasan materi 1 paragraf (100 kata max)",
      "kegiatan": [
        {{
          "nama": "Kegiatan 1 - Judul Menarik",
          "petunjuk": "Petunjuk langkah jelas (3-5 kalimat)",
          "tugas_interaktif": [
            "Tugas praktik 1", 
            "Tugas praktik 2"
          ],
          "pertanyaan_pemantik": [
            {{"pertanyaan": "Pertanyaan refleksi 1 (jawab 3-5 kalimat)"}},
            {{"pertanyaan": "Pertanyaan refleksi 2 (jawab 3-5 kalimat)"}}
          ]
        }},
        {{
          "nama": "Kegiatan 2 - Judul Menarik", 
          "petunjuk": "Petunjuk langkah jelas (3-5 kalimat)",
          "tugas_interaktif": ["Tugas praktik utama"],
          "pertanyaan_pemantik": [
            {{"pertanyaan": "Pertanyaan evaluasi (jawab 5-7 kalimat)"}}
          ]
        }}
      ]
    }}
    """
    
    try:
        response = _model.generate_content(prompt)
        json_str = response.text.strip()
        
        # Clean JSON
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        
        # Parse & Validate
        data = json.loads(json_str)
        
        # Validate structure
        required_keys = ['judul', 'tujuan_pembelajaran', 'materi_singkat', 'kegiatan']
        if not all(key in data for key in required_keys):
            raise ValueError("Missing required keys in JSON")
            
        logger.info(f"✅ LKPD generated for theme: {theme}")
        return data
        
    except json.JSONDecodeError:
        st.error("❌ **JSON Error** - AI response tidak valid")
        logger.error("JSON decode error")
        return None
    except Exception as e:
        st.error(f"❌ **AI Error:** {str(e)}")
        logger.error(f"Generate error: {e}")
        return None

# ========== AI SCORING ==========
@st.cache_data
def score_jawaban(jawaban_text: str, pertanyaan: str) -> Dict[str, Any]:
    """AI Auto-Scoring for student answer"""
    if not _model:
        return {"total_score": 0, "feedback": "Model tidak tersedia"}
    
    prompt = f"""
    **NILAI JAWABAN SISWA** (skala 0-100):
    
    Pertanyaan: {pertanyaan}
    Jawaban: {jawaban_text}
    
    **KRITERIA:**
    - Pemahaman konsep: 40%
    - Kejelasan jawaban: 30%  
    - Contoh/referensi: 20%
    - Bahasa/grammar: 10%
    
    **OUTPUT HANYA JSON:**
    {{
      "total_score": 85,
      "feedback": "Feedback positif + saran (50 kata max)",
      "strengths": ["Kelebihan 1", "Kelebihan 2"],
      "improvements": ["Perbaikan 1", "Perbaikan 2"]
    }}
    """
    
    try:
        response = _model.generate_content(prompt)
        json_str = response.text.strip().replace("```json", "").replace("```", "")
        score_data = json.loads(json_str)
        
        logger.info(f"📊 Scored: {score_data['total_score']}")
        return score_data
        
    except Exception as e:
        logger.error(f"Scoring error: {e}")
        return {
            "total_score": 0,
            "feedback": "Error dalam penilaian",
            "strengths": [],
            "improvements": ["Coba lagi"]
        }

# ========== BULK SCORING ==========
def score_all_jawaban(lkpd_id: str) -> bool:
    """Score all student answers for LKPD"""
    all_jawaban = load_all_jawaban(lkpd_id)
    
    for jawaban in all_jawaban:
        total_score = 0
        all_feedback = []
        all_strengths = []
        all_improvements = []
        
        # Score each question
        for key, answer_text in jawaban['jawaban'].items():
            if answer_text.strip():
                # Extract question from key or use generic
                pertanyaan = "Jawab pertanyaan dengan lengkap"
                score = score_jawaban(answer_text, pertanyaan)
                
                total_score += score['total_score']
                all_feedback.append(score['feedback'])
                all_strengths.extend(score['strengths'])
                all_improvements.extend(score['improvements'])
        
        # Average score
        jawaban['total_score'] = total_score // max(len(jawaban['jawaban']), 1)
        jawaban['feedback'] = " | ".join(all_feedback[:2])
        jawaban['strengths'] = list(set(all_strengths))[:3]
        jawaban['improvements'] = list(set(all_improvements))[:3]
        
        # Save updated
        filename = f"{JAWABAN_DIR}/{lkpd_id}_{jawaban['nama_siswa']}_*.json"
        # Note: In production, use exact filename tracking
        
    logger.info(f"✅ Bulk scoring completed for {lkpd_id}: {len(all_jawaban)} students")
    return True

# ========== INITIALIZATION ==========
def initialize_app():
    """Initialize all components"""
    ensure_directories()
    model = init_gemini()
    return model is not None

# ========== GLOBAL MODEL ACCESSOR ==========
def get_model() -> Optional[genai.GenerativeModel]:
    """Get cached model instance"""
    global _model
    if _model is None:
        init_gemini()
    return _model

# ========== STATS ==========
def get_stats() -> Dict[str, int]:
    """Get app statistics"""
    lkpd_count = len([f for f in os.listdir(LKPD_DIR) if f.endswith('.json')])
    jawaban_count = len([f for f in os.listdir(JAWABAN_DIR) if f.endswith('.json')])
    
    return {
        "lkpd_total": lkpd_count,
        "jawaban_total": jawaban_count,
        "siswa_unik": len(set([f.split('_')[1] for f in os.listdir(JAWABAN_DIR) if f.endswith('.json')]))
    }

# ========== AUTO-INIT ON IMPORT ==========
if __name__ == "__main__":
    initialize_app()
    print("🚀 LMS EduAI Config Loaded!")
