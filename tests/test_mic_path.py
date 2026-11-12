"""Real-browser mic path with a fake capture device (controlled audio fixture). No Gnani call: the key is unset, so the server
must convert the real MediaRecorder blob, then refuse with the 'No Gnani call was made' message, which the UI must show."""
import os, subprocess, sys, time, tempfile
from playwright.sync_api import sync_playwright
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {k: v for k, v in os.environ.items() if k != "GNANI_API_KEY"}; env["LEDGER_PATH"] = os.path.join(tempfile.mkdtemp(), "l.json")
srv = subprocess.Popen([sys.executable, "server.py"], cwd=root, env=env); time.sleep(1)
shots = sys.argv[1] if len(sys.argv) > 1 else None
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"), args=["--headless=new", "--no-sandbox", "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream", "--use-fake-device-with-fake-audio-capture", "--use-file-for-fake-audio-capture=/tmp/fake.wav"])
        ctx = br.new_context(permissions=["microphone"], viewport=dict(width=390, height=800)); pg = ctx.new_page(); pg.goto("http://127.0.0.1:8000/")
        reqs = []; pg.on("response", lambda r: reqs.append((r.request.method, r.url, r.status)) if r.request.method == "POST" else None)
        box = pg.locator("#b").bounding_box(); pg.mouse.move(box["x"] + 40, box["y"] + 40); pg.mouse.down()
        try: pg.wait_for_function("document.querySelector('#b').classList.contains('rec')", timeout=8000)
        except Exception: raise SystemExit("recording never started; status text: " + pg.inner_text("#s"))
        assert "Release" in pg.inner_text("#bl")
        time.sleep(2); pg.mouse.up()
        pg.wait_for_function("document.querySelector('#s').classList.contains('err')", timeout=15000)
        msg = pg.inner_text("#s"); assert "No Gnani call was made" in msg, msg
        assert any(m == "POST" and s == 500 for m, u, s in reqs), reqs
        assert pg.locator("#rv").is_hidden() and pg.locator("#a").is_hidden()
        if shots: pg.screenshot(path=f"{shots}/ui-mobile-nokey-error-fullpage.png", full_page=True)
        br.close()
    print("mic path test pass: real MediaRecorder blob -> server -> ffmpeg ok -> refused without key; UI shows the error, no review card, no audio control")
finally: srv.terminate()
