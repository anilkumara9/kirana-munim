"""Script-tolerant name key. 'Ramesh', 'रमेश' and 'ರಮೇಶ್' give the same key, so a spoken name in another script can be matched to an existing
customer. Used only to SUGGEST a match; the shopkeeper confirms. Deliberately coarse: consonant skeleton with similar sounds merged."""
import re
_DEV = {}
for chars, lat in (("कखक", "k"), ("गघ", "g"), ("चछ", "c"), ("जझ", "j"), ("टठतथ", "t"), ("डढदध", "d"), ("णन", "n"), ("पफ", "p"), ("बभ", "b"),
                   ("म", "m"), ("य", "y"), ("रऱ", "r"), ("ळलऴ", "l"), ("व", "v"), ("शषस", "s"), ("क़", "k"), ("ख़", "k"), ("ग़", "g"), ("ज़", "j"), ("फ़", "p"), ("ड़ढ़", "d")):
    for c in chars: _DEV[c] = lat
_DEV.update({"ह": "", "ं": "n", "ँ": "n"})  # h dropped (aspiration); anusvara = n
def _to_dev(ch):
    o = ord(ch)
    return chr(o - 0x380) if 0x0C80 <= o <= 0x0CFF else ch  # Kannada block lines up with Devanagari for basic letters
def key(name):
    s = []
    for ch in (name or "").strip().lower():
        ch = _to_dev(ch)
        if ch in _DEV: s.append(_DEV[ch])
        elif "a" <= ch <= "z": s.append(ch)
    t = "".join(s)
    for a, b in (("sh", "s"), ("ch", "c"), ("th", "t"), ("dh", "d"), ("kh", "k"), ("gh", "g"), ("bh", "b"), ("ph", "p"), ("jh", "j")): t = t.replace(a, b)
    t = t.translate(str.maketrans({"w": "v", "z": "j", "f": "p", "q": "k"}))
    t = re.sub(r"[aeiouh]", "", t)
    return re.sub(r"(.)\1+", r"\1", t)
