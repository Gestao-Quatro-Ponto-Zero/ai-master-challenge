"""Ligação simulada do canal telefone (Jó, 2026-11-16): transcrição e voz locais.

- O áudio é validado antes de ir ao modelo (vazio, não WAV, curto, longo, grande).
- A transcrição usa português e o vocabulário do suporte; a voz não lê marcação nem link.
- O texto transcrito entra na conversa como texto digitado: dado pessoal falado é mascarado igual.
- A ida e volta real (voz da atendente → transcrição) roda quando os modelos estão instalados.
"""
from __future__ import annotations

import io
import json
import sys
import wave
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

import conversa as cv  # noqa: E402
import voz  # noqa: E402
from modelo import carregar  # noqa: E402


def wav(segundos: float, taxa: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(b"\x00\x00" * int(segundos * taxa))
    return buf.getvalue()


@pytest.mark.parametrize("dados, motivo", [(b"", "vazio"), (None, "vazio"), (b"isto nao e audio", "WAV"),
                                           (wav(0.1), "curto"), (wav(61), "60 segundos")])
def test_audio_invalido_nao_vai_ao_modelo(dados, motivo):
    with pytest.raises(voz.AudioInvalido, match=motivo):
        voz.transcrever(dados, modelo=SimpleNamespace(transcribe=lambda *a, **k: pytest.fail("chamou o modelo")))


def test_audio_grande_demais(monkeypatch):
    monkeypatch.setattr(voz, "MAX_BYTES", 1000)
    with pytest.raises(voz.AudioInvalido, match="grande"):
        voz.validar_audio(wav(1))


def test_transcricao_em_portugues_com_vocabulario_do_suporte():
    chamadas = []

    def transcribe(_audio, **k):
        chamadas.append(k)
        return [SimpleNamespace(text=" meu Outlook "), SimpleNamespace(text="parou.")], None
    texto = voz.transcrever(wav(2), modelo=SimpleNamespace(transcribe=transcribe))
    assert texto == "meu Outlook parou."
    assert chamadas[0]["language"] == "pt" and "Outlook" in chamadas[0]["initial_prompt"]


@pytest.mark.parametrize("etapa, trecho", [("nome", "primeiro nome"), ("email", "arroba"), ("cpf", "dígito"),
                                           ("assist_cep", "dígito"), ("relato", "Outlook"), (None, "Outlook")])
def test_contexto_da_transcricao_segue_a_etapa(etapa, trecho):
    assert trecho in voz.contexto(etapa)


@pytest.mark.parametrize("texto, fala", [
    ("Passo 1: abra o **Outlook**.\nDeu certo?", "Passo 1: abra o Outlook. Deu certo?"),
    ("Olá, Ana,\n\nComo posso ajudar", "Olá, Ana, Como posso ajudar."),
    ("Veja em https://exemplo.com/ajuda o guia", "Veja em o guia."),
    ("  \n ", ""),
])
def test_fala_sem_marcacao_nem_link(texto, fala):
    assert voz.texto_para_fala(texto) == fala


def test_nada_para_falar_nao_chama_a_voz():
    assert voz.sintetizar("**  **", voz=SimpleNamespace(synthesize_wav=lambda *a: pytest.fail("chamou a voz"))) is None


def test_ligacao_marca_o_registro_e_mascara_cpf_falado(monkeypatch, tmp_path):
    monkeypatch.setattr(cv, "chave_deepseek", lambda: None)
    monkeypatch.setattr(cv, "CONVERSAS", tmp_path / "conversas.jsonl")
    c = cv.Conversa(carregar(), canal="telefone", voz=True)
    c.receber("Ana")
    c.receber("quero o reembolso do pedido 4521, o fone veio quebrado")
    c.receber("o pedido 4521 do fone de ouvido")
    c.receber("meu CPF é 123.456.789-09")   # como a transcrição escreve um CPF ditado
    reg = [json.loads(x) for x in (tmp_path / "conversas.jsonl").read_text().splitlines()]
    assert reg[-1]["voz"] is True and reg[-1]["canal"] == "telefone"
    assert "123.456.789-09" not in json.dumps(reg[-1], ensure_ascii=False)


def test_voz_so_vale_no_telefone(monkeypatch, tmp_path):
    monkeypatch.setattr(cv, "chave_deepseek", lambda: None)
    monkeypatch.setattr(cv, "CONVERSAS", tmp_path / "conversas.jsonl")
    c = cv.Conversa(carregar(), canal="chat", voz=True)
    c.receber("Ana")
    assert json.loads((tmp_path / "conversas.jsonl").read_text())["voz"] is False


@pytest.mark.skipif(not voz.disponivel(), reason="Piper ou faster-whisper não instalados")
def test_ida_e_volta_real_voz_e_transcricao():
    audio = voz.sintetizar("Quero o reembolso do pedido, o fone veio quebrado.")
    assert 1 < voz.duracao_wav(audio) < 10
    texto = voz.transcrever(audio).lower()
    assert "reembolso" in texto and "pedido" in texto


@pytest.mark.parametrize("transcrito, etapa, esperado", [
    ("1.00.000.001.08", "assist_cpf", "10000000108"),                       # bateria 67: CPF ditado
    ("Um, três, zero, dois, cinco, traço, zero, zero, zero.", "assist_cep", "13025000"),
    ("onze nove um dois três quatro cinco seis sete oito", "telefone", "11912345678"),
    ("1191 234 5678", "telefone", "11912345678"),
    ("Ana, ponto teste a rouba, exemplo ponto com.", "email", "ana.teste@exemplo.com"),
    ("Ana.testearrobaexemplo.com", "email", "ana.teste@exemplo.com"),          # bateria 68: arroba grudado
    ("Prefiro não informar.", "cpf", "Prefiro não informar."),               # recusa segue como foi dita
    ("não tenho e-mail", "email", "não tenho e-mail"),
    ("pedido 4587, teclado", "detalhe", "pedido 4587, teclado"),              # fora da coleta, nada muda
    ("um dois três", "relato", "um dois três"),
])
def test_ditado_volta_ao_formato_do_validador(transcrito, etapa, esperado):
    assert voz.ditado(transcrito, etapa) == esperado


@pytest.mark.parametrize("transcrito", ["E aí, né?", "Vem lá.", "Ahn.", "Alô?", "Tá, certo."])
def test_muleta_de_fala_nao_vira_nome(transcrito):
    from dados_pessoais import extrair_nome
    assert extrair_nome(transcrito) is None


def test_nome_transcrito_continua_valendo():
    from dados_pessoais import extrair_nome
    assert extrair_nome("Meu nome é Ana.") == "Ana" and extrair_nome("Carlos.") == "Carlos"


# Ligação contínua e interpretação da fala (Jó, 2026-11-16, segundo pedido) ------------------------------------------
import base64  # noqa: E402

from ligacao import audio_da_fala  # noqa: E402
from roteador import ENCERRADA, EXECUCAO  # noqa: E402


def test_fala_do_navegador_vira_audio():
    w = wav(1)
    assert audio_da_fala({"seq": 3, "wav": base64.b64encode(w).decode()}) == (3, w)


@pytest.mark.parametrize("valor", [None, "texto", {"seq": 1}, {"seq": 1, "wav": "isto não é base64!"},
                                   {"seq": "x", "wav": "AAAA"}])
def test_fala_fora_do_formato_e_ignorada(valor):
    assert audio_da_fala(valor) is None


class _Resp:
    def __init__(self, corpo):
        self._corpo, self.status_code = corpo, 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._corpo


def _ia_falsa(monkeypatch, enviados):
    def post(*_a, **k):
        msgs = k["json"]["messages"]
        enviados.append(json.dumps(msgs, ensure_ascii=False))
        if k["json"].get("response_format"):
            corpo = json.dumps({"resumo_pt": "outlook", "resumo_en": "outlook not syncing email", "acao_sensivel": None,
                                "resolvido": False, "cliente_desistiu": False, "assistencia_tecnica": False,
                                "comando_restrito": None})
        else:
            corpo = "Qual é a versão do Outlook?"
        return _Resp({"choices": [{"message": {"content": corpo}}], "usage": {"total_tokens": 10}})
    monkeypatch.setattr(cv, "chave_deepseek", lambda: "chave-de-teste")
    monkeypatch.setattr(cv.requests, "post", post)


@pytest.mark.parametrize("canal, voz_ligada, espera", [("telefone", True, True), ("telefone", False, False),
                                                       ("chat", True, False)])
def test_ia_interpreta_a_transcricao_so_na_ligacao_por_voz(monkeypatch, tmp_path, canal, voz_ligada, espera):
    monkeypatch.setattr(cv, "CONVERSAS", tmp_path / "conversas.jsonl")
    enviados = []
    _ia_falsa(monkeypatch, enviados)
    c = cv.Conversa(carregar(), canal=canal, voz=voz_ligada)
    c.receber("Meu nome é Carlos")
    c.receber("meu altuco parou de sincronizar os e-mails")
    assert enviados and all(("transcrição automática" in e) is espera for e in enviados)


def test_desligar_no_meio_fecha_como_desistencia(monkeypatch, tmp_path):
    monkeypatch.setattr(cv, "chave_deepseek", lambda: None)
    monkeypatch.setattr(cv, "CONVERSAS", tmp_path / "conversas.jsonl")
    c = cv.Conversa(carregar(), canal="telefone", voz=True)
    c.receber("Carlos")
    c.desligar()
    reg = json.loads((tmp_path / "conversas.jsonl").read_text().splitlines()[-1])
    assert c.encerrada and reg["destino"] == ENCERRADA and not reg["em_andamento"]
    c.desligar()                                    # segundo clique não muda nada
    assert len(c.rodadas) == 2


def test_desligar_com_pedido_de_reembolso_continua_com_pessoa(monkeypatch, tmp_path):
    monkeypatch.setattr(cv, "chave_deepseek", lambda: None)
    monkeypatch.setattr(cv, "CONVERSAS", tmp_path / "conversas.jsonl")
    c = cv.Conversa(carregar(), canal="telefone", voz=True)
    c.receber("Carlos")
    c.receber("quero o reembolso do pedido 4521, o fone veio quebrado")
    c.receber("pedido 4521 do fone")
    assert c.pendente is not None and c.pendente.destino == EXECUCAO
    c.desligar()
    reg = json.loads((tmp_path / "conversas.jsonl").read_text().splitlines()[-1])
    assert reg["destino"] == EXECUCAO and not reg["em_andamento"]


def test_desligar_antes_de_falar_nao_cria_chamada(monkeypatch, tmp_path):
    monkeypatch.setattr(cv, "CONVERSAS", tmp_path / "conversas.jsonl")
    cv.Conversa(carregar(), canal="telefone", voz=True).desligar()
    assert not (tmp_path / "conversas.jsonl").exists()
