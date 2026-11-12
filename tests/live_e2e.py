"""LIVE end-to-end (uses real Gnani calls = real credits, tiny: ~3 s STT + ~60 chars TTS). Fake mic plays a fixture WAV.
Run: GNANI_API_KEY=... python3 tests/live_e2e.py FIXTURE.wav OUTDIR"""
import os, subprocess, sys, time, tempfile
from playwright.sync_api import sync_playwright
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fx, out = sys.argv[1], sys.argv[2]
env = dict(os.environ, LEDGER_PATH=os.path.join(tempfile.mkdtemp(), "l.json"))
srv = subprocess.Popen([sys.executable, "server.py"], cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"), args=["--headless=new", "--no-sandbox", "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream", "--use-fake-device-with-fake-audio-capture", f"--use-file-for-fake-audio-capture={fx}"])
        pg = br.new_context(permissions=["microphone"], viewport=dict(width=390, height=800)).new_page(); pg.goto("http://127.0.0.1:8000/")
        box = pg.locator("#b").bounding_box(); pg.mouse.move(box["x"] + 40, box["y"] + 40); pg.mouse.down()
        pg.wait_for_function("document.querySelector('#b').classList.contains('rec')"); time.sleep(2.6); pg.mouse.up()
        pg.wait_for_function("!document.querySelector('#rv').hidden || document.querySelector('#s').classList.contains('err')", timeout=30000)
        print("STATUS:", pg.inner_text("#s")); print("REVIEW visible:", pg.locator("#rv").is_visible())
        if pg.locator("#rv").is_visible(): print("name:", pg.input_value("#cn"), "| amount:", pg.input_value("#ca"), "| type:", pg.input_value("#ck"), "| warning:", pg.inner_text("#wn") if pg.locator("#wn").is_visible() else "none")
        print("audio shown:", pg.locator("#a").is_visible(), "| audio src bytes (b64 chars):", len(pg.get_attribute("#a", "src") or ""))
        pg.screenshot(path=f"{out}/ui-live-e2e-mobile.png", full_page=True); br.close()
finally: srv.terminate()
