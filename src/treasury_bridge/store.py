"""SQLite snapshots and review journal for the single-user local demo."""
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
from .domain import Transaction
from .engine import reconcile

class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reviews(run_id TEXT, bank_id TEXT, ledger_id TEXT,
                    decision TEXT, reviewer TEXT, note TEXT, created_at TEXT,
                    PRIMARY KEY(run_id,bank_id));
                CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT, bank_id TEXT, ledger_id TEXT, decision TEXT,
                    reviewer TEXT, note TEXT, created_at TEXT);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def save(self, report):
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO runs VALUES (?,?)", (report["run_id"], json.dumps(report)))
        return report["run_id"]

    def _load(self, db, rid):
        row = db.execute("SELECT payload FROM runs WHERE id=?", (rid,)).fetchone()
        if not row:
            raise ValueError("Execução não encontrada")
        payload = json.loads(row[0])
        reviews = {r["bank_id"]: dict(r) for r in db.execute("SELECT * FROM reviews WHERE run_id=?", (rid,))}
        return payload, reviews

    def report(self, rid):
        with self.connect() as db:
            payload, reviews = self._load(db, rid)
            events = [dict(r) for r in db.execute("SELECT * FROM events WHERE run_id=? ORDER BY id", (rid,))]
        result = reconcile([Transaction.from_dict(x) for x in payload["bank"]], [Transaction.from_dict(x) for x in payload["ledger"]], payload["window_days"], reviews)
        result["events"] = events
        return result

    def review(self, rid, bank_id, ledger_id, decision, reviewer, note):
        reviewer, note = str(reviewer).strip(), str(note).strip()
        if decision not in ("APPROVE", "REJECT") or not reviewer or not note:
            raise ValueError("Informe decisão, responsável e justificativa")
        if len(reviewer) > 100 or len(note) > 1000:
            raise ValueError("Responsável ou justificativa muito longos")
        item = {"bank_id": bank_id, "ledger_id": ledger_id, "decision": decision, "reviewer": reviewer, "note": note,
                "created_at": datetime.now(timezone.utc).isoformat()}
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            payload, reviews = self._load(db, rid)
            reviews[bank_id] = item
            reconcile([Transaction.from_dict(x) for x in payload["bank"]], [Transaction.from_dict(x) for x in payload["ledger"]], payload["window_days"], reviews)
            values = (rid, bank_id, ledger_id, decision, reviewer, note, item["created_at"])
            db.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?,?,?,?,?)", values)
            db.execute("INSERT INTO events(run_id,bank_id,ledger_id,decision,reviewer,note,created_at) VALUES (?,?,?,?,?,?,?)", values)
        return self.report(rid)
