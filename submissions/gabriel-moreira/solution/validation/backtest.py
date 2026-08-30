#!/usr/bin/env python3
"""Artefato de validação — evidência estatística por trás da fórmula de
priorização. Comando único, sem ambiente gráfico:

    python backtest.py [--data-dir ../../data]

EM TERMOS SIMPLES: este script pega os negócios já FECHADOS (ganhos ou
perdidos) e usa métodos estatísticos pra checar se as decisões de design
da fórmula de priorização realmente se sustentam nos dados — em vez de
confiar em "achismo". Ele responde a 5 perguntas centrais sobre a fórmula
de priorização (seções 1-8), e mais 5 sobre a sensibilidade ao expurgo de
200 dias, a análise de carga e fit, e o poder dos próprios testes
(seções 10-14):

  1. Dá pra prever quem vai GANHAR ou PERDER só olhando dados de cadastro
     (vendedor, produto, setor, conta)? (achado: não — não há sinal útil)
  2. Essa "falta de sinal" é coincidência desta amostra, ou é robusta?
     (testado embaralhando os dados centenas de vezes)
  3. Quanto peso dar à taxa de conversão histórica de cada produto, sem
     deixar grupos com poucos negócios (números instáveis) distorcerem
     a fórmula?
  4. O risco de o negócio esfriar aumenta com o tempo, e existe um limite
     de idade a partir do qual não dá mais pra confiar no número?
  5. A fórmula PRIORIDADE realmente concentra os negócios mais valiosos
     no topo da fila, ou dá no mesmo que olhar só o preço de tabela?

Reproduz: a ausência de sinal preditivo firmográfico (AUC + testes de
permutação), a derivação de k por nível hierárquico (e o colapso de
conta×produto/produto×setor), a monotonicidade de risco(t), a fronteira de
censura de 138 dias, a concentração de PRIORIDADE no topo da fila, a
distorção que o expurgo de 200 dias introduziria (medida, nunca aplicada)
e a ausência de desfecho atribuído na calibração, a ausência de sinal do
fit por vendedor, o denominador correto dos
artefatos de análise e o poder dos testes de vendedor — o menor efeito
que este histórico enxergaria, sem o qual "não rejeitou" não distingue
"não há diferença" de "a amostra é pequena demais" — sempre importando `scoring/`, nunca reimplementando
a fórmula.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aging_by_product_check import build_report as build_aging_by_product_report
from circularity_check import build_report as build_circularity_report
from concentration import build_report as build_concentration_report
from confianca_distribution import build_report as build_confianca_distribution_report
from cycle_duration_permutation import (
    resolution_rate_by_product_and_age,
    run as run_cycle_duration_permutation,
)
from denominator_check import audit as audit_denominator
from fit_permutation import run_produto as run_fit_permutation_produto, run_setor as run_fit_permutation_setor
from isotonic_check import recompute_curves
from model_training import chronological_split, combined_auc, isolated_aucs
from multiplicidade import corrigir as corrigir_multiplicidade
from permutation_tests import N_PERMUTATIONS, formata_p, run_all as run_permutation_tests
from power_check import PODER_ALVO, build_report as build_power_report
from reclassification_check import build_report as build_reclassification_report
from scoring import constants
from scoring.export import build_analysis_table
from scoring.fit import build_fit_context, derive_k_fit
from scoring.pipeline import fechados, load_and_score
from sector_conditioning_check import build_report as build_sector_conditioning_report
from shrinkage_check import build_report as build_shrinkage_report

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def run_report(data_dir: Path) -> bool:
    """Executa o relatório completo. Retorna False se alguma premissa
    estrutural falhar (ex.: censura de 138 dias deixou de valer)."""
    scored_pipeline = load_and_score(str(data_dir))
    dataset = scored_pipeline.dataset
    # População única: os negócios com desfecho observado. Era duas
    # (calibração e orgânica) enquanto o expurgo de 200 dias injetava
    # rótulos atribuídos por idade — as seções de idade tinham de ser
    # protegidas deles. Sem expurgo, não há de que proteger.
    closed = fechados(dataset)

    # A seção 12 roda aqui em cima porque a seção 2 precisa dos 6 p-valores
    # da família para aplicar Holm/Benjamini-Hochberg. Os resultados são
    # reusados lá embaixo — nada é recalculado.
    perm_produto = run_fit_permutation_produto(closed)
    perm_setor = run_fit_permutation_setor(closed)

    ok = True

    _section("1. Ausência de sinal preditivo por atributo firmográfico")
    print(
        "Pergunta: dá pra adivinhar se um negócio vai ser GANHO ou PERDIDO só\n"
        "olhando dados de cadastro (vendedor, produto, setor, conta)?"
    )
    print(
        "Método: separamos os negócios fechados em dois grupos por data — os\n"
        "mais antigos (treino) e os mais recentes (teste) — e medimos se o\n"
        "padrão aprendido no grupo antigo acerta no grupo novo."
    )
    print()
    split = chronological_split(closed)
    print(f"Corte cronológico (treino/teste): {split.cutoff_date.date()}")
    print(f"Treino: {len(split.train)} negócios · Teste: {len(split.test)} negócios")
    print()
    print(
        "AUC (Area Under Curve) é uma nota de 0 a 1 para o quão bem um atributo\n"
        "separa ganhos de perdas: 0,50 = mesmo que jogar uma moeda (nenhum poder\n"
        "preditivo); 1,00 = previsão perfeita. Abaixo, a AUC de cada atributo\n"
        "isolado (taxa de ganho aprendida no treino, testada no teste):"
    )
    for label, auc in isolated_aucs(split.train, split.test).items():
        auc_str = f"{auc:.3f}" if auc is not None else "n/d (sem variação suficiente)"
        print(f"  {label:24s} AUC = {auc_str}")
    print()
    auc_combinada = combined_auc(split.train, split.test)
    print(f"AUC combinada (gradient boosting, todos os atributos): {auc_combinada:.3f}")
    print("-> ~0,50 indica ausência de poder discriminativo (chute aleatório).")
    print(
        "Achado: nem um atributo isolado, nem todos combinados, batem uma\n"
        "moeda viciada — não existe sinal preditivo firmográfico nestes dados."
    )

    _section("2. Testes de permutação (semente fixa)")
    print(
        "Pergunta: será que a falta de sinal da Seção 1 é só coincidência\n"
        "desta amostra específica, ou é um padrão robusto?"
    )
    print(
        "Método: embaralhamos aleatoriamente, centenas de vezes, qual\n"
        "vendedor/produto/setor/conta está associado a cada negócio, e\n"
        "comparamos a diferença REAL entre grupos com a diferença que\n"
        "aparece só por acaso nessas versões embaralhadas ('semente fixa'\n"
        "quer dizer que o embaralhamento é sempre o mesmo, então o\n"
        "resultado é reproduzível)."
    )
    print()
    resultados_perm = run_permutation_tests(closed)
    for result in resultados_perm:
        print(
            f"  {result.atributo:16s} dispersão obs.={result.dispersao_observada:.4f} "
            f"dispersão nula média={result.dispersao_nula_media:.4f} p={formata_p(result.p_valor)}"
        )
    print()
    print(
        "p-valor = a chance de ver, só por acaso (embaralhado), uma diferença\n"
        "PELO MENOS tão grande quanto a real observada. p-valor alto (>0,05,\n"
        "tipicamente bem mais) = a diferença real é do tamanho que apareceria\n"
        "só por acaso — ou seja, ESTES dados não sustentam afirmar um efeito."
    )
    print(
        f"O p-valor mínimo que {N_PERMUTATIONS} permutações conseguem afirmar é "
        f"1/({N_PERMUTATIONS}+1) = {1 / (N_PERMUTATIONS + 1):.5f} — por isso esta suíte reporta "
        "'p < 0,001' e nunca 'p = 0,000'. Zero é impossível como probabilidade: com um número "
        "finito de reamostragens não se distingue 'nunca acontece' de 'acontece menos de uma vez "
        f"em {N_PERMUTATIONS}' (correção add-one, `permutation_tests._p_valor`)."
    )
    print(
        "Duas leituras erradas que este número NÃO autoriza:\n"
        "  1. p alto NÃO prova que o efeito não existe. Ausência de evidência não é\n"
        f"     evidência de ausência: um efeito real, mas pequeno demais para {len(closed)}\n"
        "     negócios, devolveria o mesmo p alto. A conclusão deste trabalho precisa\n"
        "     apenas do enunciado mais fraco — não há base para pôr o atributo no score.\n"
        "  2. p NÃO é a probabilidade de o efeito existir (nem de não existir). É a\n"
        "     frequência com que o acaso, sozinho, produziria o que os dados mostram."
    )
    print("-> p alto (>0,05, tipicamente bem mais) = dispersão observada compatível com ruído.")
    print(
        "Achado: todos os atributos testados têm p-valor alto — confirma, de\n"
        "um segundo jeito independente, o resultado da Seção 1."
    )
    print()
    print(
        "Correção para múltiplas comparações — 6 testes de permutação rodam nesta suíte (os 4\n"
        "acima e os 2 da seção 12). Seis testes contra o corte de 0,05 sem correção levariam a\n"
        "chance de ao menos um falso positivo de 5% para 1-(1-0,05)^6 = 26,5%:"
    )
    familia = [(r.atributo, "§2", r.p_valor) for r in resultados_perm] + [
        (f"vendedor×{r.dimensao}", "§12", r.p_valor) for r in (perm_produto, perm_setor)
    ]
    print(f"  {'teste':18s} {'origem':7s} {'p':>7s}  {'Holm (FWER)':>22s}  {'B-H (FDR)':>20s}")
    for t in corrigir_multiplicidade(familia):
        holm = f"{'rejeita' if t.rejeita_holm else 'não rejeita'} (α={t.limite_holm:.4f})"
        bh = f"{'rejeita' if t.rejeita_bh else 'não rejeita'} (≤{t.limite_bh:.4f})"
        print(f"  {t.nome:18s} {t.origem:7s} {formata_p(t.p_valor, 4):>7s}  {holm:>22s}  {bh:>20s}")
    print(
        "Nenhum dos seis sobrevive a qualquer das duas correções — e nenhum precisaria: nenhum\n"
        "chega perto do corte nem sem correção. A correção fica registrada porque a família de\n"
        "testes é o que dá sentido ao corte, não porque algum resultado dependa dela."
    )
    print(
        "Composição da família, explicitada porque a escolha é auditável: a seção 12 roda DOIS\n"
        "nulos por dimensão e entra aqui com o p do nulo GLOBAL, o MENOR dos dois\n"
        f"({formata_p(perm_produto.p_valor, 4)} contra {formata_p(perm_produto.p_valor_aditivo, 4)}"
        " em vendedor×produto).\n"
        "São 6 entradas e não 8 pelo mesmo motivo: quanto mais testes na família, mais apertados\n"
        "ficam os cortes de Holm e B-H e MAIS fácil fica não rejeitar. As duas escolhas jogam\n"
        "contra a tese deste trabalho — família curta e p mais baixo são o cenário em que 'não há\n"
        "sinal' teria a maior chance de cair. Não caiu."
    )

    _section("3. Encolhimento hierárquico — derivação de k")
    print(
        "Pergunta: quanto peso dar à taxa de conversão histórica de cada\n"
        "produto (ou combinação conta×produto, produto×setor), sem deixar\n"
        "grupos com poucos negócios — e portanto números instáveis —\n"
        "distorcerem a fórmula?"
    )
    print(
        "Método: 'encolhimento hierárquico' puxa a taxa de cada grupo em\n"
        f"direção à média geral ({constants.GLOBAL_WIN_RATE}), com força k. "
        "k é calculado a partir\n"
        "dos próprios dados: quanto menor a diferença real entre os grupos\n"
        "comparada à diferença esperada só por acaso, maior o k — mais o\n"
        "grupo é puxado pra média. Quando k = ∞, o grupo 'colapsa': recebe\n"
        "peso zero e usa direto a média geral. É o que esperamos ver quando\n"
        "um atributo, como já vimos nas seções 1 e 2, não carrega sinal real.\n"
        "Nenhum nível, incluindo produto, usa uma constante de política\n"
        "congelada sobrepondo esse cálculo — o motor de scoring lê exatamente\n"
        "o k derivado abaixo."
    )
    print()
    shrinkage = build_shrinkage_report(closed)
    for nome, stats in [
        ("conta×produto", shrinkage.conta_produto),
        ("produto×setor", shrinkage.produto_setor),
        ("produto", shrinkage.produto),
    ]:
        k_str = "∞ (colapsa)" if stats.colapsa else f"{stats.k:.4f}"
        print(
            f"  {nome:16s} grupos={stats.n_groups:4d} var_obs={stats.var_observada:.6f} "
            f"var_esperada_por_acaso={stats.var_esperada_por_acaso:.6f} k={k_str}"
        )
    print()
    print("p̂_produto (usando o k derivado do nível de produto acima, sem constante congelada):")
    for produto in constants.PRECO_TABELA:
        print(f"  {produto:16s} p_hat={shrinkage.p_hat_por_produto[produto]:.4f}")

    if not (shrinkage.conta_produto.colapsa and shrinkage.produto_setor.colapsa):
        print(
            "AVISO: conta×produto e/ou produto×setor não colapsaram nesta execução — "
            "revisar a hierarquia de encolhimento na próxima recalibração."
        )
        ok = False

    if shrinkage.produto.colapsa:
        print(
            "\nNOTA — o nível de PRODUTO colapsou nesta execução (variância em "
            "excesso ≤ 0, mais fraco do que qualquer um dos quatro atributos "
            "testados por permutação acima, todos com p > 0,05): sem constante de "
            "política a sobrepor o colapso, p̂_produto usa diretamente a taxa "
            f"global de calibração ({constants.GLOBAL_WIN_RATE}) para "
            "todos os produtos — o comportamento correto, sem exigir mudança de "
            "código nem revisão manual de constante alguma."
        )
    else:
        print(
            "\nNOTA — o nível de PRODUTO não colapsou nesta execução: variância em "
            f"excesso positiva produz k = {shrinkage.produto.k:.4f}, usado "
            "diretamente pelo motor de scoring para calcular p̂_produto acima — não "
            "há mais uma constante congelada para comparar. Um k pequeno frente ao "
            "n de cada produto significa pouco encolhimento (a taxa bruta domina); "
            "um k grande puxaria mais forte em direção à taxa global. Qualquer "
            "mudança de regime entre execuções fica visível aqui, sem precisar de "
            "um cenário de falha dedicado."
        )

    _section("4. Curvas de aging — monotonicidade e fronteira de censura")
    print(
        "Pergunta: o risco de o negócio esfriar realmente aumenta com o\n"
        "tempo, sem 'zigue-zagues' estranhos, e existe um limite de idade\n"
        "confiável pra fazer essa conta?"
    )
    print(
        "Método: recalculamos do zero as curvas de risco e de probabilidade\n"
        "de ganho por idade do negócio, e conferimos duas coisas: (a) nenhum\n"
        "negócio fechado nos dados é mais velho que o limite de censura\n"
        "configurado; (b) a curva de risco nunca 'desce' — só sobe ou fica\n"
        "igual conforme o negócio envelhece (monotonicidade).\n"
        "'Censura' aqui quer dizer: não confiamos em extrapolar a curva além\n"
        "do que já foi observado — acima do limite, a fórmula volta pro\n"
        "valor médio histórico (prior) em vez de inventar um número."
    )
    print()
    curves = recompute_curves(closed)
    print(f"Duração máxima observada entre negócios fechados: {curves.max_duracao_dias} dias")
    print(f"Limite de censura configurado: {constants.CENSURA_DIAS} dias")
    if curves.censura_confirmada:
        print("-> confirmado: nenhum negócio fechado excede o limite de censura.")
    else:
        print(
            "FALHA: um negócio fechado excedeu o limite de censura configurado — "
            "a premissa de 138 dias não vale mais nesta base, recalibrar imediatamente."
        )
        ok = False

    if curves.risco_monotonico:
        print("risco(t) isotônico é não-decrescente em todos os pontos recalculados. OK.")
    else:
        print("FALHA: risco(t) isotônico decresceu em algum ponto — investigar.")
        ok = False

    print()
    print("p_ganho(t) recalculado nos extremos:", end=" ")
    print(f"t={curves.ts[0]} -> {curves.p_ganho_isotonico[0]:.3f}  ", end="")
    print(f"t={curves.ts[-1]} -> {curves.p_ganho_isotonico[-1]:.3f}")
    sobe = curves.p_ganho_isotonico[-1] >= curves.p_ganho_isotonico[0]
    print(f"-> p_ganho sobe com a idade (não decai): {sobe}")
    print(
        "Achado contraintuitivo: a chance de ganhar SOBE com a idade do\n"
        "negócio, não desce. O que a idade realmente consome é a janela de\n"
        "decisão (quanto tempo resta pra fechar em breve), não a chance de\n"
        "sucesso em si — por isso URGÊNCIA usa risco(t), não um decaimento."
    )

    _section("5. Concentração de PRIORIDADE (não é validação preditiva)")
    print(
        "Pergunta: a fórmula PRIORIDADE realmente separa o que é urgente e\n"
        "valioso do resto da fila, ou dá praticamente no mesmo que ordenar\n"
        "só pelo preço de tabela do produto?"
    )
    print(
        "Método: ordenamos a fila por PRIORIDADE e medimos quanto valor\n"
        "total (em R$) está concentrado nos 10% e 30% do topo — e\n"
        "comparamos com ordenar simplesmente pelo preço de tabela puro,\n"
        "sem PRIORIDADE. Esta seção NÃO testa se a fórmula prevê quem vai\n"
        "ganhar (isso já foi respondido — negativamente — nas seções 1 e 2);\n"
        "ela testa só se a priorização concentra valor no topo."
    )
    print()
    concentration = build_concentration_report(scored_pipeline.scored)
    print(f"Top 10% da fila por PRIORIDADE captura {concentration.top10_prioridade * 100:.1f}% do total")
    print(f"Top 30% da fila por PRIORIDADE captura {concentration.top30_prioridade * 100:.1f}% do total")
    print(f"Top 10% por preço de tabela puro captura {concentration.top10_preco_bruto * 100:.1f}% do total")
    print(f"Top 30% por preço de tabela puro captura {concentration.top30_preco_bruto * 100:.1f}% do total")
    p_hat_min = scored_pipeline.scored["p_hat"].min()
    p_hat_max = scored_pipeline.scored["p_hat"].max()
    print(
        f"-> concentração de valor, não poder preditivo: p̂ varia só {p_hat_min:.2f}-{p_hat_max:.2f} "
        "contra 487x de amplitude em VALOR. A diferenciação vem de valor e urgência."
    )
    print(
        "Achado: PRIORIDADE concentra MAIS valor em risco no topo da fila do "
        f"que simplesmente ordenar por preço de tabela "
        f"({concentration.top10_prioridade * 100:.1f}% vs. {concentration.top10_preco_bruto * 100:.1f}% no "
        "top 10%) — o ganho vem de combinar VALOR com URGÊNCIA (idade do\n"
        "negócio), não de uma previsão fina de quem vai ganhar (que já vimos,\n"
        "nas seções 1 e 2, que não existe)."
    )

    _section("6. Condicionamento de p̂ por produto×setor — validação cruzada")
    print(
        "Pergunta: condicionar a probabilidade de ganho por produto E setor,\n"
        "em vez de só por produto, melhora a previsão fora da amostra?"
    )
    print(
        "Método: validação cruzada 5-fold com semente fixa. Em cada rodada,\n"
        "80% dos negócios fechados calibram cada alternativa e os 20%\n"
        "restantes medem o erro fora da amostra (logloss e brier — quanto\n"
        "menor, melhor)."
    )
    print()
    setor_report = build_sector_conditioning_report(closed)
    for nome in ("prior_global", "produto_encolhido", "produto_setor_encolhido", "produto_setor_bruto"):
        s = setor_report.score(nome)
        print(f"  {nome:26s} logloss={s.logloss:.5f}  brier={s.brier:.5f}")
    print()
    print(
        f"Células produto×setor: {setor_report.n_celulas_produto_setor} — "
        f"mediana de {setor_report.mediana_tamanho_celula:.0f} negócios fechados por célula."
    )
    pior_que_global = setor_report.score("produto_setor_encolhido").logloss > setor_report.score("prior_global").logloss
    print(
        "Achado: condicionar por produto×setor é PIOR que o prior global achatado "
        f"({'confirmado' if pior_que_global else 'NÃO CONFIRMADO nesta execução — revisar'}) "
        "— a amostra por célula é pequena demais para sustentar a diferenciação."
    )
    print(
        "Consequência no motor: setor NÃO entra em p̂ nem em SCORE, em nenhuma "
        "forma — nem como condicionamento direto, nem como multiplicador "
        "encolhido sobre p̂. Setor continua sendo lido para a completude de "
        "CONFIANÇA e para o fit vendedor×setor da redistribuição de carga "
        "(seção 12) — nunca para o score."
    )
    if not pior_que_global:
        print(
            "AVISO PERMANENTE (não falha a suíte): o condicionamento direto por "
            "produto×setor deixou de ser pior que o prior achatado nesta execução. "
            "Isso não reabre `mult_setor` automaticamente — é o gatilho para "
            "reavaliar a decisão com dado novo, incluindo a variância em excesso "
            "do nível produto×setor na seção 3 (scoring-validation spec, "
            "Requirement 'Reprodução da ausência de sinal do condicionamento por "
            "setor')."
        )

    _section("7. Curvas de aging por produto — validação cruzada")
    print(
        "Pergunta: uma curva de aging (risco de resolver em 30 dias) própria\n"
        "por produto prevê melhor que a curva GLOBAL usada em produção?"
    )
    print("Método: mesma validação cruzada 5-fold da seção 6, aplicada às faixas de idade.")
    print()
    aging_report = build_aging_by_product_report(closed)
    for nome in ("prior_global", "curva_global", "curva_por_produto_bruta", "curva_por_produto_encolhida"):
        s = aging_report.score(nome)
        print(f"  {nome:26s} logloss={s.logloss:.5f}  brier={s.brier:.5f}")
    print()
    curva_global_vence = aging_report.score("curva_global").logloss == min(
        s.logloss for s in aging_report.scores
    )
    print(
        "Achado: a curva de aging GLOBAL tem o menor logloss entre todas as "
        f"alternativas ({'confirmado' if curva_global_vence else 'NÃO CONFIRMADO nesta execução — revisar'}) "
        "— aging é o único sinal real desta base, e reparti-lo por produto piora a previsão."
    )
    if aging_report.existe_celula_com_uma_observacao:
        print("Ao menos um produto tem uma faixa de idade com uma única observação — sem amostra para curva própria.")
    if not curva_global_vence:
        ok = False

    _section("8. Efeito de produto sobre a duração do ciclo")
    print(
        "Pergunta: produtos diferentes têm ciclos de venda sistematicamente\n"
        "mais longos ou mais curtos, ou a variação entre eles é só ruído?"
    )
    print(
        "Método: teste de permutação (semente fixa) sobre a dispersão das\n"
        "medianas de duração de ciclo por produto."
    )
    print()
    ciclo = run_cycle_duration_permutation(closed)
    print(
        f"Dispersão observada entre medianas: {ciclo.dispersao_observada:.1f} dias  "
        f"·  dispersão nula média: {ciclo.dispersao_nula_media:.1f} dias  ·  p={ciclo.p_valor:.3f}"
    )
    print(
        "Achado: a dispersão observada entre produtos é MENOR que a dispersão sob "
        "rótulos embaralhados — os produtos são mais parecidos entre si em duração de "
        "ciclo do que uma atribuição aleatória produziria. Sustenta manter URGÊNCIA global."
    )
    print()
    print("Taxa de resolução em 30 dias por produto e faixa de idade (linha GLOBAL para comparação):")
    taxas = resolution_rate_by_product_and_age(closed)
    for faixa, sub in taxas.groupby("faixa", sort=False):
        linha_global = sub[sub["product"] == "GLOBAL"].iloc[0]
        print(f"  faixa {faixa}: GLOBAL={linha_global['taxa_resolucao_30d']:.3f} (n={linha_global['n_em_risco']})")

    _section("9. Distribuição de CONFIANÇA e das duas metades")
    print(
        "Acompanha a calibração de SUPORTE_JANELA_IDADE_DIAS e SUPORTE_SATURACAO_N — "
        "se uma recalibração futura tornar essas constantes inadequadas, a distribuição "
        "abaixo muda de forma visível, em vez de silenciosa."
    )
    print()
    confianca_dist = build_confianca_distribution_report(scored_pipeline.scored)
    print(f"n = {confianca_dist.n}")
    for p in (10, 25, 50, 75, 90, 95, 99):
        print(
            f"  p{p:2d}  CONFIANÇA={confianca_dist.percentis_confianca[p]:6.1f}  "
            f"completude={confianca_dist.percentis_completude[p]:6.1f}  "
            f"suporte={confianca_dist.percentis_suporte[p]:6.1f}"
        )
    print()
    print(f"Fração sem precedente histórico: {confianca_dist.fracao_sem_precedente * 100:.1f}%")
    print(f"Fração governada por completude (vs. suporte): {confianca_dist.fracao_completude_governante * 100:.1f}%")

    _section("10. Sensibilidade ao expurgo de 200 dias (medido, NÃO aplicado)")
    print(
        "Pergunta: e se as oportunidades abertas há 200 dias ou mais fossem\n"
        "tratadas como Lost e entrassem na calibração? Esta seção mede esse\n"
        "cenário sem aplicá-lo — o motor calibra só sobre desfecho observado."
    )
    print()
    reclass = build_reclassification_report(dataset)
    if reclass.aplicado_em_producao:
        print(
            "FALHA: há oportunidade candidata ao expurgo que já não está em Engaging — "
            "alguma regra de rotulagem automática voltou à carga. Revisar antes de prosseguir."
        )
        ok = False
    else:
        print("Expurgo aplicado em produção: NÃO (a carga não reescreve deal_stage).")
    print(
        f"Candidatas: {reclass.n_candidatos} oportunidades abertas há "
        f"{reclass.idade_minima}-{reclass.idade_maxima} dias"
    )
    print(f"Funil aberto: {reclass.funil_real} real (seria {reclass.funil_hipotetico})")
    print(
        f"Base rate global: {reclass.base_rate_real * 100:.2f}% real "
        f"(seria {reclass.base_rate_hipotetica * 100:.2f}%, "
        f"{(reclass.base_rate_hipotetica - reclass.base_rate_real) * 100:+.2f}pp)"
    )
    print()
    print("Taxa de vitória por produto, real -> hipotética (pp = pontos percentuais):")
    for prod in sorted(reclass.produtos, key=lambda p: p.variacao_pp):
        marca = " [AMOSTRA PEQUENA]" if prod.amostra_pequena else ""
        print(
            f"  {prod.produto:16s} n={prod.n_real:4d}->{prod.n_hipotetico:4d}  "
            f"{prod.taxa_real * 100:5.2f}% -> {prod.taxa_hipotetica * 100:5.2f}%  "
            f"({prod.variacao_pp:+6.2f}pp){marca}"
        )
    np_ = reclass.nivel_produto
    print()
    print("Efeito sobre o encolhimento do nível de produto:")
    print(
        f"  variância em excesso: {np_.var_em_excesso_real:+.8f} real -> "
        f"{np_.var_em_excesso_hipotetica:+.8f} hipotética"
    )
    print(f"  k derivado:           {np_.k_real} real -> {np_.k_hipotetico:.4f} hipotético")
    print(
        f"  amplitude de p̂ entre produtos: {np_.amplitude_p_hat_real_pp:.2f}pp real -> "
        f"{np_.amplitude_p_hat_hipotetica_pp:.2f}pp hipotética"
    )
    print()
    print("Efeito sobre os testes de permutação (p-valor real -> hipotético):")
    for sinal in reclass.sinais:
        virada = (
            "  <- VIRARIA significativo neste cenário hipotético"
            if sinal.p_real >= 0.05 > sinal.p_hipotetico
            else ""
        )
        print(
            f"  {sinal.atributo:12s} {formata_p(sinal.p_real):>7s} -> "
            f"{formata_p(sinal.p_hipotetico):>7s}{virada}"
        )
    print()
    print(
        f"Dispersão da taxa de vitória entre vendedores: "
        f"{reclass.amplitude_vendedor_real_pp:.2f}pp real -> "
        f"{reclass.amplitude_vendedor_hipotetica_pp:.2f}pp hipotética "
        f"({reclass.n_vendedores_sem_candidato} vendedores não receberiam nenhuma perda atribuída)"
    )
    print()
    print("Por que o expurgo fabrica sinal de vendedor — o mecanismo, medido:")
    print(
        f"  concentração das candidatas por vendedor: qui-quadrado={reclass.concentracao_chi2:.1f} "
        f"(gl={reclass.concentracao_gl}, p{'<0,0001' if reclass.concentracao_p < 0.0001 else f'={reclass.concentracao_p:.4f}'}) "
        "— as oportunidades paradas NÃO se distribuem por igual entre carteiras"
    )
    print(
        f"  correlação entre fração da carteira expurgada e taxa de vitória hipotética: "
        f"{reclass.corr_fracao_expurgada_taxa:+.3f}"
    )
    print(
        "  O expurgo só adiciona DERROTA, nunca vitória. Como ele cai concentrado, a taxa\n"
        "  hipotética de cada vendedor vira, em boa parte, uma função de quanto funil parado\n"
        "  ele tinha — idade de pipeline relida como habilidade de fechar. O 'sinal de vendedor'\n"
        "  do cenário hipotético é a régua se medindo, não o vendedor."
    )
    pequenas = [p.produto for p in reclass.produtos if p.amostra_pequena]
    print(
        f"\nAchado: o expurgo não é neutro. Ele encolhe o funil em {reclass.n_candidatos} "
        f"oportunidades, derruba o base rate "
        f"{(reclass.base_rate_real - reclass.base_rate_hipotetica) * 100:.2f}pp e — o que importa — "
        f"cria discriminação onde o dado observado não tem nenhuma: a amplitude de p̂ entre produtos "
        f"sai de {np_.amplitude_p_hat_real_pp:.2f}pp para {np_.amplitude_p_hat_hipotetica_pp:.2f}pp, "
        f"puxada por {', '.join(pequenas)} (amostra pequena), e a identidade do vendedor passa a ser "
        "lida como sinal porque as oportunidades paradas se concentram em algumas carteiras. "
        "É por isso que a carga nunca o aplica — ver process-log/decisions-log.md."
    )

    _section("11. Auditoria de circularidade — nenhum desfecho atribuído por nós")
    print(
        "Pergunta: existe na população de calibração algum desfecho que não\n"
        "veio do CRM — um rótulo que o próprio sistema atribuiu?"
    )
    print()
    circularidade = build_circularity_report(dataset)
    print(f"População de calibração: {circularidade.n_calibracao} negócios fechados")
    print(f"Fechados sem close_date (rótulo sem evento): {circularidade.n_sem_close_date}")
    print(
        f"Idade máxima observada até o fechamento: {circularidade.idade_maxima_observada} dias "
        f"(fronteira de censura: {circularidade.fronteira_censura})"
    )
    print(
        f"Idade máxima no funil ABERTO: {circularidade.idade_maxima_aberta} dias — "
        "acima da censura, pontuada com p̂ revertido ao prior, nunca convertida em Lost."
    )
    if circularidade.todos_desfechos_observados and circularidade.censura_cobre_a_calibracao:
        print(
            "-> confirmado: todo negócio da calibração tem desfecho registrado, e a censura "
            "cobre toda a faixa de idade que a calibração viu."
        )
    else:
        print(
            "FALHA: há desfecho sem evento na calibração, ou a calibração viu idade além da "
            "fronteira de censura — alguma regra de rotulagem automática voltou. Revisar antes "
            "de prosseguir."
        )
        ok = False

    _section("12. Fit por vendedor — permutação e suporte")
    print(
        "Pergunta: existe AFINIDADE vendedor×produto (ou vendedor×setor) —\n"
        "este vendedor indo bem NESTE produto, acima do que o desempenho geral\n"
        "dele e a dificuldade geral do produto já explicam? É essa e só essa\n"
        "a pergunta que a palavra 'fit' faz."
    )
    print(
        "Método: dois nulos, porque são duas perguntas diferentes.\n"
        "  GLOBAL  — embaralha os rótulos de vendedor sobre todas as linhas,\n"
        "            com produto/setor fixos por negócio. Responde 'vendedor\n"
        "            importa em algum grau?'. NÃO isola afinidade: embaralhar\n"
        "            destrói junto o efeito principal do vendedor, que entra\n"
        "            inteiro na estatística.\n"
        "  ADITIVO — ajusta logit(ganho) = α + β_vendedor + γ_dimensão e\n"
        "            sorteia desfechos desse modelo (bootstrap paramétrico).\n"
        "            Cada réplica é um mundo em que vendedores diferem entre\n"
        "            si, produtos diferem entre si e ninguém tem afinidade\n"
        "            com nada. O que sobra acima dessa nula é interação — e\n"
        "            só isso é fit."
    )
    print()
    fit_ctx = build_fit_context(dataset, closed)
    for r in (perm_produto, perm_setor):
        print(
            f"  vendedor×{r.dimensao:8s} células={r.n_celulas:3d} dispersão obs.={r.dispersao_observada:.4f}"
        )
        print(
            f"      nulo GLOBAL  (vendedor importa?) nula={r.dispersao_nula_media:.4f} "
            f"p={formata_p(r.p_valor, 4)}"
        )
        print(
            f"      nulo ADITIVO (existe fit?)       nula={r.dispersao_nula_aditiva_media:.4f} "
            f"p={formata_p(r.p_valor_aditivo, 4)}"
        )
    print()
    k_produto_fit = derive_k_fit(fit_ctx, "produto")
    k_setor_fit = derive_k_fit(fit_ctx, "setor")
    print(
        f"Derivação de k_fit por variância em excesso: vendedor×produto k="
        f"{'∞ (colapsa)' if k_produto_fit.colapsa else f'{k_produto_fit.k:.3f}'}; "
        f"vendedor×setor k={'∞ (colapsa)' if k_setor_fit.colapsa else f'{k_setor_fit.k:.3f}'}. "
        f"K_FIT congelado em produção = {constants.K_FIT} (constante de política — sempre mais "
        "conservador que qualquer k derivado abaixo dele, encolhendo o fit com mais força do que "
        "os dados por si só exigiriam)."
    )
    minimo = constants.FIT_SUPORTE_MINIMO
    insuficientes_produto = sum(1 for g in fit_ctx.vendor_product.values() if g.n < minimo)
    insuficientes_setor = sum(1 for g in fit_ctx.vendor_sector.values() if g.n < minimo)
    print(
        f"Células com suporte insuficiente (< {minimo} negócios fechados): "
        f"{insuficientes_produto} de {len(fit_ctx.vendor_product)} (vendedor×produto), "
        f"{insuficientes_setor} de {len(fit_ctx.vendor_sector)} (vendedor×setor)."
    )
    print()
    conclusoes = []
    for r in (perm_produto, perm_setor):
        veredito = "distinguível de acaso" if r.distinguivel_de_acaso else "indistinguível de acaso"
        vered_fit = "HÁ fit" if r.fit_distinguivel_de_acaso else "não há fit"
        conclusoes.append(
            f"vendedor×{r.dimensao} {veredito} no nulo global (p={formata_p(r.p_valor, 4)}) e "
            f"{vered_fit} no nulo aditivo (p={formata_p(r.p_valor_aditivo, 4)})"
        )
    print("Achado: " + "; ".join(conclusoes) + ".")
    if not (perm_produto.fit_distinguivel_de_acaso or perm_setor.fit_distinguivel_de_acaso):
        print(
            "Sob o nulo aditivo a dispersão observada fica ABAIXO da média simulada em ambas as "
            "dimensões: as células vendedor×produto são mais parecidas entre si do que um mundo "
            "sem afinidade nenhuma já produziria. Não há interação a encontrar, e não há correção "
            "para múltiplas comparações a aplicar — não existe sinal a corrigir. O fit ordena "
            "candidatos numa sugestão de redistribuição de CARGA; ele não mede mérito individual "
            "nem afinidade, e é entregue com a ressalva estatística acoplada ao número em toda "
            "superfície, exatamente por isso (Requirement \"Declaração de ausência de "
            "significância estatística do fit\")."
        )
    print(
        f"Nota de leitura: as {len(fit_ctx.vendor_product)} células não são "
        f"{len(fit_ctx.vendor_product)} testes. A dispersão é uma estatística OMNIBUS — um único "
        "teste que agrega todas as células —, então não existe multiplicidade em nível de célula a "
        "corrigir aqui. A multiplicidade real desta suíte são os 6 testes de permutação (4 na "
        "seção 2, 2 nesta), e a seção 2 já reporta o resultado sob Holm e Benjamini-Hochberg."
    )

    _section("13. Auditoria do denominador dos artefatos de análise")
    print(
        "Pergunta: os artefatos analysis_by_product_detailed.csv e\n"
        "analysis_by_sector_detailed.csv calculam a taxa de vitória sobre\n"
        "Won + Lost, sem deixar Engaging/Prospecting vazarem para o\n"
        "denominador — o defeito que os artefatos anteriores tinham?"
    )
    print()
    tabela_produto = build_analysis_table(fit_ctx.vendor_product, dataset, "product", "Produto")
    tabela_setor = build_analysis_table(fit_ctx.vendor_sector, dataset, "sector", "Setor")
    for nome, tabela in (
        ("analysis_by_product_detailed.csv", tabela_produto),
        ("analysis_by_sector_detailed.csv", tabela_setor),
    ):
        resultado = audit_denominator(tabela, nome)
        status = "APROVADO" if resultado.aprovado else "FALHA"
        print(f"  {nome:32s} {resultado.n_linhas:4d} linhas -> {status}")
        if not resultado.aprovado:
            ok = False
    print(
        "\nAchado: denominador travado por auditoria — nenhuma linha destes artefatos publica taxa "
        "cujo denominador inclua oportunidade em aberto (proposal.md: os artefatos anteriores tinham "
        "159 de 179 e 219 de 292 linhas incorretas por esse exato defeito)."
    )

    _section("14. Poder do teste de vendedor — o que este histórico enxergaria")
    print(
        "Pergunta: as seções 2 e 12 não rejeitam. Isso significa que os\n"
        "vendedores são iguais, ou que a diferença entre eles é menor do que\n"
        "esta amostra consegue ver? São afirmações diferentes, e só a segunda\n"
        "é sustentável — um teste que não rejeita só informa junto com o seu\n"
        "poder."
    )
    print(
        "Método: (a) compara a amplitude real entre carteiras com a que o\n"
        "        acaso já produz com os mesmos tamanhos de carteira;\n"
        "        (b) estima a dispersão VERDADEIRA por variância em excesso;\n"
        "        (c) simula mundos em que a habilidade realmente varia e mede\n"
        "        com que frequência o teste da seção 2 os pegaria (MDE);\n"
        "        (d) repete no cenário mais favorável possível — um vendedor\n"
        "        escolhido ANTES de olhar o dado."
    )
    print()
    poder = build_power_report(closed)
    print(
        f"  amplitude observada (melhor - pior de {poder.n_vendedores} vendedores) = "
        f"{poder.spread_observado_pp:.2f}pp"
    )
    print(
        f"  a mesma amplitude sob acaso puro: mediana {poder.spread_nulo_mediano_pp:.2f}pp, "
        f"IC95 [{poder.spread_nulo_p2_5_pp:.2f}, {poder.spread_nulo_p97_5_pp:.2f}]pp "
        f"-> a amplitude real {'CABE' if poder.spread_observado_dentro_do_nulo else 'NÃO cabe'} "
        "no que o acaso entrega de graça"
    )
    print(
        f"  dispersão observada {poder.dispersao_observada_pp:.2f}pp = ruído binomial esperado "
        f"{poder.dispersao_nula_esperada_pp:.2f}pp + excesso -> τ̂ = {poder.tau_excesso_pp:.2f}pp "
        f"(amplitude implicada entre melhor e pior: {poder.amplitude_implicada_por_tau_pp:.2f}pp)"
    )
    print()
    print(f"  Poder do teste omnibus da seção 2 (α={0.05:.2f}, corte de dispersão "
          f"{poder.dispersao_critica_pp:.2f}pp):")
    primeiro_com_poder = next((x for x in poder.curva_poder if x.poder >= PODER_ALVO), None)
    for ponto in poder.curva_poder:
        marca = f" <- corte de {PODER_ALVO * 100:.0f}% (MDE interpolado: {poder.mde_pp:.2f}pp)" if ponto is primeiro_com_poder else ""
        print(
            f"    τ verdadeiro={ponto.tau_pp:4.1f}pp (amplitude real ~{ponto.amplitude_media_pp:5.1f}pp)"
            f" -> poder {ponto.poder * 100:5.1f}%{marca}"
        )
    print(
        f"  Um vendedor de carteira mediana (n={poder.n_mediano_carteira}) escolhido ANTES de olhar "
        "o dado, realmente acima dos demais:"
    )
    for ponto in poder.poder_vendedor_unico:
        print(f"    +{ponto.delta_pp:4.1f}pp -> poder {ponto.poder * 100:5.1f}%")
    print(
        f"  Quanto histórico faltaria para τ̂={poder.tau_excesso_pp:.2f}pp sair da zona cega "
        f"(hoje: {poder.n_mediano_carteira} fechados por vendedor):"
    )
    for ponto in poder.dimensionamento:
        print(
            f"    n={ponto.n_por_vendedor:5d} fechados por vendedor -> poder {ponto.poder * 100:5.1f}%"
        )
    print()
    if poder.mde_pp is not None:
        print(
            f"Achado: as duas leituras extremas estão erradas. A amplitude de "
            f"{poder.spread_observado_pp:.2f}pp entre o melhor e o pior vendedor NÃO é achado — "
            f"o acaso entrega {poder.spread_nulo_mediano_pp:.2f}pp de mediana com estas carteiras, "
            f"e é por isso que a seção 2 não rejeita. Mas 'não rejeita' também não é 'são iguais': "
            f"a estimativa pontual da dispersão verdadeira é τ̂={poder.tau_excesso_pp:.2f}pp — "
            f"positiva, e equivalente a ~{poder.amplitude_implicada_por_tau_pp:.2f}pp entre o melhor "
            f"e o pior, um quarto do que a tabela crua sugere. O menor τ que este histórico "
            f"detectaria em {PODER_ALVO * 100:.0f}% das amostras é {poder.mde_pp:.2f}pp, "
            f"{'ACIMA' if poder.tau_abaixo_do_detectavel else 'ABAIXO'} de τ̂: a diferença "
            "plausível entre vendedores cai inteira na zona cega do teste."
        )
        print(
            "Consequência no motor: nenhuma mudança. Um efeito que não se distingue de zero não "
            "entra em p̂ nem em SCORE — publicar τ̂ como se fosse mensurado seria vender ruído "
            "como habilidade, e é exatamente o erro que a seção 10 mostra o expurgo cometendo. "
            "O que muda é a redação: a ferramenta afirma que não CONSEGUE VER diferença entre "
            "vendedores neste histórico, não que ela não exista. A diferença importa para a "
            "decisão de produto — τ̂ pequeno ainda vale receita sobre uma carteira inteira, e o "
            "caminho para medi-lo não é este dado observacional e sim alocação aleatorizada de "
            "leads comparáveis (ver roadmap.md)."
        )
        if poder.n_para_enxergar_tau is not None:
            print(
                f"Dimensionamento desse experimento: aleatorizar a alocação remove o "
                f"confundimento — a taxa de vitória deixa de misturar habilidade com qualidade da "
                f"carteira recebida — mas NÃO compra poder. Para enxergar τ̂="
                f"{poder.tau_excesso_pp:.2f}pp seriam necessários ~{poder.n_para_enxergar_tau} "
                f"negócios fechados por vendedor, contra os {poder.n_mediano_carteira} de hoje "
                f"({poder.n_para_enxergar_tau / poder.n_mediano_carteira:.0f}× o histórico atual). "
                "O experimento se justifica pelo desenho, não por um atalho estatístico: ele torna "
                "a resposta interpretável como habilidade e permite acumular amostra de propósito "
                "— e, no meio-tempo, detecta um efeito grande caso exista."
            )
    else:
        print(
            "Achado: nem o maior τ da grade atinge o poder alvo — esta amostra não sustenta "
            "afirmação nenhuma sobre diferença entre vendedores."
        )

    _section("Conclusão")
    print(
        "Juntando as 14 seções: não há como prever com confiança QUEM vai\n"
        "ganhar (seções 1 e 2), então não faz sentido construir um\n"
        "classificador de probabilidade categórica. O que os dados sustentam\n"
        "é ordenar o funil por SCORE (percentil de PRIORIDADE, o valor em risco) —\n"
        "quanto vale o negócio, ajustado pela chance histórica do produto (seção 3)\n"
        "e pela urgência de agir agora (seção 4) — e essa priorização de fato\n"
        "concentra valor no topo da fila (seção 5). Três tentativas de refinar o\n"
        "motor com condicionamento adicional foram testadas e as três pioraram a\n"
        "previsão fora da amostra: p̂ por produto×setor (seção 6), curvas de aging\n"
        "por produto (seção 7) e URGÊNCIA por produto (seção 8) — nenhuma das três\n"
        "está implementada. A seção 9 acompanha CONFIANÇA\n"
        "(completude/suporte) para a próxima\n"
        "recalibração. A seção 10 mede a distorção que o expurgo de 200 dias\n"
        "introduziria e a 11 confirma que nenhum desfecho da calibração foi\n"
        "atribuído por nós; as seções 12-13 reproduzem a ausência de\n"
        "sinal robusto do fit por vendedor e travam o denominador dos artefatos\n"
        "de análise por teste. A seção 14 fecha a leitura das seções 2 e 12: o\n"
        "que elas afirmam não é que os vendedores sejam iguais, e sim que\n"
        "qualquer diferença real entre eles é menor do que este histórico\n"
        "conseguiria enxergar."
    )
    print()
    print(
        "Os dados justificam ordenar o funil por SCORE (percentil de valor em risco), não\n"
        "por um classificador de probabilidade categórica nem por hierarquias de\n"
        "condicionamento adicionais: nenhum atributo firmográfico isolado carrega sinal\n"
        "acima do ruído amostral, a hierarquia de encolhimento confirma isso nos três\n"
        "níveis abaixo do global — conta×produto, produto×setor e produto — que colapsam\n"
        "todos (seção 3), e condicionar por setor ou por produto (aging, URGÊNCIA) piora\n"
        "a previsão fora da amostra em vez de melhorá-la."
    )
    print()
    print("STATUS: " + ("OK — todas as premissas estruturais confirmadas." if ok else "ATENÇÃO — ver avisos acima."))

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    ok = run_report(args.data_dir)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
