"""Optional end-to-end check. Requires Playwright and Chromium, not needed by users."""
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "var" / "browser-check"
OUTPUT.mkdir(parents=True, exist_ok=True)

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
            page.locator("#filter").select_option("pending")
            assert page.locator("#items article").count()==5
            page.screenshot(path=str(OUTPUT/"desktop.png"),full_page=True)
            page.locator("#filter").select_option("rule")
            item=page.locator("#items article").filter(has_text="B001")
            item.locator("summary").click()
            item.get_by_label("Responsável por B001",exact=True).fill("Revisor demonstração")
            item.get_by_label("Justificativa para B001",exact=True).fill("Referência fictícia REF-A conferida")
            item.get_by_role("button",name="Aprovar vínculo").click()
            page.get_by_text("Decisão registrada.",exact=False).wait_for()
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
            assert not errors, errors
            browser.close()
        print("Browser smoke passed: demo, filters, review, reload, CSV, upload, mobile layout and no JS errors")
    finally:
        process.terminate()
        process.wait(timeout=10)

if __name__=="__main__": main()
