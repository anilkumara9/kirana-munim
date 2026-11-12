"""Local audio-path tests: browser-style webm/opus and ogg -> 16k mono WAV via ffmpeg; missing-key error. No network, no credits."""
import subprocess, os, sys, wave, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server, gnani_client as g
for ext, codec in (("webm", "libopus"), ("ogg", "libopus")):
    raw = subprocess.run(["ffmpeg","-loglevel","error","-f","lavfi","-i","sine=frequency=440:duration=2","-c:a",codec,"-f",ext,"pipe:1"],capture_output=True).stdout
    w = wave.open(io.BytesIO(server.to_wav(raw)))
    assert (w.getframerate(), w.getnchannels()) == (16000, 1) and 1.8 < w.getnframes()/16000 < 2.2, ext
long = subprocess.run(["ffmpeg","-loglevel","error","-f","lavfi","-i","sine=duration=45","-c:a","libopus","-f","webm","pipe:1"],capture_output=True).stdout
assert wave.open(io.BytesIO(server.to_wav(long))).getnframes()/16000 <= 30.1, "must cap at 30 s (API limit)"
try: server.to_wav(b"not audio"); raise SystemExit("garbage should fail")
except g.GnaniError: pass
os.environ.pop("GNANI_API_KEY", None)
try: g.transcribe(b"x"); raise SystemExit("must refuse without key")
except g.GnaniError as e: assert "No Gnani call was made" in str(e)
print("audio path tests pass (local only)")
