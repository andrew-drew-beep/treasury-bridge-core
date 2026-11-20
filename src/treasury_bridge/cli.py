import argparse
import json
from pathlib import Path
from .demo import load_demo
from .ingest import read_file
from .engine import reconcile
from .export import csv_report

def main():
    parser = argparse.ArgumentParser(description="Treasury Bridge | dados fictícios e revisão local")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--out", default="var/report.json")
    demo.add_argument("--data", default="data/synthetic")
    rec = sub.add_parser("reconcile")
    rec.add_argument("--bank", nargs="+", required=True)
    rec.add_argument("--ledger", required=True)
    rec.add_argument("--window", type=int, default=2)
    rec.add_argument("--out", default="var/report.json")
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--db", default="var/reviews.sqlite")
    args = parser.parse_args()
    if args.command == "serve":
        from .server import serve as start
        start(args.port, args.db)
        return
    try:
        if args.command == "demo":
            bank, ledger = load_demo(args.data)
        else:
            bank = [t for path in args.bank for t in read_file(path, "bank")]
            ledger = read_file(args.ledger, "ledger")
        result = reconcile(bank, ledger, getattr(args, "window", 2))
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        path.with_suffix(".csv").write_text(csv_report(result), encoding="utf-8")
        print(json.dumps({"run_id":result["run_id"], "bank_records":len(bank), "ledger_records":len(ledger), "counts":result["counts"], "report":str(path)}, ensure_ascii=False))
    except ValueError as exc:
        parser.error(str(exc))
