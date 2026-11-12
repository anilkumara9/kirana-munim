"""Thin client for Gnani REST APIs (Prisma STT, Timbre TTS). Key comes from env GNANI_API_KEY only."""
import os, json, uuid, urllib.request

STT_URL = "https://api.vachana.ai/stt/v3"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"


class GnaniError(Exception):
    pass


# Hard usage guard. Dashboard (owner screenshot, Nov 12): 5,000 credits ~ 15k min STT or ~27.8 lakh TTS chars, i.e. an ESTIMATE of
# ~0.33 credit per STT minute and ~0.0018 credit per TTS char. At those rates the caps below cost at most ~1.1 (200 STT s) + ~10.8 (6000 TTS chars)
# = ~11.9 credits against the 500-credit budget; the budget would only be reached if the real rate were ~40x worse than the dashboard conversion.
# That is an estimate, not measured. Cumulative use is logged below and never retried.
import wave, io, time
# Cumulative local usage log. Deliberately OUTSIDE the project folder so packaging, copying or deleting the package never resets it.
# Override with KIRANA_USAGE_LOG. This is a LOCAL safety guard, not a vendor-side credit cap: Gnani's dashboard is the source of truth.
USAGE = os.environ.get("KIRANA_USAGE_LOG") or os.path.join(os.path.expanduser("~"), ".kirana-munim", "usage_log.json")
MAX_STT_SECONDS, MAX_TTS_CHARS, MAX_CALLS = 200.0, 6000, 100


def _errbody(ex):
    try: return ex.read().decode("utf-8", "replace")[:300]  # vendor error text (never contains our key)
    except Exception: return ""


def _usage():
    return json.load(open(USAGE)) if os.path.exists(USAGE) else {"stt_seconds": 0.0, "tts_chars": 0, "calls": []}


def _guard(kind, amount):
    u = _usage()
    if len(u["calls"]) >= MAX_CALLS: raise GnaniError("Usage guard: call limit reached. No Gnani call was made.")
    if kind == "stt" and u["stt_seconds"] + amount > MAX_STT_SECONDS: raise GnaniError("Usage guard: STT seconds cap reached. No Gnani call was made.")
    if kind == "tts" and u["tts_chars"] + amount > MAX_TTS_CHARS: raise GnaniError("Usage guard: TTS character cap reached. No Gnani call was made.")
    return u


def _save(u):
    os.makedirs(os.path.dirname(USAGE), exist_ok=True)
    tmp = USAGE + ".tmp"; json.dump(u, open(tmp, "w"), indent=1); os.replace(tmp, USAGE)


def _reserve(u, kind, amount):
    """Count the call BEFORE the network request, so a crash, timeout or error still counts (conservative)."""
    u["stt_seconds" if kind == "stt" else "tts_chars"] += amount
    u["calls"].append({"t": time.strftime("%H:%M:%S"), "kind": kind, "amount": amount, "result": "reserved"})
    _save(u); return len(u["calls"]) - 1


def _finish(i, status):
    u = _usage(); u["calls"][i]["result"] = status; _save(u)


def _key():
    k = os.environ.get("GNANI_API_KEY")
    if not k:
        raise GnaniError("Voice service is not configured (GNANI_API_KEY missing). No Gnani call was made.")
    return k


def transcribe(wav_bytes, language_code="indic-auto", model="prisma-v3.0"):
    key = _key()
    w = wave.open(io.BytesIO(wav_bytes))
    # header length can be wrong (streamed WAVs); never trust it above what the bytes can hold
    secs = min(w.getnframes(), max(len(wav_bytes) - 44, 0) // (w.getsampwidth() * w.getnchannels())) / w.getframerate()
    if secs > 30: raise GnaniError("Clip longer than 30 s. No Gnani call was made.")
    u = _guard("stt", secs); idx = _reserve(u, "stt", secs)
    boundary = uuid.uuid4().hex
    parts = []
    for name, val in (("model", model), ("language_code", language_code), ("format", "transcribe")):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode())
    parts.append(
        (f'--{boundary}\r\nContent-Disposition: form-data; name="audio_file"; filename="a.wav"\r\n'
         'Content-Type: audio/wav\r\n\r\n').encode() + wav_bytes + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(STT_URL, data=b"".join(parts), method="POST", headers={
        "X-API-Key-ID": key, "User-Agent": "kirana-munim/0.1", "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read())
    except Exception as ex:
        _finish(idx, "http-error: %s" % str(ex)[:80]); raise GnaniError("STT request failed: %s %s" % (ex, _errbody(ex)))
    _finish(idx, "ok" if body.get("success") else "api-error")
    if not body.get("success"):
        raise GnaniError(str(body.get("error", body)))
    return body  # transcript, detected_language_code, request_id, ...


def synthesize(text, language="auto", voice="Shivani", model="timbre-v3.0"):
    key = _key()
    if len(text) > 120: raise GnaniError("Reply text over 120 characters. No Gnani call was made.")
    u = _guard("tts", len(text)); idx = _reserve(u, "tts", len(text))
    payload = {"text": text, "voice": voice, "model": model, "language": language, "speed": 1.0,
               "audio_config": {"sample_rate": 24000, "num_channels": 1, "sample_width": 2,
                                "encoding": "linear_pcm", "container": "wav"}}
    req = urllib.request.Request(TTS_URL, data=json.dumps(payload).encode(), method="POST", headers={
        "X-API-Key-ID": key, "Content-Type": "application/json", "User-Agent": "kirana-munim/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except Exception as ex:
        _finish(idx, "http-error: %s" % str(ex)[:80]); raise GnaniError("TTS request failed: %s %s" % (ex, _errbody(ex)))
    _finish(idx, "ok")
    return data  # WAV bytes per docs; verified at first live run
