"""
Dimsum Analyst Bot — Main Telegram Bot
"""
import logging, re, os, asyncio, io
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

from config import (
    TELEGRAM_TOKEN, MENU, cari_item_dari_synonym,
    hitung_margin, get_margin_kategori, get_hpp, semua_nama_menu
)
from sheets import SheetsDB
from chart import bar_chart, pie_chart, profit_chart, trend_chart
from ai import generate_insight

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

db = SheetsDB()

# ─── HELPERS ───
def rupiah(n):
    return f"Rp{n:,}"

def _parse_transaction(text):
    """Parse natural language transaction input.
    Examples:
    - "jual 5 dimsum 3 mentai 2 gyoza"
    - "hari ini 10 dimsum, 4 mentai, 6 mix"
    - "5 dimsum mentai 3 tofu"
    - "catat: biasa 8, tofu 4, ekado 6"
    """
    text = text.lower().strip()
    # Remove common prefixes/suffixes
    for prefix in ["jual ", "catat ", "catat: ", "hari ini ", "hari ini: ",
                   "transaksi ", "tambah ", "terjual "]:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break

    # Split by commas and spaces
    parts = re.split(r"[,;]+", text)
    items_found = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Try to match "number word" or "word number"
        matches = re.findall(r"(\d+)\s+([a-zA-Z\s]+)", part)
        if matches:
            for num_str, word in matches:
                jumlah = int(num_str)
                word = word.strip()
                item_key = cari_item_dari_synonym(word)
                if item_key and jumlah > 0:
                    items_found.append((item_key, jumlah))
        else:
            # Try "word number" (e.g. "biasa 8")
            matches = re.findall(r"([a-zA-Z\s]+)\s+(\d+)", part)
            for word, num_str in matches:
                jumlah = int(num_str)
                word = word.strip()
                item_key = cari_item_dari_synonym(word)
                if item_key and jumlah > 0:
                    items_found.append((item_key, jumlah))

    return items_found

# ─── COMMAND HANDLERS ───

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🥟 *Dimsum Analyst Bot*\n"
        "Bismillah, catat penjualan dan pantau bisnis dimsummu!\n\n"
        "*📝 Catat Penjualan:*\n"
        "Ketik bebas, misal:\n"
        "`jual 5 dimsum 3 mentai 2 gyoza`\n"
        "`hari ini 10 dimsum, 4 mentai, 6 mix`\n\n"
        "*📊 Laporan:*\n"
        "/hari — Laporan hari ini\n"
        "/minggu — Laporan minggu ini\n"
        "/bulan — Laporan bulan ini\n"
        "/rekap — Insight AI + rekomendasi\n\n"
        "*⚙️ Lainnya:*\n"
        "/menu — Daftar menu & harga\n"
        "/profit — Rincian profit\n"
        "/hpp — Lihat/ubah HPP\n"
        "/biaya — Biaya operasional\n"
        "/export — Download CSV\n"
        "/help — Semua command"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🥟 *MENU & HARGA*\n"]
    for key, item in MENU.items():
        margin = hitung_margin(item["harga"], get_hpp(item["hpp_key"]))
        label = get_margin_kategori(margin)
        lines.append(
            f"• {item['nama']}\n"
            f"  Jual: {rupiah(item['harga'])} | HPP: {rupiah(get_hpp(item['hpp_key']))}\n"
            f"  Margin: {margin}% {label}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def transaksi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural language transaction input"""
    text = update.message.text.strip()
    items = _parse_transaction(text)

    if not items:
        # Show inline keyboard for interactive input
        await _show_menu_keyboard(update, context)
        return

    # Confirmation
    lines = ["📋 *Yang mau dicatat:*\n"]
    total_rev = 0
    for item_key, jumlah in items:
        item = MENU[item_key]
        total = item["harga"] * jumlah
        total_rev += total
        lines.append(f"• {item['nama']} _{jumlah}_ pcs × {rupiah(item['harga'])} = {rupiah(total)}")

    lines.append(f"\n💵 *Total: {rupiah(total_rev)}*")
    lines.append("")
    lines.append("👇 Klik tombol di bawah untuk konfirmasi")

    # Store in context
    context.user_data["pending_transaksi"] = items

    keyboard = [
        [InlineKeyboardButton("✅ Simpan", callback_data="simpan"),
         InlineKeyboardButton("❌ Batal", callback_data="batal")],
        [InlineKeyboardButton("➕ Edit jumlah", callback_data="edit_transaksi")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown",
                                    reply_markup=reply_markup)

async def _show_menu_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show interactive menu selection"""
    if "cart" not in context.user_data:
        context.user_data["cart"] = []

    keyboard = []
    for key, item in MENU.items():
        btn_text = f"{item['nama']} ({rupiah(item['harga'])})"
        # Show count if already in cart
        count = sum(1 for k, _ in context.user_data["cart"] if k == key)
        if count > 0:
            btn_text += f" [{count}]"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"add_{key}")])

    if context.user_data["cart"]:
        total = sum(MENU[k]["harga"] * j for k, j in context.user_data["cart"])
        keyboard.append([InlineKeyboardButton(f"✅ Selesai — {rupiah(total)}",
                                               callback_data="checkout")])
        keyboard.append([InlineKeyboardButton("🗑️ Hapus semua", callback_data="clear_cart")])
    else:
        keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="batal")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "Pilih item & jumlah, lalu konfirmasi:"
    await update.message.reply_text(msg, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "batal":
        context.user_data.pop("pending_transaksi", None)
        context.user_data.pop("cart", None)
        await query.edit_message_text("❌ Dibatalkan.")

    elif data == "simpan":
        items = context.user_data.pop("pending_transaksi", None)
        if not items:
            await query.edit_message_text("❌ Tidak ada data.")
            return

        # Save all transactions
        msg_lines = ["✅ *Transaksi tersimpan:*\n"]
        total_rev = 0
        total_profit = 0
        for item_key, jumlah in items:
            item = MENU[item_key]
            txn = db.add_transaction(item["nama"], jumlah, item["harga"], get_hpp(item_key))
            total_rev += txn["total"]
            total_profit += txn["profit"]
            msg_lines.append(f"• {item['nama']} × {jumlah} = {rupiah(txn['total'])}")

        msg_lines.append(f"\n💵 *Revenue: {rupiah(total_rev)}*")
        msg_lines.append(f"💰 *Profit: {rupiah(total_profit)}*")

        await query.edit_message_text("\n".join(msg_lines), parse_mode="Markdown")

    elif data == "checkout":
        cart = context.user_data.pop("cart", [])
        context.user_data["pending_transaksi"] = cart
        # Re-use simpan logic
        await button_handler(update, context)

    elif data == "clear_cart":
        context.user_data["cart"] = []
        await query.edit_message_text("🔄 Keranjang dikosongkan. Pilih /menu lagi.")

    elif data == "edit_transaksi":
        await query.edit_message_text(
            "Ketik ulang pesanan dengan format:\n"
            "`5 dimsum 3 mentai 2 gyoza`"
        )

    elif data.startswith("add_"):
        item_key = data[4:]
        if item_key in MENU:
            # Show quantity selector
            keyboard = []
            row = []
            for qty in [1, 2, 3, 5, 10]:
                row.append(InlineKeyboardButton(
                    str(qty), callback_data=f"qty_{item_key}_{qty}"))
            keyboard.append(row)
            keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="batal_add")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"Berapa pcs *{MENU[item_key]['nama']}*?",
                parse_mode="Markdown", reply_markup=reply_markup)

    elif data.startswith("qty_"):
        parts = data.split("_")
        item_key = parts[1]
        qty = int(parts[2])
        if "cart" not in context.user_data:
            context.user_data["cart"] = []
        for _ in range(qty):
            context.user_data["cart"].append((item_key, 1))
        await query.edit_message_text(f"✅ {qty} {MENU[item_key]['nama']} ditambahkan.")
        await asyncio.sleep(0.5)
        # Show menu again
        if update.effective_chat:
            fake_msg = type("obj", (object,), {"reply_text": lambda s, **kw: None})()
            await _show_menu_keyboard(update, context)

# ─── REPORT HANDLERS ───

async def _send_report(update: Update, context: ContextTypes.DEFAULT_TYPE,
                       title, txns, with_insight=False):
    """Generate and send a report with chart + text"""
    summary = db.summary(txns)

    if summary["total_pcs"] == 0:
        await update.message.reply_text(f"📭 Belum ada data untuk {title.lower()}.")
        return

    # Text report
    lines = [f"📊 *{title}*\n"]
    for item in summary["item_order"]:
        data = summary["per_item"][item]
        pct = round(data["pcs"]/summary["total_pcs"]*100, 1)
        margin = round((data["revenue"]-data["hpp"])/data["revenue"]*100, 1)
        lines.append(
            f"• {item}: {data['pcs']} pcs ({pct}%) | "
            f"{rupiah(data['revenue'])} | margin {margin}%"
        )

    lines.append(f"\n💵 *Total: {summary['total_pcs']} pcs*")
    lines.append(f"💵 *Revenue: {rupiah(summary['total_revenue'])}*")
    lines.append(f"💰 *Profit: {rupiah(summary['total_profit'])}*")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    # Charts
    try:
        chart_path = bar_chart(summary, title)
        if chart_path and os.path.exists(chart_path):
            with open(chart_path, "rb") as f:
                await update.message.reply_photo(f)

        profit_path = profit_chart(summary, f"Profit {title}")
        if profit_path and os.path.exists(profit_path):
            with open(profit_path, "rb") as f:
                await update.message.reply_photo(f)
    except Exception as e:
        logger.warning(f"Chart generation failed: {e}")
        await update.message.reply_text("⚠️ Gagal generate chart.")

    # Insight
    if with_insight:
        await update.message.reply_text("💡 *Menganalisis data...*", parse_mode="Markdown")
        insight = generate_insight(summary, title)
        await update.message.reply_text(insight)

async def today_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txns = db.get_today()
    await _send_report(update, context, "LAPORAN HARI INI", txns, with_insight=False)

async def week_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txns = db.get_this_week()
    await _send_report(update, context, "LAPORAN MINGGU INI", txns, with_insight=True)

async def month_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txns = db.get_this_month()
    await _send_report(update, context, "LAPORAN BULAN INI", txns, with_insight=True)

async def rekap_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI insight for today"""
    txns = db.get_today()
    summary = db.summary(txns)
    if summary["total_pcs"] == 0:
        await update.message.reply_text("📭 Belum ada data hari ini.")
        return

    await update.message.reply_text("💡 *Menganalisis data...*", parse_mode="Markdown")
    insight = generate_insight(summary, "hari ini")
    await update.message.reply_text(insight)

async def profit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profit breakdown per item + total"""
    txns = db.get_this_month()
    summary = db.summary(txns)
    if summary["total_pcs"] == 0:
        txns = db.get_today()
        summary = db.summary(txns)

    lines = ["💰 *RINCIAN PROFIT*\n"]
    for item in summary["item_order"]:
        data = summary["per_item"][item]
        margin = round((data["revenue"]-data["hpp"])/data["revenue"]*100, 1)
        label = get_margin_kategori(margin)
        lines.append(
            f"• {item}\n"
            f"  Revenue: {rupiah(data['revenue'])} | HPP: {rupiah(data['hpp'])}\n"
            f"  Profit: {rupiah(data['profit'])} | Margin: {margin}% {label}"
        )

    lines.append(f"\nTotal Revenue: {rupiah(summary['total_revenue'])}")
    lines.append(f"Total HPP: {rupiah(summary['total_hpp'])}")
    lines.append(f"*Total Profit: {rupiah(summary['total_profit'])}*")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    # Profit chart
    try:
        pp = profit_chart(summary, "Profit per Item (Bulan Ini)")
        if pp and os.path.exists(pp):
            with open(pp, "rb") as f:
                await update.message.reply_photo(f)
    except Exception:
        pass

async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export transactions as CSV"""
    txns = db.get_this_month()
    if not txns:
        txns = db.get_transactions()
    csv_data = db.export_csv(txns)

    await update.message.reply_document(
        document=io.BytesIO(csv_data),
        filename=f"dimsum_transaksi_{datetime.now().strftime('%Y%m')}.csv",
        caption="📊 Data transaksi"
    )

async def hpp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View or update HPP"""
    args = context.args
    if not args:
        # Show current HPP
        lines = ["📋 *HPP SAAT INI*\n"]
        for key, item in MENU.items():
            margin = hitung_margin(item["harga"], get_hpp(item["hpp_key"]))
            lines.append(f"• {item['nama']}: {rupiah(get_hpp(item['hpp_key']))} (margin {margin}%)")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    # Format: /hpp [item] [harga]
    if len(args) >= 2:
        try:
            hpp_baru = int(args[-1].replace(".", ""))
            item_name = " ".join(args[:-1]).lower()
            item_key = cari_item_dari_synonym(item_name)
            if item_key:
                import json
                hpp_path = os.path.join(os.path.dirname(__file__), "hpp.json")
                with open(hpp_path) as f:
                    hpp_data = json.load(f)
                hpp_data[item_key] = hpp_baru
                with open(hpp_path, "w") as f:
                    json.dump(hpp_data, f, indent=2)
                # Reload HPP in memory
                from config import HPP_DATA, load_hpp
                HPP_DATA.clear()
                HPP_DATA.update(load_hpp())
                margin = hitung_margin(MENU[item_key]["harga"], hpp_baru)
                await update.message.reply_text(
                    f"✅ HPP {MENU[item_key]['nama']} diubah jadi {rupiah(hpp_baru)}\n"
                    f"Margin sekarang: {margin}%"
                )
            else:
                await update.message.reply_text("❌ Item tidak ditemukan.")
        except ValueError:
            await update.message.reply_text("❌ Format: `/hpp [item] [harga]`")

async def biaya_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage operational costs"""
    args = context.args
    if not args:
        biaya = db.get_biaya()
        lines = ["📋 *BIAYA OPERASIONAL*\n"]
        total = 0
        for b in biaya["bulanan"]:
            lines.append(f"• {b['nama']}: {rupiah(b['jumlah'])}")
            total += b["jumlah"]
        lines.append(f"\nTotal: {rupiah(total)}")
        lines.append("\nGunakan: `/biaya [nama] [jumlah]` untuk menambah")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    if len(args) >= 2:
        try:
            jumlah = int(args[-1].replace(".", ""))
            nama = " ".join(args[:-1])
            db.add_biaya(nama, jumlah)
            await update.message.reply_text(f"✅ Biaya '{nama}' {rupiah(jumlah)} tersimpan.")
        except ValueError:
            await update.message.reply_text("❌ Format: `/biaya [nama] [jumlah]`")

async def best_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Best seller ranking"""
    txns = db.get_this_month()
    if not txns:
        txns = db.get_today()
    summary = db.summary(txns)

    if not summary["item_order"]:
        await update.message.reply_text("📭 Belum ada data.")
        return

    lines = ["🏆 *BESTSELLER RANKING*\n"]
    for i, item in enumerate(summary["item_order"], 1):
        data = summary["per_item"][item]
        pct = round(data["pcs"]/summary["total_pcs"]*100, 1)
        trophy = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        lines.append(f"{trophy} {item}: {data['pcs']} pcs ({pct}%)")

    lines.append(f"\nTotal: {summary['total_pcs']} pcs dari {len(summary['item_order'])} menu")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    # Pie chart
    try:
        pp = pie_chart(summary, "Kontribusi Revenue Bulan Ini")
        if pp and os.path.exists(pp):
            with open(pp, "rb") as f:
                await update.message.reply_photo(f)
    except Exception:
        pass

# ─── RUN ───
def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN belum diisi. Buat file .env")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("hari", today_report))
    app.add_handler(CommandHandler("minggu", week_report))
    app.add_handler(CommandHandler("bulan", month_report))
    app.add_handler(CommandHandler("rekap", rekap_cmd))
    app.add_handler(CommandHandler("profit", profit_cmd))
    app.add_handler(CommandHandler("export", export_cmd))
    app.add_handler(CommandHandler("hpp", hpp_cmd))
    app.add_handler(CommandHandler("biaya", biaya_cmd))
    app.add_handler(CommandHandler("best", best_cmd))
    app.add_handler(CommandHandler("bestseller", best_cmd))

    # Handle natural language input + inline buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, transaksi_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
