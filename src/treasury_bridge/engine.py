"""Conservative, one-to-one reconciliation with explicit human resolutions."""
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from .domain import RULE_VERSION

def run_id(bank, ledger, window):
    body = {"bank": [x.to_dict() for x in bank], "ledger": [x.to_dict() for x in ledger], "window": window, "rule": RULE_VERSION}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:24]

def reconcile(bank, ledger, window=2, reviews=None):
    if not isinstance(window, int) or not 0 <= window <= 31:
        raise ValueError("Date window must be 0..31 calendar days")
    if not bank or not ledger:
        raise ValueError("Both sides must contain transactions")
    for side, rows in (("bank", bank), ("ledger", ledger)):
        ids = [r.id for r in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate {side} transaction ID; import rejected")
    # Bound the comparison cost of the local portfolio demo.
    if len(bank) * len(ledger) > 2_000_000:
        raise ValueError("Demo limit: at most 2 million bank/ledger comparisons")
    candidates = {}
    for b in bank:
        candidates[b.id] = [l.id for l in ledger if b.cnpj and b.cnpj == l.cnpj and b.scope == l.scope and b.amount == l.amount and abs((b.date-l.date).days) <= window and not (b.reference and l.reference and b.reference != l.reference)]
    # Compute degrees before any assignment: do not greedily consume repeated values.
    degree = Counter(lid for lids in candidates.values() for lid in lids)
    reviews = reviews or {}
    used = set()
    for bid, review in reviews.items():
        if bid not in candidates:
            raise ValueError("Review refers to an unknown bank transaction")
        if review["decision"] == "APPROVE":
            lid = review["ledger_id"]
            if lid not in candidates[bid] or lid in used:
                raise ValueError("Review violates evidence or one-to-one assignment")
            used.add(lid)
    result = []
    matched_ledger = set(used)
    for b in bank:
        review = reviews.get(b.id)
        available = [x for x in candidates[b.id] if x not in used]
        lid = None
        if review and review["decision"] == "APPROVE":
            status, lid = "APPROVED", review["ledger_id"]
            reason = "Correspondência aprovada por revisão humana"
        elif review and review["decision"] == "REJECT":
            status, reason = "HELD", "Sugestão rejeitada; pendência mantida para investigação"
        elif len(candidates[b.id]) == 1 and degree[candidates[b.id][0]] == 1 and available:
            status, lid = "RULE_MATCH", available[0]
            matched_ledger.add(lid)
            reason = "CNPJ, valor e contexto iguais; data na janela; vínculo exclusivo"
        elif candidates[b.id]:
            status, reason = "AMBIGUOUS", "Candidatos repetidos ou concorrência pelo mesmo lançamento"
        elif not b.cnpj:
            status, reason = "MISSING_ID", "Sem CNPJ; associação automática bloqueada"
        else:
            status, reason = "UNMATCHED", "Sem candidato compatível; investigar valor, CNPJ, referência e datas"
        result.append({"bank": b.to_dict(), "ledger_id": lid, "status": status, "reason": reason,
                       "candidate_ids": candidates[b.id], "available_candidate_ids": available,
                       "review": review})
    groups = defaultdict(lambda: {"bank": Decimal(0), "ledger": Decimal(0), "bank_pending": 0, "ledger_pending": 0, "unreviewed": 0})
    for row in result:
        b = row["bank"]
        key = tuple(b[x] for x in ("company", "bank_account", "ledger_account", "currency", "direction"))
        g = groups[key]
        g["bank"] += Decimal(b["amount"])
        g["bank_pending"] += row["status"] not in ("RULE_MATCH", "APPROVED")
        g["unreviewed"] += row["status"] == "RULE_MATCH"
    for l in ledger:
        g = groups[l.scope]
        g["ledger"] += l.amount
        g["ledger_pending"] += l.id not in matched_ledger
    summaries = []
    for scope, g in sorted(groups.items()):
        diff = g["bank"] - g["ledger"]
        state = "PENDING" if diff or g["bank_pending"] or g["ledger_pending"] else ("READY_FOR_REVIEW" if g["unreviewed"] else "REVIEWED")
        summaries.append(dict(zip(("company", "bank_account", "ledger_account", "currency", "direction"), scope)) | {
            "bank_total": str(g["bank"]), "ledger_total": str(g["ledger"]), "difference": str(diff),
            "bank_pending": g["bank_pending"], "ledger_pending": g["ledger_pending"], "status": state})
    return {"run_id": run_id(bank, ledger, window), "rule_version": RULE_VERSION, "window_days": window,
            "bank": [b.to_dict() for b in bank], "ledger": [l.to_dict() for l in ledger],
            "items": result, "groups": summaries,
            "unmatched_ledger": [l.to_dict() for l in ledger if l.id not in matched_ledger],
            "counts": dict(Counter(row["status"] for row in result))}
