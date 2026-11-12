import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from parser import parse
def t(s, kind, amt, cust):
    r = parse(s); assert (r["kind"], r["amount"], r["customer"]) == (kind, amt, cust), (s, r)
t("Ramesh ko 200 rupaye udhaar", "credit", 200.0, "Ramesh")
t("Ramesh ko ५०० रुपये उधार", "credit", 500.0, "Ramesh")
t("Ramesh paid 150 rupees", "payment", 150.0, "Ramesh")
t("ರಮೇಶ್ ಗೆ ೨೦೦ ರೂಪಾಯಿ ಉದ್ರಿ", "credit", 200.0, "ರಮೇಶ್")
# REAL Prisma v3.0 output (Nov 12 live run on Timbre-synthesised audio; no digits, English number words in Devanagari)
r = parse("रमेश को टू हंड्रेड रुपये उधार।"); assert (r["customer"], r["amount"], r["kind"]) == ("रमेश", 200.0, "credit"), r
# REAL Prisma outputs from Timbre-synthesised Kannada/Hindi audio (live run Nov 12)
for s, k, a, c in [("ರಮೇಶ್ಗೆ 200 ರೂಪಾಯಿ ಉದ್ರಿ.", "credit", 200.0, "ರಮೇಶ್"), ("ರಮೇಶ್ 200 ರೂಪಾಯಿ ಕೊಟ್ಟರು.", "payment", 200.0, "ರಮೇಶ್"),
                   ("रमेश ने 150 रुपये दिए।", "payment", 150.0, "रमेश"), ("रमेश के 100 रुपये उधरे।", "credit", 100.0, "रमेश")]:
    r = parse(s); assert (r["kind"], r["amount"], r["customer"]) == (k, a, c), (s, r)
assert not parse("hello there")["ok"]
for s in ["Ramesh ko 200 aur 500 udhaar", "Ramesh udhaar", "Ramesh ko 200 udhaar aur paid 100", "udhaar 200", "Ramesh ko 900000 udhaar"]:
    r = parse(s); assert not r["ok"] and r["issues"], (s, r)
print("parser tests pass (text only; no Gnani calls)")
