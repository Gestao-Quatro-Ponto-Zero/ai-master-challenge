"""Voz da atendente com o Kokoro, tocada frase a frase (Jó autorizou em 2026-11-16 21:45 BRT)."""
from __future__ import annotations

import io
import sys
import wave
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pytest  # noqa: E402

import ligacao  # noqa: E402
import voz  # noqa: E402


def test_frases_primeira_curta_sai_sozinha():
    assert voz.frases("Entendi. Antes de passar o seu atendimento para uma pessoa do time, preciso de três dados "
                      "rápidos. Qual é o CPF usado na compra?") == [
        "Entendi. Antes de passar o seu atendimento para uma pessoa do time, preciso de três dados rápidos.",
        "Qual é o CPF usado na compra?"]


def test_frase_curta_nao_picota():
    assert voz.frases("Certo. Ok. Tudo bem.") == ["Certo. Ok. Tudo bem."]
    assert voz.frases("Obrigada. Qual é o melhor telefone para contato, com DDD? Pode ser.") == [
        "Obrigada. Qual é o melhor telefone para contato, com DDD? Pode ser."]


def test_primeira_frase_sai_sozinha_mesmo_curta():
    assert voz.frases("Prazer, João. Certo. Qual é o sistema, programa ou aparelho que está com problema?") == [
        "Prazer, João.", "Certo. Qual é o sistema, programa ou aparelho que está com problema?"]


def test_abreviacao_por_extenso_e_sem_corte():
    partes = voz.frases("A mais perto fica na Av. Francisco Glicério, 1000, Centro. Fale com o Dr. Paulo lá.")
    assert partes == ["A mais perto fica na Avenida Francisco Glicério, 1000, Centro.", "Fale com o Doutor Paulo lá."]


def test_frases_vazias():
    assert voz.frases("**  **") == [] and voz.frases("") == []


def test_wav_do_kokoro_e_16_bits():
    dados = voz._wav(np.array([0.0, 0.5, -1.5, 1.0], dtype=np.float32), 24000)
    with wave.open(io.BytesIO(dados)) as w:
        assert (w.getsampwidth(), w.getnchannels(), w.getframerate(), w.getnframes()) == (2, 1, 24000, 4)
        assert list(np.frombuffer(w.readframes(4), "<i2")) == [0, 16383, -32767, 32767]


def test_motor_piper_quando_escolhido(monkeypatch):
    monkeypatch.setattr(voz, "VOZ_MOTOR", "piper")
    assert voz.motor() == "piper"


def test_motor_piper_quando_modelo_falta(monkeypatch, tmp_path):
    monkeypatch.setattr(voz, "VOZ_KOKORO", tmp_path / "nao-existe.onnx")
    assert voz.motor() == "piper"


def test_voz_explicita_usa_piper_mesmo_com_kokoro(monkeypatch):
    usada = []
    falsa = SimpleNamespace(synthesize_wav=lambda texto, w: (usada.append(texto), w.setnchannels(1), w.setsampwidth(2),
                                                              w.setframerate(16000), w.writeframes(b"\0\0" * 10)))
    monkeypatch.setattr(voz, "_kokoro", lambda: pytest.fail("cliente da bateria não pode usar a voz da atendente"))
    assert voz.sintetizar("Oi.", voz=falsa) and usada == ["Oi."]


def test_fila_de_trechos_no_navegador():
    js = ligacao.JS
    assert "S.filaFala.push(fala)" in js and "function fimDoTrecho" in js
    assert "if (S.mais)" in js                       # espera o próximo trecho sem reabrir a escuta
    assert "S.mais = !!data.mais" in js


@pytest.mark.skipif(voz.motor() != "kokoro", reason="Kokoro não instalado")
def test_kokoro_ida_e_volta():
    audio = voz.sintetizar("Quero o reembolso do pedido, o fone veio quebrado.")
    assert 1.5 < voz.duracao_wav(audio) < 8
    assert "reembolso" in voz.transcrever(audio).lower()


def test_desligar_corta_trecho_atrasado():
    assert "if (S.fechada) return;" in ligacao.JS
