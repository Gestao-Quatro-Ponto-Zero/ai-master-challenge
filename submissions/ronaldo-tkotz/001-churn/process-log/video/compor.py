"""Monta o vídeo final: clipes gravados + narração + legendas (gravadas na imagem e em faixa SRT).
Uso: python3 -I compor.py <saida.mp4>  (na pasta video/)"""
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SHOT = os.path.join(AQUI, "..", "shot")
SAIDA = sys.argv[1]
os.chdir(AQUI)
run = lambda *a: subprocess.run(list(a), check=True)
def dura(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True, check=True).stdout.strip()
    if r and r != "N/A":
        return float(r)
    pts = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "packet=pts_time", "-of", "csv=p=0", f], capture_output=True, text=True, check=True).stdout.split()
    return max(float(x.strip(",")) for x in pts if x.strip(",") not in ("", "N/A"))

rot = json.load(open("roteiro.json", encoding="utf-8"))
dur = json.load(open("duracoes.json"))
LEAD, GAP, CAUDA = 0.35, 0.3, 1.2
os.makedirs("tmp", exist_ok=True)

t, legendas, faixas, partes = 0.0, [], [], []
for seg in rot:
    sid = seg["id"]
    narr = LEAD + sum(dur[f"{sid}_{i}"] + GAP for i in range(len(seg["frases"]))) - GAP
    clip = f"clip_{sid}.webm"
    cd = dura(clip)
    L = round(min(cd, narr + CAUDA) if sid not in ("s5", "s7") else max(cd - 0.3, narr + CAUDA), 2)
    L = max(L, narr + 0.6)
    pad = max(0.0, L - cd)
    vf = "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p" + (f",tpad=stop_mode=clone:stop_duration={pad:.2f}" if pad else "")
    out = f"tmp/{sid}.mp4"
    run("ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-t", f"{L}", "-vf", vf, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16", out)
    partes.append(out)
    s = t + LEAD
    for i, frase in enumerate(seg["frases"]):
        d = dur[f"{sid}_{i}"]
        faixas.append((f"audio/{sid}_{i}.wav", s))
        legendas.append({"n": len(legendas), "texto": frase, "ini": round(s, 2), "fim": round(s + d + 0.25, 2)})
        s += d + GAP
    t += dura(out)
    print(f"{sid}: clipe {cd:.1f}s → {L:.1f}s, narração {narr:.1f}s")

# vídeo contínuo
with open("tmp/lista.txt", "w") as f:
    f.writelines(f"file '{os.path.abspath(p)}'\n" for p in partes)
run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "tmp/lista.txt", "-c", "copy", "tmp/video.mp4")
total = dura("tmp/video.mp4")

# narração numa faixa só, cada frase no seu instante
ins, fil = [], []
for k, (w, s) in enumerate(faixas):
    ins += ["-i", w]
    ms = int(s * 1000)
    fil.append(f"[{k}:a]adelay={ms}|{ms}[a{k}]")
fil.append("".join(f"[a{k}]" for k in range(len(faixas))) + f"amix=inputs={len(faixas)}:normalize=0,apad,atrim=0:{total:.3f},loudnorm=I=-16:TP=-1.5:LRA=11[out]")
run("ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fil), "-map", "[out]", "-ar", "48000", "tmp/narracao.wav")

# legendas: PNG por frase + SRT
json.dump(legendas, open("tmp/legendas.json", "w"), ensure_ascii=False)
run("bun", os.path.join(SHOT, "legenda.ts"), os.path.abspath("tmp/legendas.json"), os.path.abspath("tmp"))
hms = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round((x-int(x))*1000)):03d}"
srt = os.path.splitext(SAIDA)[0] + ".srt"
with open(srt, "w", encoding="utf-8") as f:
    for i, l in enumerate(legendas, 1):
        f.write(f"{i}\n{hms(l['ini'])} --> {hms(l['fim'])}\n{l['texto']}\n\n")

ins, fil, ult = ["-i", "tmp/video.mp4", "-i", "tmp/narracao.wav"], [], "0:v"
for k, l in enumerate(legendas):
    ins += ["-i", f"tmp/cap_{l['n']:02d}.png"]
    fil.append(f"[{ult}][{k+2}:v]overlay=0:0:enable='between(t,{l['ini']},{l['fim']})'[v{k}]")
    ult = f"v{k}"
run("ffmpeg", "-y", "-loglevel", "error", *ins, "-i", srt, "-filter_complex", ";".join(fil),
    "-map", f"[{ult}]", "-map", "1:a", "-map", f"{len(legendas)+2}:s",
    "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    "-c:a", "aac", "-b:a", "128k", "-c:s", "mov_text", "-metadata:s:s:0", "language=por", SAIDA)
print(f"{SAIDA}: {dura(SAIDA):.1f}s, {os.path.getsize(SAIDA)/1e6:.1f} MB; legendas {len(legendas)}; srt {srt}")
