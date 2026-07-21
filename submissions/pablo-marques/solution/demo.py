"""
demo.py — a demonstracao rodando, em linha de comando

Recebe o texto de um chamado e imprime o que o agente veria: a categoria, a
rota, a regra que decidiu, e o contexto de chamados similares.

    .venv/Scripts/python.exe demo.py "meu notebook nao liga desde ontem"
    echo "please grant access to the finance folder" | .venv/Scripts/python.exe demo.py
    .venv/Scripts/python.exe demo.py --sessao     # 5 chamados reais do teste

Nada e treinado nem medido aqui. Este arquivo so compoe o que ja existe:

    bloco 3 (03_classificador.py) -> curva_medida.json, os limiares por classe
    bloco 4 (04_triagem.py)       -> Triador, a politica e o retorno estruturado
    bloco 5 (05_contexto_similar.py) -> PainelDeContexto, os vizinhos

Mesma semente (42), mesmo split, mesmo modelo. Sem dependencia nova.

A rota "auto" significa auto-ROTEADO. Nada aqui fecha ticket nem responde
cliente — ver SECAO 1B do bloco 1.
"""

from __future__ import annotations

import sys
import textwrap
import time
from importlib import import_module
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

b5 = import_module("05_contexto_similar")
PainelDeContexto, Contexto = b5.PainelDeContexto, b5.Contexto
Tee, titulo = b5.Tee, b5.titulo

PASTA_DEMO = AQUI / "demo"
SESSAO = PASTA_DEMO / "sessao_demo.txt"
LARGURA = 78


def regra_de(decisao) -> str:
    """Qual das quatro regras do bloco 4 decidiu. Deduzida da propria decisao."""
    if decisao.rota == "aprovacao":
        return "R1 — categoria sensivel (vence tudo, inclusive confianca alta)"
    if decisao.motivo.startswith("empate"):
        return "R2 — abstencao por empate no topo"
    if decisao.rota == "humano":
        return "R3 — confianca abaixo do limiar medido da classe"
    return "R4 — auto-roteado (nenhuma regra anterior disparou)"


ROTULO_ROTA = {
    "auto": "AUTO        -> fila automatica. auto-ROTEADO, NAO resolvido.",
    "aprovacao": "APROVACAO   -> humano com poder de aprovar decide.",
    "humano": "HUMANO      -> fila de triagem manual, com a sugestao anexada.",
}


def bloco(titulo_: str):
    print("-" * LARGURA)
    print(titulo_)
    print("-" * LARGURA)


def imprimir(ctx: Contexto, texto: str, real: str | None = None):
    d = ctx.decisao
    print("=" * LARGURA)
    print("CHAMADO RECEBIDO")
    print("=" * LARGURA)
    for linha in textwrap.wrap(texto.strip(), width=LARGURA - 4) or ["(vazio)"]:
        print(f"  {linha}")
    if real is not None:
        print(f"\n  [rotulo real: {real} — mostrado so nesta demo, o sistema nao ve]")
    print()

    bloco("1. CLASSIFICACAO")
    print(f"  categoria prevista : {d.categoria}")
    print(f"  confianca          : {d.confianca:.3f}")
    print(f"  segunda hipotese   : {d.segunda_categoria} (margem {d.margem:.3f})")
    print()

    bloco("2. DECISAO DE TRIAGEM")
    print(f"  rota   : {ROTULO_ROTA[d.rota]}")
    print(f"  regra  : {regra_de(d)}")
    print(f"  limiar : tau={d.limiar_aplicado:.2f} para '{d.categoria}', "
          f"da curva medida do bloco 3")
    print("  motivo :")
    for linha in textwrap.wrap(d.motivo, width=LARGURA - 13):
        print(f"           {linha}")
    print()

    bloco("3. CONTEXTO — CHAMADOS SIMILARES JA ROTEADOS")
    print(f"  {ctx.aviso}")
    print()
    if not ctx.similares:
        print("  (nenhum chamado comparavel na base acima do limiar de similaridade.")
        print("   O painel devolve VAZIO em vez de inventar tres — acontece em 30.6%")
        print("   do conjunto de teste, e e informacao: este chamado nao tem precedente.)")
    for i, s in enumerate(ctx.similares, start=1):
        print(f"  {i}. similaridade {s.similaridade:.3f} | foi para a fila '{s.fila}'")
        linhas = textwrap.wrap(s.trecho, width=LARGURA - 18) or [""]
        print(f"     texto     : {linhas[0]}")
        for extra in linhas[1:]:
            print(f"                 {extra}")
        print(f"     resolucao : {s.resolucao_aplicada}")
    if ctx.voto_vizinhos is not None:
        veredito = "CONCORDAM" if ctx.concorda else "DISCORDAM"
        print(f"\n  voto dos vizinhos : '{ctx.voto_vizinhos}'")
        print(f"  modelo            : '{d.categoria}'   -> {veredito}")
        if not ctx.concorda:
            print("  (discordancia nao muda a rota nesta politica; e um sinal para o")
            print("   agente. Precisao medida: 0.928 quando concordam, 0.733 quando nao.)")
    print()


def carregar() -> PainelDeContexto:
    t0 = time.time()
    print("carregando o classificador do bloco 3 e a politica do bloco 4...",
          file=sys.stderr)
    p = PainelDeContexto()
    print(f"pronto em {time.time() - t0:.1f}s\n", file=sys.stderr)
    return p


# --------------------------------------------------------------------------
# SESSAO GRAVADA — 5 chamados reais do conjunto de teste
# --------------------------------------------------------------------------

def sessao():
    """Cinco casos do teste, escolhidos por criterio declarado e nao a dedo."""
    PASTA_DEMO.mkdir(exist_ok=True)
    sys.stdout = Tee(SESSAO)

    painel = carregar()
    textos, reais = painel.tri._teste
    ctxs, _ = painel.montar_lote(textos)

    titulo("DEMO — CINCO CHAMADOS REAIS DO CONJUNTO DE TESTE")
    print(f"""
Chamados do split de teste (semente 42), que o modelo nunca viu no treino.
Nao sao exemplos escritos por mim: sao os PRIMEIROS do conjunto de teste que
satisfazem cada criterio abaixo, para cobrir as tres rotas, o caso sem
precedente e um erro. Nenhum foi escolhido por ficar bonito.

  caso 1  primeiro 'auto' em que os vizinhos concordam com o modelo
  caso 2  primeiro 'aprovacao' (categoria sensivel — R1)
  caso 3  primeiro 'humano' (o modelo se abstem)
  caso 4  primeiro caso sem nenhum chamado comparavel (painel VAZIO)
  caso 5  primeiro caso em que o modelo ERROU a categoria
""")

    criterios = [
        ("auto + vizinhos concordam",
         lambda i: ctxs[i].decisao.rota == "auto" and ctxs[i].concorda is True),
        ("aprovacao (categoria sensivel)",
         lambda i: ctxs[i].decisao.rota == "aprovacao"),
        ("humano (abstencao)",
         lambda i: ctxs[i].decisao.rota == "humano"),
        ("sem precedente (painel vazio)",
         lambda i: len(ctxs[i].similares) == 0),
        ("o modelo errou",
         lambda i: ctxs[i].decisao.categoria != reais[i]),
    ]

    usados: set[int] = set()
    for n, (nome, criterio) in enumerate(criterios, start=1):
        escolhido = next((i for i in range(len(textos))
                          if i not in usados and criterio(i)), None)
        if escolhido is None:
            print(f"\n### CASO {n} — {nome}: nenhum caso satisfaz o criterio.\n")
            continue
        usados.add(escolhido)
        print(f"\n\n### CASO {n} — criterio: {nome}\n")
        imprimir(ctxs[escolhido], str(textos[escolhido]), str(reais[escolhido]))

    titulo("FIM DA SESSAO")
    print("""
Os cinco casos acima sao saida literal deste script. O caso 5 mostra o sistema
errando, e o caso 4 mostra o painel devolvendo vazio: os dois ficaram porque o
criterio os escolheu, nao apesar disso.
""")
    print(f"sessao salva em: {SESSAO}")
    sys.stdout.flush()


def main():
    args = [a for a in sys.argv[1:] if a.strip()]
    if args and args[0] == "--sessao":
        sessao()
        return
    if args:
        texto = " ".join(args)
    elif not sys.stdin.isatty():
        texto = sys.stdin.read()
    else:
        print(__doc__)
        raise SystemExit("ERRO: passe o texto do chamado como argumento ou por stdin.")
    if not texto.strip():
        raise SystemExit("ERRO: texto vazio.")
    imprimir(carregar().montar(texto), texto)


if __name__ == "__main__":
    main()
