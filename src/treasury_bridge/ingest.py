"""Three explicit file contracts; none claims to be an actual SAP interface."""
import csv
import io
from pathlib import Path
from .domain import Transaction, money, tax_id, parse_date

CANONICAL = {"id", "company", "bank_account", "currency", "direction", "date", "amount", "cnpj"}
ALPHA = {"ID", "Empresa", "Conta", "Moeda", "Tipo", "Data", "Valor", "CNPJ"}
BETA = {"transaction_id", "company", "account", "currency", "booking_date", "signed_amount", "tax_id"}

def account_for(direction):
    return {"IN": "DEMO_RECEIPTS", "OUT": "DEMO_PAYMENTS"}[direction]

def normalize(row, source, index, side):
    keys = set(row)
    if ALPHA <= keys and side == "bank":
        direction = {"ENTRADA": "IN", "SAIDA": "OUT", "SAÍDA": "OUT"}.get(str(row["Tipo"]).strip().upper())
        r = dict(id=row["ID"], company=row["Empresa"], bank_account=row["Conta"], currency=row["Moeda"], direction=direction, date=row["Data"], amount=row["Valor"], cnpj=row["CNPJ"], reference=row.get("Documento", ""), description=row.get("Historico", ""))
    elif BETA <= keys and side == "bank":
        currency = str(row["currency"]).strip().upper()
        signed = money(row["signed_amount"], currency)
        r = dict(id=row["transaction_id"], company=row["company"], bank_account=row["account"], currency=currency, direction="IN" if signed > 0 else "OUT", date=row["booking_date"], amount=str(abs(signed)), cnpj=row["tax_id"], reference=row.get("reference", ""), description=row.get("description", ""))
    elif CANONICAL <= keys:
        r = dict(row)
    else:
        raise ValueError("Unknown file layout or missing required columns")
    direction = str(r["direction"]).strip().upper()
    if direction not in ("IN", "OUT"):
        raise ValueError("Unknown movement direction")
    if side == "ledger" and str(r.get("posting_status", "")).strip() != "POSTED":
        raise ValueError("Ledger requires posting_status=POSTED; planned titles are not booked movements")
    ledger_account = str(r.get("ledger_account", "")).strip()
    if side == "ledger" and not ledger_account:
        raise ValueError("Missing ledger_account")
    currency = str(r["currency"]).strip().upper()
    raw_tax = r.get("cnpj", "")
    if raw_tax is None:
        raw_tax = ""
    return Transaction(
        id=str(r["id"]).strip(), company=str(r["company"]).strip(), bank_account=str(r["bank_account"]).strip(),
        ledger_account=ledger_account or account_for(direction), currency=currency, direction=direction,
        date=parse_date(r["date"]), amount=money(r["amount"], currency), cnpj=tax_id(raw_tax),
        reference=str(r.get("reference") or "").strip().upper(), description=str(r.get("description") or ""), source=source, source_row=index,
    )

def read_bytes(content, filename, side):
    if side not in ("bank", "ledger"):
        raise ValueError("Unknown side")
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("CSV must use UTF-8 encoding") from exc
        first = text.splitlines()[0] if text.splitlines() else ""
        delimiter = ";" if first.count(";") > first.count(",") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("Missing or duplicate column names")
        rows = list(reader)
    elif suffix == ".xlsx":
        try:
            import openpyxl
        except ImportError as exc:
            raise ValueError("Install the excel extra to import XLSX") from exc
        try:
            book = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=False)
            sheet = book.active
            all_rows = list(sheet.iter_rows(values_only=True))
            book.close()
        except Exception as exc:
            raise ValueError("Invalid XLSX workbook") from exc
        if not all_rows:
            raise ValueError("Empty workbook")
        headers = [str(x or "") for x in all_rows[0]]
        if "" in headers or len(set(headers)) != len(headers):
            raise ValueError("Missing or duplicate column names")
        rows = []
        for values in all_rows[1:]:
            if all(x is None for x in values):
                continue
            if any(isinstance(x, str) and x.startswith("=") for x in values):
                raise ValueError("Formula cells are not supported; export values")
            rows.append(dict(zip(headers, values)))
    else:
        raise ValueError("Only CSV and XLSX are supported")
    if not rows:
        raise ValueError("Empty transaction file")
    if len(rows) > 5000:
        raise ValueError("Demo limit: 5000 records per file")
    result = []
    for index, row in enumerate(rows, start=2):
        if None in row:
            raise ValueError(f"{filename}:{index}: extra cells")
        try:
            result.append(normalize(row, Path(filename).name, index, side))
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"{Path(filename).name}:{index}: {exc}") from exc
    return result

def read_file(path, side):
    path = Path(path)
    return read_bytes(path.read_bytes(), path.name, side)
