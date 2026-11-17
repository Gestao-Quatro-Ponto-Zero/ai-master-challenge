"""Narração: uma faixa por frase com a voz pt-BR do macOS, mais a duração de cada uma.
Uso: python3 -I tts.py  (na pasta video/). Escreve audio/<seg>_<n>.wav e duracoes.json."""
import json, os, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(AQUI, "audio"), exist_ok=True)
VOZ, TAXA = os.environ.get("VOZ", "Luciana"), os.environ.get("TAXA", "182")
rot = json.load(open(os.path.join(AQUI, "roteiro.json"), encoding="utf-8"))
dur = {}
for seg in rot:
    for i, frase in enumerate(seg["frases"]):
        base = os.path.join(AQUI, "audio", f"{seg['id']}_{i}")
        dita = frase.replace("SQL", "ésse quê éle").replace("DevTools", "Dévi Tuls").replace("RavenStack", "Raven Stack").replace("PowerPoint", "Páuer Póint").replace("churn", "tchârni").replace("Minto", "Mínto").replace("de IA", "de inteligência artificial")
        subprocess.run(["say", "-v", VOZ, "-r", TAXA, "-o", base + ".aiff", dita], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base + ".aiff", "-ar", "48000", "-ac", "2", base + ".wav"], check=True)
        os.remove(base + ".aiff")
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", base + ".wav"],
                                 capture_output=True, text=True, check=True).stdout)
        dur[f"{seg['id']}_{i}"] = round(d, 3)
json.dump(dur, open(os.path.join(AQUI, "duracoes.json"), "w"), indent=1)
segs = {}
for k, v in dur.items():
    segs[k.split("_")[0]] = segs.get(k.split("_")[0], 0) + v + 0.3
print({k: round(v, 1) for k, v in segs.items()}, "total", round(sum(segs.values()), 1), "s")
