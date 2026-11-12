"""No vendor call. Proves: log lives outside the package; counts persist across 'restart' and packaging; a call is counted before the network
request and kept when it fails; caps are enforced. This is a LOCAL guard, not a Gnani-side credit cap."""
import os, sys, json, tempfile, importlib, shutil
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, root)
log = os.path.join(tempfile.mkdtemp(), "u.json"); os.environ["KIRANA_USAGE_LOG"] = log; os.environ["GNANI_API_KEY"] = "test-not-real"
import gnani_client as g
default = os.path.join(os.path.expanduser("~"), ".kirana-munim", "usage_log.json")
assert not os.path.abspath(default).startswith(root), "default log must be outside the project folder"
import urllib.request
def boom(*a, **k): raise OSError("network down")
urllib.request.urlopen = boom
try: g.synthesize("hello"); raise SystemExit("should fail")
except g.GnaniError: pass
u = json.load(open(log)); assert u["tts_chars"] == 5 and u["calls"][0]["result"].startswith("http-error"), u  # failed attempt still counted
importlib.reload(g)  # 'restart'
shutil.copytree(root, tempfile.mkdtemp() + "/pkg", ignore=shutil.ignore_patterns("__pycache__"))  # 'packaging' must not touch the log
assert json.load(open(log))["tts_chars"] == 5, "counts must persist across restart and packaging"
json.dump({"stt_seconds": 0, "tts_chars": g.MAX_TTS_CHARS - 2, "calls": []}, open(log, "w"))
try: g.synthesize("hello"); raise SystemExit("cap not enforced")
except g.GnaniError as e: assert "cap reached" in str(e)
assert json.load(open(log))["tts_chars"] == g.MAX_TTS_CHARS - 2, "refused call must not be counted"
print("usage guard tests pass (no vendor call; local guard only)")
