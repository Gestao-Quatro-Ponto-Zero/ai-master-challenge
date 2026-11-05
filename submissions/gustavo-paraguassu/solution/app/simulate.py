"""Roda o núcleo sem Telegram: mostra o que o bot faria com cada mensagem.

Uso (de dentro de solution/):
  python -m app.simulate "meu notebook não liga"
  python -m app.simulate --cenarios          # os cenários do experimento (usa o cache: não precisa de chave)
"""
import json
import sys

from . import config
from .engine import Motor, FILAS


def mostrar(motor: Motor, texto: str):
    tri, meta, d = motor.processar(texto)
    print("=" * 100)
    print(f"CLIENTE: {texto}")
    print(f"  LLM ({meta.get('fonte')}): {tri.resumo_pt}")
    print(f"  inglês p/ roteador: {tri.texto_ingles}")
    campos = {k: v for k, v in tri.campos.model_dump().items() if v}
    print(f"  campos: {campos}  riscos: {tri.sinais_de_risco}  pede_humano: {tri.pede_humano}")
    print(f"  roteador: {d.fila} {d.conf:.0%} (limiar {d.limiar:.0%}) | top3: "
          + ", ".join(f"{q} {p:.0%}" for q, p in d.top3) + f" | P(sensível)={d.p_sens:.0%}"
          + f" | LLM sugeriu: {tri.fila_sugerida_llm}")
    print(f"  DESTINO: {'equipe ' + FILAS[d.fila]['nome_pt'] if d.destino == 'fila' else 'TRIAGEM HUMANA'}"
          + (f"  motivos: {d.motivos}" if d.motivos else ""))
    if d.pergunta:
        print(f"  -> PERGUNTA AO CLIENTE: {d.pergunta}")
    elif d.auto:
        print(f"  -> RESPOSTA AUTOMÁTICA ({d.auto})")
    print(f"  rascunho p/ atendente: {d.rascunho}")


if __name__ == "__main__":
    motor = Motor()
    if sys.argv[1:] == ["--cenarios"]:
        for c in json.loads(config.SCENARIOS_PATH.read_text()):
            mostrar(motor, c["texto_pt"])
            print(f"  (fila verdadeira no Dataset 2: {c['fila_verdadeira']})")
    else:
        for t in sys.argv[1:]:
            mostrar(motor, t)
