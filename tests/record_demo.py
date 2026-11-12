"""Records the demo from the REAL running app with REAL Gnani calls and writes events.json for mux_demo.py.
Mic input = Timbre-generated test speech (disclosed). Run after gen_demo_assets.py:
GNANI_API_KEY=... python3 tests/record_demo.py /downloads/demo"""
import os, sys, subprocess, time, tempfile, json, base64
from playwright.sync_api import sync_playwright
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = sys.argv[1]; A = out + "/assets"
env = dict(os.environ, LEDGER_PATH=os.path.join(tempfile.mkdtemp(), "l.json")); EV = []
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
def start(): s = subprocess.Popen([sys.executable, "server.py"], cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); return s
CSS = "body{margin:0;background:#fff;color:#0f1419;font-family:system-ui;display:flex;flex-direction:column;justify-content:center;height:100vh;padding:0 28px;box-sizing:border-box}h1{font-size:34px;margin:0 0 14px;line-height:1.1}p{font-size:19px;line-height:1.45;margin:6px 0;color:#536471}b{color:#0a7d5a}small{color:#536471;font-size:15px;margin-top:22px}.mk{width:54px;height:54px;border-radius:50%;background:#0a7d5a;color:#fff;font-size:30px;display:flex;align-items:center;justify-content:center;margin-bottom:22px}"
W, H = 405, 720; CAPS = []
class S:
    def __init__(s, pw, scene, fixture):
        s.scene = scene; s.br = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"), args=["--headless=new", "--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--use-fake-device-with-fake-audio-capture", f"--use-file-for-fake-audio-capture={fixture}"])
        s.ctx = s.br.new_context(permissions=["microphone"], viewport=dict(width=W, height=H), device_scale_factor=2, record_video_dir=f"{out}/{scene}", record_video_size=dict(width=W * 2, height=H * 2)); s.pg = s.ctx.new_page(); s.t0 = time.time()
    def t(s): return time.time() - s.t0
    def sl(s, x): s.pg.wait_for_timeout(int(x * 1000))
    def ev(s, f, at=None, vol=1.0): EV.append(dict(scene=s.scene, t=s.t() if at is None else at, file=f, vol=vol))
    def cap(s, text): CAPS.append(dict(scene=s.scene, t=s.t(), text=text))
    def say(s, n, cap=None):
        if cap: s.cap(cap)
        s.ev(f"{A}/{n}.wav"); s.sl(dur(f"{A}/{n}.wav") + 0.4)
    def card(s, html, n, cap=None): s.pg.set_content(f"<style>{CSS}</style>{html}"); s.say(n, cap)
    def speak(s, testfile):
        box = s.pg.locator("#b").bounding_box(); s.pg.mouse.move(box["x"] + 40, box["y"] + 20); th = s.t(); s.pg.mouse.down()
        s.pg.wait_for_function("document.querySelector('#b').classList.contains('rec')"); s.ev(testfile, at=th + 0.3, vol=0.9); s.sl(2.8); s.pg.mouse.up()
        s.pg.wait_for_function("!document.querySelector('#rv').hidden || document.querySelector('#s').classList.contains('err')", timeout=40000)
        tr = s.t(); src = s.pg.get_attribute("#a", "src") or ""
        if src.startswith("data:"):
            p = f"{out}/{s.scene}_reply.wav"; open(p, "wb").write(base64.b64decode(src.split(",", 1)[1])); subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", p, p + ".fix.wav"], check=True); s.ev(p + ".fix.wav", at=tr); return dur(p + ".fix.wav")
        return 0
    def close(s): s.ctx.close(); s.br.close()
with sync_playwright() as pw:
    srv = start(); a = S(pw, "a", f"{A}/test_hi.wav"); pg = a.pg
    a.card("<div class=mk>&#8377;</div><h1>Kirana Munim</h1><p>A voice udhaar ledger for neighbourhood shops.</p><p>Built on <b>Gnani Prisma</b> and <b>Gnani Timbre</b>.</p>", "n1", "Speak. Review. Keep track.")
    pg.goto("http://127.0.0.1:8000/"); a.sl(0.5); a.say("n2", "Udhaar, by voice. Hindi, Kannada or English.")
    a.say("n3", "Every voice here is generated: narrator Yashraj, test speech Shubham, app reply Shivani.")
    a.cap("Hindi test speech: Ramesh ko 200 rupaye udhaar"); a.say("n4")
    d = a.speak(f"{A}/test_hi.wav"); a.cap("Prisma transcript is staged. Timbre reads it back."); a.sl(d + 0.3)
    a.say("n5", "Nothing is saved until the shopkeeper confirms.")
    pg.click("#sv"); a.cap("Saved. Rs 200 owed by Ramesh."); a.sl(3.0); a.close(); srv.terminate(); time.sleep(1)
    srv = start(); b = S(pw, "b", f"{A}/test_kn.wav"); pg = b.pg
    pg.goto("http://127.0.0.1:8000/"); b.sl(0.5); b.say("n6", "Server restarted. The ledger still shows Rs 200 owed.")
    pg.click(".cust >> nth=0"); pg.wait_for_selector(".stmt"); pg.locator("#cp").scroll_into_view_if_needed(); b.say("n13", "Statement with running balance. Reminder text is copied, never sent."); pg.click(".cust >> nth=0"); pg.wait_for_selector(".stmt", state="detached"); pg.evaluate("window.scrollTo(0,0)")
    b.cap("Kannada test speech: Ramesh paid 200 rupees"); b.say("n7")
    d = b.speak(f"{A}/test_kn.wav"); b.cap("The name came back in Kannada script. Save is blocked until the shopkeeper chooses."); b.sl(d + 0.3)
    b.say("n8"); b.sl(0.8); pg.click("#mt button[data-i='0']"); b.cap("Existing customer chosen. Balance after this payment: Rs 0."); b.sl(0.6)
    b.say("n9"); pg.click("#sv"); b.cap("Payment saved. Balance is Rs 0."); b.sl(3.2); pg.click(".cust >> nth=0"); pg.wait_for_selector(".stmt"); b.cap("Statement: udhaar Rs 200, payment Rs 200, running balance Rs 0."); b.sl(3.5); pg.click(".cust >> nth=0"); pg.wait_for_selector(".stmt", state="detached"); pg.screenshot(path=f"{out}/paid.png")
    pg.evaluate("window.scrollTo(0,0)"); pg.evaluate("document.querySelector('details').open=true"); pg.fill("#tx", "रमेश 200"); pg.click("#tb"); b.sl(0.8)
    b.cap("Typed test: no payment or credit stated. Flagged, Save blocked."); b.say("n10"); pg.screenshot(path=f"{out}/ambiguous.png"); b.sl(1.2)
    pg.fill("#tx", "रमेश ने 500 रुपये दिए"); pg.click("#tb"); b.sl(0.8); pg.fill("#ca", "500"); pg.click("#sv", force=True); b.sl(0.6)
    b.cap("Typed test: payment above the balance is refused."); b.say("n11"); pg.screenshot(path=f"{out}/overpay.png"); b.sl(1.5)
    b.card("<h1>What is real</h1><p>Gnani Prisma and Timbre calls. Staged confirmation. Ledger in whole paise. Restart persistence. Name matching is a rule-based suggestion.</p><p>Not tested yet: real voices, noisy shops, physical microphones.</p><small>Prepared for Anil Kumara. Private review copy. Not submitted, not published.</small>", "n12", "Tested with generated voices only."); b.sl(3.0)
    b.cap(""); b.close(); srv.terminate()
json.dump(EV, open(out + "/events.json", "w"), indent=1); json.dump(CAPS, open(out + "/caps.json", "w"), indent=1)
