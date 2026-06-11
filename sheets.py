"""
Google Sheets backend — transaction log + config sync
"""
import json, os, csv, io
from datetime import datetime
from config import SHEET_ID, SHEET_CREDS

class SheetsDB:
    """Local JSON fallback when Google Sheets unavailable"""
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or os.path.expanduser("~/.dimsum_data")
        os.makedirs(self.data_dir, exist_ok=True)
        self._transactions = []
        self._load()

    def _path(self, name):
        return os.path.join(self.data_dir, name)

    def _load(self):
        path = self._path("transactions.json")
        if os.path.exists(path):
            with open(path) as f:
                self._transactions = json.load(f)

    def _save(self):
        path = self._path("transactions.json")
        with open(path, "w") as f:
            json.dump(self._transactions, f, indent=2)

    # ─── Transactions ───
    def add_transaction(self, item, jumlah, harga, hpp):
        txn = {
            "id": len(self._transactions) + 1,
            "tanggal": datetime.now().strftime("%Y-%m-%d"),
            "jam": datetime.now().strftime("%H:%M"),
            "item": item,
            "jumlah": jumlah,
            "harga_satuan": harga,
            "total": harga * jumlah,
            "hpp_satuan": hpp,
            "profit": (harga - hpp) * jumlah,
        }
        self._transactions.append(txn)
        self._save()
        return txn

    def edit_transaction(self, txn_id, item=None, jumlah=None, harga=None, hpp=None):
        for t in self._transactions:
            if t["id"] == txn_id:
                if item: t["item"] = item
                if jumlah: t["jumlah"] = jumlah
                if harga: t["harga_satuan"] = harga
                if hpp: t["hpp_satuan"] = hpp
                t["total"] = t["jumlah"] * t["harga_satuan"]
                t["profit"] = (t["harga_satuan"] - t["hpp_satuan"]) * t["jumlah"]
                self._save()
                return t
        return None

    def delete_transaction(self, txn_id):
        self._transactions = [t for t in self._transactions if t["id"] != txn_id]
        self._save()

    def get_transactions(self, start_date=None, end_date=None, item=None):
        txns = self._transactions
        if start_date:
            txns = [t for t in txns if t["tanggal"] >= start_date]
        if end_date:
            txns = [t for t in txns if t["tanggal"] <= end_date]
        if item:
            txns = [t for t in txns if t["item"].lower() == item.lower()]
        return txns

    def get_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return [t for t in self._transactions if t["tanggal"] == today]

    def get_this_week(self):
        from datetime import timedelta
        today = datetime.now()
        start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        return self.get_transactions(start_date=start, end_date=today.strftime("%Y-%m-%d"))

    def get_this_month(self):
        today = datetime.now()
        start = today.strftime("%Y-%m-01")
        return self.get_transactions(start_date=start, end_date=today.strftime("%Y-%m-%d"))

    # ─── Aggregates ───
    def summary(self, txns):
        if not txns:
            return {"total_pcs": 0, "total_revenue": 0, "total_hpp": 0,
                    "total_profit": 0, "per_item": {}, "item_order": []}
        per_item = {}
        for t in txns:
            item = t["item"]
            if item not in per_item:
                per_item[item] = {"pcs": 0, "revenue": 0, "hpp": 0, "profit": 0}
            per_item[item]["pcs"] += t["jumlah"]
            per_item[item]["revenue"] += t["total"]
            per_item[item]["hpp"] += t["hpp_satuan"] * t["jumlah"]
            per_item[item]["profit"] += t["profit"]

        # Sort by pcs descending
        item_order = sorted(per_item.keys(), key=lambda k: per_item[k]["pcs"], reverse=True)
        return {
            "total_pcs": sum(t["jumlah"] for t in txns),
            "total_revenue": sum(t["total"] for t in txns),
            "total_hpp": sum(t["hpp_satuan"] * t["jumlah"] for t in txns),
            "total_profit": sum(t["profit"] for t in txns),
            "per_item": per_item,
            "item_order": item_order,
        }

    # ─── Export ───
    def export_csv(self, txns=None):
        if txns is None:
            txns = self._transactions
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Tanggal", "Jam", "Item", "Jumlah",
                         "Harga Satuan", "Total", "HPP Satuan", "Profit"])
        for t in txns:
            writer.writerow([
                t["id"], t["tanggal"], t["jam"], t["item"], t["jumlah"],
                t["harga_satuan"], t["total"], t["hpp_satuan"], t["profit"]
            ])
        return output.getvalue().encode("utf-8")

    # ─── HPP Config ───
    def get_hpp_config(self):
        path = self._path("hpp_config.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    def set_hpp(self, item, hpp):
        config = self.get_hpp_config()
        config[item] = hpp
        with open(self._path("hpp_config.json"), "w") as f:
            json.dump(config, f, indent=2)

    # ─── Biaya Operasional ───
    def get_biaya(self):
        path = self._path("biaya.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {"bulanan": []}

    def add_biaya(self, nama, jumlah):
        biaya = self.get_biaya()
        biaya["bulanan"].append({"nama": nama, "jumlah": jumlah,
                                 "tanggal": datetime.now().strftime("%Y-%m-%d")})
        with open(self._path("biaya.json"), "w") as f:
            json.dump(biaya, f, indent=2)
