"""UI interaction tests (typed fallback only: no Gnani calls, no credits). Run: python3 tests/test_ui.py"""
import os, subprocess, sys, time, tempfile, json, urllib.request
from playwright.sync_api import sync_playwright
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
led = os.path.join(tempfile.mkdtemp(), "l.json"); env = dict(os.environ, LEDGER_PATH=led)
def start(): 
    p = subprocess.Popen([sys.executable, "server.py"], cwd=root, env=env); time.sleep(1); return p
srv = start()
shots = sys.argv[1] if len(sys.argv) > 1 else None
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        for name, vp in (("desktop", (1100, 900)), ("mobile", (390, 800))):
            pg = br.new_page(viewport=dict(width=vp[0], height=vp[1])); pg.goto("http://127.0.0.1:8000/")
            assert pg.locator("#a").is_hidden(), "empty audio control must be hidden"
            pg.evaluate("document.querySelector('details').open=true"); pg.fill("#tx", "Ramesh ko 200 aur 500 udhaar"); pg.click("#tb"); pg.wait_for_selector("#wn:not([hidden])")
            assert pg.locator("#sv").is_disabled(), "Save must be disabled when ambiguous"
            assert "more than one amount" in pg.inner_text("#wn")
            if shots: pg.screenshot(path=f"{shots}/ui-{name}-ambiguous.png")
            before = pg.inner_text("#t")
            pg.fill("#ca", "500"); assert pg.locator("#sv").is_enabled()
            pg.click("#ds"); pg.wait_for_selector("#rv", state="hidden"); assert pg.inner_text("#t") == before, "discard must not save"
            pg.fill("#tx", "Ramesh ko 200 rupaye udhaar"); pg.click("#tb"); pg.wait_for_selector("#wn", state="hidden")
            assert pg.locator("#sv").is_enabled() and not pg.locator("#wn").is_visible()
            if shots: pg.screenshot(path=f"{shots}/ui-{name}-review.png")
            pg.click("#sv"); pg.wait_for_selector("#rv", state="hidden"); exp = "₹200" if name == "desktop" else "₹400"; pg.wait_for_function("t => document.querySelector('#t').innerText.includes(t)", arg=exp)
            assert "Ramesh" in pg.inner_text("#t")
            if shots: pg.screenshot(path=f"{shots}/ui-{name}-saved.png")
            if name == "desktop":
                srv.terminate(); srv.wait(); srv = start()  # persistence across restart
                pg.reload(); pg.wait_for_selector("#t tr"); assert "₹200" in pg.inner_text("#t")
                # overpayment must be refused, not stored as negative debt
                pg.evaluate("document.querySelector('details').open=true"); pg.fill("#tx", "Ramesh paid 999"); pg.click("#tb"); pg.wait_for_selector("#rv:not([hidden])"); pg.click("#sv")
                pg.wait_for_function("document.querySelector('#wn').innerText.includes('more than')")
                pg.click("#ds"); pg.wait_for_selector("#rv", state="hidden"); assert "₹200" in pg.inner_text("#t")
                # unconfirmed entries never persist
                pg.evaluate("document.querySelector('details').open=true"); pg.fill("#tx", "Sita ko 90 udhaar"); pg.click("#tb"); pg.wait_for_selector("#rv:not([hidden])")
                srv.terminate(); srv.wait(); srv = start(); pg.reload(); pg.wait_for_selector("#t tr")
                assert "Sita" not in pg.inner_text("#t")
            pg.close()
        br.close()
    print("UI interaction tests pass: ambiguous Save disabled, discard, save, persistence, unconfirmed-not-saved")
finally:
    srv.terminate()

# --- name matching + balance preview (typed, no Gnani call) ---
srv2 = subprocess.Popen([sys.executable, "server.py"], cwd=root, env=dict(os.environ, LEDGER_PATH=os.path.join(tempfile.mkdtemp(), "m.json")), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        pg = br.new_page(viewport=dict(width=1100, height=900)); pg.goto("http://127.0.0.1:8000/")
        def typed(t): pg.evaluate("document.querySelector('details').open=true"); pg.fill("#tx", t); pg.click("#tb"); pg.wait_for_selector("#rv:not([hidden])")
        typed("रमेश को 200 रुपये उधार"); pg.click("#sv"); pg.wait_for_selector("#rv", state="hidden")
        typed("Ramesh ne 150 rupaye diye")
        assert pg.locator("#mt").is_visible() and "रमेश" in pg.inner_text("#mt"), "should suggest the existing customer"
        assert pg.locator("#sv").is_disabled(), "Save must stay blocked while the suggestion is unresolved"
        pg.click("#mt button[data-i='0']"); assert pg.input_value("#cn") == "रमेश" and pg.locator("#mt").is_hidden()
        assert "₹50" in pg.inner_text("#im"), pg.inner_text("#im")  # 200 owed -> 50 after a 150 payment
        pg.fill("#ca", "999"); assert "more than" in pg.inner_text("#im") and "bad" in pg.get_attribute("#im", "class")
        pg.fill("#ca", "150")
        if len(sys.argv) > 1: pg.screenshot(path=f"{sys.argv[1]}/ui-match-desktop.png")
        pg.click("#sv"); pg.wait_for_selector("#rv", state="hidden"); assert "₹50" in pg.inner_text("#t")
        mb = br.new_page(viewport=dict(width=390, height=844)); mb.goto("http://127.0.0.1:8000/"); mb.evaluate("document.querySelector('details').open=true"); mb.fill("#tx", "Ramesh ne 20 rupaye diye"); mb.click("#tb"); mb.wait_for_selector("#mt:not([hidden])")
        if len(sys.argv) > 1: mb.screenshot(path=f"{sys.argv[1]}/ui-match-mobile.png")
        typed("Ramesh ko 70 rupaye udhaar"); assert pg.locator("#sv").is_disabled()
        pg.click("#nc"); assert pg.locator("#sv").is_enabled() and pg.locator("#mt").is_hidden()  # deliberate new customer
        pg.click("#sv"); pg.wait_for_selector("#rv", state="hidden"); assert "Ramesh" in pg.inner_text("#t")
        typed("Ramesh ne 10 rupaye diye"); assert pg.locator("#mt").is_hidden(); pg.click("#sv"); pg.wait_for_selector("#rv", state="hidden")  # exact existing Ramesh now: no suggestion needed on later entries
        pg.reload(); pg.click(".cust >> nth=0"); pg.wait_for_selector(".stmt"); assert pg.locator(".stmt li").count() >= 1 and pg.locator("#cp").count() == 1, "statement + reminder button for a customer who owes"
        assert "₹" in pg.inner_text(".stmt") and pg.get_attribute(".cust >> nth=0", "aria-expanded") == "true"
        pg.screenshot(path="/tmp/stmt.png", clip=dict(x=680,y=60,width=360,height=330)) if len(sys.argv) > 1 else None
        pg.click(".cust >> nth=0"); pg.wait_for_selector(".stmt", state="detached")
        br.close()
    print("match + balance preview UI tests pass")
finally: srv2.terminate()
