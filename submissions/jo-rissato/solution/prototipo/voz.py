"""Ligação simulada no canal telefone: transcrição da fala do cliente e voz da atendente, tudo local.

A voz do cliente é dado pessoal: o áudio é transcrito nesta máquina (faster-whisper), não é gravado em disco e
não vai para nenhuma IA externa. O texto transcrito entra na conversa como se tivesse sido digitado, então passa
pelas mesmas máscaras de nome, CPF, telefone e e-mail. A resposta da atendente vira fala com o Piper, também local.

Os modelos carregam só na primeira ligação (preguiçoso) e ficam um por processo.
"""
from __future__ import annotations

import io
import re
import threading
import wave

from config import MAX_SEGUNDOS_FALA, VOZ_PIPER, WHISPER_MODELO

SAUDACAO = "Você ligou para o suporte. Pode falar."
# Vocabulário do suporte para a transcrição: sem ele o modelo escrevia "Altuco" no lugar de Outlook.
VOCABULARIO = ("Atendimento de suporte ao cliente. Outlook, Excel, iPhone, Android, Wi-Fi, impressora, notebook, "
               "reembolso, cancelamento, cobrança, CPF, pedido, e-mail.")
# Contexto da transcrição por etapa (bateria 68, 2026-11-16): o vocabulário do suporte atrapalhava o nome ("Carlos"
# saía "Calos") e o e-mail saía grudado ("anatestearrobaexemplo"); com o contexto da etapa, saem certos.
CONTEXTO = {"nome": "A atendente perguntou como pode chamar o cliente. Ele responde só o primeiro nome, por exemplo "
                    "Maria, João, Ana, Pedro, Carla.",
            "email": "O cliente dita o e-mail falando arroba e ponto, por exemplo: maria ponto silva arroba gmail ponto "
                     "com, joao arroba exemplo ponto com ponto br.",
            "numero": "O cliente dita os números dígito por dígito."}
MAX_BYTES = 12_000_000  # 60 s de WAV 48 kHz mono 16 bits ocupam cerca de 5,8 MB; folga para estéreo

_trava = threading.Lock()
_modelos: dict = {}


class AudioInvalido(ValueError):
    """Áudio vazio, que não é WAV, grande ou longo demais."""


def duracao_wav(dados: bytes) -> float:
    try:
        with wave.open(io.BytesIO(dados)) as w:
            return w.getnframes() / float(w.getframerate() or 1)
    except (wave.Error, EOFError) as erro:
        raise AudioInvalido("o áudio não é WAV") from erro


def validar_audio(dados: bytes | None) -> float:
    """Devolve a duração em segundos ou levanta AudioInvalido com o motivo em português."""
    if not dados:
        raise AudioInvalido("áudio vazio")
    if len(dados) > MAX_BYTES:
        raise AudioInvalido("áudio grande demais")
    segundos = duracao_wav(dados)
    if segundos < 0.3:
        raise AudioInvalido("áudio curto demais")
    if segundos > MAX_SEGUNDOS_FALA:
        raise AudioInvalido(f"fala com mais de {MAX_SEGUNDOS_FALA} segundos")
    return segundos


def texto_para_fala(texto: str) -> str:
    """O que a atendente fala: sem marcação, sem link e sem assinatura de e-mail."""
    t = re.sub(r"https?://\S+", "", texto or "")
    t = re.sub(r"[*_#`>\[\]]", "", t)
    t = re.sub(r"([,;:!?.])\s*\n+\s*", r"\1 ", t)
    t = re.sub(r"\s*\n+\s*", ". ", t)
    t = re.sub(r"([.!?:])\s*\.", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" .")
    if not t:
        return ""
    return t if t[-1] in "!?" else t + "."


# Ditado ao telefone (bateria 67, 2026-11-16): a transcrição escreve "um, três, zero" ou "ana ponto teste a rouba
# exemplo ponto com". Nas etapas de dado, o que foi ditado volta ao formato que o validador lê. Se a conversão não
# der um dado plausível, o texto segue como foi dito (ex.: "prefiro não informar").
ETAPAS_NUMERO = {"cpf", "telefone", "assist_cpf", "assist_cep"}
_NUMEROS = {"zero": "0", "um": "1", "uma": "1", "dois": "2", "duas": "2", "três": "3", "tres": "3", "quatro": "4",
            "cinco": "5", "seis": "6", "meia": "6", "sete": "7", "oito": "8", "nove": "9", "dez": "10", "onze": "11",
            "doze": "12", "treze": "13", "catorze": "14", "quatorze": "14", "quinze": "15", "dezesseis": "16",
            "dezessete": "17", "dezoito": "18", "dezenove": "19"}
# "arroba" vem solto ("a rouba") ou grudado no texto ("anatestearrobaexemplo"): troca em qualquer posição.
_ARROBA = re.compile(r"arroba|arrouba|\ba\s?r?oub?a\b|\ba\s?roba\b|arrob[aá]\b")
_EMAIL = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")


def ditado(texto: str, etapa: str) -> str:
    """Converte dado ditado (CPF, telefone, CEP, e-mail) para o formato escrito; o resto passa igual."""
    t = (texto or "").lower()
    if etapa in ETAPAS_NUMERO:
        t = re.sub(r"[a-zçãéêíóôú]+", lambda m: _NUMEROS.get(m.group(0), m.group(0)), t)
        digitos = re.sub(r"\D", "", t)
        return digitos if len(digitos) >= 8 else texto
    if etapa == "email":
        t = _ARROBA.sub(" @ ", t)
        t = re.sub(r"\bponto\b", " . ", t)
        t = re.sub(r"\b(?:underline|sublinhado)\b", " _ ", t)
        t = re.sub(r"\b(?:hífen|hifen|traço|traco)\b", " - ", t)
        t = re.sub(r"[\s,;!?]+", "", t).strip(".")
        return t if _EMAIL.match(t) else texto
    return texto


def _whisper():
    if "whisper" not in _modelos:
        from faster_whisper import WhisperModel
        _modelos["whisper"] = WhisperModel(WHISPER_MODELO, device="cpu", compute_type="int8", cpu_threads=4)
    return _modelos["whisper"]


def _piper():
    if "piper" not in _modelos:
        from piper import PiperVoice
        _modelos["piper"] = PiperVoice.load(str(VOZ_PIPER))
    return _modelos["piper"]


def aquecer() -> None:
    """Carrega a transcrição em segundo plano quando o cliente clica em Ligar: a primeira fala não espera os 6 s
    de carga do modelo (medido em 2026-11-16)."""
    def carregar():
        with _trava:
            _whisper()
    threading.Thread(target=carregar, daemon=True).start()


def disponivel() -> bool:
    """Ligação por voz só aparece se a voz da atendente e a transcrição estiverem instaladas."""
    try:
        import faster_whisper  # noqa: F401
        import piper  # noqa: F401
    except ImportError:
        return False
    return VOZ_PIPER.exists()


def contexto(etapa: str | None) -> str:
    if etapa in ETAPAS_NUMERO:
        return CONTEXTO["numero"]
    return CONTEXTO.get(etapa or "", VOCABULARIO)


def transcrever(dados: bytes, modelo=None, etapa: str | None = None) -> str:
    """Fala do cliente em texto, com o contexto da etapa da conversa. Um áudio por vez (a CPU é a mesma do link
    público)."""
    validar_audio(dados)
    with _trava:
        m = modelo or _whisper()
        segmentos, _ = m.transcribe(io.BytesIO(dados), language="pt", beam_size=1, vad_filter=True,
                                    initial_prompt=contexto(etapa))
        return " ".join(s.text.strip() for s in segmentos).strip()


def sintetizar(texto: str, voz=None) -> bytes | None:
    """Fala da atendente em WAV, ou None se não houver o que falar."""
    fala = texto_para_fala(texto)
    if not fala:
        return None
    buf = io.BytesIO()
    with _trava:
        v = voz or _piper()
        with wave.open(buf, "wb") as w:
            v.synthesize_wav(fala, w)
    return buf.getvalue()


__all__ = ["SAUDACAO", "AudioInvalido", "aquecer", "contexto", "disponivel", "ditado", "duracao_wav", "sintetizar", "texto_para_fala",
           "transcrever", "validar_audio"]
