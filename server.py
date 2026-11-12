"""Run: GNANI_API_KEY=... python3 server.py  -> http://localhost:8000 (needs ffmpeg)."""
import json, subprocess, base64, os
from http.server import BaseHTTPRequestHandler, HTTPServer
import gnani_client as g, parser as p, ledger

STATIC = os.path.join(os.path.dirname(__file__), "static")

def to_wav(raw):
    """Browser webm/ogg -> 16 kHz mono WAV, max 30 s. Written to a file so the WAV header has a real length (piped WAV does not)."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "in"), os.path.join(d, "out.wav")
        open(src, "wb").write(raw)
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-t", "30", "-ar", "16000", "-ac", "1", dst], capture_output=True)
        if r.returncode or not os.path.exists(dst): raise g.GnaniError("Could not read the recording: " + r.stderr.decode()[:120])
        return open(dst, "rb").read()

def reply_text(e, total):
    if not e["ok"]:
        return "Sorry, I could not understand. Please say the name, credit or payment, and the amount."
    k = {"credit": "credit of", "payment": "payment of", "sale": "sale of"}[e["kind"]]
    return f"Noted. {e['customer']}, {k} {int(e['amount'])} rupees. Total due {int(total)} rupees."

# Hint the three languages a shop here uses. Fixed a live case where a Kannada number word was transcribed as Hindi "100".
STT_HINT = "kn-IN,hi-IN,en-IN"

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ct="application/json"):
        self.send_response(code); self.send_header("Content-Type", ct); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == "/ledger": return self._send(200, json.dumps({"entries": ledger.load(), "balances": ledger.balances()}, ensure_ascii=False).encode())
        return self._send(200, open(os.path.join(STATIC, "index.html"), "rb").read(), "text/html; charset=utf-8")
    def do_POST(self):
        if self.path.startswith("/confirm"):
            d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            if d.get("discard"): ledger.discard(d["pending_id"]); return self._send(200, b"{}")
            try: ledger.confirm(d["pending_id"], d.get("amount"), d.get("customer"), d.get("kind"), bool(d.get("new_customer")))
            except KeyError: return self._send(404, b'{"error":"This entry was already saved or discarded."}')
            except ledger.Rejected as ex: return self._send(409, json.dumps({"error": str(ex), "candidates": getattr(ex, "candidates", [])}, ensure_ascii=False).encode())
            return self._send(200, json.dumps({"balances": ledger.balances()}, ensure_ascii=False).encode())
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path.startswith("/parse"):  # typed fallback: parser only, no Gnani call, no credits
            e = p.parse(json.loads(raw)["text"]); e.update(language="typed", request_id=None); e["match"] = ledger.match(e.get("customer"))
            pid = ledger.stage(e)
            text = "Please check this entry: " + "; ".join(e["issues"]) if e["issues"] else "Confirm before saving."
            return self._send(200, json.dumps({"pending_id": pid, "entry": e, "reply": text}, ensure_ascii=False).encode())
        try:
            stt = g.transcribe(to_wav(raw), language_code=STT_HINT)
            e = p.parse(stt["transcript"]); e.update(language=stt.get("detected_language_code"), request_id=stt.get("request_id")); e["match"] = ledger.match(e.get("customer"))
            pid = ledger.stage(e)
            if e["ok"]:
                label = {"credit": "credit, udhaar", "payment": "payment received"}.get(e["kind"], e["kind"])
                text = "Got it. %s, %s rupees, for %s. Please check and confirm." % (label.capitalize(), int(e["amount"]), e["customer"])
            else:
                text = "Please check this entry: " + "; ".join(e["issues"])
            audio = base64.b64encode(g.synthesize(text, language="en-IN")).decode()
            self._send(200, json.dumps({"pending_id": pid, "entry": e, "reply": text, "audio_wav_b64": audio, "balances": ledger.balances()}, ensure_ascii=False).encode())
        except Exception as ex:
            self._send(500, json.dumps({"error": str(ex)}).encode())

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8000), H).serve_forever()
