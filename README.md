# Dimsum Analyst Bot 🥟

Telegram bot for sales tracking, reporting, and business analytics — built for **Dumpling Warehouse Project**, a real UMKM based in Cianjur, Indonesia.

📸 **Instagram:** [@dumpling_warehouseproject](https://instagram.com/dumpling_warehouseproject)

## Features

- **Natural language input:** `jual 5 dimsum 3 mentai 2 gyoza`
- **Daily / weekly / monthly reports** with charts
- **Profit tracking** — auto-calculates margin from HPP (cost of goods)
- **AI Insight** — business recommendations based on sales data
- **Operational expenses** — rent, wages, etc.
- **CSV export**

## Menu

| Item | Price |
|------|-------|
| 🥟 Dimsum | Rp17.000 |
| 🥟 Dimsum Mentai | Rp18.000 |
| 🥟 Gyoza | Rp17.000 |
| 🥟 Ekado | Rp17.000 |
| 🥟 Tofu | Rp17.000 |
| 🥟 Mix Dimsum | Rp20.000 |

> Menu and prices maintained by the owner. Profit margin data is private — check the bot.

## Tech Stack

- Python 3.12
- python-telegram-bot
- matplotlib (charts)
- Google Sheets API (optional)
- Local JSON storage (fallback)

## Run Locally

```bash
git clone <repo-url>
cd dimsum-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up your token
cp .env.example .env
# edit .env → fill in TELEGRAM_TOKEN

python3 bot.py
```

## Structure

```
├── bot.py       # Main bot — handlers + commands
├── config.py    # Menu, HPP, constants
├── sheets.py    # Database layer (JSON → Google Sheets ready)
├── chart.py     # Chart generator (matplotlib)
├── ai.py        # AI insight (9router)
└── .env.example # Template config
```

## License

Private — internal business tool.
