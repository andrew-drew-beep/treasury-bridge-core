"""CSV is spreadsheet-safe; all text is treated as data, never as a formula."""
import csv
import io

def safe(value):
    text = str(value if value is not None else "")
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")) else text

def csv_report(report):
    stream = io.StringIO(newline="")
    fields = ["bank_id","company","bank_account","ledger_account","currency","direction","date","amount","cnpj","reference","status","ledger_id","reason","reviewer","note"]
    w = csv.DictWriter(stream, fields, delimiter=";")
    w.writeheader()
    for item in report["items"]:
        b = item["bank"]
        row = {**b, "bank_id":b["id"], "status":item["status"], "ledger_id":item["ledger_id"], "reason":item["reason"],
               "reviewer":(item["review"] or {}).get("reviewer", ""), "note":(item["review"] or {}).get("note", "")}
        w.writerow({k:safe(row.get(k, "")) for k in fields})
    # Separate row types prevent an unmatched ledger entry from disappearing in export.
    for l in report["unmatched_ledger"]:
        row = {**l, "bank_id":"", "status":"LEDGER_UNMATCHED", "ledger_id":l["id"], "reason":"Registro contábil sem vínculo"}
        w.writerow({k:safe(row.get(k, "")) for k in fields})
    return "\ufeff" + stream.getvalue()
