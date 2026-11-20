# Treasury Bridge continuation contract

Read `docs/STATE.md`, `docs/DISCOVERY.md`, `docs/DECISIONS.md` and `docs/HANDOFF.md` before changing code.
All public data is fictitious. Do not add company names, internal screenshots, account numbers,
real fiscal identifiers, credentials, personal CV files or corporate exports.

Business invariants: bank import already exists in the discovered process. This project compares
exported bank/posted-ledger records after import. IN and OUT use distinct ledger accounts.
Zero means bank minus booked ledger per company/account/currency/direction/period, never IN minus OUT.
Equal totals do not imply item reconciliation. Match exact money + fiscal ID + scope + date window;
conflicting nonempty references block matching. Do not select among ambiguous candidates without human review.
No duplicate assignment, no missing-ID auto match, no floating-point money, no ERP writebacks.

Run `python -m unittest discover -s tests -v`, `python run.py demo --out var/report.json` and a web smoke test.
Update STATE and HANDOFF with commands, observed results, limitations and next steps after each work block.
Keep base demo offline and dependency-free; XLSX is optional. Do not describe rule-based matching as AI.
Do not add FX/LLM before explicit scope expansion. Public portfolio code is not an enterprise deployment.
