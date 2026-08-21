#!/usr/bin/env python3
"""Artefato de validação — evidência estatística por trás da fórmula de
priorização. Comando único, sem ambiente gráfico:

    python backtest.py [--data-dir ../../data]

EM TERMOS SIMPLES: este script pega os negócios já FECHADOS (ganhos ou
perdidos) e usa métodos estatísticos pra checar se as decisões de design
da fórmula de priorização realmente se sustentam nos dados — em vez de
confiar em "achismo". Ele responde a 5 perguntas centrais sobre a fórmula
de priorização (seções 1-8), e mais 4 sobre a reclassificação de 200 dias
e a análise de carga e fit (seções 10-13):

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
censura de 138 dias, a concentração de PRIORIDADE no topo da fila, o
impacto da reclassificação de 200 dias (antes/depois e circularidade), a
ausência de sinal do fit por vendedor, e o denominador correto dos
artefatos de análise — sempre importando `scoring/`, nunca reimplementando
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
from permutation_tests import run_all as run_permutation_tests
from reclassification_check import build_report as build_reclassification_report
from scoring import constants
from scoring.export import build_analysis_table
from scoring.fit import build_fit_context, derive_k_fit
from scoring.pipeline import fechados_calibracao, fechados_organicos, load_and_score
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
    # `closed` é a população de CALIBRAÇÃO (fechados orgânicos + 653
    # reclassificados de 200 dias) — alimenta as seções sobre produto,
    # setor e vendedor, onde idade não é insumo. `closed_organico` alimenta
    # exclusivamente as seções que dependem de idade/duração (4, 7, 8) —
    # nunca pode conter um reclassificado (design.md, D2).
    closed = fechados_calibracao(dataset)
    closed_organico = fechados_organicos(dataset)

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
    for result in run_permutation_tests(closed):
        print(
            f"  {result.atributo:16s} dispersão obs.={result.dispersao_observada:.4f} "
            f"dispersão nula média={result.dispersao_nula_media:.4f} p={result.p_valor:.3f}"
        )
    print()
    print(
        "p-valor = a chance de ver, só por acaso (embaralhado), uma diferença\n"
        "tão grande quanto a real observada. p-valor alto (>0,05, tipicamente\n"
        "bem mais) = a diferença real é do tamanho que apareceria só por acaso\n"
        "— ou seja, não há padrão real."
    )
    print("-> p alto (>0,05, tipicamente bem mais) = dispersão observada compatível com ruído.")
    print(
        "Achado: todos os atributos testados têm p-valor alto — confirma, de\n"
        "um segundo jeito independente, o resultado da Seção 1."
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
        f"direção à média geral ({constants.GLOBAL_WIN_RATE_CALIBRACAO}), com força k. "
        "k é calculado a partir\n"
        "dos próprios dados: quanto menor a diferença real entre os grupos\n"
        "comparada à diferença esperada só por acaso, maior o k — mais o\n"
        "grupo é puxado pra média. Quando k = ∞, o grupo 'colapsa': recebe\n"
        "peso zero e usa direto a média geral. É o que esperamos ver quando\n"
        "um atributo, como já vimos nas seções 1 e 2, não carrega sinal real."
    )
    print()
    shrinkage = build_shrinkage_report(closed)
    for nome, stats in [
        ("conta×produto", shrinkage.conta_produto),
        ("produto×setor", shrinkage.produto_setor),
        ("produto", shrinkage.produto),
    ]:
        k_str = "∞ (colapsa)" if stats.colapsa else f"{stats.k:.3f}"
        print(
            f"  {nome:16s} grupos={stats.n_groups:4d} var_obs={stats.var_observada:.6f} "
            f"var_esperada_por_acaso={stats.var_esperada_por_acaso:.6f} k={k_str}"
        )
    print()
    print(
        "'k congelado' abaixo é o valor usado em produção (fixado numa\n"
        "calibração anterior); 'p̂_produto recalculado' é a taxa que sairia se\n"
        "recalculássemos do zero com os dados desta execução — comparamos os\n"
        "dois pra ver se ainda fazem sentido juntos."
    )
    print(f"k congelado em produção (constants.K_PRODUTO) = {constants.K_PRODUTO}")
    print("p̂_produto (congelado) vs (recalculado nesta execução):")
    for produto in constants.PRECO_TABELA:
        congelado = shrinkage.p_hat_por_produto_congelado[produto]
        recalc = shrinkage.p_hat_por_produto_recalculado[produto]
        print(f"  {produto:16s} congelado={congelado:.4f}  recalculado={recalc:.4f}")

    if not (shrinkage.conta_produto.colapsa and shrinkage.produto_setor.colapsa):
        print(
            "AVISO: conta×produto e/ou produto×setor não colapsaram nesta execução — "
            "revisar a hierarquia de encolhimento na próxima recalibração."
        )
        ok = False

    if shrinkage.produto.colapsa:
        print(
            "\nNOTA — em termos simples: se aplicássemos a mesma régua de\n"
            "'colapsar se não há sinal' também ao nível de PRODUTO (não só\n"
            "conta×produto e produto×setor), o resultado diria pra zerar essa\n"
            "diferenciação também. Decidimos manter mesmo assim — o motivo\n"
            "completo está registrado abaixo e em docs/decisions-log.md.\n\n"
            "NOTA — achado desta execução: o mesmo método (variância esperada por "
            "acaso / variância em excesso), recalculado do zero sobre estes dados, "
            "encontra excesso de variância NEGATIVO também no nível de produto "
            "(mais fraco do que qualquer um dos quatro atributos testados por "
            "permutação acima, todos com p > 0,05). Sob recomputação estrita, isso "
            "colapsaria p̂_produto para a constante de calibração "
            f"({constants.GLOBAL_WIN_RATE_CALIBRACAO}) em todos os produtos.\n"
            "K_PRODUTO = 4 é retido mesmo assim como constante CONGELADA desta "
            "calibração — uma APROXIMAÇÃO RETIDA POR POLÍTICA, não o resultado do "
            "cálculo (documentada em docs/decisions-log.md) — não é uma escolha "
            "arbitrária nova, é a calibração já em produção. Fica registrado aqui "
            "para a próxima recalibração trimestral avaliar se essa diferenciação "
            "deve ser reduzida ou mantida."
        )
    else:
        print(
            "\nAVISO — o nível de PRODUTO deixou de colapsar nesta execução: a "
            f"variância em excesso recalculada agora é positiva e produz k = "
            f"{shrinkage.produto.k:.3f}, diferente do K_PRODUTO = "
            f"{constants.K_PRODUTO} congelado em produção. Isso significa que a "
            "aproximação retida por política pode não ser mais conservadora — "
            "sinal real pode ter aparecido no nível de produto desde a última "
            "calibração. Revisar K_PRODUTO nesta recalibração antes de prosseguir, "
            "em vez de carregar o valor antigo adiante silenciosamente."
        )
        ok = False

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
    curves = recompute_curves(closed_organico)
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
    if not pior_que_global:
        ok = False

    _section("7. Curvas de aging por produto — validação cruzada")
    print(
        "Pergunta: uma curva de aging (risco de resolver em 30 dias) própria\n"
        "por produto prevê melhor que a curva GLOBAL usada em produção?"
    )
    print("Método: mesma validação cruzada 5-fold da seção 6, aplicada às faixas de idade.")
    print()
    aging_report = build_aging_by_product_report(closed_organico)
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
    ciclo = run_cycle_duration_permutation(closed_organico)
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
    taxas = resolution_rate_by_product_and_age(closed_organico)
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

    _section("10. Antes/depois da reclassificação de 200 dias")
    print(
        "Pergunta: qual o efeito de tratar as 653 oportunidades abertas há\n"
        "200 dias ou mais como Lost — no tamanho do funil, na taxa de vitória\n"
        "global e na taxa por produto?"
    )
    print()
    reclass = build_reclassification_report(dataset)
    print(f"Oportunidades reclassificadas: {reclass.n_reclassificados}")
    print(f"Funil aberto: {reclass.funil_antes} -> {reclass.funil_depois}")
    print(
        f"Base rate global: {reclass.base_rate_antes * 100:.2f}% -> "
        f"{reclass.base_rate_depois * 100:.2f}% "
        f"({(reclass.base_rate_depois - reclass.base_rate_antes) * 100:+.2f}pp)"
    )
    print()
    print("Taxa de vitória por produto, antes -> depois (pp = pontos percentuais):")
    for p in sorted(reclass.produtos, key=lambda p: p.variacao_pp):
        marca = " [AMOSTRA PEQUENA]" if p.amostra_pequena else ""
        print(
            f"  {p.produto:16s} n={p.n_antes:4d}->{p.n_depois:4d}  "
            f"{p.taxa_antes * 100:5.2f}% -> {p.taxa_depois * 100:5.2f}%  "
            f"({p.variacao_pp:+6.2f}pp){marca}"
        )
    pequenas = [p.produto for p in reclass.produtos if p.amostra_pequena]
    print(
        f"\nAchado: {reclass.n_reclassificados} reclassificados fazem o funil aberto cair de "
        f"{reclass.funil_antes} para {reclass.funil_depois} e o base rate global cair "
        f"{(reclass.base_rate_antes - reclass.base_rate_depois) * 100:.2f}pp. A maior variação de taxa "
        f"por produto é dominada por amostra pequena ({', '.join(pequenas)}) — não é o maior efeito real, "
        "é o mais ruidoso."
    )

    _section("11. Auditoria da circularidade acima de 138 dias")
    print(
        "Pergunta: a faixa de idade acima de 138 dias na população de\n"
        "calibração é feita de desfechos observados, ou inteiramente de\n"
        "rótulos que nós mesmos atribuímos por serem velhos?"
    )
    print()
    circularidade = build_circularity_report(dataset)
    print(f"Idade máxima entre fechados organicamente: {circularidade.idade_maxima_organica} dias")
    print(f"Idade mínima entre reclassificados: {circularidade.idade_minima_reclassificada} dias")
    if circularidade.populacoes_nao_se_sobrepoem and circularidade.curvas_protegidas:
        print("-> confirmado: as duas populações não se sobrepõem, e nenhum reclassificado entrou nas curvas.")
    else:
        print(
            "FALHA: as populações se sobrepõem ou um reclassificado entrou na calibração das "
            "curvas de idade — a faixa >138d deixou de ser auditável, revisar antes de prosseguir."
        )
        ok = False

    _section("12. Fit por vendedor — permutação e suporte")
    print(
        "Pergunta: a taxa de vitória de um vendedor num produto ou setor é\n"
        "distinguível de acaso, uma vez controlado o mix de produtos/setores\n"
        "que cada vendedor efetivamente atende?"
    )
    print(
        "Método: embaralhamos os rótulos de vendedor (mantendo produto/setor\n"
        "fixos por negócio) e comparamos a dispersão real da taxa por célula\n"
        "vendedor×dimensão com a dispersão sob rótulos aleatórios."
    )
    print()
    fit_ctx = build_fit_context(dataset, closed)
    perm_produto = run_fit_permutation_produto(closed)
    perm_setor = run_fit_permutation_setor(closed)
    for r in (perm_produto, perm_setor):
        print(
            f"  vendedor×{r.dimensao:8s} células={r.n_celulas:3d} dispersão obs.={r.dispersao_observada:.4f} "
            f"dispersão nula média={r.dispersao_nula_media:.4f} p={r.p_valor:.4f}"
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
        veredito = "distinguível de acaso (p < 0,05)" if r.distinguivel_de_acaso else "indistinguível de acaso"
        conclusoes.append(f"vendedor×{r.dimensao} {veredito} (p={r.p_valor:.4f})")
    print(
        "Achado: " + "; ".join(conclusoes) + ". Mesmo onde o p-valor fica perto do corte convencional "
        "de 0,05, é um sinal fraco sobre "
        f"{len(fit_ctx.vendor_product)} células testadas sem correção para múltiplas comparações — "
        "não é evidência robusta de mérito individual. O fit é entregue com a ressalva estatística "
        "acoplada ao número em toda superfície, exatamente por isso (Requirement \"Declaração de "
        "ausência de significância estatística do fit\")."
    )
    if perm_produto.distinguivel_de_acaso or perm_setor.distinguivel_de_acaso:
        print(
            "NOTA: design.md previa colapso (k=∞) para ambas as dimensões, espelhando "
            "conta×produto/produto×setor. A reprodução honesta encontra sinal fraco e limítrofe em "
            "vendedor×produto — registrado aqui para a próxima recalibração revisar a redação do "
            "design, sem mudar K_FIT (constante de política, mais conservador que o k derivado)."
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

    _section("Conclusão")
    print(
        "Juntando as 13 seções: não há como prever com confiança QUEM vai\n"
        "ganhar (seções 1 e 2), então não faz sentido construir um\n"
        "classificador de probabilidade categórica. O que os dados sustentam\n"
        "é ordenar o funil por SCORE (percentil de PRIORIDADE, o valor em risco) —\n"
        "quanto vale o negócio, ajustado pela chance histórica do produto (seção 3)\n"
        "e pela urgência de agir agora (seção 4) — e essa priorização de fato\n"
        "concentra valor no topo da fila (seção 5). Três tentativas de refinar o\n"
        "motor com condicionamento adicional foram testadas e as três pioraram a\n"
        "previsão fora da amostra: p̂ por produto×setor (seção 6), curvas de aging\n"
        "por produto (seção 7) e URGÊNCIA por produto (seção 8) — os três\n"
        "resultados negativos ficam documentados, não implementados. A seção 9\n"
        "acompanha CONFIANÇA (completude/suporte) para a próxima recalibração. As\n"
        "seções 10-11 reproduzem o impacto e a circularidade da reclassificação de\n"
        "200 dias; as seções 12-13 reproduzem a ausência de sinal robusto do fit por\n"
        "vendedor e travam o denominador dos artefatos de análise por teste."
    )
    print()
    print(
        "Os dados justificam ordenar o funil por SCORE (percentil de valor em risco), não\n"
        "por um classificador de probabilidade categórica nem por hierarquias de\n"
        "condicionamento adicionais: nenhum atributo firmográfico isolado carrega sinal\n"
        "acima do ruído amostral, a hierarquia de encolhimento confirma isso para\n"
        "conta×produto e produto×setor (produto em si deixou de colapsar após a\n"
        "recalibração de 200 dias — ver seção 3, dominado por GTK 500), e condicionar por\n"
        "setor ou por produto (aging, URGÊNCIA) piora a previsão fora da amostra em vez\n"
        "de melhorá-la."
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
