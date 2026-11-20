"""Optional end-to-end check. Requires Playwright and Chromium, not needed by users."""
from pathlib import Path
import csv
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "var" / "browser-check"
OUTPUT.mkdir(parents=True, exist_ok=True)

def pending_button(page, company, account, direction, ledger_account, currency):
    label=f"Ver pendências de {company}, {account}, {direction}, {ledger_account}, {currency}"
    return page.get_by_role("button",name=label,exact=True)

def check_pending_shortcuts(page):
    incoming=pending_button(page,"FICTICIA-A","DEMO-01","Entrada","DEMO_RECEIPTS","BRL")
    incoming.focus()
    incoming.press("Enter")
    assert page.locator("#filter").input_value()=="pending"
    assert page.locator("#items article").count()==3
    assert page.locator("#ledgerPending .pending-record").count()==3
    assert "B006" not in page.locator("#items").inner_text()
    assert page.evaluate("document.activeElement.classList.contains('item')")
    assert incoming.get_attribute("aria-pressed")=="true"
    page.screenshot(path=str(OUTPUT/"pending-shortcut.png"),full_page=True)
    pending_button(page,"FICTICIA-A","DEMO-02","Saída","DEMO_PAYMENTS","BRL").click()
    assert page.locator("#items article").count()==1
    assert "B020" in page.locator("#items").inner_text()
    assert page.locator("#ledgerPending .pending-record").count()==0
    page.get_by_role("button",name="Ver todas as contas",exact=True).click()
    assert page.locator("#scopeContext").is_hidden()
    assert page.locator("#items article").count()==5
    assert page.locator("#ledgerPending .pending-record").count()==4

def check_scope_isolation_and_ledger_only(page):
    fields=["id","company","bank_account","ledger_account","currency","direction","date","amount","cnpj","reference","posting_status"]
    def record(identifier,company,direction,currency,amount):
        return dict(zip(fields,[identifier,company,"SHARED","DEMO_RECEIPTS" if direction=="IN" else "DEMO_PAYMENTS",currency,direction,"2026-11-03",amount,"DEMO0000000001","","POSTED"]))
    banks=[record("B-A-IN","A","IN","BRL","100"),record("B-B-IN","B","IN","BRL","100"),record("B-A-USD","A","IN","USD","100"),record("B-A-OUT","A","OUT","BRL","50")]
    ledger=[record("L-A-IN","A","IN","BRL","99"),record("L-B-IN","B","IN","BRL","98"),record("L-A-USD","A","IN","USD","97"),record("L-A-OUT","A","OUT","BRL","49"),record("L-C-ONLY","C","OUT","BRL","70")]
    paths=[]
    for name,rows in [("scoped-bank.csv",banks),("scoped-ledger.csv",ledger)]:
        path=OUTPUT/name
        with path.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fields,delimiter=";");writer.writeheader();writer.writerows(rows)
        paths.append(str(path))
    pending_button(page,"FICTICIA-A","DEMO-01","Entrada","DEMO_RECEIPTS","BRL").click()
    if page.locator("details.import").get_attribute("open") is None:
        page.locator("details.import summary").click()
    page.locator("#banks").set_input_files(paths[0]);page.locator("#ledger").set_input_files(paths[1])
    page.get_by_role("button",name="Conferir arquivos").click()
    page.get_by_text("Arquivos conferidos.",exact=False).wait_for()
    page.wait_for_function("document.querySelector('#scopeContext').hidden")
    pending_button(page,"A","SHARED","Entrada","DEMO_RECEIPTS","BRL").click()
    assert page.locator("#items article").count()==1
    assert "B-A-IN" in page.locator("#items").inner_text()
    assert page.locator("#ledgerPending .pending-record").count()==1
    assert "L-A-IN" in page.locator("#ledgerPending").inner_text()
    pending_button(page,"C","SHARED","Saída","DEMO_PAYMENTS","BRL").click()
    assert page.locator("#items article").count()==0
    assert page.locator("#ledgerPending .pending-record").count()==1
    assert "L-C-ONLY" in page.locator("#ledgerPending").inner_text()
    assert page.evaluate("document.activeElement.classList.contains('pending-record')")
    page.screenshot(path=str(OUTPUT/"ledger-only-shortcut.png"),full_page=True)
    page.get_by_role("button",name="Ver todas as contas",exact=True).click()
    assert page.locator("#items article").count()==4
    assert page.locator("#ledgerPending .pending-record").count()==5

def main():
    from playwright.sync_api import sync_playwright
    process = subprocess.Popen([sys.executable, "run.py", "serve", "--port", "8766", "--db", "var/browser-check/reviews.sqlite"], cwd=ROOT)
    try:
        for _ in range(100):
            try:
                with urlopen("http://127.0.0.1:8766",timeout=1) as response:
                    if response.status==200: break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError("Test server did not start")
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":1440,"height":1100},device_scale_factor=1)
            errors=[]
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto("http://127.0.0.1:8766")
            page.get_by_role("button",name="Abrir demonstração").click()
            page.locator("#workspace").wait_for(state="visible")
            assert page.locator("#groups tr").count()==14
            check_pending_shortcuts(page)
            page.locator("#filter").select_option("pending")
            assert page.locator("#items article").count()==5
            page.screenshot(path=str(OUTPUT/"desktop.png"),full_page=True)
            pending_button(page,"FICTICIA-A","DEMO-01","Entrada","DEMO_RECEIPTS","BRL").click()
            page.locator("#filter").select_option("rule")
            item=page.locator("#items article").filter(has_text="B001")
            item.locator("summary").click()
            item.get_by_label("Responsável por B001",exact=True).fill("Revisor demonstração")
            item.get_by_label("Justificativa para B001",exact=True).fill("Referência fictícia REF-A conferida")
            item.get_by_role("button",name="Aprovar vínculo").click()
            page.get_by_text("Decisão registrada.",exact=False).wait_for()
            assert page.locator("#scopeContext").is_visible()
            assert "DEMO-01, Entrada" in page.locator("#scopeLabel").inner_text()
            page.get_by_role("button",name="Ver todas as contas",exact=True).click()
            page.reload()
            page.locator("#workspace").wait_for(state="visible")
            assert "Revisor demonstração" in page.locator("#events").inner_text()
            with page.expect_download() as download:
                page.locator("#exportCsv").click()
            download.value.save_as(str(OUTPUT/"conferencia.csv"))
            assert "APPROVED" in (OUTPUT/"conferencia.csv").read_text(encoding="utf-8-sig")
            # Import the actual generated files through the UI, preserving the same review.
            page.locator("details.import summary").click()
            page.locator("#banks").set_input_files([str(ROOT/"var/browser-check/synthetic"/name) for name in ("bank_alpha.csv","bank_beta.csv","bank_canonical.csv")])
            page.locator("#ledger").set_input_files(str(ROOT/"var/browser-check/synthetic/ledger.csv"))
            page.get_by_role("button",name="Conferir arquivos").click()
            page.get_by_text("Arquivos conferidos.",exact=False).wait_for()
            assert "Revisor demonstração" in page.locator("#events").inner_text()
            page.set_viewport_size({"width":390,"height":844})
            page.screenshot(path=str(OUTPUT/"mobile.png"),full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            check_scope_isolation_and_ledger_only(page)
            assert not errors, errors
            browser.close()
        print("Browser smoke passed: pending shortcuts, scope isolation, ledger-only navigation, review persistence, demo, filters, reload, CSV, upload, mobile layout and no JS errors")
    finally:
        process.terminate()
        process.wait(timeout=10)

if __name__=="__main__": main()
