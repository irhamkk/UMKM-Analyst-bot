"""
Dimsum Analyst Bot — Configuration
Menu prices, HPP, constants
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ─── Menu (HPP di-load dari file terpisah) ───
MENU = {
    "dimsum":        {"nama": "Dimsum",        "harga": 17000, "hpp_key": "dimsum"},
    "dimsum mentai": {"nama": "Dimsum Mentai", "harga": 18000, "hpp_key": "dimsum mentai"},
    "gyoza":         {"nama": "Gyoza",         "harga": 17000, "hpp_key": "gyoza"},
    "ekado":         {"nama": "Ekado",         "harga": 17000, "hpp_key": "ekado"},
    "tofu":          {"nama": "Tofu",          "harga": 17000, "hpp_key": "tofu"},
    "mix dimsum":    {"nama": "Mix Dimsum",    "harga": 20000, "hpp_key": "mix dimsum"},
}

HPP_PATH = os.path.join(os.path.dirname(__file__), "hpp.json")

def load_hpp():
    """Load HPP from local JSON file. Returns 0 if file not found."""
    if os.path.exists(HPP_PATH):
        import json
        with open(HPP_PATH) as f:
            return json.load(f)
    return {}

HPP_DATA = load_hpp()

def get_hpp(item_key):
    """Get HPP for a menu item, default 0."""
    return HPP_DATA.get(item_key, 0)

# Synonyms for natural language parsing
SYNONYMS = {
    "dimsum":        ["dimsum", "biasa", "original"],
    "dimsum mentai": ["mentai", "dimsum mentai", "d mentai"],
    "gyoza":         ["gyoza", "gyoza"],
    "ekado":         ["ekado", "ekado"],
    "tofu":          ["tofu", "tahu"],
    "mix dimsum":    ["mix", "mix dimsum", "campur"],
}

# ─── Google Sheets ───
SHEET_ID = os.getenv("SHEET_ID", "")
SHEET_CREDS = os.getenv("SHEET_CREDS", "")  # path or JSON string

# ─── Telegram ───
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# ─── AI (9router / Groq) ───
AI_API_URL = os.getenv("AI_API_URL", "http://localhost:20128/v1/chat/completions")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "bigpickle")

# ─── Constants ───
KATEGORI_MARGIN = {
    (0, 30):    "⚠️ Tipis (butuh evaluasi)",
    (30, 45):   "📉 Cukup",
    (45, 55):   "✅ Baik",
    (55, 70):   "🔥 Bagus",
    (70, 101):  "🚀 Superior"
}

def hitung_margin(harga, hpp):
    if harga == 0:
        return 0
    return round((harga - hpp) / harga * 100, 1)

def get_margin_kategori(margin_persen):
    for (bawah, atas), label in KATEGORI_MARGIN.items():
        if bawah <= margin_persen < atas:
            return label
    return "—"

def cari_item_dari_synonym(kata):
    """Find menu key from user's synonym input"""
    kata = kata.lower().strip()
    for key, aliases in SYNONYMS.items():
        if kata in aliases:
            return key
    return None

def semua_nama_menu():
    return [item["nama"] for item in MENU.values()]

def semua_harga():
    return {k: v["harga"] for k, v in MENU.items()}
