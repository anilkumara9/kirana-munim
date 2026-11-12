"""Deterministic parser: spoken shop-ledger sentence -> entry. No LLM, no network.
Handles English/Hindi/Kannada number words and digits (incl. Devanagari/Kannada digits)."""
import re

DIG = {c: str(i) for i, d in enumerate(["0123456789", "०१२३४५६७८९", "೦೧೨೩೪೫೬೭೮೯"]) for i, c in enumerate(d)}
NUM_WORDS = {
 "ten":10,"twenty":20,"fifty":50,"hundred":100,"two hundred":200,"five hundred":500,"thousand":1000,
 "सौ":100,"दो सौ":200,"पाँच सौ":500,"पांच सौ":500,"सो":100,"हज़ार":1000,"हजार":1000,"पचास":50,"बीस":20,"दस":10,
 "वन हंड्रेड":100,"टू हंड्रेड":200,"थ्री हंड्रेड":300,"फाइव हंड्रेड":500,"हंड्रेड":100,"थाउजेंड":1000,"फिफ्टी":50,
 "three hundred":300,"hundred rupees":100,"ನೂರು":100,"ಇನ್ನೂರು":200,"ಐನೂರು":500,"ಸಾವಿರ":1000,"ಐವತ್ತು":50,"ಇಪ್ಪತ್ತು":20,"ಹತ್ತು":10,
}
CREDIT = ["उधरे","udhaar","udhar","उधार","ಉದ್ರಿ","ಉಧಾರ","credit","on credit","baaki","बाकी","ಬಾಕಿ"]
PAID = ["दिए","दिये","diye","ಕೊಟ್ಟರು","ಕೊಟ್ಟ","paid","जमा","दिया","ಕೊಟ್ಟ","payment","received","जमा किया","ಜಮಾ"]
SALE = ["sold","sale","बेचा","बिक्री","ಮಾರಿ","ಮಾರಾಟ"]


def norm_digits(s):
    return "".join(DIG.get(c, c) for c in s)


def find_amount(text):
    t = norm_digits(text.lower())
    m = re.search(r"(?:rs\.?|₹|rupees?|रुपये|रुपए|ರೂ\.?|ರೂಪಾಯಿ)?\s*(\d[\d,]*(?:\.\d+)?)\s*(?:rs|₹|rupees?|रुपये|रुपए|ರೂಪಾಯಿ|ರೂ)?", t)
    if m:
        return float(m.group(1).replace(",", ""))
    for w in sorted(NUM_WORDS, key=len, reverse=True):
        if w in t:
            return float(NUM_WORDS[w])
    return None


def parse(text):
    t = norm_digits(text.strip())
    low = t.lower()
    kind = "unknown"
    if any(k in low for k in CREDIT): kind = "credit"
    elif any(k in low for k in PAID): kind = "payment"
    elif any(k in low for k in SALE): kind = "sale"
    amount = find_amount(t)
    # customer: first capitalised/Indic token before a keyword, or after 'to'/'for'
    cust = None
    W = r"[A-Za-z\u0900-\u097F\u0C80-\u0CFF]+"
    m = re.search(r"(" + W + r")\s+(?:ko|ge|ne|को|के|ने|ಗೆ)(?!" + W[1:-1] + r")", t, re.I) or re.search(r"(?:to|for)\s+(" + W + r")", t, re.I)
    if m: cust = m.group(1)
    else:
        m = re.match(r"\s*([A-Za-z\u0900-\u097F\u0C80-\u0CFF]+)", t)
        if m: cust = m.group(1)
    if cust and len(cust) > 3 and cust.endswith("ಗೆ"): cust = cust[:-1] if cust.endswith("ಗೆ") and False else cust[:-2]  # Kannada dative suffix attached to the name
    amounts = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", t)]
    kinds = [k for k, ws in (("credit", CREDIT), ("payment", PAID), ("sale", SALE)) if any(w in low for w in ws)]
    issues = []
    if kind == "unknown": issues.append("could not tell if this is credit, payment or sale")
    if len(set(kinds)) > 1: issues.append("both credit and payment words heard")
    if amount is None: issues.append("no amount heard")
    if len(set(amounts)) > 1: issues.append("I heard more than one amount (" + " and ".join(str(int(a)) if a == int(a) else str(a) for a in sorted(set(amounts))) + "). Please pick the right one")
    if amount is not None and (amount <= 0 or amount > 50000): issues.append("amount outside 1-50000")
    if cust is None and "no customer name heard" not in issues: issues.append("no customer name heard")
    if cust and cust.lower() in {w.lower() for w in CREDIT+PAID+SALE}:
        cust = None; issues.append("no customer name heard")
    # never auto-accept: ok means 'parsed cleanly', the user must still confirm before saving
    return {"kind": kind, "amount": amount, "customer": cust, "raw": text,
            "issues": issues, "ok": not issues}
