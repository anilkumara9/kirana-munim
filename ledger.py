import json, os, time
PATH = os.environ.get("LEDGER_PATH") or os.path.join(os.path.dirname(__file__), "ledger.json")

def load():
    return json.load(open(PATH)) if os.path.exists(PATH) else []

def add(entry):
    data = load(); entry = dict(entry, ts=time.strftime("%Y-%m-%d %H:%M:%S")); data.append(entry)
    json.dump(data, open(PATH, "w"), ensure_ascii=False, indent=1); return entry

def to_paise(x):
    from decimal import Decimal, ROUND_HALF_UP
    return int((Decimal(str(x)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))

def balances():
    """Integer paise per customer (no floats in money math)."""
    b = {}
    for e in load():
        p = e["amount_paise"]
        d = p if e["kind"] == "credit" else -p if e["kind"] == "payment" else 0
        b[e["customer"]] = b.get(e["customer"], 0) + d
    return b

def match(name):
    """Existing customers whose name has the same sound key in another spelling or script. Returns a list (maybe several, maybe empty).
    Suggestion only: never merges by itself; confirm() refuses to save a similar-but-different name until the user picks one or says new customer."""
    import names
    k = names.key(name)
    if len(k) < 2: return []
    b = balances()
    if name in b: return []
    return [{"name": c, "paise": paise} for c, paise in b.items() if names.key(c) == k]

class Rejected(Exception):
    pass

class Similar(Rejected):
    def __init__(self, cands, name):
        super().__init__("'%s' sounds like an existing customer (%s). Use that account, or confirm this is a new customer." % (name, ", ".join(c["name"] for c in cands)))
        self.candidates = cands

PENDING = {}

def stage(entry):
    """Hold a parsed entry; nothing is written to the ledger until confirm()."""
    import uuid
    pid = uuid.uuid4().hex[:8]; PENDING[pid] = entry; return pid

def confirm(pid, amount=None, customer=None, kind=None, new_customer=False):
    e = dict(PENDING[pid])  # popped only after validation passes
    if amount is not None: e["amount"] = amount
    if customer: e["customer"] = customer
    if kind: e["kind"] = kind
    if not new_customer:
        c = match(e["customer"])
        if c: raise Similar(c, e["customer"])
    p = to_paise(e["amount"])
    if p <= 0: raise Rejected("Amount must be above zero.")
    if e["kind"] == "payment" and p > balances().get(e["customer"], 0):
        raise Rejected("Payment is more than %s owes (Rs %.2f). Check the name and amount." % (e["customer"], max(balances().get(e["customer"], 0), 0) / 100))
    e["amount_paise"] = p; e["amount"] = p / 100
    PENDING.pop(pid)
    e["ok"] = True; e["issues"] = []; e["confirmed_by_user"] = True
    return add(e)

def discard(pid):
    PENDING.pop(pid, None)
