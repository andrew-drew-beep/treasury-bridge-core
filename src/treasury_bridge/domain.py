"""Validated values. Monetary calculations never use binary floats."""
from dataclasses import dataclass, asdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re

CURRENCY_SCALE = {"BRL": 2, "USD": 2, "EUR": 2, "GBP": 2, "CNY": 2, "JPY": 0}
RULE_VERSION = "reconcile-1.0"

def money(value, currency="BRL"):
    if currency not in CURRENCY_SCALE:
        raise ValueError(f"Unsupported currency: {currency}")
    text = str(value).strip()
    # Locale is explicit: comma decimal means dots are grouping separators.
    if "," in text:
        if not re.fullmatch(r"[+-]?(?:\d{1,3}(?:\.\d{3})+|\d+),\d+", text):
            raise ValueError(f"Invalid localized amount: {text}")
        text = text.replace(".", "").replace(",", ".")
    elif not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
        raise ValueError(f"Invalid amount: {text}")
    try:
        result = Decimal(text)
        unit = Decimal(1).scaleb(-CURRENCY_SCALE[currency])
        quantized = result.quantize(unit)
        if not result.is_finite() or quantized != result:
            raise ValueError("Amount has unsupported fractional precision")
        return quantized
    except InvalidOperation as exc:
        raise ValueError("Invalid monetary value") from exc

def tax_id(value):
    if not isinstance(value, str):
        raise ValueError("Tax identifier must be text; preserve leading zeros")
    normalized = re.sub(r"[./\-\s]", "", value).upper()
    if normalized and not re.fullmatch(r"[A-Z0-9]{14}", normalized):
        raise ValueError("Tax identifier must have 14 alphanumeric characters")
    return normalized

def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date: {value}")

@dataclass(frozen=True)
class Transaction:
    id: str
    company: str
    bank_account: str
    ledger_account: str
    currency: str
    direction: str
    date: date
    amount: Decimal
    cnpj: str
    reference: str = ""
    description: str = ""
    source: str = ""
    source_row: int = 0

    def __post_init__(self):
        for name in ("id", "company", "bank_account", "ledger_account"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"Missing {name}")
        if self.direction not in ("IN", "OUT"):
            raise ValueError("Direction must be IN or OUT")
        if self.currency not in CURRENCY_SCALE:
            raise ValueError("Unsupported currency")
        if not isinstance(self.date, date) or isinstance(self.date, datetime):
            raise ValueError("Date must be a calendar date")
        if not isinstance(self.amount, Decimal) or self.amount != money(self.amount, self.currency) or self.amount <= 0:
            raise ValueError("Amount must be a positive exact Decimal")
        if self.cnpj != tax_id(self.cnpj):
            raise ValueError("Tax identifier must be normalized")

    @property
    def scope(self):
        return (self.company, self.bank_account, self.ledger_account, self.currency, self.direction)

    def to_dict(self):
        return {**asdict(self), "date": self.date.isoformat(), "amount": str(self.amount)}

    @classmethod
    def from_dict(cls, value):
        row = dict(value)
        row["date"] = parse_date(row["date"])
        row["amount"] = money(row["amount"], row["currency"])
        return cls(**row)
