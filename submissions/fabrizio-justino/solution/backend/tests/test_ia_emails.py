"""Testes da camada de IA e dos e-mails com um LLM FALSO — sem rede, sem chave real.
Cobrem o que importa: fallback sem chave, validação de números, frase proibida,
cache, loop de ferramentas e geração dos e-mails sem envio."""
import json
from types import SimpleNamespace

import pytest

from app import config, emails, ia
from app.main import MOTOR

DATA_PRESSAO = "2017-12-04"


@pytest.fixture
def v():
    return MOTOR.visao(DATA_PRESSAO)


@pytest.fixture
def llm_falso(monkeypatch, tmp_path):
    """Liga a IA com chave fictícia e troca _chamar por respostas programadas."""
    monkeypatch.setattr(config, "OPENAI_API_KEY", "chave-de-teste")
    monkeypatch.setattr(config, "IA_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "IA_LOG", tmp_path / "ia.jsonl")
    monkeypatch.setattr(ia, "_cache_memoria", {})
    respostas, chamadas = [], []

    def chamar(mensagens, json_saida=False, max_tokens=700, ferramentas=None):
        chamadas.append(mensagens)
        r = respostas.pop(0)
        if callable(r):
            r = r(mensagens)
        if isinstance(r, str):
            return SimpleNamespace(content=r, tool_calls=None)
        return r

    monkeypatch.setattr(ia, "_chamar", chamar)
    return SimpleNamespace(respostas=respostas, chamadas=chamadas, log=tmp_path / "ia.jsonl")


def _deal_atacar(v):
    return v.deals[v.deals.acao == "Atacar agora"].iloc[0].opportunity_id


def test_sem_chave_usa_template(monkeypatch, v):
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    r = ia.explicar_deal(v, _deal_atacar(v))
    assert r["fonte"] == "template" and r["texto"].startswith("Score ")
    assert ia.briefing(v, agente=v.deals.iloc[0].agente)["fonte"] == "template"


def test_numero_inventado_refaz_e_cai_no_template(llm_falso, v):
    llm_falso.respostas += ["Este deal vale US$ 999.999 e tem 87% de chance.", "Ainda inventando: 12345."]
    r = ia.explicar_deal(v, _deal_atacar(v))
    assert r["fonte"] == "template"
    assert len(llm_falso.chamadas) == 2  # tentativa + 1 refação
    assert "não está nos fatos" in llm_falso.chamadas[1][-1]["content"]


def test_texto_valido_vira_ia_e_fica_em_cache(llm_falso, v):
    oid = _deal_atacar(v)
    d = ia.fato_deal(MOTOR.visao(DATA_PRESSAO).deals.set_index("opportunity_id").loc[oid].to_dict() | {"opportunity_id": oid})
    texto = f"Score {d['score']}: chance de {d['chance_no_prazo']} e {d['valor_esperado']} esperados. Peça a decisão."
    llm_falso.respostas.append(texto)
    r1 = ia.explicar_deal(v, oid)
    r2 = ia.explicar_deal(v, oid)
    assert r1["fonte"] == "ia" and r1["texto"] == texto
    assert r2.get("cache") is True and len(llm_falso.chamadas) == 1
    assert llm_falso.log.exists()


def test_frase_proibida_e_bloqueada():
    problemas = ia.problemas_no_texto("A conta tem alta chance de fechar, perfil ideal.", "{}")
    assert len(problemas) == 2


def test_perguntar_usa_ferramenta_e_valida_contra_o_resultado(llm_falso, v):
    chamada = SimpleNamespace(id="c1", function=SimpleNamespace(name="consultar_emergencia", arguments="{}"))
    llm_falso.respostas.append(SimpleNamespace(content=None, tool_calls=[chamada]))

    def responde_com_fato(mensagens):
        fatos = json.loads(mensagens[-1]["content"])
        return f"Faltam {fatos['falta_para_a_meta']} para a meta."

    llm_falso.respostas.append(responde_com_fato)
    r = ia.perguntar(v, "Quanto falta para a meta?")
    assert r["fonte"] == "ia" and r["ferramentas"] == ["consultar_emergencia"]
    assert "US$" in r["texto"]


def test_ferramenta_com_filtro_invalido_devolve_erro_ao_modelo(v):
    assert "erro" in ia.executar_ferramenta(v, "consultar_time", {"manager": "Ninguém"})


def test_rascunho_json(llm_falso, v):
    llm_falso.respostas.append(json.dumps({"assunto": "Próximos passos", "corpo": "Olá, podemos avançar?"}))
    r = ia.rascunho(v, _deal_atacar(v), "followup")
    assert r["fonte"] == "ia" and r["assunto"] == "Próximos passos"


def test_emails_gerados_em_arquivo_sem_envio(monkeypatch, tmp_path, v):
    monkeypatch.setattr(config, "OPENAI_API_KEY", None)
    monkeypatch.setattr(config, "EMAIL_SAIDA", tmp_path / "saida")
    r = emails.executar(v, modo="arquivo", nome="Head de Revenue Operations")
    assert len(r["emails"]) == 1 and not r["emails"][0]["enviado"]
    html = (tmp_path / "saida" / DATA_PRESSAO / r["emails"][0]["arquivo"]).read_text(encoding="utf-8")
    assert "Plano de resgate" in html and "Ritmo por vendedor" in html

    agente = v.deals[v.deals.acao == "Atacar agora"].iloc[0].agente
    email = emails.montar(v, "vendedor", agente, ["x@example.com"])
    assert email.publico == "equipe" and "Atacar agora" in email.html and "EMERGÊNCIA" in email.assunto


def test_envio_real_recusa_destinatario_de_exemplo(monkeypatch, v):
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.teste")
    monkeypatch.setattr(config, "SMTP_USER", "u")
    monkeypatch.setattr(config, "SMTP_PASSWORD", "p")
    monkeypatch.setattr(config, "EMAIL_REDIRECIONAR", None)
    email = emails.Email("equipe", "vendedor", "Fulano", ["fulano@example.com"], "a", "<p>x</p>", "x")
    with pytest.raises(RuntimeError, match="example.com"):
        emails.enviar(email)
