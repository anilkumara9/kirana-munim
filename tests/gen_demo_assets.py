"""Generates demo audio with real Gnani Timbre calls (bounded by the usage guard).
Three clearly different voices: narrator Yashraj (male, narrates), test speech Shubham (stands in for a shopkeeper), app replies Shivani."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gnani_client as g
A = "/downloads/demo/assets"
NARR = {
 "n1": "Kirana Munim. A voice ledger for neighbourhood shops, built on Gnani Prisma and Timbre.",
 "n2": "Shopkeepers track udhaar on paper. Here, they just say it, in Hindi, Kannada or English.",
 "n3": "Every voice in this demo is generated: me, the test speech, and the app's replies. There is no real shopkeeper.",
 "n4": "A Hindi entry. Hold the orb, and speak.",
 "n5": "Prisma turned the speech into an entry, and Timbre read it back. Nothing is saved until the shopkeeper confirms.",
 "n6": "Saved. After a full server restart, the ledger still shows two hundred rupees.",
 "n7": "Now Kannada. A payment of two hundred rupees.",
 "n8": "The name came back in Kannada script. The app spots the same customer, and shows the balance after this payment.",
 "n9": "One tap, and the payment settles the account. Saved.",
 "n10": "Unclear entries are flagged, and Save stays blocked.",
 "n11": "A payment above what is owed is refused before anything changes.",
 "n13": "Tap a customer for a statement with a running balance, and a reminder text to copy. Nothing is sent automatically.",
 "n12": "Tested with generated voices only. Real voices, noisy shops and physical microphones are next.",
}
TEST = {"hi": ("Ramesh ko 200 rupaye udhaar", "hi-en"), "kn": ("ರಮೇಶ್ ಇನ್ನೂರು ರೂಪಾಯಿ ಕೊಟ್ಟರು", "kn-IN")}
def fix(raw, out, pad=0):
    open(out + ".raw", "wb").write(raw)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", out + ".raw"] + (["-af", "apad=whole_dur=%d" % pad] if pad else []) + ["-ar", "16000" if pad else "24000", "-ac", "1", out]
    subprocess.run(cmd, check=True); os.remove(out + ".raw")
for k, t in NARR.items():
    p = f"{A}/{k}.wav"
    if not os.path.exists(p): fix(g.synthesize(t, language="en-IN", voice="Yashraj"), p)
for k, (t, lang) in TEST.items():
    p = f"{A}/test_{k}.wav"
    if not os.path.exists(p): fix(g.synthesize(t, language=lang, voice="Shubham"), p, pad=14)
print("ok")
