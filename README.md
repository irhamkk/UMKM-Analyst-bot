# Dimsum Analyst Bot 🥟

Telegram bot buat catat penjualan, laporan, dan insight bisnis UMKM.

## Fitur

- **Natural language input:** `jual 5 dimsum 3 mentai 2 gyoza`
- **Laporan harian/mingguan/bulanan** + chart
- **Profit tracking** — otomatis hitung margin dari HPP
- **AI Insight** — rekomendasi bisnis dari data penjualan
- **Biaya operasional** — sewa, gaji, dll
- **Export CSV**

## Menu

| Item | Harga | HPP | Margin |
|------|:----:|:---:|:------:|
| Dimsum | Rp17.000 | Rp8.000 | 52,9% |
| Dimsum Mentai | Rp18.000 | Rp8.500 | 52,8% |
| Gyoza | Rp17.000 | Rp6.500 | 61,8% 🔥 |
| Ekado | Rp17.000 | Rp9.500 | 44,1% |
| Tofu | Rp17.000 | Rp11.000 | 35,3% |
| Mix Dimsum | Rp20.000 | Rp12.000 | 40,0% |

## Tech Stack

- Python 3.12
- python-telegram-bot
- matplotlib (chart)
- Google Sheets API (opsional)
- Local JSON storage (fallback)

## Cara Jalankan

```bash
git clone <repo-url>
cd dimsum-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Isi token
cp .env.example .env
# edit .env → isi TELEGRAM_TOKEN

python3 bot.py
```

## Struktur

```
├── bot.py       # Main bot — handler + command
├── config.py    # Menu, HPP, constants
├── sheets.py    # Database (JSON → Google Sheets ready)
├── chart.py     # Chart generator (matplotlib)
├── ai.py        # AI insight (9router)
└── .env.example # Template config
```
