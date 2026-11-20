from dataclasses import replace
from decimal import Decimal
from datetime import timedelta
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from treasury_bridge.domain import money, tax_id
from treasury_bridge.demo import transaction as t, load_demo
from treasury_bridge.engine import reconcile
from treasury_bridge.ingest import read_bytes
from treasury_bridge.store import Store
from treasury_bridge.export import csv_report, safe

class MoneyTests(unittest.TestCase):
    def test_locale_and_exact_sum(self):
        self.assertEqual(money("1.234,56"), Decimal("1234.56"))
        self.assertEqual(money("0.10")+money("0.20"),money("0.30"))

    def test_precision_nonfinite_and_invalid_locale_rejected(self):
        for value in ("1.001", "NaN", "Infinity", "1,2,3", "1e2", "1.23,00"):
            with self.subTest(value=value), self.assertRaises(ValueError): money(value)

    def test_currency_scale(self):
        self.assertEqual(money("10", "JPY"),Decimal(10))
        with self.assertRaises(ValueError): money("10.01","JPY")
        with self.assertRaises(ValueError): money("10","XYZ")

    def test_tax_id_text_and_alphanumeric(self):
        self.assertEqual(tax_id("00.000.000/0001-00"),"00000000000100")
        self.assertEqual(tax_id("demo0000000001"),"DEMO0000000001")
        with self.assertRaises(ValueError): tax_id(123)

class EngineTests(unittest.TestCase):
    def test_unique_match_is_not_human_approval(self):
        r=reconcile([t("B")],[t("L")])
        self.assertEqual(r["items"][0]["status"],"RULE_MATCH")
        self.assertEqual(r["groups"][0]["status"],"READY_FOR_REVIEW")

    def test_different_tax_ids_resolve_equal_values(self):
        r=reconcile([t("B",cnpj="DEMO0000000002")],[t("L1"),t("L2",cnpj="DEMO0000000002")])
        self.assertEqual(r["items"][0]["ledger_id"],"L2")

    def test_repeated_value_and_tax_id_abstains(self):
        r=reconcile([t("B")],[t("L1"),t("L2")])
        self.assertEqual(r["items"][0]["status"],"AMBIGUOUS")

    def test_two_bank_items_cannot_consume_one_ledger(self):
        r=reconcile([t("B1"),t("B2")],[t("L")])
        self.assertTrue(all(i["status"]=="AMBIGUOUS" for i in r["items"]))

    def test_scopes_cannot_cross(self):
        original=t("L")
        for change in ({"company":"OTHER"},{"bank_account":"OTHER"},{"ledger_account":"OTHER"},{"direction":"OUT"},{"currency":"USD"}):
            with self.subTest(change=change):
                self.assertEqual(reconcile([t("B")],[replace(original,**change)])["items"][0]["status"],"UNMATCHED")

    def test_missing_cnpj_does_not_match_by_value(self):
        self.assertEqual(reconcile([t("B",cnpj="")],[t("L",cnpj="")])["items"][0]["status"],"MISSING_ID")

    def test_date_boundary(self):
        l=replace(t("L"),date=t("B").date+timedelta(days=2))
        self.assertEqual(reconcile([t("B")],[l],2)["items"][0]["status"],"RULE_MATCH")
        self.assertEqual(reconcile([t("B")],[l],1)["items"][0]["status"],"UNMATCHED")

    def test_conflicting_references_block_match(self):
        r=reconcile([t("B",reference="A")],[t("L",reference="B")])
        self.assertEqual(r["items"][0]["status"],"UNMATCHED")

    def test_zero_total_with_wrong_counterparty_does_not_close(self):
        r=reconcile([t("B")],[t("L",cnpj="DEMO0000000002")])
        self.assertEqual(Decimal(r["groups"][0]["difference"]),0)
        self.assertEqual(r["groups"][0]["status"],"PENDING")

    def test_in_and_out_never_cancel_each_other(self):
        r=reconcile([t("B","100","IN")],[t("L","100","OUT")])
        self.assertEqual(len(r["groups"]),2)
        self.assertEqual({Decimal(g["difference"]) for g in r["groups"]},{Decimal(100),Decimal(-100)})

    def test_duplicate_import_ids_are_rejected(self):
        with self.assertRaises(ValueError): reconcile([t("B"),t("B")],[t("L")])
        with self.assertRaises(ValueError): reconcile([t("B")],[t("L"),t("L")])

    def test_invalid_window_and_empty_input(self):
        for window in (-1,32):
            with self.assertRaises(ValueError): reconcile([t("B")],[t("L")],window)
        with self.assertRaises(ValueError): reconcile([],[])

    def test_manual_resolution_keeps_remaining_ambiguity(self):
        r=reconcile([t("B1"),t("B2")],[t("L1"),t("L2")],reviews={"B1":{"decision":"APPROVE","ledger_id":"L1"}})
        self.assertEqual([i["status"] for i in r["items"]],["APPROVED","AMBIGUOUS"])

    def test_manual_resolution_cannot_reuse_ledger_or_override_evidence(self):
        for reviews in ({"B1":{"decision":"APPROVE","ledger_id":"L1"},"B2":{"decision":"APPROVE","ledger_id":"L1"}}, {"B1":{"decision":"APPROVE","ledger_id":"NONEXISTENT"}}):
            with self.assertRaises(ValueError): reconcile([t("B1"),t("B2")],[t("L1")],reviews=reviews)

class ImportTests(unittest.TestCase):
    def test_three_layouts_roundtrip_and_twelve_accounts(self):
        with tempfile.TemporaryDirectory() as directory:
            bank,ledger=load_demo(directory)
        self.assertEqual(len(bank),20)
        self.assertEqual(len(ledger),19)
        self.assertEqual(len({b.bank_account for b in bank}),12)
        self.assertEqual(len({b.source for b in bank}),3)

    def test_missing_columns_and_invalid_row(self):
        for text in ("amount\n100\n","id,id\n1,2\n",""):
            with self.subTest(text=text), self.assertRaises(ValueError): read_bytes(text.encode(),"bad.csv","bank")

    def test_xlsx_roundtrip_and_formula_rejection(self):
        try: import openpyxl
        except ImportError: self.skipTest("optional excel extra not installed")
        import io
        book=openpyxl.Workbook();sheet=book.active
        sheet.append(["ID","Empresa","Conta","Moeda","Tipo","Data","Valor","CNPJ"])
        sheet.append(["B","A","DEMO","BRL","ENTRADA","2026-11-03","0.10","DEMO0000000001"])
        buf=io.BytesIO();book.save(buf)
        self.assertEqual(read_bytes(buf.getvalue(),"demo.xlsx","bank")[0].amount,Decimal("0.10"))
        sheet.cell(2,7,"=1+1");buf=io.BytesIO();book.save(buf)
        with self.assertRaises(ValueError): read_bytes(buf.getvalue(),"demo.xlsx","bank")

    def test_unposted_ledger_rejected(self):
        text="id;company;bank_account;ledger_account;currency;direction;date;amount;cnpj;posting_status\nL;A;B;C;BRL;IN;2026-11-03;100;DEMO0000000001;PLANNED\n"
        with self.assertRaises(ValueError): read_bytes(text.encode(),"ledger.csv","ledger")

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.directory.name)/"demo.sqlite")
        self.r=reconcile([t("B")],[t("L")])
        self.rid=self.store.save(self.r)

    def tearDown(self): self.directory.cleanup()

    def test_approval_persists_and_is_audited(self):
        self.store.review(self.rid,"B","L","APPROVE","Demo Reviewer","Documentos fictícios conferidos")
        r=Store(self.store.path).report(self.rid)
        self.assertEqual(r["groups"][0]["status"],"REVIEWED")
        self.assertEqual(len(r["events"]),1)
        self.assertEqual(r["events"][0]["reviewer"],"Demo Reviewer")

    def test_rejection_reopens_and_history_retained(self):
        self.store.review(self.rid,"B","L","APPROVE","Demo","Conferido")
        r=self.store.review(self.rid,"B",None,"REJECT","Demo","Reabrir para investigar")
        self.assertEqual(r["groups"][0]["status"],"PENDING")
        self.assertEqual(len(r["events"]),2)

    def test_bad_review_rolls_back(self):
        with self.assertRaises(ValueError): self.store.review(self.rid,"B","NO","APPROVE","Demo","Test")
        self.assertEqual(len(self.store.report(self.rid)["events"]),0)

    def test_reimport_same_snapshot_retains_review(self):
        self.store.review(self.rid,"B","L","APPROVE","Demo","Conferido")
        self.assertEqual(self.store.save(self.r),self.rid)
        self.assertEqual(self.store.report(self.rid)["counts"],{"APPROVED":1})

    def test_blank_reviewer_or_note_rejected(self):
        with self.assertRaises(ValueError): self.store.review(self.rid,"B","L","APPROVE","","note")
        with self.assertRaises(ValueError): self.store.review(self.rid,"B","L","APPROVE","name","")

    def test_export_contains_unmatched_ledger(self):
        r=reconcile([t("B")],[t("L",cnpj="DEMO0000000002")])
        self.assertIn("LEDGER_UNMATCHED",csv_report(r))

    def test_csv_formula_injection_escaped(self):
        for text in ("=HYPERLINK()"," +cmd","@SUM()","\t=1"):
            self.assertTrue(safe(text).startswith("'"))

if __name__ == "__main__": unittest.main()
