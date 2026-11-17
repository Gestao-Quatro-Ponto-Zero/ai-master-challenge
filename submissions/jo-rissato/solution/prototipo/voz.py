"""Ligação simulada no canal telefone: transcrição da fala do cliente e voz da atendente, tudo local.

A voz do cliente é dado pessoal: o áudio é transcrito nesta máquina (faster-whisper), não é gravado em disco e
não vai para nenhuma IA externa. O texto transcrito entra na conversa como se tivesse sido digitado, então passa
pelas mesmas máscaras de nome, CPF, telefone e e-mail. A resposta da atendente vira fala com o Kokoro (ou o Piper,
de reserva), também local.

Os modelos carregam só na primeira ligação (preguiçoso) e ficam um por processo.
"""
from __future__ import annotations

import io
import re
import threading
import wave

from config import (MAX_SEGUNDOS_FALA, NOME_ATENDENTE, VOZ_KOKORO, VOZ_KOKORO_NOME, VOZ_KOKORO_VOZES, VOZ_MOTOR,
                    VOZ_PIPER, WHISPER_MODELO)

SAUDACAO = f"Suporte, aqui é a {NOME_ATENDENTE}. Como posso te ajudar?"
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


_ABREVIACOES = {"Av": "Avenida", "Dr": "Doutor", "Dra": "Doutora", "Sr": "Senhor", "Sra": "Senhora", "Prof": "Professor"}
_SEM_CORTE = re.compile(r"\b(?:[A-Z][a-z]{0,3}|n|nº)\.$")   # abreviação que sobrou: não termina frase


def texto_para_fala(texto: str) -> str:
    """O que a atendente fala: sem marcação, sem link e sem assinatura de e-mail."""
    t = re.sub(r"https?://\S+", "", texto or "")
    t = re.sub(r"[*_#`>\[\]]", "", t)
    t = re.sub(r"([,;:!?.])\s*\n+\s*", r"\1 ", t)
    t = re.sub(r"\s*\n+\s*", ". ", t)
    t = re.sub(r"([.!?:])\s*\.", r"\1", t)
    for abrev, extenso in _ABREVIACOES.items():   # a voz soletrava "Av." como "A V"
        t = re.sub(rf"\b{abrev}\.(?=\s)", extenso, t)
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
        # 6 threads: 3,0 s contra 3,7 s com 4 numa fala de 4 s; 8 ganharia só mais 0,2 s e disputaria a CPU (2026-11-16).
        _modelos["whisper"] = WhisperModel(WHISPER_MODELO, device="cpu", compute_type="int8", cpu_threads=6)
    return _modelos["whisper"]


def _piper():
    if "piper" not in _modelos:
        from piper import PiperVoice
        _modelos["piper"] = PiperVoice.load(str(VOZ_PIPER))
    return _modelos["piper"]


def _kokoro():
    if "kokoro" not in _modelos:
        from kokoro_onnx import Kokoro
        _modelos["kokoro"] = Kokoro(str(VOZ_KOKORO), str(VOZ_KOKORO_VOZES))
    return _modelos["kokoro"]


# A voz pt-BR do Kokoro foi treinada com os fonemas do espeak "pt-br" em que o "dj" de "de", o "tch" de "te" e os
# ditongos ("bem", "mal") são um símbolo só (ʤ, ʧ, A, W). O kokoro-onnx, sozinho, entrega esses sons em dois símbolos
# soltos, que a voz conhece de outras línguas, e o Jó ouviu sotaque de Portugal (2026-11-16 23:08 BRT). Aqui o texto
# vira fonemas no mesmo formato do treino (tabela do misaki, o conversor oficial do Kokoro).
_JUNTA = sorted({"a^ɪ": "I", "a^ʊ": "W", "d^z": "ʣ", "d^ʒ": "ʤ", "e^ɪ": "A", "o^ʊ": "O", "ə^ʊ": "Q", "s^s": "S",
                 "t^s": "ʦ", "t^ʃ": "ʧ", "ɔ^ɪ": "Y"}.items())


def fonemas(fala: str) -> str:
    """Fonemas pt-BR da fala no formato com que a voz do Kokoro foi treinada."""
    if "espeak" not in _modelos:
        _kokoro()  # aponta o phonemizer para o espeak que vem com o kokoro-onnx
        from phonemizer.backend import EspeakBackend
        _modelos["espeak"] = EspeakBackend("pt-br", preserve_punctuation=True, with_stress=True, tie="^",
                                           language_switch="remove-flags")
    ps = _modelos["espeak"].phonemize([fala])[0].strip()
    for velho, novo in _JUNTA:
        ps = ps.replace(velho, novo)
    return ps.replace("^", "")


def motor() -> str:
    """Motor da voz da atendente: o Kokoro se estiver instalado e escolhido, senão o Piper."""
    if VOZ_MOTOR == "kokoro" and VOZ_KOKORO.exists() and VOZ_KOKORO_VOZES.exists():
        try:
            import kokoro_onnx  # noqa: F401
            return "kokoro"
        except ImportError:
            pass
    return "piper"


def aquecer() -> None:
    """Carrega a transcrição em segundo plano quando o cliente clica em Ligar: a primeira fala não espera os 6 s
    de carga do modelo (medido em 2026-11-16)."""
    def carregar():
        with _trava:
            _whisper()
            if motor() == "kokoro":
                fonemas("Oi.")
    threading.Thread(target=carregar, daemon=True).start()


def disponivel() -> bool:
    """Ligação por voz só aparece se a voz da atendente e a transcrição estiverem instaladas."""
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    if motor() == "kokoro":
        return True
    try:
        import piper  # noqa: F401
    except ImportError:
        return False
    return VOZ_PIPER.exists()


def contexto(etapa: str | None) -> str:
    if etapa in ETAPAS_NUMERO:
        return CONTEXTO["numero"]
    return CONTEXTO.get(etapa or "", VOCABULARIO)


ETAPAS_DITADO = ETAPAS_NUMERO | {"nome", "email"}


def busca(etapa: str | None) -> int:
    """Caminhos da busca da transcrição: 5 no ditado de dados, 1 no resto (0,8 s mais rápido em fala longa)."""
    return 5 if etapa in ETAPAS_DITADO else 1


def transcrever(dados: bytes, modelo=None, etapa: str | None = None) -> str:
    """Fala do cliente em texto, com o contexto da etapa da conversa. Um áudio por vez (a CPU é a mesma do link
    público)."""
    validar_audio(dados)
    with _trava:
        m = modelo or _whisper()
        # Medido em 12 falas humanas do FLEURS pt-BR (2026-11-16): sem o filtro de silêncio o erro por palavra caiu de
        # 6,9% para 6,2% (a ligação já manda só o trecho falado). Na mesma base, com o contexto atual, a busca com 5
        # caminhos erra 5,0% contra 5,4% com 1 caminho, mas leva 4,38 s contra 3,59 s de mediana. Os 5 caminhos ficam
        # só onde um erro custa caro (nome, e-mail, CPF, telefone, CEP); no relato a IA entende a frase mesmo assim.
        segmentos, _ = m.transcribe(io.BytesIO(dados), language="pt", beam_size=busca(etapa), vad_filter=False,
                                    without_timestamps=True, initial_prompt=contexto(etapa))
        return " ".join(s.text.strip() for s in segmentos).strip()


def frases(texto: str) -> list[str]:
    """Resposta da atendente em trechos para tocar um a um: a primeira frase começa a tocar enquanto o resto é gerado.
    A primeira sai sozinha a partir de 12 caracteres ("Prazer, João."), porque é a que o cliente espera; juntar com a
    seguinte levou uma resposta a 11,5 s no teste do navegador. Depois dela, frase muito curta ("Certo.") vai junto
    com a seguinte, para não picotar a fala."""
    fala = texto_para_fala(texto)
    if not fala:
        return []
    partes, atual = [], ""
    for f in re.split(r"(?<=[.!?])\s+", fala):
        atual = f"{atual} {f}".strip()
        if len(atual) >= (12 if not partes else 25) and not _SEM_CORTE.search(atual):
            partes.append(atual)
            atual = ""
    if atual:
        if partes and len(atual) < 25:
            partes[-1] = f"{partes[-1]} {atual}"
        else:
            partes.append(atual)
    return partes


def _wav(amostras, taxa: int) -> bytes:
    import numpy as np
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes((np.clip(amostras, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def sintetizar(texto: str, voz=None) -> bytes | None:
    """Fala da atendente em WAV, ou None se não houver o que falar. `voz` força uma voz do Piper (cliente da bateria)."""
    fala = texto_para_fala(texto)
    if not fala:
        return None
    with _trava:
        if voz is None and motor() == "kokoro":
            amostras, taxa = _kokoro().create(fonemas(fala), voice=VOZ_KOKORO_NOME, speed=1.0, is_phonemes=True)
            return _wav(amostras, taxa)
        buf = io.BytesIO()
        v = voz or _piper()
        with wave.open(buf, "wb") as w:
            v.synthesize_wav(fala, w)
    return buf.getvalue()


__all__ = ["SAUDACAO", "AudioInvalido", "aquecer", "busca", "contexto", "disponivel", "ditado", "duracao_wav", "fonemas",
           "frases", "motor", "sintetizar", "texto_para_fala", "transcrever", "validar_audio"]
