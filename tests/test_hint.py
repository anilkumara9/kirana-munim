"""No Gnani call: checks the server passes the language hint to STT."""
import os, sys, json, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server, gnani_client
seen = {}
def fake_t(w, language_code="indic-auto", **k): seen["lc"] = language_code; return {"transcript": "रमेश को 200 रुपये उधार", "detected_language_code": "hi-IN", "request_id": "x"}
gnani_client.transcribe = fake_t; gnani_client.synthesize = lambda *a, **k: b"RIFF"; server.to_wav = lambda b: b
class F:  # minimal handler stand-in
    def __init__(s): s.path = "/voice"; s.headers = {"Content-Length": "3"}; s.rfile = type("R", (), {"read": lambda self, n: b"abc"})(); s.out = None
    def _send(s, code, body): s.out = (code, body)
f = F(); server.H.do_POST(f)
assert seen["lc"] == "kn-IN,hi-IN,en-IN", seen; assert f.out[0] == 200
print("hint test passes (no Gnani call)")
