import streamlit as st
import time
import random
import datetime
import os
import joblib
import pandas as pd
import re

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CareFlow AI — Smart Hospital Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background-color: #F1F5F9 !important;
    background-image: none !important;
    min-height: 100vh;
}

#MainMenu, header, footer { visibility: hidden; }

/* ── ALL TEXT COLOR DEFAULTS ── */
.stApp p, .stApp span, .stApp label, .stApp li, .stApp div,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stMarkdownContainer"] *,
[data-testid="stText"] *,
[data-testid="stCaptionContainer"] * {
    color: #1E293B;
}

/* ── SIDEBAR OVERRIDES ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
}

/* ── MAIN CONTENT AREA ── */
.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1300px;
}

/* ── STEPPER COMPONENT ── */
.stepper-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}
.step-item-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    text-align: center;
}
.step-line-active {
    position: absolute;
    top: 22px;
    left: 50%;
    width: 100%;
    height: 2px;
    background: #2563EB;
    z-index: 1;
}
.step-line-inactive {
    position: absolute;
    top: 22px;
    left: 50%;
    width: 100%;
    height: 2px;
    border-top: 2px dotted #CBD5E1;
    z-index: 1;
}
.step-btn-wrap button {
    border-radius: 50% !important;
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    max-width: 44px !important;
    padding: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-family: 'Material Symbols Outlined' !important;
    font-size: 20px !important;
    border: 2px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    color: #64748B !important;
    z-index: 2 !important;
    position: relative !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
}
.step-btn-wrap.active button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    border-color: #2563EB !important;
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15), 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important;
}
.step-btn-wrap.done button {
    background: #10B981 !important;
    color: #FFFFFF !important;
    border-color: #10B981 !important;
    box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2) !important;
}
.step-btn-wrap.unlocked button:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    transform: scale(1.05) !important;
    cursor: pointer !important;
}
.step-btn-wrap.active button:hover {
    color: #FFFFFF !important;
    transform: scale(1.05) !important;
}
.step-btn-wrap.done button:hover {
    color: #FFFFFF !important;
    transform: scale(1.05) !important;
}
.step-btn-wrap.locked button {
    background: #F8FAFC !important;
    color: #94A3B8 !important;
    border-color: #E2E8F0 !important;
    cursor: not-allowed !important;
    opacity: 0.6 !important;
}
.step-lbl {
    margin-top: 8px;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B !important;
    z-index: 2;
}
.step-btn-wrap.active + .step-lbl,
.step-btn-wrap.active ~ .step-lbl {
    /* styled via script dynamically if needed, but this class is set */
}

/* ── SPLIT PANEL LAYOUT ── */
.welcome-card {
    background: linear-gradient(145deg, #0B192F 0%, #1A365D 50%, #2563EB 100%);
    border-radius: 20px;
    padding: 40px;
    color: #FFFFFF !important;
    height: 100%;
    min-height: 520px;
    box-shadow: 0 10px 25px -5px rgba(11, 25, 47, 0.3), inset 0 1px 0 rgba(255,255,255,0.15);
    display: flex;
    flex-direction: column;
}
.welcome-card * {
    color: #FFFFFF !important;
}
.welcome-folder-img {
    width: 64px;
    height: auto;
    margin-bottom: 24px;
    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.25));
}
.welcome-title {
    font-size: 32px !important;
    font-weight: 900 !important;
    line-height: 1.15 !important;
    margin-bottom: 16px !important;
    letter-spacing: -0.5px !important;
}
.welcome-subtitle {
    font-size: 14px !important;
    color: rgba(255, 255, 255, 0.8) !important;
    line-height: 1.6 !important;
    margin-bottom: 32px !important;
}
.feature-list {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-top: auto;
}
.feature-item {
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 14px 18px;
    transition: all 0.2s ease;
}
.feature-item:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
}
.feature-icon-wrap {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.feature-icon-wrap span {
    font-family: 'Material Symbols Outlined' !important;
    font-size: 22px !important;
    color: inherit !important;
}
.feature-text {
    display: flex;
    flex-direction: column;
}
.feature-title {
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
}
.feature-desc {
    font-size: 12px !important;
    color: rgba(255, 255, 255, 0.6) !important;
    margin-top: 2px;
}

/* ── WORKSPACE CARD ── */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker),
div[class*="stVerticalBlock"]:has(.workspace-marker),
div[data-testid="stVerticalBlock"]:has(.workspace-marker) {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 20px !important;
    padding: 36px !important;
    min-height: 520px !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02) !important;
}
/* We allow custom colored text inside card widgets */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) .stTextInput input,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) .stTextArea textarea,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) .stDateInput input,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) .stTimeInput input,
div[class*="stVerticalBlock"]:has(.workspace-marker) .stTextInput input,
div[class*="stVerticalBlock"]:has(.workspace-marker) .stTextArea textarea,
div[class*="stVerticalBlock"]:has(.workspace-marker) .stDateInput input,
div[class*="stVerticalBlock"]:has(.workspace-marker) .stTimeInput input {
    background: #F8FAFC !important;
    color: #0F172A !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) .stTextInput input:focus,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) .stTextArea textarea:focus,
div[class*="stVerticalBlock"]:has(.workspace-marker) .stTextInput input:focus,
div[class*="stVerticalBlock"]:has(.workspace-marker) .stTextArea textarea:focus {
    border-color: #2563EB !important;
    background: #FFFFFF !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) label p,
div[class*="stVerticalBlock"]:has(.workspace-marker) label p {
    color: #475569 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) div[data-baseweb="select"] > div,
div[class*="stVerticalBlock"]:has(.workspace-marker) div[data-baseweb="select"] > div {
    background: #F8FAFC !important;
    color: #0F172A !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.workspace-marker) div[data-baseweb="select"] *,
div[class*="stVerticalBlock"]:has(.workspace-marker) div[data-baseweb="select"] * {
    color: #0F172A !important;
    background: transparent !important;
}
[role="listbox"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
}
[role="option"] {
    color: #1E293B !important;
}
[role="option"]:hover {
    background: #F1F5F9 !important;
}

/* ── DEFAULT LANDING ── */
.landing-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    height: 100%;
    padding: 40px 20px;
}
.landing-img {
    width: 140px;
    height: auto;
    margin-bottom: 24px;
    filter: drop-shadow(0 8px 16px rgba(0,0,0,0.06));
}
.landing-title {
    font-size: 22px !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    margin-bottom: 8px !important;
    line-height: 1.3 !important;
}
.landing-subtitle {
    font-size: 14px !important;
    color: #64748B !important;
    margin-bottom: 24px !important;
}

/* ── TABS OVERRIDES ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: #F1F5F9;
    border-radius: 12px;
    padding: 4px;
    border-bottom: none;
    margin-bottom: 20px;
}
.stTabs [data-baseweb="tab"] {
    height: 38px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 8px;
    color: #64748B !important;
    font-size: 13px;
    font-weight: 600;
    border: none;
    padding: 0 16px;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #2563EB !important;
    background: rgba(37, 99, 235, 0.05);
}
.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #2563EB !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
}
.stTabs [aria-selected="true"] span,
.stTabs [aria-selected="true"] p {
    color: #2563EB !important;
}

/* ── PREMIUM BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 10px rgba(37,99,235,0.2) !important;
    width: 100%;
}
.stButton > button p,
.stButton > button span {
    color: #FFFFFF !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 14px rgba(37,99,235,0.3) !important;
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── METRICS ── */
[data-testid="metric-container"] {
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

/* ── PHONE SMS MOCKUP ── */
.phone-wrap {
    background: #0F172A;
    border-radius: 28px;
    border: 6px solid #1E293B;
    width: 240px; height: 380px;
    margin: 0 auto;
    overflow: hidden;
    display: flex; flex-direction: column;
    box-shadow: 0 10px 20px rgba(0,0,0,0.15);
}
.phone-screen {
    background: #F8FAFC;
    flex: 1;
    margin-top: 6px;
    border-radius: 18px 18px 0 0;
    padding: 12px;
    display: flex; flex-direction: column;
}
.phone-status {
    display: flex; justify-content: space-between;
    font-size: 8px; color: #94A3B8 !important; padding-bottom: 6px;
    border-bottom: 1px solid #E2E8F0; margin-bottom: 8px;
}
.sms-bubble {
    background: #E2E8F0;
    color: #1E293B !important;
    padding: 8px 10px;
    border-radius: 12px 12px 12px 2px;
    font-size: 10px; line-height: 1.4;
    max-width: 85%; margin-bottom: 4px;
}
.sms-time { font-size: 7px; color: #94A3B8 !important; text-align: right; margin-top: 2px; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "registered_users" not in st.session_state:
    st.session_state.registered_users = {
        "navya":  {"password": "password",  "phone": "9876543210", "name": "Navya Sree"},
        "admin":  {"password": "admin",      "phone": "9999999999", "name": "Admin User"},
    }
if "global_token_counter" not in st.session_state:
    st.session_state.global_token_counter = 24
if "medicine_history" not in st.session_state:
    st.session_state.medicine_history = [
        {"Medicine": "Cetirizine",  "Dosage": "1 Tablet Daily",    "Duration": "5 Days",  "Doctor": "Dr. Rajesh Varma",  "Date": "2026-07-03"},
        {"Medicine": "Paracetamol", "Dosage": "650 mg Thrice Daily","Duration": "3 Days",  "Doctor": "Dr. Priya Sharma",  "Date": "2026-06-15"},
        {"Medicine": "Vitamin D3",  "Dosage": "1 Tablet Weekly",    "Duration": "8 Weeks", "Doctor": "Dr. Kiran Kumar",   "Date": "2026-05-10"},
    ]
for k, v in {
    "current_user": None, "workflow_stage": "Auth",
    "max_unlocked_stage_idx": 0,
    "symptom_input": "", "symptom_lang": "English",
    "recommended_specialist": "", "recommended_reason": "",
    "analyzed_raw_specialist": "General Physician",
    "appointment_details": {}, "payment_details": {},
    "my_token": None, "consultation_details": {},
    "auth_tab": "login",
    "auth_show_form": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── QUERY PARAMS INTERCEPT ───────────────────────────────────────────────────
if "voice_text" in st.query_params:
    v_text = st.query_params["voice_text"]
    if v_text:
        st.session_state.symptom_input = v_text
    del st.query_params["voice_text"]
    st.rerun()


# ─── WORKFLOW STAGES ───────────────────────────────────────────────────────────
STAGES = ["Auth","Symptom Analysis","Appointment Booking","Payment Gateway",
          "Token Generation","Waiting Time","SMS Reminders",
          "Consultation Room","Medicine History","Patient History"]

STAGE_ICONS = ["🔐","🩺","📅","💳","🎫","⏳","📩","🩻","💊","📜"]

def advance_stage(done):
    idx = STAGES.index(done)
    nxt = idx + 1
    if nxt < len(STAGES):
        st.session_state.max_unlocked_stage_idx = max(st.session_state.max_unlocked_stage_idx, nxt)
        st.session_state.workflow_stage = STAGES[nxt]
        st.rerun()

def reset_workflow():
    keys = ["workflow_stage","max_unlocked_stage_idx","current_user",
            "symptom_input","symptom_lang","recommended_specialist",
            "recommended_reason","analyzed_raw_specialist",
            "appointment_details","payment_details","my_token","consultation_details"]
    defaults = ["Auth",0,None,"","English","","","General Physician",{},{},None,{}]
    for k,d in zip(keys, defaults):
        st.session_state[k] = d
    st.rerun()

# ─── ML MODEL ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_model_path = os.path.join(BASE_DIR, "models", "wait_time_prediction_model.pkl")
ml_model = None
if os.path.exists(_model_path):
    try:
        ml_model = joblib.load(_model_path)
    except Exception:
        pass

# ─── ASSET BASE64 LOADING ──────────────────────────────────────────────────────
import base64
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
folder_icon_path = os.path.join(ASSETS_DIR, "medical_folder_icon.png")
clipboard_icon_path = os.path.join(ASSETS_DIR, "medical_clipboard_icon.png")

def get_base64_img(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return ""

folder_base64 = get_base64_img(folder_icon_path)
clipboard_base64 = get_base64_img(clipboard_icon_path)


# ─── DATA DICTS ───────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "English": {
        "rec_specialist": "Recommended Specialist",
        "rec_reason": "Reason",
        "warning": "⚠️ Disclaimer: We recommend specialists based on symptoms only. We do not diagnose diseases or prescribe treatments.",
    },
    "తెలుగు": {
        "rec_specialist": "సిఫార్సు చేయబడిన నిపుణుడు",
        "rec_reason": "కారణం",
        "warning": "⚠️ నిరాకరణ: మేము లక్షణాల ఆధారంగా మాత్రమే నిపుణులను సిఫార్సు చేస్తాము.",
    },
    "हिन्दी": {
        "rec_specialist": "अनुशंसित विशेषज्ञ",
        "rec_reason": "कारण",
        "warning": "⚠️ अस्वीकरण: हम केवल लक्षणों के आधार पर विशेषज्ञों की सिफारिश करते हैं।",
    },
}

SPECIALIST_MAP = {
    "English": {
        "Cardiologist":     {"name": "Cardiologist",         "reason": "Chest pain, pressure or breathlessness may indicate a cardiac concern."},
        "Dermatologist":    {"name": "Dermatologist",        "reason": "Skin rash, itching, or lesions require a dermatology evaluation."},
        "Orthopedic":       {"name": "Orthopedic Specialist","reason": "Joint, bone, or muscle pain needs an orthopedic consultation."},
        "ENT Specialist":   {"name": "ENT Specialist",       "reason": "Ear, nose, or throat symptoms require an ENT evaluation."},
        "Neurologist":      {"name": "Neurologist",          "reason": "Headache, dizziness, or neurological symptoms need specialist review."},
        "Gynecologist":     {"name": "Gynecologist",         "reason": "Women's health, pregnancy, or reproductive symptoms."},
        "Pediatrician":     {"name": "Pediatrician",         "reason": "Child or infant health care needs a pediatric specialist."},
        "General Physician":{"name": "General Physician",    "reason": "Fever, fatigue, cold, or general ailments — a primary physician is recommended."},
    },
    "తెలుగు": {
        "Cardiologist":     {"name": "గుండె నిపుణుడు (Cardiologist)",   "reason": "ఛాతీ నొప్పి లేదా గుండె సమస్యలకు గుండె నిపుణుడిని సంప్రదించండి."},
        "Dermatologist":    {"name": "చర్మ నిపుణుడు (Dermatologist)",   "reason": "చర్మంపై దద్దుర్లు లేదా దురద సమస్యలకు చర్మ నిపుణుడు సరైనవారు."},
        "Orthopedic":       {"name": "ఆర్థోపెడిక్ (Orthopedic)",        "reason": "కీళ్ళు లేదా ఎముకల నొప్పులకు ఆర్థోపెడిక్ వైద్యుడు."},
        "ENT Specialist":   {"name": "ఈఎన్‌టీ నిపుణుడు (ENT)",         "reason": "చెవి, ముక్కు, గొంతు సమస్యలకు ఈఎన్‌టీ నిపుణుడు."},
        "Neurologist":      {"name": "న్యూరాలజిస్ట్ (Neurologist)",     "reason": "తలనొప్పి లేదా నరాల సమస్యలకు న్యూరాలజిస్ట్."},
        "Gynecologist":     {"name": "గైనకాలజిస్ట్ (Gynecologist)",     "reason": "గర్భధారణ మరియు మహిళల ఆరోగ్య సమస్యలకు."},
        "Pediatrician":     {"name": "పీడియాట్రిషియన్ (Pediatrician)", "reason": "పిల్లల ఆరోగ్య సమస్యలకు పీడియాట్రిషియన్."},
        "General Physician":{"name": "జనరల్ ఫిజీషియన్",                "reason": "సాధారణ జ్వరం లేదా జలుబుకు జనరల్ ఫిజీషియన్."},
    },
    "हिन्दी": {
        "Cardiologist":     {"name": "हृदय रोग विशेषज्ञ (Cardiologist)", "reason": "छाती में दर्द या सांस फूलने पर हृदय रोग विशेषज्ञ से मिलें।"},
        "Dermatologist":    {"name": "त्वचा विशेषज्ञ (Dermatologist)",   "reason": "त्वचा पर दाने या खुजली के लिए त्वचा विशेषज्ञ।"},
        "Orthopedic":       {"name": "हड्डी विशेषज्ञ (Orthopedic)",      "reason": "हड्डी या जोड़ों के दर्द के लिए ऑर्थोपेडिक।"},
        "ENT Specialist":   {"name": "ईएनटी विशेषज्ञ (ENT)",             "reason": "कान, नाक या गले की समस्याओं के लिए।"},
        "Neurologist":      {"name": "न्यूरोलॉजिस्ट (Neurologist)",      "reason": "सिरदर्द या नसों की समस्याओं के लिए।"},
        "Gynecologist":     {"name": "स्त्री रोग विशेषज्ञ",              "reason": "गर्भावस्था या महिला स्वास्थ्य के लिए।"},
        "Pediatrician":     {"name": "बाल रोग विशेषज्ञ",                 "reason": "बच्चों की स्वास्थ्य समस्याओं के लिए।"},
        "General Physician":{"name": "सामान्य चिकित्सक",                 "reason": "बुखार, सर्दी या सामान्य बीमारी के लिए।"},
    },
}

DOCTOR_LIST = {
    "Cardiologist":      ["Dr. Rajesh Varma",  "Dr. Shalini Sen"],
    "Dermatologist":     ["Dr. Priya Sharma",  "Dr. Amit Roy"],
    "Orthopedic":        ["Dr. Kiran Kumar",   "Dr. Vikram Seth"],
    "ENT Specialist":    ["Dr. Ravi Teja",     "Dr. Sneha Paul"],
    "Neurologist":       ["Dr. Anjali Gupta",  "Dr. Sameer Alvi"],
    "Gynecologist":      ["Dr. Swapna Reddy",  "Dr. Meera Nair"],
    "Pediatrician":      ["Dr. Suresh Reddy",  "Dr. Kavita Rao"],
    "General Physician": ["Dr. Harish Prasad", "Dr. Divya Singhal"],
}

# ─── SYMPTOM DETECTOR ─────────────────────────────────────────────────────────
def detect_symptoms(text):
    t = text.lower()
    is_tel = bool(re.search(r'[\u0c00-\u0c7f]', text))
    is_hin = bool(re.search(r'[\u0900-\u097f]', text))
    lang = "తెలుగు" if is_tel else ("हिन्दी" if is_hin else "English")
    kw = {
        "Cardiologist":      ["chest","heart","cardio","breathless","palpitation","ఛాతీ","గుండె","छाती","दिल","धड़कन"],
        "Dermatologist":     ["skin","rash","itch","allergy","pimple","acne","చర్మం","దురద","దానే","खुजली","त्वचा"],
        "Orthopedic":        ["bone","joint","knee","back pain","muscle","shoulder","ఎముక","కీళ్ల","हड्डी","जोड़","कमर"],
        "ENT Specialist":    ["ear","nose","throat","sinus","cough","tonsil","చెవి","ముక్కు","కాన","नाक","गला","खांसी"],
        "Neurologist":       ["brain","headache","migraine","dizzy","seizure","మెదడు","తలనొప్పి","सिरदर्द","चक्कर","माइग्रेन"],
        "Gynecologist":      ["pregnancy","period","menstrual","గర్భం","నెలసరి","गर्भावस्था","मासिक","महिला"],
        "Pediatrician":      ["child","baby","infant","newborn","పిల్లలు","పాప","बच्चा","शिशु"],
    }
    for spec, words in kw.items():
        if any(w in t for w in words):
            return lang, spec
    return lang, "General Physician"

# ─── TOP STEPPER NAVIGATION ───────────────────────────────────────────────────
STEPPER_STAGES = ["Auth", "Symptom Analysis", "Appointment Booking", "Payment Gateway", "Token Generation", "Waiting Time"]
STEPPER_LABELS = ["AUTH", "SYMPTOM ANALYSIS", "APPOINTMENT BOOKING", "PAYMENT GATEWAY", "TOKEN GENERATION", "WAITING TIME"]
STEPPER_ICONS = ["person", "stethoscope", "calendar_month", "credit_card", "confirmation_number", "schedule"]

current_linear_stage = st.session_state.workflow_stage
current_stepper_idx = 0
if current_linear_stage in ["SMS Reminders", "Consultation Room", "Medicine History", "Patient History"]:
    current_stepper_idx = 5
elif current_linear_stage in STEPPER_STAGES:
    current_stepper_idx = STEPPER_STAGES.index(current_linear_stage)

max_unlocked_stage_idx = st.session_state.max_unlocked_stage_idx
max_unlocked_stepper_idx = 0
if STAGES[max_unlocked_stage_idx] in ["SMS Reminders", "Consultation Room", "Medicine History", "Patient History"]:
    max_unlocked_stepper_idx = 5
elif STAGES[max_unlocked_stage_idx] in STEPPER_STAGES:
    max_unlocked_stepper_idx = STEPPER_STAGES.index(STAGES[max_unlocked_stage_idx])

# ─── CAREFLOW AI TITLE HEADER ───────────────────────────────────────────────
st.markdown("""
<div style="
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 12px;
    padding: 18px 24px;
    margin-bottom: 8px;
">
    <div style="
        width: 48px; height: 48px;
        background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Material Symbols Outlined';
        font-size: 26px; color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(37,99,235,0.3);
    ">local_hospital</div>
    <div>
        <div style="font-size:28px;font-weight:900;color:#0F172A;letter-spacing:-0.5px;line-height:1.1;">CareFlow <span style='color:#2563EB;'>AI</span></div>
        <div style="font-size:13px;color:#64748B;font-weight:500;margin-top:4px;">Smart Hospital Assistant</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Stepper CSS styles
stepper_css = """<style>
div[data-testid="stVerticalBlockBorderWrapper"]:has(.stepper-marker),
div[class*="stVerticalBlock"]:has(.stepper-marker) {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 16px !important;
    padding: 24px 20px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.stepper-marker) div[data-testid="column"],
div[class*="stVerticalBlock"]:has(.stepper-marker) div[data-testid="column"],
div[data-testid="stVerticalBlockBorderWrapper"]:has(.stepper-marker) [data-testid="column"],
div[class*="stVerticalBlock"]:has(.stepper-marker) [data-testid="column"] {
    position: relative !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.stepper-marker) div[data-testid="column"] button,
div[class*="stVerticalBlock"]:has(.stepper-marker) div[data-testid="column"] button,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.stepper-marker) [data-testid="column"] button,
div[class*="stVerticalBlock"]:has(.stepper-marker) [data-testid="column"] button {
    border-radius: 50% !important;
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    max-width: 44px !important;
    padding: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-family: 'Material Symbols Outlined' !important;
    font-size: 20px !important;
    border: 2px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    color: #64748B !important;
    z-index: 2 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
}
</style>"""

stepper_container = st.container(border=True)
with stepper_container:
    st.markdown('<div class="stepper-marker"></div>' + stepper_css, unsafe_allow_html=True)
    
    # Generate active/done/locked styles dynamically for the columns
    stepper_state_css = "<style>"
    for idx in range(6):
        nth = idx * 2 + 1
        is_active = (idx == current_stepper_idx)
        is_done = (idx < current_stepper_idx)
        is_locked = (idx > max_unlocked_stepper_idx)
        
        if is_active:
            stepper_state_css += f"""div:has(.stepper-marker) [data-testid="column"]:nth-child({nth}) button {{background: #2563EB !important;color: #FFFFFF !important;border-color: #2563EB !important;box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15), 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important;}}"""
        elif is_done:
            stepper_state_css += f"""div:has(.stepper-marker) [data-testid="column"]:nth-child({nth}) button {{background: #10B981 !important;color: #FFFFFF !important;border-color: #10B981 !important;box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2) !important;}}"""
        elif is_locked:
            stepper_state_css += f"""div:has(.stepper-marker) [data-testid="column"]:nth-child({nth}) button {{background: #F8FAFC !important;color: #94A3B8 !important;border-color: #E2E8F0 !important;cursor: not-allowed !important;opacity: 0.6 !important;}}"""
    stepper_state_css += "</style>"
    st.markdown(stepper_state_css, unsafe_allow_html=True)

    cols = st.columns(6)
    
    for idx, col in enumerate(cols):
        with col:
            # Connectors
            if idx < 5:
                line_class = "step-line-active" if idx < current_stepper_idx else "step-line-inactive"
                st.markdown(f'<div class="{line_class}"></div>', unsafe_allow_html=True)
                
            icon_name = STEPPER_ICONS[idx]
            is_locked = (idx > max_unlocked_stepper_idx)
            if st.button(icon_name, key=f"step_btn_{idx}", disabled=is_locked):
                if idx == 5:
                    if current_linear_stage in ["SMS Reminders", "Consultation Room", "Medicine History", "Patient History"]:
                        pass
                    else:
                        st.session_state.workflow_stage = "Waiting Time"
                else:
                    st.session_state.workflow_stage = STEPPER_STAGES[idx]
                st.rerun()
                
            st.markdown(f'<div class="step-lbl">{STEPPER_LABELS[idx]}</div>', unsafe_allow_html=True)

# ─── SPLIT PANEL LAYOUT ────────────────────────────────────────────────────────
if st.session_state.workflow_stage == "Auth":
    col_right = st.container()

    if False:
        st.markdown(f"""
        <div class="welcome-card">
            <img src="data:image/png;base64,{folder_base64}" class="welcome-folder-img" />
            <h1 class="welcome-title">Welcome to<br>CareFlow AI</h1>
            <p class="welcome-subtitle">Your intelligent healthcare companion. Book specialists, track your queue, and manage your medical journey.</p>
            
            <div class="feature-list">
                <div class="feature-item">
                    <div class="feature-icon-wrap" style="background: rgba(59, 130, 246, 0.15); color: #3B82F6;">
                        <span>stethoscope</span>
                    </div>
                    <div class="feature-text">
                        <div class="feature-title">AI Specialist Router</div>
                        <div class="feature-desc">English · Telugu · Hindi</div>
                    </div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon-wrap" style="background: rgba(16, 185, 129, 0.15); color: #10B981;">
                        <span>hourglass_empty</span>
                    </div>
                    <div class="feature-text">
                        <div class="feature-title">Smart Queue & Wait Times</div>
                        <div class="feature-desc">ML-powered predictions</div>
                    </div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon-wrap" style="background: rgba(236, 72, 153, 0.15); color: #EC4899;">
                        <span>pill</span>
                    </div>
                    <div class="feature-text">
                        <div class="feature-title">Medicine & Health Records</div>
                        <div class="feature-desc">Full prescription history</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="workspace-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div style="padding: 8px 0;">', unsafe_allow_html=True)
        
        # ─── MODULE 1: AUTH ───
        if not st.session_state.current_user and not st.session_state.auth_show_form:
            st.markdown(f"""
            <div class="landing-wrap">
                <img src="data:image/png;base64,{clipboard_base64}" class="landing-img" />
                <h2 class="landing-title">Your healthcare journey starts here</h2>
                <p class="landing-subtitle">Use the navigation above to get started, or click below to sign in or create an account.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Get Started / Sign In →", key="start_btn"):
                st.session_state.auth_show_form = True
                st.rerun()
        else:
            ta_col, tb_col = st.columns(2)
            with ta_col:
                btn_type_a = "primary" if st.session_state.auth_tab == "login" else "secondary"
                if st.button("🔐  Sign In", key="tab_login", type=btn_type_a):
                    st.session_state.auth_tab = "login"
                    st.rerun()
            with tb_col:
                btn_type_b = "primary" if st.session_state.auth_tab == "register" else "secondary"
                if st.button("✏️  Create Account", key="tab_reg", type=btn_type_b):
                    st.session_state.auth_tab = "register"
                    st.rerun()

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            if st.session_state.auth_tab == "login":
                st.markdown('<div style="font-size:22px;font-weight:800;color:#0F172A;margin-bottom:4px;">Welcome back 👋</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:13px;color:#64748B;margin-bottom:20px;">Sign in to access your health dashboard</div>', unsafe_allow_html=True)

                lu = st.text_input("Username", key="li_u", placeholder="Enter your username")
                lp = st.text_input("Password", type="password", key="li_p", placeholder="Enter your password")

                if st.button("Sign In →", key="li_btn"):
                    if lu in st.session_state.registered_users and st.session_state.registered_users[lu]["password"] == lp:
                        st.session_state.current_user = lu
                        st.session_state.max_unlocked_stage_idx = max(st.session_state.max_unlocked_stage_idx, 1)
                        st.success(f"✅ Welcome back, {st.session_state.registered_users[lu]['name']}!")
                        st.balloons()
                        time.sleep(1)
                        advance_stage("Auth")
                    else:
                        st.error("❌ Incorrect username or password.")

                st.markdown("""
                <div style="margin-top:18px;padding:12px 14px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;">
                    <div style="font-size:11px;font-weight:700;color:#64748B;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">💡 Demo Credentials</div>
                    <div style="font-size:12px;color:#64748B;">Username: <code style="background:#E2E8F0;padding:2px 6px;border-radius:4px;color:#0F172A;">navya</code></div>
                    <div style="font-size:12px;color:#64748B;margin-top:4px;">Password: <code style="background:#E2E8F0;padding:2px 6px;border-radius:4px;color:#0F172A;">password</code></div>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.markdown('<div style="font-size:22px;font-weight:800;color:#0F172A;margin-bottom:4px;">Create Account 🎉</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:13px;color:#64748B;margin-bottom:20px;">Join CareFlow AI — it\'s completely free</div>', unsafe_allow_html=True)

                ru = st.text_input("Full Name",    key="rg_name", placeholder="e.g. Navya Sree")
                rn = st.text_input("Username",     key="rg_u",    placeholder="Choose a unique username")
                rp = st.text_input("Password",     type="password", key="rg_p", placeholder="Create a strong password")
                rph= st.text_input("Phone Number", key="rg_ph",   placeholder="10-digit mobile number")

                if st.button("Create My Account →", key="rg_btn"):
                    if not ru.strip():
                        st.error("❌ Full Name cannot be empty.")
                    elif not rn.strip():
                        st.error("❌ Username cannot be empty.")
                    elif rn in st.session_state.registered_users:
                        st.error("❌ Username already taken. Please choose another.")
                    elif not rp:
                        st.error("❌ Password cannot be empty.")
                    elif not re.match(r'^\d{10}$', rph):
                        st.error("❌ Please enter a valid 10-digit phone number.")
                    else:
                        st.session_state.registered_users[rn] = {
                            "password": rp, "phone": rph, "name": ru.strip()
                        }
                        st.success(f"🎉 Account created for {ru.strip()}! Please sign in.")
                        st.session_state.auth_tab = "login"
                        time.sleep(1)
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    workspace_ctx = st.container()
    workspace_ctx.__enter__()
    st.markdown('<div class="workspace-marker"></div>', unsafe_allow_html=True)

    # ─── MODULE 2: SYMPTOM ANALYSIS ───
    if st.session_state.workflow_stage == "Symptom Analysis":
        st.markdown('<div style="font-size:22px;font-weight:800;color:#0F172A;margin-bottom:4px;">AI Symptom Analysis</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;color:#64748B;margin-bottom:20px;">Auto-detects English · తెలుగు · हिन्दी and routes to the right specialist</div>', unsafe_allow_html=True)

        col_in, col_out = st.columns([1, 1], gap="medium")

        with col_in:
            st.markdown('<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:12px;">Describe Your Symptoms</div>', unsafe_allow_html=True)
            
            # Presets
            st.markdown('<div style="font-size:11px;font-weight:600;color:#64748B;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">Quick Presets</div>', unsafe_allow_html=True)
            p1, p2, p3 = st.columns(3)
            eng_sym = "I have severe chest pain and pressure on my left side. Breathing is difficult."
            tel_sym = "నాకు చర్మంపై ఎర్రటి దద్దుర్లు వచ్చాయి మరియు దురద పెడుతోంది."
            hin_sym = "मेरे सिर में बहुत तेज़ दर्द हो रहा है और चक्कर आ रहा है।"
            with p1:
                if st.button("💓 Chest Pain", key="sp1"):
                    st.session_state.symptom_input = eng_sym
                    st.rerun()
            with p2:
                if st.button("🇮🇳 Skin (Telugu)", key="sp2"):
                    st.session_state.symptom_input = tel_sym
                    st.rerun()
            with p3:
                if st.button("🇮🇳 Head (Hindi)", key="sp3"):
                    st.session_state.symptom_input = hin_sym
                    st.rerun()

            sym_text = st.text_area(
                "Your Symptoms",
                value=st.session_state.symptom_input,
                height=100,
                placeholder="Describe how you feel... (supports English, Telugu, Hindi)"
            )
            st.session_state.symptom_input = sym_text

            # Multilingual Voice Input
            voice_html = """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                .voice-btn-container {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-top: 10px;
                    font-family: 'Inter', sans-serif;
                }
                .mic-btn {
                    background: #2563EB;
                    border: none;
                    border-radius: 50%;
                    width: 38px;
                    height: 38px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    cursor: pointer;
                    box-shadow: 0 4px 6px rgba(37,99,235,0.2);
                    transition: all 0.2s ease;
                }
                .mic-btn:hover {
                    background: #1D4ED8;
                    transform: scale(1.05);
                }
                .mic-btn.recording {
                    background: #EF4444;
                    animation: pulse 1.2s infinite;
                    box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.3);
                }
                .voice-lang-select {
                    padding: 6px 10px;
                    border-radius: 8px;
                    border: 1px solid #E2E8F0;
                    background: #F8FAFC;
                    color: #475569;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    outline: none;
                }
                .voice-lang-select:hover {
                    border-color: #CBD5E1;
                    background: #F1F5F9;
                }
                .status-lbl {
                    font-size: 11px;
                    color: #64748B;
                    font-weight: 500;
                }
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.08); }
                    100% { transform: scale(1); }
                }
            </style>
            <div class="voice-btn-container">
                <button id="mic-btn" class="mic-btn" onclick="startDictation(event)">
                    <span style="font-size: 16px;">🎙️</span>
                </button>
                <select id="voice-lang-select" class="voice-lang-select">
                    <option value="en-IN">English (India)</option>
                    <option value="te-IN">తెలుగు (Telugu)</option>
                    <option value="hi-IN">हिन्दी (Hindi)</option>
                </select>
                <span id="status-lbl" class="status-lbl">Click mic to record symptoms</span>
            </div>
            
            <script>
                function startDictation(e) {
                    e.preventDefault();
                    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                        alert("Speech Recognition not supported in this browser. Please try Chrome or Edge.");
                        return;
                    }
                    
                    const btn = document.getElementById("mic-btn");
                    const lbl = document.getElementById("status-lbl");
                    const langSelect = document.getElementById("voice-lang-select");
                    
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    const recognition = new SpeechRecognition();
                    
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.lang = langSelect.value;
                    
                    btn.classList.add("recording");
                    lbl.textContent = "Listening...";
                    
                    recognition.onresult = function(event) {
                        const transcript = event.results[0][0].transcript;
                        btn.classList.remove("recording");
                        lbl.textContent = "Updating...";
                        
                        try {
                            const parentUrl = new URL(window.parent.location.href);
                            parentUrl.searchParams.set("voice_text", transcript);
                            window.parent.location.href = parentUrl.toString();
                        } catch(err) {
                            navigator.clipboard.writeText(transcript).then(() => {
                                alert("Recognized: '" + transcript + "'\\nCopied to clipboard. Please paste into text area.");
                            });
                        }
                    };
                    
                    recognition.onerror = function(event) {
                        btn.classList.remove("recording");
                        lbl.textContent = "Error: " + event.error;
                    };
                    
                    recognition.onend = function() {
                        btn.classList.remove("recording");
                    };
                    
                    recognition.start();
                }
            </script>
            """
            st.components.v1.html(voice_html, height=55)

            st.markdown(f"""
            <div style="background:#FFFBEB;border-left:4px solid #F59E0B;padding:10px 14px;border-radius:8px;margin:12px 0;">
                <span style="font-size:11px;color:#92400E;font-weight:500;">
                    ⚠️ We recommend specialists based on symptoms only. We do not diagnose diseases.
                </span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔍 Analyze Symptoms →", key="analyze_btn"):
                if not sym_text.strip():
                    st.error("Please enter your symptoms first.")
                else:
                    lang, spec = detect_symptoms(sym_text)
                    info = SPECIALIST_MAP[lang].get(spec, SPECIALIST_MAP[lang]["General Physician"])
                    st.session_state.symptom_lang = lang
                    st.session_state.recommended_specialist = info["name"]
                    st.session_state.recommended_reason    = info["reason"]
                    st.session_state.analyzed_raw_specialist = spec
                    st.success(f"✅ Analysis complete! Language detected: {lang}")
                    st.rerun()

        with col_out:
            if st.session_state.recommended_specialist:
                spec = st.session_state.recommended_specialist
                reason = st.session_state.recommended_reason
                lang = st.session_state.symptom_lang
                st.markdown(f"""
                <div style="background:#2563EB;border:none;border-radius:12px;padding:20px;color:#FFFFFF !important;box-shadow:0 10px 15px -3px rgba(37,99,235,0.15);">
                    <div style="font-size:11px;font-weight:700;color:rgba(255,255,255,0.75) !important;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">AI Recommendation</div>
                    <div style="font-size:20px;font-weight:800;color:#FFFFFF !important;line-height:1.2;margin-bottom:8px;">{spec}</div>
                    <div style="display:inline-flex;padding:2px 8px;background:rgba(255,255,255,0.2);color:#FFFFFF !important;font-size:10px;font-weight:700;border-radius:999px;margin-bottom:12px;">Route Assigned ✓</div>
                    <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.2);">
                        <div style="font-size:11px;font-weight:700;color:rgba(255,255,255,0.75) !important;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Reason</div>
                        <div style="font-size:13px;color:#FFFFFF !important;line-height:1.5;">{reason}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if st.button("Proceed to Booking →", key="sym_next"):
                    advance_stage("Symptom Analysis")
            else:
                st.markdown("""
                <div style="text-align:center;padding:40px 20px;border:2px dashed #E2E8F0;border-radius:12px;background:#F8FAFC;">
                    <div style="font-size:36px;margin-bottom:12px;">🩺</div>
                    <div style="font-size:13px;font-weight:600;color:#475569;">Awaiting Analysis</div>
                    <div style="font-size:11px;color:#94A3B8;margin-top:4px;">Enter symptoms and click Analyze</div>
                </div>
                """, unsafe_allow_html=True)

    # ─── MODULE 3: APPOINTMENT BOOKING ───
    elif st.session_state.workflow_stage == "Appointment Booking":
        st.markdown('<div style="font-size:22px;font-weight:800;color:#0F172A;margin-bottom:4px;">Appointment Scheduling</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;color:#64748B;margin-bottom:20px;">Specialist doctors pre-filtered by your AI referral</div>', unsafe_allow_html=True)

        col_f, col_s = st.columns([1, 1], gap="medium")

        with col_f:
            st.markdown(f"""
            <div style="background:#2563EB;border:none;border-radius:10px;padding:10px 14px;margin-bottom:16px;font-size:12px;color:#FFFFFF !important;font-weight:600;box-shadow:0 4px 6px -1px rgba(37,99,235,0.15);">
                📋 AI-Routed Specialist: &nbsp;<strong style="color:#FFFFFF !important;">{st.session_state.recommended_specialist}</strong>
            </div>
            """, unsafe_allow_html=True)

            p_name = st.text_input("Patient Full Name",
                value=st.session_state.registered_users.get(st.session_state.current_user, {}).get("name", ""),
                placeholder="Full name as on medical record")

            spec_key = st.session_state.analyzed_raw_specialist
            docs = DOCTOR_LIST.get(spec_key, DOCTOR_LIST["General Physician"])
            sel_doc = st.selectbox("Select Specialist Doctor", docs)

            c1, c2 = st.columns(2)
            with c1:
                appt_date = st.date_input("Appointment Date", min_value=datetime.date.today())
            with c2:
                slots = [datetime.time(h, m) for h in range(9, 17) for m in (0, 30)]
                appt_time = st.selectbox("Time Slot", slots, index=4)

            if st.button("Confirm Appointment →", key="appt_btn"):
                if not p_name.strip():
                    st.error("Patient name is required.")
                else:
                    st.session_state.appointment_details = {
                        "id": random.randint(100000, 999999),
                        "patient": p_name.strip(),
                        "doctor": sel_doc,
                        "specialist": st.session_state.recommended_specialist,
                        "raw_specialist": spec_key,
                        "date": appt_date,
                        "time": appt_time,
                    }
                    st.success("✅ Appointment confirmed! Proceeding to payment.")
                    time.sleep(1)
                    advance_stage("Appointment Booking")

        with col_s:
            st.markdown(f"""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:20px;">
                <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;">Booking Summary</div>
                <div style="font-size:11px;color:#94A3B8;margin-bottom:2px;">SPECIALIST</div>
                <div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:10px;">{st.session_state.recommended_specialist}</div>
                <div style="font-size:11px;color:#94A3B8;margin-bottom:2px;">SYMPTOM LANGUAGE</div>
                <div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:10px;">{st.session_state.symptom_lang}</div>
                <div style="font-size:11px;color:#94A3B8;margin-bottom:2px;">CONSULTATION FEE</div>
                <div style="font-size:22px;font-weight:800;color:#059669;margin-bottom:2px;">₹590</div>
                <div style="font-size:10px;color:#94A3B8;">incl. 18% GST</div>
            </div>
            """, unsafe_allow_html=True)

    # ─── MODULE 4: PAYMENT ───
    elif st.session_state.workflow_stage == "Payment Gateway":
        st.markdown('<div style="font-size:22px;font-weight:800;color:#0F172A;margin-bottom:4px;">Secure Checkout</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;color:#64748B;margin-bottom:20px;">256-bit encrypted payment gateway</div>', unsafe_allow_html=True)

        appt = st.session_state.appointment_details
        if not appt:
            st.warning("No appointment found. Please go back and book one.")
        else:
            col_inv, col_pay = st.columns([1, 1], gap="medium")

            with col_inv:
                st.markdown(f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:20px;">
                    <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;">Invoice</div>
                    <div style="font-size:11px;color:#94A3B8;">APPOINTMENT ID</div>
                    <div style="font-family:monospace;font-size:14px;font-weight:700;color:#0F172A;margin-bottom:10px;">#{appt['id']}</div>
                    <div style="font-size:11px;color:#94A3B8;">PATIENT</div>
                    <div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:10px;">{appt['patient']}</div>
                    <div style="font-size:11px;color:#94A3B8;">DOCTOR · DEPT</div>
                    <div style="font-size:13px;font-weight:600;color:#0F172A;margin-bottom:2px;">{appt['doctor']}</div>
                    <div style="font-size:11px;color:#64748B;margin-bottom:10px;">{appt['specialist']}</div>
                    <div style="font-size:11px;color:#94A3B8;">SCHEDULE</div>
                    <div style="font-size:13px;font-weight:600;color:#0F172A;margin-bottom:16px;">{appt['date'].strftime('%d %b %Y')} · {appt['time'].strftime('%I:%M %p')}</div>
                    <div style="border-top:1px solid #E2E8F0;padding-top:12px;">
                        <div style="display:flex;justify-content:space-between;font-size:12px;color:#64748B;margin-bottom:4px;">
                            <span>Consultation Fee</span><span>₹500.00</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:12px;color:#64748B;margin-bottom:8px;">
                            <span>GST (18%)</span><span>₹90.00</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:16px;font-weight:800;color:#0F172A;">
                            <span>Total</span><span style="color:#059669;">₹590.00</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_pay:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:10px;">Payment Method</div>', unsafe_allow_html=True)
                method = st.selectbox("", ["UPI", "Debit Card", "Credit Card", "Net Banking", "Cash at Hospital"], label_visibility="collapsed")

                if method == "UPI":
                    st.markdown("""
                    <div style="text-align:center;background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:10px;padding:14px;margin-bottom:10px;">
                        <img src="https://img.icons8.com/color/96/qr-code.png" width="56"/>
                        <div style="font-size:11px;color:#64748B;margin-top:4px;">Scan with GPay · PhonePe · Paytm</div>
                        <div style="font-size:13px;font-weight:700;color:#2563EB;margin-top:2px;">careflowai@okaxis</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.text_input("Your UPI ID", placeholder="e.g. user@okhdfcbank", key="upi_id")

                elif method in ["Debit Card", "Credit Card"]:
                    st.text_input("Card Number", placeholder="1234  5678  9012  3456", key="card_num")
                    c1, c2 = st.columns(2)
                    with c1: st.text_input("Expiry", placeholder="MM/YY", key="card_exp")
                    with c2: st.text_input("CVV", type="password", placeholder="•••", key="card_cvv")
                    st.text_input("Name on Card", placeholder="As printed on card", key="card_name")

                elif method == "Net Banking":
                    bank = st.selectbox("Select Bank", ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra"], key="nb_bank")
                    st.info(f"You'll be redirected to {bank}'s secure portal.")

                elif method == "Cash at Hospital":
                    st.markdown("""
                    <div style="background:#F0FDF4;border:1px solid #A7F3D0;border-radius:10px;padding:10px;font-size:12px;color:#065F46;font-weight:500;margin-bottom:10px;">
                        ✅ Pay ₹590 in cash at the Hospital Billing Counter on arrival.
                    </div>
                    """, unsafe_allow_html=True)

                if st.button("Pay ₹590 Securely →", key="pay_btn"):
                    bar = st.progress(0, text="Verifying payment…")
                    for pct in range(101):
                        time.sleep(0.01)
                        bar.progress(pct, text=f"Processing… {pct}%")
                    bar.empty()
                    txn = "TXN" + str(random.randint(10000000, 99999999))
                    st.session_state.payment_details = {"method": method, "amount": 590, "txn_id": txn, "status": "Successful"}
                    st.success(f"✅ Payment Successful · TXN: `{txn}`")
                    time.sleep(1)
                    advance_stage("Payment Gateway")

    # ─── MODULE 5: TOKEN GENERATION ───
    elif st.session_state.workflow_stage == "Token Generation":
        st.markdown('<div style="font-size:22px;font-weight:800;color:#0F172A;margin-bottom:4px;">Queue Token</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;color:#64748B;margin-bottom:20px;">Your sequential pass to the consultation room</div>', unsafe_allow_html=True)

        appt = st.session_state.appointment_details
        pay  = st.session_state.payment_details

        col_tok, col_info = st.columns([1, 1], gap="medium")

        with col_tok:
            if st.session_state.my_token is None:
                st.markdown('<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:24px;text-align:center;">', unsafe_allow_html=True)
                if appt:
                    st.markdown(f"""
                    <div style="font-size:11px;color:#64748B;margin-bottom:4px;">Patient</div>
                    <div style="font-size:16px;font-weight:700;color:#0F172A;margin-bottom:4px;">{appt['patient']}</div>
                    <div style="font-size:12px;color:#64748B;margin-bottom:2px;">{appt['doctor']} · {appt['specialist']}</div>
                    <div style="font-size:11px;font-family:monospace;color:#94A3B8;margin-bottom:16px;">TXN: {pay.get('txn_id','—')}</div>
                    """, unsafe_allow_html=True)
                if st.button("🎫 Generate My Token", key="gen_tok"):
                    st.session_state.global_token_counter += 1
                    st.session_state.my_token = st.session_state.global_token_counter
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                tok = st.session_state.my_token
                st.markdown(f"""
                <div style="text-align:center;background:linear-gradient(135deg,#ECFDF5,#D1FAE5);border:2px dashed #10B981;border-radius:12px;padding:30px 20px;">
                    <div style="display:inline-flex;padding:2px 8px;background:#D1FAE5;color:#065F46;font-size:10px;font-weight:700;border-radius:999px;margin-bottom:12px;">Active Queue Pass</div>
                    <div style="font-size:12px;font-weight:700;color:#065F46;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Your Token Number</div>
                    <div style="font-size:64px;font-weight:900;color:#047857;font-family:monospace;line-height:1;margin-bottom:6px;">#{tok}</div>
                    <div style="font-size:11px;color:#065F46;opacity:0.8;">Show this at the department counter</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if st.button("Continue → Waiting Time", key="tok_next"):
                    advance_stage("Token Generation")

        with col_info:
            st.markdown(f"""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:20px;">
                <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;">Queue Status</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <span style="font-size:12px;color:#64748B;">Currently Serving</span>
                    <span style="font-size:16px;font-weight:800;color:#0F172A;">#{st.session_state.global_token_counter - 3}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <span style="font-size:12px;color:#64748B;">Patients Ahead</span>
                    <span style="font-size:16px;font-weight:800;color:#2563EB;">~3</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                    <span style="font-size:12px;color:#64748B;">Est. Wait</span>
                    <span style="font-size:16px;font-weight:800;color:#059669;">~30 min</span>
                </div>
                <div style="background:#E2E8F0;border-radius:8px;padding:10px;font-size:11px;color:#475569;line-height:1.4;">
                    📢 We'll send SMS alerts at 60, 30 & 10 minutes before your slot.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ─── SUB-NAV CLINICAL FLOW (WAITING TIME AND SUBSEQUENT STAGES) ───
    elif st.session_state.workflow_stage in ["Waiting Time", "SMS Reminders", "Consultation Room", "Medicine History", "Patient History"]:
        st.markdown('<div style="font-size:22px;font-weight:800;color:#0F172A;margin-bottom:4px;">Consultation & Care Workflow</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;color:#64748B;margin-bottom:12px;">Track your live queue, view alerts, checkout consultation and access E-Records</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "⏳ Wait Estimator", 
            "📩 SMS Alerts", 
            "🩻 Consult Room", 
            "💊 Pharmacy Log", 
            "📜 Health Record"
        ])

        with tab1:
            my_tok = st.session_state.my_token or 25
            col_q, col_ml = st.columns([1, 1], gap="medium")

            with col_q:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:12px;">📊 Queue Estimator</div>', unsafe_allow_html=True)
                curr = st.slider("Currently serving token", 1, max(my_tok, 50), max(1, my_tok - 5))
                ahead = max(0, my_tok - curr)
                wait  = ahead * 10
                st.metric("Patients Ahead", f"{ahead}")
                st.markdown(f"""
                <div style="background:#2563EB;padding:12px;border-radius:8px;margin-top:12px;color:#FFFFFF !important;box-shadow:0 4px 6px -1px rgba(37,99,235,0.15);">
                    <div style="font-size:10px;font-weight:700;color:rgba(255,255,255,0.8) !important;text-transform:uppercase;letter-spacing:0.05em;">Queue Wait Time</div>
                    <div style="font-size:28px;font-weight:900;color:#FFFFFF !important;margin:2px 0;">{wait} min</div>
                    <div style="font-size:10px;color:rgba(255,255,255,0.7) !important;">Formula: ({my_tok} − {curr}) × 10 min avg</div>
                </div>
                """, unsafe_allow_html=True)

            with col_ml:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:12px;">🧠 Smart AI Predictor (ML)</div>', unsafe_allow_html=True)
                g_sel = st.selectbox("Gender", ["Female","Male","Other"], key="wt_g")
                a_sel = st.slider("Age", 0, 100, 28, key="wt_a")
                r_sel = st.selectbox("Race", ["White","African American","Asian","Native American","Two or More Races","Pacific Islander","Declined to Identify"], key="wt_r")
                adm_sel = st.selectbox("Needs Admission Bed?", ["No","Yes"], key="wt_adm")
                cm_sel  = st.selectbox("Co-morbidities?", ["No","Yes"], key="wt_cm")

                if st.button("⚡ Predict Smart Wait Time", key="ml_btn"):
                    gmap = {"Female":0,"Male":1,"Other":2}
                    rmap = {"African American":0,"Asian":1,"Declined to Identify":2,"Native American":3,"Pacific Islander":4,"Two or More Races":5,"White":6}
                    spec_k = st.session_state.analyzed_raw_specialist
                    dept = 2
                    if "Cardio" in spec_k: dept=0
                    elif "Neuro" in spec_k: dept=3
                    elif "Ortho" in spec_k: dept=4

                    today = datetime.date.today()
                    feats = pd.DataFrame([[
                        gmap.get(g_sel,1), a_sel, rmap.get(r_sel,6), dept,
                        1 if adm_sel=="Yes" else 0, 3,
                        1 if cm_sel=="Yes" else 0,
                        today.year, today.month, today.day, today.weekday()
                    ]], columns=["Patient Gender","Patient Age","Patient Race","Department Referral",
                                 "Patient Admission Flag","Patient Satisfaction Score","Patients CM",
                                 "Admission_Year","Admission_Month","Admission_Day","Admission_Weekday"])

                    if ml_model:
                        try:
                            pred = round(float(ml_model.predict(feats)[0]), 1)
                            st.markdown(f"""
                            <div style="background:#ECFDF5;border-left:4px solid #059669;padding:12px;border-radius:8px;margin-top:10px;">
                                <div style="font-size:10px;font-weight:700;color:#047857;text-transform:uppercase;letter-spacing:0.05em;">ML Prediction</div>
                                <div style="font-size:28px;font-weight:900;color:#059669;margin:2px 0;">{pred} min</div>
                                <div style="font-size:10px;color:#10B981;">RandomForest · trained on ER data</div>
                            </div>
                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Prediction error: {e}")
                    else:
                        sim = random.randint(20,50) + a_sel//10
                        st.markdown(f"""
                        <div style="background:#ECFDF5;border-left:4px solid #059669;padding:12px;border-radius:8px;margin-top:10px;">
                            <div style="font-size:10px;font-weight:700;color:#047857;text-transform:uppercase;letter-spacing:0.05em;">ML Prediction (Simulated)</div>
                            <div style="font-size:28px;font-weight:900;color:#059669;margin:2px 0;">{sim} min</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Continue → SMS Reminders →", key="wt_next"):
                advance_stage("Waiting Time")

        with tab2:
            appt = st.session_state.appointment_details
            my_t = st.session_state.my_token or 25

            if not appt:
                st.warning("No active appointment. Complete previous steps first.")
            else:
                col_tl, col_ph = st.columns([1, 1], gap="medium")

                with col_tl:
                    st.markdown('<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:12px;">Notification Schedule</div>', unsafe_allow_html=True)
                    for mins in [60, 50, 40, 30, 20, 10]:
                        msg = f"Reminder: Your appointment with {appt['doctor']} is at {appt['time'].strftime('%I:%M %p')}. Token #{my_t}"
                        icon = "🔔" if mins <= 30 else "📢"
                        st.markdown(f"""
                        <div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #E2E8F0;">
                            <div style="background:#2563EB;color:#FFFFFF !important;font-size:9px;font-weight:700;padding:2px 6px;border-radius:4px;white-space:nowrap;">{icon} T−{mins}m</div>
                            <div style="font-family:monospace;font-size:11px;color:#334155;background:#F8FAFC;padding:6px 10px;border-radius:6px;flex:1;">{msg}</div>
                        </div>
                        """, unsafe_allow_html=True)

                with col_ph:
                    st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
                    st.markdown('<div style="font-size:13px;font-weight:700;color:#0F172A;margin-bottom:10px;">Live SMS Preview</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="phone-wrap">
                        <div class="phone-screen">
                            <div class="phone-status">
                                <span>📶 CareFlow</span><span>10:42 AM</span><span>🔋 94%</span>
                            </div>
                            <div style="font-size:8px;font-weight:700;color:#64748B;text-align:center;margin-bottom:6px;">💬 CAREFLOW-AI</div>
                            <div class="sms-bubble">
                                Reminder: Your appointment with {appt['doctor']} is at {appt['time'].strftime('%I:%M %p')}.
                                Token #{my_t}. Please arrive 10 min early.
                                <div class="sms-time">Just now</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🔊 Test Notification Chime", key="chime_btn"):
                        beep = """<script>
                        try {
                            const ctx = new (window.AudioContext||window.webkitAudioContext)();
                            [880,1100].forEach((f,i) => {
                                const o=ctx.createOscillator(), g=ctx.createGain();
                                o.connect(g); g.connect(ctx.destination);
                                o.frequency.value=f; g.gain.value=0.08;
                                o.start(ctx.currentTime+i*0.18);
                                o.stop(ctx.currentTime+i*0.18+0.15);
                            });
                        } catch(e){}
                        </script>"""
                        st.components.v1.html(beep, height=0)
                        st.toast("📩 SMS dispatched!", icon="✅")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Enter Consultation Room →", key="sms_next"):
                    advance_stage("SMS Reminders")

        with tab3:
            appt = st.session_state.appointment_details
            if not appt:
                st.warning("No active appointment found.")
            else:
                col_i, col_w = st.columns([1, 1], gap="medium")

                with col_i:
                    st.markdown(f"""
                    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                        <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:12px;">Session Details</div>
                        <div style="margin-bottom:8px;"><span style="font-size:11px;color:#94A3B8;">PATIENT</span><br><span style="font-size:14px;font-weight:700;color:#0F172A;">{appt['patient']}</span></div>
                        <div style="margin-bottom:8px;"><span style="font-size:11px;color:#94A3B8;">SPECIALTY</span><br><span style="font-size:14px;font-weight:700;color:#0F172A;">{appt['specialist']}</span></div>
                        <div style="margin-bottom:8px;"><span style="font-size:11px;color:#94A3B8;">DATE · TIME</span><br><span style="font-size:14px;font-weight:700;color:#0F172A;">{appt['date'].strftime('%d %b %Y')} · {appt['time'].strftime('%I:%M %p')}</span></div>
                        <div style="margin-top:12px;padding:10px;background:#E2E8F0;border-radius:8px;">
                            <div style="font-size:10px;font-weight:700;color:#64748B;margin-bottom:4px;">SYMPTOMS LOGGED</div>
                            <div style="font-size:11px;font-style:italic;color:#334155;">"{st.session_state.symptom_input}"</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_w:
                    st.markdown('<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:12px;">Clinical Checkout</div>', unsafe_allow_html=True)
                    v1 = st.checkbox("✅ Vitals recorded (BP · Heart Rate · Temp · SpO2)", key="vit1")
                    v2 = st.checkbox("✅ Consultation completed", key="vit2")

                    med = st.text_input("Prescribed Medicine", placeholder="e.g. Amoxicillin, Cetirizine", key="med_in")
                    dos = st.selectbox("Dosage", ["1 Tablet Daily", "1 Tablet Twice Daily", "1 Tablet Thrice Daily", "650 mg SOS", "1 Tablet Weekly"], key="dos_in")
                    dur = st.selectbox("Duration", ["3 Days", "5 Days", "7 Days", "10 Days", "2 Weeks", "1 Month"], key="dur_in")

                    if st.button("✅ Complete & Log Prescription", key="consult_btn"):
                        if not v1 or not v2:
                            st.error("Please tick both clinical checkboxes before completing.")
                        elif not med.strip():
                            st.error("Please enter the prescribed medicine.")
                        else:
                            st.session_state.consultation_details = {
                                "date": str(datetime.date.today()),
                                "doctor": appt['doctor'],
                                "specialist": appt['specialist'],
                                "status": "Completed"
                            }
                            st.session_state.medicine_history.insert(0, {
                                "Medicine": med.strip(), "Dosage": dos, "Duration": dur,
                                "Doctor": appt['doctor'], "Date": str(datetime.date.today())
                            })
                            st.success("🎉 Consultation complete! Prescription saved.")
                            time.sleep(1)
                            advance_stage("Consultation Room")

        with tab4:
            df = pd.DataFrame(st.session_state.medicine_history)
            st.dataframe(df, use_container_width=True)

            if len(st.session_state.medicine_history) > 0:
                latest = st.session_state.medicine_history[0]
                st.markdown(f"""
                <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:12px;padding:16px;margin-top:16px;">
                    <div style="font-size:12px;font-weight:700;color:#065F46;margin-bottom:8px;">📝 Latest Prescription</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px;">
                        <div><span style="color:#64748B;">Medicine</span><br><strong style="color:#0F172A;">{latest['Medicine']}</strong></div>
                        <div><span style="color:#64748B;">Dosage</span><br><strong style="color:#0F172A;">{latest['Dosage']}</strong></div>
                        <div><span style="color:#64748B;">Duration</span><br><strong style="color:#0F172A;">{latest['Duration']}</strong></div>
                        <div><span style="color:#64748B;">Doctor</span><br><strong style="color:#0F172A;">{latest['Doctor']}</strong></div>
                    </div>
                    <div style="font-size:10px;color:#10B981;margin-top:10px;">Authorized: {latest['Date']} · CareFlow Pharmacy Network</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("View Patient History →", key="med_next"):
                advance_stage("Medicine History")

        with tab5:
            appt = st.session_state.appointment_details
            pay  = st.session_state.payment_details
            user = st.session_state.current_user
            udata= st.session_state.registered_users.get(user, {})
            consult = st.session_state.consultation_details
            status_done = consult.get("status") == "Completed"

            col_a, col_b = st.columns([1, 1], gap="medium")
            with col_a:
                st.markdown(f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;margin-bottom:12px;">
                    <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;">👤 Patient Profile</div>
                    <div style="margin-bottom:6px;"><span style="font-size:11px;color:#94A3B8;">FULL NAME</span><br><span style="font-size:14px;font-weight:700;color:#0F172A;">{udata.get('name','—')}</span></div>
                    <div style="margin-bottom:6px;"><span style="font-size:11px;color:#94A3B8;">PHONE</span><br><span style="font-size:13px;font-weight:600;color:#0F172A;">{udata.get('phone','—')}</span></div>
                    <div style="margin-bottom:6px;"><span style="font-size:11px;color:#94A3B8;">USERNAME</span><br><span style="font-size:13px;font-weight:600;color:#64748B;">@{user}</span></div>
                </div>
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                    <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;">🩺 AI Diagnosis Route</div>
                    <div style="font-size:11px;color:#94A3B8;">SYMPTOMS</div>
                    <div style="font-size:12px;font-style:italic;color:#334155;margin-bottom:8px;">"{st.session_state.symptom_input}"</div>
                    <div style="font-size:11px;color:#94A3B8;">LANGUAGE DETECTED</div>
                    <div style="font-size:13px;font-weight:700;color:#0F172A;margin-bottom:6px;">{st.session_state.symptom_lang}</div>
                    <div style="font-size:11px;color:#94A3B8;">SPECIALIST ROUTED TO</div>
                    <div style="font-size:14px;font-weight:800;color:#2563EB;">{st.session_state.recommended_specialist}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_b:
                if appt:
                    st.markdown(f"""
                    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;margin-bottom:12px;">
                        <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;">📅 Appointment</div>
                        <div style="margin-bottom:6px;"><span style="font-size:11px;color:#94A3B8;">APPOINTMENT ID</span><br><span style="font-family:monospace;font-size:13px;font-weight:700;color:#0F172A;">#{appt['id']}</span></div>
                        <div style="margin-bottom:6px;"><span style="font-size:11px;color:#94A3B8;">DOCTOR</span><br><span style="font-size:13px;font-weight:700;color:#0F172A;">{appt['doctor']}</span></div>
                        <div style="margin-bottom:6px;"><span style="font-size:13px;font-weight:700;color:#0F172A;">{appt['date'].strftime('%d %b %Y')} · {appt['time'].strftime('%I:%M %p')}</span></div>
                    </div>
                    """, unsafe_allow_html=True)

                if pay:
                    status_badge = '<span style="display:inline-flex;padding:2px 8px;background:#ECFDF5;color:#047857;font-size:10px;font-weight:700;border-radius:999px;">Completed ✓</span>' if status_done else '<span style="display:inline-flex;padding:2px 8px;background:#FFFBEB;color:#B45309;font-size:10px;font-weight:700;border-radius:999px;">Pending ⏳</span>'
                    st.markdown(f"""
                    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                        <div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;">💳 Payment & Queue</div>
                        <div style="margin-bottom:6px;"><span style="font-size:11px;color:#94A3B8;">TRANSACTION ID</span><br><span style="font-family:monospace;font-size:12px;font-weight:700;color:#0F172A;">{pay.get('txn_id','—')}</span></div>
                        <div style="margin-bottom:6px;"><span style="font-size:11px;color:#94A3B8;">AMOUNT PAID</span><br><span style="font-size:16px;font-weight:800;color:#059669;">₹{pay.get('amount','—')}</span></div>
                        <div style="margin-bottom:6px;"><span style="font-size:11px;color:#94A3B8;">TOKEN</span><br><span style="font-size:18px;font-weight:900;color:#2563EB;font-family:monospace;">#{st.session_state.my_token}</span></div>
                        <div><span style="font-size:11px;color:#94A3B8;margin-bottom:2px;">STATUS</span><br>{status_badge}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Start New Session", key="finish_btn"):
                reset_workflow()

    workspace_ctx.__exit__(None, None, None)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:24px 0 8px;border-top:1px solid #E2E8F0;margin-top:32px;">
    <span style="font-size:18px;">🏥</span>
    <div style="font-size:13px;font-weight:700;color:#334155;margin-top:4px;">CareFlow AI</div>
    <div style="font-size:11px;color:#94A3B8;margin-top:2px;">Secure · Smart · Fast · Multi-lingual · ML-Powered</div>
</div>
""", unsafe_allow_html=True)