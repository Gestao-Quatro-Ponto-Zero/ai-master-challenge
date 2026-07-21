"""
04_triagem.py — Bloco 4: o roteador de triagem

Recebe o texto de um chamado e devolve uma decisao estruturada de ROTEAMENTO.

A distincao que rege este arquivo inteiro, vinda da SECAO 1B do bloco 1:

    rota "auto" significa AUTO-ROTEADO, nunca auto-resolvido.

O que a maquina faz e escolher a fila e poupar a triagem manual. O agente
continua atendendo, escrevendo e resolvendo. Nada aqui fecha ticket, e nada
aqui responde ao cliente. Auto-resolucao exigiria medir repeticao de solucao
(resolution_code, item 10 da PARTE 3 do bloco 0), campo que nao existe nestes
dados — entao nao existe rota que a proponha.

Quatro regras, nesta ordem de precedencia:

  R1. CATEGORIA SENSIVEL   -> aprovacao humana obrigatoria, sempre.
                              Vence tudo, inclusive confianca de 99%.
  R2. ABSTENCAO POR EMPATE -> as duas classes do topo estao proximas demais
                              para escolher entre elas. Vai para humano
                              mesmo que a primeira passe do limiar.
  R3. LIMIAR POR CLASSE    -> tau_c vem da CURVA MEDIDA do bloco 3, nao de
                              um numero global escolhido a dedo.
  R4. caso contrario       -> auto-roteado.

Uso:
    .venv/Scripts/python.exe 04_triagem.py            # demonstracao + avaliacao
    from importlib import import_module
    t = import_module("04_triagem").Triador(); t.rotear("texto do chamado")

Dependencias: pandas, scikit-learn (ver requirements.txt)
Saida: stdout + 04_triagem_saida.txt + politica_triagem.json
"""

from __future__ import annotations

import io
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "04_triagem_saida.txt"
CURVA_JSON = AQUI / "curva_medida.json"
POLITICA_JSON = AQUI / "politica_triagem.json"

SEMENTE = 42
FRACAO_TESTE = 0.20

# --------------------------------------------------------------------------
# PARAMETROS DA POLITICA — cada um com procedencia
# --------------------------------------------------------------------------

# [premissa arbitrada, sem fonte] kappa = M/T, custo do misrouting em multiplos
# do tempo de triagem. Define o piso de precisao p* = kappa/(1+kappa) que os
# limiares por classe tem de respeitar. Mesma grandeza da SECAO 1B do bloco 1.
KAPPA = 5
PISO_PRECISAO = KAPPA / (1 + KAPPA)          # 83.3%

# [convencao do analista] margem minima entre a 1a e a 2a probabilidade.
# Nao sai dos dados: e a linha que eu escolhi para chamar um caso de "empate".
# Existe porque precisao alta na classe do topo nao diz nada sobre o caso em
# que duas classes disputam o mesmo documento — e esse caso e justamente o
# que mais custa quando erra.
MARGEM_MINIMA = 0.15

# [decisao de processo, nao dos dados] categorias que exigem aprovacao humana
# independentemente da confianca. Nao ha nada na precisao que justifique isto:
# a justificativa e de risco, nao de acuracia. Concessao de privilegio
# administrativo e mudanca de acesso sao acoes com efeito de seguranca e sem
# desfazer barato — o custo de errar nao esta na fila errada, esta no
# privilegio concedido a quem nao devia.
CATEGORIAS_SENSIVEIS = {"Administrative rights", "Access"}


class Tee:
    def __init__(self, caminho: Path):
        self.arquivo = open(caminho, "w", encoding="utf-8")
        self.console = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    def write(self, texto: str):
        self.arquivo.write(texto)
        self.console.write(texto)

    def flush(self):
        self.arquivo.flush()
        self.console.flush()


def titulo(texto: str, char: str = "="):
    print("\n" + char * 78)
    print(texto)
    print(char * 78)


def achar_pasta_dados() -> Path:
    for pasta in [AQUI, *AQUI.parents]:
        if (pasta / "data" / "all_tickets_processed_improved_v3.csv").exists():
            return pasta / "data"
    raise SystemExit(f"ERRO: nao encontrei data/ subindo a partir de {AQUI}.")


# --------------------------------------------------------------------------
# RETORNO ESTRUTURADO
# --------------------------------------------------------------------------

@dataclass
class Decisao:
    """O que a triagem devolve para cada chamado.

    rota:
      "auto"     -> auto-ROTEADO para a fila da categoria. Nao resolvido.
      "humano"   -> vai para triagem manual; a sugestao segue junto.
      "aprovacao"-> vai para humano com poder de aprovar; categoria sensivel.
    """
    categoria: str
    confianca: float
    rota: str
    motivo: str
    limiar_aplicado: float
    segunda_categoria: str
    margem: float

    def __str__(self) -> str:
        return (f"{self.rota.upper():<9} {self.categoria:<22} "
                f"conf {self.confianca:.3f}  margem {self.margem:.3f}  | {self.motivo}")


# --------------------------------------------------------------------------
# LIMIARES POR CLASSE, DERIVADOS DA CURVA MEDIDA
# --------------------------------------------------------------------------

def limiares_da_curva(curva_json: Path, piso: float) -> dict[str, dict]:
    """Para cada classe, o MENOR tau cuja precisao medida alcanca o piso.

    Menor tau e nao maior: dentro da regiao que respeita p*, queremos a maior
    cobertura possivel. Se nenhum tau alcanca o piso, a classe recebe tau=1.01
    — ou seja, nunca e auto-roteada. Isso e o "o que NAO automatizar" saindo
    da medicao e nao de opiniao.
    """
    if not curva_json.exists():
        raise SystemExit(
            "ERRO: curva_medida.json nao existe. Rode 03_classificador.py antes — "
            "os limiares desta triagem vem da curva medida, nao de numero chutado."
        )
    dados = json.loads(curva_json.read_text(encoding="utf-8"))
    out = {}
    for classe, pontos in dados["curva"].items():
        validos = [p for p in pontos
                   if p["n_canal"] > 0 and p["precisao"] == p["precisao"]
                   and p["precisao"] >= piso]
        if validos:
            melhor = min(validos, key=lambda p: p["tau"])
            out[classe] = {"tau": melhor["tau"], "cobertura": melhor["cobertura"],
                           "precisao": melhor["precisao"], "automatizavel": True}
        else:
            melhor_p = max((p["precisao"] for p in pontos
                            if p["precisao"] == p["precisao"]), default=0.0)
            out[classe] = {"tau": 1.01, "cobertura": 0.0, "precisao": melhor_p,
                           "automatizavel": False}
    return out


# --------------------------------------------------------------------------
# O TRIADOR
# --------------------------------------------------------------------------

class Triador:
    """Classificador + politica de triagem. A politica e separada do modelo."""

    def __init__(self, kappa: int = KAPPA, margem_minima: float = MARGEM_MINIMA,
                 sensiveis: set[str] | None = None, verbose: bool = False):
        self.kappa = kappa
        self.piso = kappa / (1 + kappa)
        self.margem_minima = margem_minima
        self.sensiveis = CATEGORIAS_SENSIVEIS if sensiveis is None else sensiveis
        self.limiares = limiares_da_curva(CURVA_JSON, self.piso)

        dados = achar_pasta_dados()
        itsm = pd.read_csv(dados / "all_tickets_processed_improved_v3.csv")
        itsm["Document"] = itsm["Document"].astype(str)
        i_tr, i_te = train_test_split(
            np.arange(len(itsm)), test_size=FRACAO_TESTE,
            random_state=SEMENTE, stratify=itsm["Topic_group"],
        )
        # mesmo split e mesmos hiperparametros do bloco 3: os limiares medidos
        # la so valem se o modelo aqui for o mesmo modelo.
        self.vetor = TfidfVectorizer(min_df=3, ngram_range=(1, 2),
                                     sublinear_tf=True, strip_accents="unicode")
        Xtr = self.vetor.fit_transform(itsm["Document"].to_numpy()[i_tr])
        self.modelo = LogisticRegression(max_iter=1000, C=4.0,
                                         random_state=SEMENTE, n_jobs=-1)
        self.modelo.fit(Xtr, itsm["Topic_group"].to_numpy()[i_tr])
        self.classes = list(self.modelo.classes_)
        self._teste = (itsm["Document"].to_numpy()[i_te],
                       itsm["Topic_group"].to_numpy()[i_te])
        if verbose:
            print(f"  modelo treinado em {len(i_tr):,} documentos")

    # -- decisao unitaria --------------------------------------------------

    def _decidir(self, proba: np.ndarray) -> Decisao:
        ordem = np.argsort(-proba)
        c1, c2 = self.classes[ordem[0]], self.classes[ordem[1]]
        p1, p2 = float(proba[ordem[0]]), float(proba[ordem[1]])
        margem = p1 - p2
        tau = self.limiares[c1]["tau"]

        # R1 — categoria sensivel vence tudo, inclusive confianca alta
        if c1 in self.sensiveis:
            return Decisao(c1, p1, "aprovacao",
                           f"categoria sensivel: '{c1}' concede privilegio; "
                           "exige aprovacao humana [decisao de processo]",
                           tau, c2, margem)

        # R2 — abstencao por empate no topo
        if margem < self.margem_minima:
            return Decisao(c1, p1, "humano",
                           f"empate no topo: '{c1}' e '{c2}' distam {margem:.3f} "
                           f"(<{self.margem_minima}); precisao da classe nao cobre este caso",
                           tau, c2, margem)

        # R3 — limiar por classe vindo da curva medida
        if not self.limiares[c1]["automatizavel"]:
            return Decisao(c1, p1, "humano",
                           f"classe '{c1}' nunca alcanca p*={self.piso:.1%} "
                           "na curva medida: nao e auto-roteavel em nenhum limiar",
                           tau, c2, margem)
        if p1 < tau:
            return Decisao(c1, p1, "humano",
                           f"confianca {p1:.3f} abaixo do limiar medido tau={tau:.2f} "
                           f"de '{c1}' (piso p*={self.piso:.1%})",
                           tau, c2, margem)

        # R4 — auto-roteado
        return Decisao(c1, p1, "auto",
                       f"auto-ROTEADO para a fila '{c1}': confianca {p1:.3f} "
                       f">= tau={tau:.2f}, margem {margem:.3f} ok. "
                       "Nao resolvido — agente atende normalmente.",
                       tau, c2, margem)

    def rotear(self, texto: str) -> Decisao:
        """Decisao para um chamado."""
        return self._decidir(self.modelo.predict_proba(self.vetor.transform([texto]))[0])

    def rotear_lote(self, textos) -> list[Decisao]:
        P = self.modelo.predict_proba(self.vetor.transform(textos))
        return [self._decidir(p) for p in P]


# ==========================================================================
# EXECUCAO: politica, avaliacao e demonstracao
# ==========================================================================

if __name__ == "__main__":
    sys.stdout = Tee(SAIDA)

    titulo("BLOCO 4 — TRIAGEM: ROTEADOR COM POLITICA EXPLICITA")
    print(f"""
rota "auto" = auto-ROTEADO. Nunca auto-resolvido. Ver SECAO 1B do bloco 1:
a medicao do bloco 3 licencia roteamento e nada alem disso. Nenhuma rota
deste arquivo fecha ticket ou responde cliente.

Politica:
  kappa = M/T          : {KAPPA}          [premissa arbitrada, sem fonte]
  piso p* = k/(1+k)    : {PISO_PRECISAO:.1%}      derivado, forma fechada
  margem minima        : {MARGEM_MINIMA}       [convencao do analista]
  categorias sensiveis : {sorted(CATEGORIAS_SENSIVEIS)}
                         [decisao de processo, nao dos dados]
""")

    tri = Triador()

    titulo("PARTE 1 — LIMIARES POR CLASSE, DERIVADOS DA CURVA MEDIDA", "-")
    print("""
tau_c = menor limiar cuja precisao medida alcanca o piso. Menor e nao maior:
dentro da regiao que respeita p*, queremos a maior cobertura possivel.
Nenhum destes numeros foi escolhido a mao — todos saem de curva_medida.json.
""")
    tl = pd.DataFrame([
        {"classe": c, "tau_c": v["tau"], "cobertura em tau_c": round(v["cobertura"], 3),
         "precisao em tau_c": round(v["precisao"], 3),
         "auto-rotavel": "sim" if v["automatizavel"] else "NAO",
         "sensivel": "SIM" if c in CATEGORIAS_SENSIVEIS else ""}
        for c, v in sorted(tri.limiares.items())
    ])
    print(tl.to_string(index=False))

    titulo("PARTE 2 — AVALIACAO DA POLITICA NO CONJUNTO DE TESTE", "-")
    textos_te, y_te = tri._teste
    decisoes = tri.rotear_lote(textos_te)
    df = pd.DataFrame([asdict(d) for d in decisoes])
    df["real"] = y_te
    df["acertou"] = df["categoria"] == df["real"]

    print(f"\nchamados avaliados: {len(df):,}\n")
    resumo = df.groupby("rota").agg(
        chamados=("rota", "size"),
        **{"% do total": ("rota", lambda s: round(len(s) / len(df) * 100, 1))},
        precisao=("acertou", "mean"),
    ).sort_values("chamados", ascending=False)
    resumo["precisao"] = resumo["precisao"].round(3)
    print(resumo.to_string())

    auto = df[df.rota == "auto"]
    print(f"""
LEITURA

  auto-roteados     : {len(auto):,} ({len(auto) / len(df):.1%} do volume)
  precisao no auto  : {auto.acertou.mean():.1%}   contra piso p* = {PISO_PRECISAO:.1%}
  margem de folga   : {auto.acertou.mean() - PISO_PRECISAO:+.1%}

  A taxa de automacao NAO e 100%, e nao foi forcada a nao ser: e o que sobra
  depois de as quatro regras cortarem. As tres fatias de humano tem motivos
  diferentes e mensuraveis, e e isso que a coluna 'motivo' registra em cada
  decisao individual.
""")

    print("DISTRIBUICAO DE MOTIVO PARA NAO AUTOMATIZAR")
    nao_auto = df[df.rota != "auto"].copy()
    nao_auto["tipo"] = np.where(
        nao_auto.rota == "aprovacao", "R1 categoria sensivel",
        np.where(nao_auto.motivo.str.startswith("empate"), "R2 empate no topo",
                 "R3 abaixo do limiar da classe"))
    tm = nao_auto.groupby("tipo").agg(
        chamados=("tipo", "size"),
        **{"% do total": ("tipo", lambda s: round(len(s) / len(df) * 100, 1))},
        **{"precisao da sugestao": ("acertou", "mean")},
    )
    tm["precisao da sugestao"] = tm["precisao da sugestao"].round(3)
    print(tm.to_string())
    print("""
  'precisao da sugestao' e quanto a maquina teria acertado se tivesse
  roteado sozinha esses casos. Comparar com o piso mostra se a regra esta
  cortando o que devia:
    - se ficar MUITO abaixo do piso, a regra esta salvando erro caro;
    - se ficar acima do piso, a regra esta conservadora demais e custa
      cobertura sem comprar seguranca.
  Este e o mostrador para calibrar a politica sem tocar no modelo.
""")

    titulo("PARTE 3 — O CUSTO DA REGRA R1, MEDIDO E NAO ESTIMADO", "-")
    sens = df[df.rota == "aprovacao"]
    print(f"""
  A regra R1 e a unica que NAO vem dos dados. Ela e decisao de processo, e
  por isso o minimo e medir o que ela custa em vez de deixar implicito:

    chamados desviados para aprovacao : {len(sens):,} ({len(sens) / len(df):.1%} do volume)
    precisao que a maquina teria tido : {sens.acertou.mean():.1%}
    acima do piso p*={PISO_PRECISAO:.1%}?               : {'sim' if sens.acertou.mean() >= PISO_PRECISAO else 'nao'}

  Leitura honesta: a maquina classificaria estes casos {'bem' if sens.acertou.mean() >= PISO_PRECISAO else 'mal'}. A regra
  {'nao existe porque a precisao e ruim — existe apesar de a precisao ser boa.' if sens.acertou.mean() >= PISO_PRECISAO else 'coincide com uma regiao de precisao baixa.'}
  {'Ela troca cobertura por controle de risco, deliberadamente. Quem discordar' if sens.acertou.mean() >= PISO_PRECISAO else 'Isso enfraquece o argumento de que ela e puramente sobre risco.'}
  {'dessa troca move CATEGORIAS_SENSIVEIS e reroda — o custo esta na mesa.' if sens.acertou.mean() >= PISO_PRECISAO else ''}
""")

    titulo("PARTE 4 — DEMONSTRACAO EM CHAMADOS REAIS DO TESTE", "-")
    print("\nUm exemplo de cada rota, tirado do conjunto de teste:\n")
    for rota in ["auto", "humano", "aprovacao"]:
        sub = df[df.rota == rota]
        if sub.empty:
            continue
        i = sub.index[0]
        print(f"  ---- rota: {rota} ----")
        print(f"  texto : {textos_te[i][:150]}")
        print(f"  real  : {y_te[i]}")
        print(f"  {decisoes[i]}")
        print()

    politica = {
        "origem": "04_triagem.py",
        "kappa": KAPPA,
        "piso_precisao": PISO_PRECISAO,
        "margem_minima": MARGEM_MINIMA,
        "categorias_sensiveis": sorted(CATEGORIAS_SENSIVEIS),
        "limiares_por_classe": tri.limiares,
        "resultado_teste": {
            "n": int(len(df)),
            "taxa_auto": float((df.rota == "auto").mean()),
            "precisao_auto": float(auto.acertou.mean()),
        },
        "escopo": "auto-ROTEAMENTO apenas; auto-resolucao nao avaliavel sem resolution_code",
    }
    POLITICA_JSON.write_text(json.dumps(politica, indent=2, ensure_ascii=False),
                             encoding="utf-8")

    titulo("FIM — BLOCO 4")
    print(f"politica salva em: {POLITICA_JSON.name}")
    print(f"saida salva em: {SAIDA}")
    sys.stdout.flush()
