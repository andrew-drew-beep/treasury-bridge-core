import base64
from http.server import HTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from treasury_bridge.server import handler
from treasury_bridge.store import Store

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.server=HTTPServer(("127.0.0.1",0),handler(Store(Path(self.directory.name)/"reviews.sqlite")))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.directory.cleanup()

    def request(self,path,body=None,headers=None):
        h={"Content-Type":"application/json"};h.update(headers or {})
        with urlopen(Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=h),timeout=5) as r:
            return r.status,r.read(),r.headers

    def test_demo_review_export_and_reload(self):
        _,raw,_=self.request('/api/demo',{});r=json.loads(raw);rid=r['run_id']
        self.assertEqual(len(r['bank']),20)
        _,raw,_=self.request('/api/review',dict(run_id=rid,bank_id='B001',ledger_id='L001',decision='APPROVE',reviewer='Demo',note='Referência conferida'))
        self.assertEqual(json.loads(raw)['counts']['APPROVED'],1)
        _,raw,_=self.request('/api/report?run='+rid)
        self.assertEqual(len(json.loads(raw)['events']),1)
        _,raw,headers=self.request('/api/export.csv?run='+rid)
        self.assertIn(b'bank_id;',raw)
        self.assertIn('text/csv',headers['Content-Type'])

    def test_upload_actual_fixture_files(self):
        from treasury_bridge.demo import generate
        bank,ledger=generate(Path(self.directory.name)/'inputs')
        files=[dict(name=p.name,side=side,content=base64.b64encode(p.read_bytes()).decode()) for side,paths in [('bank',bank),('ledger',[ledger])] for p in paths]
        _,raw,_=self.request('/api/import',dict(files=files,window=2))
        self.assertEqual(len(json.loads(raw)['bank']),20)

    def test_bad_origin_and_host_blocked(self):
        for headers in ({'Origin':'https://untrusted.example'},{'Host':'untrusted.example'}):
            with self.assertRaises(HTTPError) as error:self.request('/api/demo',{},headers)
            self.assertEqual(error.exception.code,403)

    def test_static_ui_and_missing_run(self):
        _,raw,headers=self.request('/')
        self.assertIn(b'Treasury Bridge',raw)
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        with self.assertRaises(HTTPError) as error:self.request('/api/report?run=missing')
        self.assertEqual(error.exception.code,400)

if __name__=='__main__':unittest.main()
