"""Repeatable fictional fixtures with intentionally unresolved exceptions."""
import csv
from pathlib import Path
from .domain import Transaction, parse_date, money
from .ingest import read_file

def transaction(identifier, amount="100.00", direction="IN", cnpj="DEMO0000000001", reference="", account="DEMO-01", company="FICTICIA-A"):
    return Transaction(identifier, company, account, "DEMO_RECEIPTS" if direction == "IN" else "DEMO_PAYMENTS", "BRL", direction,
                       parse_date("2026-11-03"), money(amount), cnpj, reference, "Movimentação inteiramente fictícia")

def fixture():
    bank = [transaction("B001", reference="REF-A"), transaction("B002", "80.00", "OUT"),
            transaction("B003", "200.00", cnpj="DEMO0000000002"), transaction("B004", "200.00", cnpj="DEMO0000000002"),
            transaction("B005", "50.00", cnpj=""), transaction("B006", "60.00", "OUT", reference="REF-DIFF"),
            transaction("B007", "120.00", "OUT", reference="REF-OK"),
            transaction("B008", "30.00", account="DEMO-02"), transaction("B009", "40.00", "OUT", account="DEMO-02")]
    ledger = [transaction("L001", reference="REF-A"), transaction("L002", "60.00", "OUT", reference="OTHER"),
              transaction("L003", "200.00", cnpj="DEMO0000000002"), transaction("L004", "200.00", cnpj="DEMO0000000002"),
              transaction("L005", "50.00"), transaction("L006", "80.00", "OUT", reference="MISMATCH"),
              transaction("L007", "120.00", "OUT", reference="REF-OK"),
              transaction("L008", "30.00", account="DEMO-02"), transaction("L009", "40.00", "OUT", account="DEMO-02")]
    # Add 10 further fictional accounts, proving account count is not layout count.
    for i in range(3, 13):
        bank.append(transaction(f"B{i+7:03}", str(i * 10), account=f"DEMO-{i:02}"))
        ledger.append(transaction(f"L{i+7:03}", str(i * 10), account=f"DEMO-{i:02}"))
    bank.append(transaction("B020", "20.00", "OUT", account="DEMO-02", reference="MISSING-POSTING"))
    return bank, ledger

def generate(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    bank, ledger = fixture()
    # Alpha and beta are two distinct bank layouts; canonical is the third.
    paths = [directory / "bank_alpha.csv", directory / "bank_beta.csv", directory / "bank_canonical.csv"]
    alpha = [b for i,b in enumerate(bank) if i % 3 == 0]
    beta = [b for i,b in enumerate(bank) if i % 3 == 1]
    canonical = [b for i,b in enumerate(bank) if i % 3 == 2]
    with paths[0].open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ID","Empresa","Conta","Moeda","Tipo","Data","Valor","CNPJ","Documento","Historico"])
        for b in alpha:
            w.writerow([b.id,b.company,b.bank_account,b.currency,"ENTRADA" if b.direction=="IN" else "SAIDA",b.date.strftime("%d/%m/%Y"),str(b.amount).replace(".",","),b.cnpj,b.reference,b.description])
    with paths[1].open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["transaction_id","company","account","currency","booking_date","signed_amount","tax_id","reference","description"])
        for b in beta:
            w.writerow([b.id,b.company,b.bank_account,b.currency,b.date.isoformat(),str(b.amount if b.direction=="IN" else -b.amount),b.cnpj,b.reference,b.description])
    fields = ["id","company","bank_account","ledger_account","currency","direction","date","amount","cnpj","reference","description"]
    for path, rows, posted in [(paths[2], canonical, False), (directory/"ledger.csv", ledger, True)]:
        with path.open("w", encoding="utf-8", newline="") as f:
            names = fields + (["posting_status"] if posted else [])
            w = csv.DictWriter(f, fieldnames=names, delimiter=";", extrasaction="ignore")
            w.writeheader()
            for r in rows:
                value = r.to_dict()
                if posted:
                    value["posting_status"] = "POSTED"
                w.writerow(value)
    return paths, directory/"ledger.csv"

def load_demo(directory):
    paths, ledger_path = generate(directory)
    return [row for path in paths for row in read_file(path, "bank")], read_file(ledger_path, "ledger")
