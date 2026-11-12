"""No vendor call. Name keys across scripts, and ledger.match suggestions."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["LEDGER_PATH"] = os.path.join(tempfile.mkdtemp(), "l.json")
import names, ledger
assert names.key("Ramesh") == names.key("रमेश") == names.key("ರಮೇಶ್") == names.key("RAMESH"), (names.key("Ramesh"), names.key("रमेश"), names.key("ರಮೇಶ್"))
assert names.key("Suresh") == names.key("सुरेश") == names.key("ಸುರೇಶ್")
assert names.key("Ramesh") != names.key("Suresh") and names.key("Geeta") == names.key("गीता")
ledger.add({"customer": "रमेश", "kind": "credit", "amount_paise": 20000, "amount": 200})
assert ledger.match("ರಮೇಶ್") == [{"name": "रमेश", "paise": 20000}] and ledger.match("Ramesh")[0]["name"] == "रमेश"
assert ledger.match("रमेश") == [], "exact name needs no suggestion"
assert ledger.match("Suresh") == [] and ledger.match("") == []
# generic, not tied to one demo name
for lat, dev, kn in (("Mahesh", "महेश", "ಮಹೇಶ್"), ("Dinesh", "दिनेश", "ದಿನೇಶ್"), ("Anita", "अनीता", None)):
    assert names.key(lat) == names.key(dev) and (kn is None or names.key(kn) == names.key(dev)), (lat, names.key(lat), names.key(dev))
# distinct but similar names must NOT collapse
for a, b in (("Ramesh", "Rakesh"), ("Ramesh", "Rajesh"), ("Suresh", "Mahesh"), ("Anil", "Amit"), ("Ravi", "Ravina")):
    assert names.key(a) != names.key(b), (a, b)
# known limit: different people can share a key (Sunil / Sonal) -> BOTH are offered, never auto-picked
ledger.add({"customer": "Sunil", "kind": "credit", "amount_paise": 10000, "amount": 100}); ledger.add({"customer": "Sonal", "kind": "credit", "amount_paise": 30000, "amount": 300})
c = ledger.match("सुनील"); assert sorted(x["name"] for x in c) == ["Sonal", "Sunil"], c
# confirm() refuses a similar-but-different name unless the user says new customer, and an exact existing name needs nothing
pid = ledger.stage({"customer": "Ramesh", "kind": "credit", "amount": 50, "issues": []})
try: ledger.confirm(pid); raise SystemExit("should refuse similar name")
except ledger.Similar as ex: assert ex.candidates[0]["name"] == "रमेश"
assert pid in ledger.PENDING, "refused entry stays pending, nothing saved"
n = len(ledger.load()); ledger.confirm(pid, new_customer=True); assert len(ledger.load()) == n + 1 and ledger.balances()["Ramesh"] == 5000
pid = ledger.stage({"customer": "रमेश", "kind": "payment", "amount": 20, "issues": []}); ledger.confirm(pid); assert ledger.balances()["रमेश"] == 18000
print("name matching tests pass (no vendor call)")
