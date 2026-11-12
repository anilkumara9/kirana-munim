"""No Gnani call, no key needed: releasing sends audio to the server; cancelling (pointercancel / Escape) sends nothing."""
import os, subprocess, sys, time, tempfile
from playwright.sync_api import sync_playwright
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fx = "/tmp/cancel_fx.wav"; subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-ar", "16000", "-ac", "1", fx], check=True)
env = dict(os.environ, LEDGER_PATH=os.path.join(tempfile.mkdtemp(), "l.json")); env.pop("GNANI_API_KEY", None)
srv = subprocess.Popen([sys.executable, "server.py"], cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"), args=["--headless=new", "--no-sandbox", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--use-fake-device-with-fake-audio-capture", f"--use-file-for-fake-audio-capture={fx}"])
        pg = br.new_context(permissions=["microphone"]).new_page(); posts = []
        pg.on("request", lambda r: posts.append(r.url) if r.method == "POST" and r.url.rstrip("/").endswith("8000") else None)
        pg.goto("http://127.0.0.1:8000/"); assert "Hold" in pg.inner_text("#bl")
        pg.focus("#b"); pg.keyboard.down("Space"); pg.wait_for_function("document.querySelector('#b').classList.contains('rec')")
        assert "Recording" in pg.inner_text("#bl") and pg.get_attribute("#b", "aria-pressed") == "true"
        time.sleep(1); pg.keyboard.press("Escape"); time.sleep(1.5); pg.keyboard.up("Space")
        assert not pg.evaluate("document.querySelector('#b').classList.contains('rec')") and not posts, posts
        assert "Cancelled" in pg.inner_text("#s") and "Hold" in pg.inner_text("#bl")
        pg.keyboard.down("Space"); pg.wait_for_function("document.querySelector('#b').classList.contains('rec')"); time.sleep(1); pg.keyboard.up("Space")
        pg.wait_for_function("document.querySelector('#s').innerText.includes('Could not process')", timeout=15000); assert len(posts) == 1, posts
        # pointercancel (finger dragged away / OS interrupt) also cancels
        posts.clear(); pg.evaluate("document.querySelector('#b').dispatchEvent(new PointerEvent('pointerdown',{pointerId:7,bubbles:true}))")
        pg.wait_for_function("document.querySelector('#b').classList.contains('rec')"); time.sleep(1)
        pg.evaluate("document.querySelector('#b').dispatchEvent(new PointerEvent('pointercancel',{pointerId:7,bubbles:true}))"); time.sleep(1.5)
        assert not posts and "Cancelled" in pg.inner_text("#s"); br.close()
    print("cancel test pass: Escape and pointercancel send nothing; release sends audio; label and aria-pressed change")
finally: srv.terminate()
