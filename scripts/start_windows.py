"""Start the source checkout from Explorer; keep errors visible via the batch wrapper."""
import argparse
from http.server import HTTPServer
from pathlib import Path
import os
import sys
import threading
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8765"

def open_browser():
    try:
        webbrowser.open(URL)
    except (webbrowser.Error, OSError):
        # The printed URL remains usable when there is no configured desktop browser.
        pass

def main():
    parser = argparse.ArgumentParser(description="Iniciar Treasury Bridge no Windows")
    parser.add_argument("--check", action="store_true", help="Verificar Python e arquivos sem abrir o servidor")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        print("Instale Python 3.11 ou superior: https://www.python.org/downloads/windows/")
        return 1
    if not (ROOT / "src" / "treasury_bridge" / "web" / "index.html").is_file():
        print("Arquivos do projeto incompletos. Extraia o ZIP inteiro usando Extrair Tudo.")
        return 1
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT / "src"))
    from treasury_bridge.server import handler
    from treasury_bridge.store import Store
    if args.check:
        print("Python " + sys.version.split()[0] + " e arquivos do projeto encontrados.")
        return 0
    try:
        store = Store(ROOT / "var" / "reviews.sqlite")
        server = HTTPServer(("127.0.0.1", 8765), handler(store))
    except OSError as exc:
        if getattr(exc, "winerror", None) == 10048 or getattr(exc, "errno", None) in (48, 98, 10048):
            print("A porta 8765 ja esta em uso. Se o Treasury Bridge ja estiver aberto, use " + URL)
            print("Caso contrario, encerre a outra instancia e abra este iniciador novamente.")
        else:
            print("Nao foi possivel iniciar o servidor local: " + str(exc))
        return 1
    print("Treasury Bridge: " + URL, flush=True)
    print("Mantenha esta janela aberta enquanto utiliza a ferramenta.", flush=True)
    print("Se o navegador nao abrir, copie o endereco acima para ele.", flush=True)
    print("Na pagina, clique em Abrir demonstracao. Para encerrar, pressione Ctrl+C.", flush=True)
    opener = threading.Timer(.5, open_browser)
    opener.daemon = True
    opener.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        opener.cancel()
        server.server_close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
