"""Interface local. Execute em solution com streamlit run app.py."""

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from supportops.analytics import MIN_RATINGS, group_stats  # noqa: E402
from supportops.classifier import classify, load_local, normalize  # noqa: E402
from supportops.impact import FRACTIONS, SCENARIOS, Scenario, calculate  # noqa: E402
from supportops.ingest import (  # noqa: E402
    ARTIFACTS,
    IT,
    IT_FIELDS,
    LOCAL,
    RAW,
    SUPPORT,
    digest,
    load,
    read_json,
)
from supportops.policy import DOMAIN_IT, DOMAIN_OTHER, SUGGEST  # noqa: E402

SECTIONS = ("Diagnóstico", "Triagem", "Qualidade e evidências", "Impacto e operação")
DIM_LABELS = {"canal": "Canal", "prioridade": "Prioridade", "tipo": "Tipo", "status": "Status"}
PARAMS = {
    "volume": "Tickets por mês",
    "elegibilidade": "Elegíveis para triagem (%)",
    "cobertura": "Sugestões entre elegíveis (%)",
    "adesao": "Uso entre sugestões (%)",
    "antes_min": "Triagem atual (min/ticket)",
    "depois_min": "Triagem assistida (min/ticket)",
    "revisao_min": "Revisão (min/sugestão usada)",
    "retrabalho_taxa": "Sugestões usadas que geram retrabalho (%)",
    "retrabalho_min": "Tempo por retrabalho (min)",
    "hora_brl": "Valor por hora (R$)",
    "ia_mensal_brl": "IA, todas as chamadas (R$/mês)",
    "infra_mensal_brl": "Infraestrutura (R$/mês)",
    "manutencao_mensal_brl": "Manutenção (R$/mês)",
    "implantacao_brl": "Implantação inicial (R$)",
    "conversao_caixa": "Capacidade positiva conversível em caixa (%)",
}


def br(value, decimals=0):
    if value is None:
        return "Indisponível"
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct(value):
    return "—" if value is None or pd.isna(value) else f"{br(value * 100, 1)}%"


def signature(path):
    info = path.stat()
    return info.st_mtime_ns, info.st_size


@st.cache_data(show_spinner=False)
def read_snapshot(path, stamp):
    return read_json(path)


def artifact(name, source=None):
    path = ARTIFACTS / name
    try:
        data = read_snapshot(path, signature(path))
        if source and data["dataset_sha256"] != source.sha256:
            raise ValueError("O artefato pertence a outra versão do dataset.")
        return data
    except (OSError, ValueError, KeyError) as exc:
        st.warning(f"Evidência indisponível ({name}). Consulte o README para regenerar.")
        with st.expander("Detalhe técnico"):
            st.text(str(exc))
        return None


@st.cache_resource(show_spinner="Carregando o modelo local…")
def model(stamps):
    return load_local(LOCAL)


@st.cache_data(show_spinner=False)
def holdout(csv_stamp, raw_stamp, csv_sha):
    path = LOCAL / "test-predictions.csv"
    if digest(path.read_bytes()) != csv_sha:
        raise ValueError("Predições locais fora de sincronia. Rode a etapa evaluate.")
    rows = pd.read_csv(path, keep_default_na=False)
    raw, _ = load(IT, IT_FIELDS)
    raw.index = [
        digest(f"{IT.sha256}:{ordinal}".encode())[:20] for ordinal in range(1, len(raw) + 1)
    ]
    return rows.sort_values("id"), raw["Document"].to_dict()


def table(data):
    st.dataframe(data, hide_index=True, width="stretch")


def diagnosis():
    st.header("Diagnóstico operacional")
    st.caption("Dataset 1 · suporte ao consumidor · snapshot Kaggle v1 · fotografia de carga")
    data = artifact("diagnosis.json", SUPPORT)
    if data is None:
        st.info("Importe os arquivos e execute python scripts/pipeline.py audit.")
        return
    quality = data["qualidade"]
    st.info(f"FRT, TTR e intervalo parcial indisponíveis. {quality['tempo']['motivo']}")
    with st.expander("Filtros", expanded=True):
        cols = st.columns(4)
        selected = {
            key: col.multiselect(
                label, sorted({row[key] for row in data["cubo"]}), placeholder="Todos"
            )
            for (key, label), col in zip(DIM_LABELS.items(), cols, strict=True)
        }
    cube = [
        r for r in data["cubo"] if all(not vals or r[key] in vals for key, vals in selected.items())
    ]
    if not cube:
        st.warning("O cruzamento selecionado não contém tickets.")
        return
    total = group_stats(cube)[0]
    statuses = {r["status"]: r["n"] for r in group_stats(cube, ("status",))}
    n = total["n"]
    active = statuses.get("Open", 0) + statuses.get("Pending Customer Response", 0)
    a, b, c, d = st.columns(4)
    a.metric("Tickets no recorte", br(n))
    b.metric(
        "Aberto ou aguardando", br(active), help="Status na fotografia, sem indicação de atraso."
    )
    c.metric(
        "Cobertura de notas",
        pct(total["cobertura_notas"]),
        help=f"{total['n_notas']} / {n} tickets.",
    )
    d.metric("Notas 4–5", pct(total["proporcao_4_5"]), help="Denominador: apenas notas válidas.")
    st.caption(
        f"Notas válidas: {br(total['n_notas'])}/{br(n)} · inversões: {br(total['inversoes'])}/{br(total['pares'])} pares de timestamps."
    )

    st.subheader("Carga e composição")
    cut = st.selectbox(
        "Corte", ("Canal", "Prioridade", "Tipo", "Status", "Canal × prioridade", "Canal × tipo")
    )
    dims = {
        "Canal": ("canal",),
        "Prioridade": ("prioridade",),
        "Tipo": ("tipo",),
        "Status": ("status",),
        "Canal × prioridade": ("canal", "prioridade"),
        "Canal × tipo": ("canal", "tipo"),
    }[cut]
    groups = group_stats(cube, dims)
    segments = pd.DataFrame(
        [
            {
                "Segmento": " / ".join(g[key] for key in dims),
                "Tickets": g["n"],
                "% do recorte": pct(g["n"] / n),
                "Notas válidas": g["n_notas"],
                "Cobertura": pct(g["cobertura_notas"]),
                "Notas 4–5": g["n_4_5"],
                "% 4–5 entre notas": pct(g["proporcao_4_5"]),
                "Mediana ordinal": g["mediana_ordinal"],
                "Leitura de satisfação": "n baixo" if g["amostra_pequena"] else "Descritiva",
                "Respostas (timestamp)": g["respostas_ts"],
                "Resoluções (timestamp)": g["resolucoes_ts"],
                "Pares invertidos": g["inversoes"],
                "Pares completos": g["pares"],
            }
            for g in groups
        ]
    ).sort_values("Tickets", ascending=False)
    st.bar_chart(segments, x="Segmento", y="Tickets", x_label=cut, y_label="Tickets")
    table(segments)

    st.subheader("Satisfação observada")
    if total["n_notas"]:
        ratings = pd.DataFrame(
            {
                "Nota": ["1", "2", "3", "4", "5"],
                "Respostas": [total[f"nota_{i}"] for i in range(1, 6)],
            }
        )
        st.bar_chart(
            ratings,
            x="Nota",
            y="Respostas",
            x_label="Nota (escala 1 a 5)",
            y_label="Tickets com nota",
        )
    else:
        st.info("Não há notas válidas no recorte selecionado.")
    st.caption(
        f"Cada linha representa um ticket. Cortes com menos de {MIN_RATINGS} notas são sinalizados. Diferenças de composição e cobertura limitam comparações."
    )
    status_rows = group_stats(cube, ("status",))
    table(
        pd.DataFrame(
            [
                {
                    "Status": r["status"],
                    "Tickets": r["n"],
                    "Notas válidas": r["n_notas"],
                    "Cobertura": pct(r["cobertura_notas"]),
                }
                for r in status_rows
            ]
        )
    )
    st.subheader("Decisão sugerida")
    st.write(
        "Instrumentar os eventos de abertura, resposta, encaminhamento e fechamento. Medir esforço ativo e retrabalho em paralelo à espera. Priorizar a coleta em categorias recorrentes e validar o efeito em um piloto assistido."
    )
    with st.expander("Qualidade do arquivo completo"):
        st.caption(f"SHA-256 do CSV · {SUPPORT.sha256}")
        st.json(quality, expanded=1)


def triage():
    st.header("Triagem assistida")
    st.caption(
        "Dataset 2 · TI interna · interface em português, modelo avaliado em corpus de TI com sinais de inglês"
    )
    st.info(
        "A sugestão é temática. Um atendente decide a fila final. A entrada livre é tratada como fora do escopo até declaração de TI interna em inglês."
    )
    try:
        stamps = tuple(signature(LOCAL / p) for p in ("model.json", "model.joblib"))
        pipeline, meta = model(stamps)
    except (OSError, ValueError, KeyError) as exc:
        st.warning("Modelo local indisponível. Execute python scripts/pipeline.py train.")
        with st.expander("Detalhe técnico"):
            st.text(str(exc))
        return

    mode = st.radio("Origem do ticket", ("Texto livre", "Teste reservado (local)"), horizontal=True)
    row_id = None
    if mode == "Teste reservado (local)":
        try:
            evaluation = read_snapshot(
                ARTIFACTS / "evaluation.json", signature(ARTIFACTS / "evaluation.json")
            )
            if evaluation["modelo_versao"] != meta["modelo_versao"]:
                raise ValueError("Avaliação de outra versão do modelo.")
            predictions, documents = holdout(
                signature(LOCAL / "test-predictions.csv"),
                signature(RAW / IT.file),
                evaluation["teste"]["predicoes_sha256"],
            )
        except (OSError, ValueError, KeyError) as exc:
            st.warning("Amostra reservada indisponível. Execute audit, train e evaluate.")
            with st.expander("Detalhe técnico"):
                st.text(str(exc))
            return
        recipe = st.selectbox(
            "Seleção do teste",
            (
                "Amostra aleatória",
                "Sugestão correta",
                "Encaminhado para revisão",
                "Sugestão incorreta",
            ),
        )
        if recipe == "Amostra aleatória":
            seed = st.number_input(
                "Semente da amostra", min_value=0, max_value=2**32 - 1, value=241
            )
            options = predictions.sample(n=min(12, len(predictions)), random_state=int(seed))
        else:
            correct = predictions["real"].eq(predictions["previsto"])
            mask = {
                "Sugestão correta": predictions["aceito"] & correct,
                "Sugestão incorreta": predictions["aceito"] & ~correct,
                "Encaminhado para revisão": ~predictions["aceito"],
            }[recipe]
            options = predictions.loc[mask].head(12)
        if options.empty:
            st.info("Sem exemplos para esse filtro no teste reservado.")
            return
        row_id = st.selectbox("ID derivado da linha", options["id"].tolist())
        text = documents[row_id]
        domain = DOMAIN_IT
        expected = options.loc[options["id"].eq(row_id), "real"].iloc[0]
        st.caption(
            f"Rótulo de referência: {expected}. O CSV fica local. A visualização abaixo omite o texto para evitar expor identificadores."
        )
        st.caption(
            f"Comprimento do texto original: {len(text)} caracteres · {len(normalize(text).split())} tokens normalizados."
        )
    else:
        domain = st.selectbox("Domínio e idioma declarados", (DOMAIN_OTHER, DOMAIN_IT))
        text = st.text_area(
            "Descrição do ticket",
            max_chars=8001,
            height=155,
            placeholder="Use um texto de teste sem dados pessoais.",
        )
    priority = st.selectbox("Prioridade de origem", ("Normal", "Crítica", "Desconhecida"))
    if st.button("Avaliar ticket", type="primary"):
        result = classify(pipeline, meta, text, domain, priority, row_id)
        if result["decisao"] == SUGGEST:
            st.success("Sugestão de roteamento")
        else:
            st.warning("Revisão humana")
        a, b, c = st.columns(3)
        a.metric("Categoria prevista", result["categoria_prevista"] or "—")
        score = result["score"]
        b.metric(
            "Score do modelo", "—" if score is None else br(score, 3), help=result["tipo_score"]
        )
        c.metric("Inferência local", f"{br(result['latencia_ms'], 2)} ms")
        st.write(" ".join(result["motivos"]))
        st.caption(
            f"Corte da validação {br(meta['limiar'], 2)} · score não calibrado · {result['versao_modelo']}"
        )
        with st.expander("Resultado estruturado"):
            st.json(result)


def evidence():
    st.header("Qualidade e evidências")
    data = artifact("evaluation.json")
    quality = artifact("it-quality.json", IT)
    manifest = artifact("manifest.json")
    if data and data["proveniencia"]["dataset_sha256"] == IT.sha256:
        test = data["teste"]
        p = test["politica"]
        a, b, c, d = st.columns(4)
        a.metric("Macro-F1 · TF-IDF", pct(test["tfidf_logit"]["macro_f1"]))
        b.metric("Macro-F1 · maioria", pct(test["classe_majoritaria"]["macro_f1"]))
        c.metric("Cobertura da política", pct(p["cobertura"]))
        d.metric("Acerto entre sugestões", pct(p["acerto_nos_aceitos"]))
        st.caption(
            f"Teste reservado · {br(test['n'])} tickets · {br(p['aceitos'])} sugestões e {br(p['revisao'])} revisões. As métricas de classe incluem todas as predições offline do modelo."
        )
        st.write(
            f"Acurácia TF-IDF **{pct(test['tfidf_logit']['accuracy'])}** · acurácia classe majoritária **{pct(test['classe_majoritaria']['accuracy'])}** · corte escolhido na validação **{pct(data['limiar'])}**."
        )
        if interval := p["ic95_wilson_acerto"]:
            st.caption(
                f"IC95% de Wilson por linha entre sugestões: {pct(interval[0])} a {pct(interval[1])}. Grupos de textos semelhantes podem reduzir o tamanho efetivo da amostra."
            )
        st.subheader("Desempenho por classe")
        table(
            pd.DataFrame(
                [
                    {
                        "Classe": name,
                        "Precisão": pct(m["precision"]),
                        "Recall": pct(m["recall"]),
                        "F1": pct(m["f1-score"]),
                        "Amostra": int(m["support"]),
                        "Sugestões": test["politica_por_classe_real"][name]["aceitos"],
                    }
                    for name, m in test["por_classe"].items()
                ]
            )
        )
        if privileged := test["politica_por_classe_real"].get("Administrative rights"):
            st.warning(
                f"{privileged['aceitos']} de {privileged['n']} tickets rotulados como acesso privilegiado "
                "receberam sugestões para outros temas. A proteção por palavras e categoria prevista é parcial."
            )
        st.subheader("Confusão do classificador")
        st.caption(
            "Linhas são classes de referência. Colunas são classes previstas. Valores em tickets."
        )
        matrix = pd.DataFrame(test["matriz_confusao"], columns=test["classes"])
        matrix.insert(0, "Referência", test["classes"])
        table(matrix)
        with st.expander("Partições, seleção de corte, latência e erros"):
            st.json(
                {
                    k: data[k]
                    for k in (
                        "modelo_versao",
                        "n_por_particao",
                        "classes_por_particao",
                        "criterio_validacao",
                        "validacao_no_limiar",
                        "splits_sha256",
                    )
                }
            )
            st.caption("Curva na validação · 21 cortes · teste reservado separado")
            table(pd.DataFrame(data["curva_validacao"]).drop(columns="ic95_wilson_acerto"))
            st.json({"latência": test["latencia_ms"], "exemplos por ID": test["exemplos_por_id"]})
    if quality:
        with st.expander("Qualidade do corpus de TI"):
            st.json(quality, expanded=1)
    if manifest:
        with st.expander("Proveniência e manifesto"):
            st.link_button("Fonte oficial · suporte ao consumidor", SUPPORT.page)
            st.link_button("Fonte oficial · TI interna", IT.page)
            st.json(manifest, expanded=1)


def impact():
    st.header("Impacto e operação")
    st.warning(
        "Cenário hipotético. Tempo ativo de triagem, sem ganhos de resolução, e sem conversão de capacidade em caixa por padrão."
    )
    st.caption(
        "Volume de referência: 30.000/ano do enunciado ÷ 12. Demais valores são premissas editáveis a validar no piloto. Cobertura operacional independente do teste de TI."
    )
    preset = st.selectbox("Cenário", list(SCENARIOS), index=1)
    defaults = SCENARIOS[preset]
    inputs = {}
    with st.expander("Premissas editáveis", expanded=True):
        cols = st.columns(3)
        for i, (field, label) in enumerate(PARAMS.items()):
            fraction = field in FRACTIONS
            value = float(getattr(defaults, field))
            inputs[field] = cols[i % 3].number_input(
                label,
                min_value=0.0,
                max_value=100.0 if fraction else None,
                value=round(value * 100, 6) if fraction else value,
                key=f"{preset}:{field}",
                step=1.0 if fraction or field == "volume" else 0.1,
            ) / (100 if fraction else 1)
    scenario = Scenario(**inputs)
    r = calculate(scenario)
    a, b, c, d = st.columns(4)
    a.metric("Triagens assistidas/mês", br(r["processados_mes"], 1))
    b.metric("Capacidade líquida (h/mês)", br(r["horas_liquidas_mes"], 2))
    c.metric("Valor da capacidade/mês", f"R$ {br(r['valor_capacidade_mes'], 2)}")
    d.metric("Caixa líquido/mês", f"R$ {br(r['caixa_liquido_mes'], 2)}")
    roi = r["roi_financeiro_12m"]
    payback = r["payback_meses"]
    st.write(
        rf"Custo recorrente **R\$ {br(r['custo_recorrente_mes'], 2)}/mês** · "
        rf"valor líquido de capacidade **R\$ {br(r['valor_liquido_capacidade_mes'], 2)}/mês** · "
        rf"caixa em 12 meses **R\$ {br(r['caixa_liquido_12m'], 2)}**."
    )
    st.caption(
        f"ROI financeiro em 12 meses: {pct(roi)} · payback: {br(payback, 1)} meses"
        if payback is not None
        else f"ROI financeiro em 12 meses: {pct(roi)} · payback indisponível sem caixa mensal positivo."
    )
    st.subheader("Sensibilidade à cobertura")
    points = sorted(
        {max(0.0, scenario.cobertura - 0.1), scenario.cobertura, min(1.0, scenario.cobertura + 0.1)}
    )
    table(
        pd.DataFrame(
            [
                {
                    "Cobertura entre elegíveis": pct(p),
                    "Horas líquidas/mês": br(out["horas_liquidas_mes"], 2),
                    "Valor líquido de capacidade/mês": f"R$ {br(out['valor_liquido_capacidade_mes'], 2)}",
                }
                for p in points
                for out in [calculate(replace(scenario, cobertura=p))]
            ]
        )
    )
    st.subheader("Fluxo do piloto")
    st.markdown(
        "1. Receber, validar campos, minimizar dados pessoais e identificar o domínio.\n"
        "2. Preservar prioridade e encaminhar risco, escopo indefinido e score baixo à fila humana.\n"
        "3. Exibir a sugestão temática e o motivo. O atendente confirma ou corrige o destino.\n"
        "4. Medir tempo ativo, revisão, retrabalho, erro de fila e CSAT por grupo com e sem assistência.\n"
        "5. Auditar a política em lotes. Acesso privilegiado, estorno e ações sensíveis exigem responsável humano."
    )


st.set_page_config(page_title="SupportOps AI", page_icon="🧭", layout="wide")
st.sidebar.title("SupportOps AI")
st.sidebar.caption("Challenge 002 · protótipo local")
section = st.sidebar.radio("Áreas de trabalho", SECTIONS)
st.sidebar.divider()
st.sidebar.caption("Operação de suporte e triagem de TI são domínios distintos.")
{
    "Diagnóstico": diagnosis,
    "Triagem": triage,
    "Qualidade e evidências": evidence,
    "Impacto e operação": impact,
}[section]()
