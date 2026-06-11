"""
AI Insight generator — 9router / Groq for business recommendations
"""
import json, requests
from datetime import datetime
from config import AI_API_URL, AI_API_KEY, AI_MODEL

def _buat_prompt(summary, periode="hari ini", prev_summary=None):
    """Construct the insight prompt from data"""

    per_item_lines = []
    for item in summary["item_order"]:
        data = summary["per_item"][item]
        pct = round(data["pcs"] / summary["total_pcs"] * 100, 1) if summary["total_pcs"] > 0 else 0
        margin = round((data["revenue"] - data["hpp"]) / data["revenue"] * 100, 1) if data["revenue"] > 0 else 0
        per_item_lines.append(
            f"- {item}: {data['pcs']} pcs ({pct}%), revenue Rp{data['revenue']:,}, "
            f"HPP Rp{data['hpp']:,}, profit Rp{data['profit']:,}, margin {margin}%"
        )

    summary_text = (
        f"Periode: {periode}\n"
        f"Total terjual: {summary['total_pcs']} pcs\n"
        f"Revenue: Rp{summary['total_revenue']:,}\n"
        f"HPP: Rp{summary['total_hpp']:,}\n"
        f"Profit: Rp{summary['total_profit']:,}\n"
        f"Margin rata-rata: {round(summary['total_profit']/summary['total_revenue']*100, 1) if summary['total_revenue']>0 else 0}%\n\n"
        f"Per item:\n" + "\n".join(per_item_lines)
    )

    prompt = f"""Kamu adalah asisten bisnis UMKM kuliner yang analitis dan praktis. 
Analisis data penjualan berikut dan berikan insight/rekomendasi bisnis yang actionable dalam Bahasa Indonesia.

DATA PENJUALAN:
{summary_text}

Tugas kamu:
1. Analisis singkat performa periode ini (2-3 kalimat)
2. Identifikasi item terlaris dan underperformer serta alasannya
3. Berikan 3-4 rekomendasi bisnis actionable (spesifik, bukan general)
4. Proyeksi singkat ke depan

Format respons:
📋 ANALISIS
[analisis singkat]

🔥 BESTSELLER
[nama item] — [alasan kenapa laris]

⚠️ PERLU PERHATIAN
[nama item] — [masalah spesifik]

💡 REKOMENDASI
1. [rekomendasi 1 — spesifik, dengan angka]
2. [rekomendasi 2 — spesifik, dengan angka]  
3. [rekomendasi 3 — spesifik, dengan angka]

📈 PROYEKSI
[estimasi singkat]

Gunakan bahasa Indonesia yang natural, santai tapi profesional.
Jangan terlalu kaku atau formal. Langsung ke intinya."""
    return prompt

def generate_insight(summary, periode="hari ini", prev_summary=None):
    """Generate AI insight from summary data"""
    if summary["total_pcs"] == 0:
        return "Belum ada data penjualan untuk periode ini."

    prompt = _buat_prompt(summary, periode, prev_summary)

    payload = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.7,
    }

    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(
            AI_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()
        else:
            return f"🤖 Insight sementara: {_fallback_insight(summary, periode)}"
    except Exception:
        return f"🤖 Insight sementara: {_fallback_insight(summary, periode)}"

def _fallback_insight(summary, periode):
    """Local fallback when AI API unavailable"""
    lines = []
    best = summary["item_order"][0] if summary["item_order"] else "-"
    lines.append(f"📊 Total {summary['total_pcs']} pcs | Rp{summary['total_revenue']:,}")
    lines.append(f"🔥 Bestseller: {best}")

    if len(summary["item_order"]) > 1:
        worst = summary["item_order"][-1]
        worst_data = summary["per_item"][worst]
        lines.append(f"⚠️ Underperformer: {worst} ({worst_data['pcs']} pcs)")

    lines.append(f"💰 Profit: Rp{summary['total_profit']:,}")
    lines.append("")
    lines.append("💡 Saran: Tambah stok bestseller, evaluasi item yang kurang laku.")

    return "\n".join(lines)
