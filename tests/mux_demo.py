import json, subprocess, glob, sys, textwrap, os
out = sys.argv[1]; EV = json.load(open(out + "/events.json")); CAPS = json.load(open(out + "/caps.json"))
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
va, vb = glob.glob(out + "/a/*.webm")[0], glob.glob(out + "/b/*.webm")[0]
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", va, "-i", vb, "-filter_complex", "[0:v]crop=405:720:0:0,setsar=1[x];[1:v]crop=405:720:0:0,setsar=1[y];[x][y]concat=n=2:v=1:a=0,fps=25,scale=608:1080:flags=lanczos[p]", "-map", "[p]", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", out + "/phone.mp4"], check=True)
off = dur(va); total = off + dur(vb)
caps = [dict(t=c["t"] + (off if c["scene"] == "b" else 0), text=c["text"]) for c in CAPS]
FB, FR = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
os.makedirs(out + "/cap", exist_ok=True); dt = []
for i, c in enumerate(caps):
    end = caps[i + 1]["t"] if i + 1 < len(caps) else total
    if not c["text"]: continue
    f = f"{out}/cap/{i}.txt"; open(f, "w").write("\n".join(textwrap.wrap(c["text"], 21)))
    dt.append(f"drawtext=fontfile={FB}:textfile={f}:fontsize=68:line_spacing=16:fontcolor=0x0f1419:x=100:y=(h-text_h)/2:enable='between(t,{c['t']:.2f},{end:.2f})'")
chain = ",".join(dt)
vf = f"color=c=0xf7f9f9:s=1920x1080:r=25,drawtext=fontfile={FB}:text='KIRANA MUNIM':fontsize=34:fontcolor=0x0a7d5a:x=100:y=80,drawtext=fontfile={FR}:text='Generated test voices. Real Gnani Prisma and Timbre calls.':fontsize=28:fontcolor=0x536471:x=100:y=h-100,drawbox=x=0:y=0:w=2:h=1080:color=0xe1e8ed:t=fill[bg]"
fc = f"{vf};[bg]{chain}[bg2];[bg2][0:v]overlay=x=1180:y=0:shortest=1[o];[o]tpad=stop_mode=clone:stop_duration=4[v]"
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out + "/phone.mp4", "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", out + "/video_only.mp4"], check=True)
ins, fl, labs = [], [], []
for i, e in enumerate(EV):
    ms = int((e["t"] + (off if e["scene"] == "b" else 0)) * 1000); ins += ["-i", e["file"]]
    fl.append(f"[{i}:a]aformat=sample_rates=24000:channel_layouts=mono,volume={e['vol']},adelay={ms}[a{i}]"); labs.append(f"[a{i}]")
fl.append("".join(labs) + f"amix=inputs={len(EV)}:normalize=0[aout]")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "[aout]", out + "/audio.wav"], check=True)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out + "/video_only.mp4", "-i", out + "/audio.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "apad", "-c:a", "aac", "-shortest", out + "/kirana-munim-demo-v2.mp4"], check=True)
print("video", dur(out + "/kirana-munim-demo-v2.mp4"))
