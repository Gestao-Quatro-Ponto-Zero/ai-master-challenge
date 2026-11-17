"""Parâmetros do protótipo. Cada valor diz de onde veio."""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
REPO = RAIZ.parents[3]

# Dados (baixados do Kaggle, fora do git). Podem ser trocados por variável de ambiente.
DATASET1 = Path(os.getenv("DATASET1", REPO / "dados/support/customer_support_tickets.csv"))
DATASET2 = Path(os.getenv("DATASET2", REPO / "dados/it/all_tickets_processed_improved_v3.csv"))

MODELO = RAIZ / "saida" / "classificador.joblib"
LOTE = RAIZ / "saida" / "lote-teste.csv"
CONVERSAS = RAIZ / "saida" / "conversas.jsonl"
TRADUCOES = RAIZ / "saida" / "traducoes-fila.json"

# Decisão do Jó (process log, rodada 45): a IA roteia sozinha a partir de 0,8 de confiança.
LIMITE_CONFIANCA = 0.8

# Nome da atendente nos 4 canais (pedido do Jó em 2026-11-16 21:16 BRT: "o assistente também precisa de um nome").
NOME_ATENDENTE = os.environ.get("NOME_ATENDENTE", "Clara")
# Versão das regras do robô em apresentação. Chamadas de versões anteriores ficam no registro e no process log, mas
# saem do painel e do dashboard (Jó, 2026-11-16: o teste do robô anterior não é resultado do produto atual).
VERSAO_ROBO = "2026-11-16"
# Parâmetro "a definir" do fluxo (rodada 48). 3 é só o valor da demonstração.
MAX_PERGUNTAS = 3
# Mesma separação do relatório do classificador (20% de teste, semente 42).
SEMENTE = 42
FRACAO_TESTE = 0.2

# Teto de gasto da IA com o link público (pedido do Jó, 2026-11-11): a conversa média gasta cerca de 6.400 tokens
# (rodada 59). Passou do teto, a IA para e uma pessoa assume, como na IA fora do ar.
LIMITE_TOKENS_CONVERSA = int(os.getenv("LIMITE_TOKENS_CONVERSA", "40000"))
LIMITE_TOKENS_DIA = int(os.getenv("LIMITE_TOKENS_DIA", "600000"))

# IA conversacional (DeepSeek, API compatível com OpenAI). Sem chave, roda o modo sem IA.
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODELO = os.getenv("DEEPSEEK_MODELO", "deepseek-chat")
# Ordem de procura do arquivo com a chave: ARQUIVO_ENV, .env do protótipo, .env fora do repositório.
ARQUIVOS_CHAVE = [Path(p) for p in [os.getenv("ARQUIVO_ENV"), RAIZ / ".env", REPO.parent / ".env"] if p]


def chave_deepseek() -> str | None:
    """Lê DEEPSEEK_API_KEY do ambiente ou do arquivo .env. Nunca imprime a chave."""
    if os.getenv("DEEPSEEK_API_KEY"):
        return os.environ["DEEPSEEK_API_KEY"]
    for arquivo in ARQUIVOS_CHAVE:
        if arquivo.exists():
            for linha in arquivo.read_text().splitlines():
                if linha.strip().startswith("DEEPSEEK_API_KEY="):
                    valor = linha.split("=", 1)[1].strip().strip('"').strip("'")
                    if valor:
                        return valor
    return None

# Ligação por voz no canal telefone (Jó, 2026-11-16: "o canal do telefone teria que simular uma ligação mesmo").
# Tudo roda nesta máquina: a voz do cliente é dado pessoal e não vai para IA externa; só o texto transcrito segue o
# caminho de sempre, com nome, CPF, telefone e e-mail mascarados.
# Transcrição: faster-whisper "small" em int8 na CPU. Medido em 2026-11-16 com 5 frases do suporte: "small" acertou
# Outlook, reembolso e impressora; "base" trocou palavras ("e-meios", "imprimi"). Em 12 falas humanas do FLEURS pt-BR:
# small 5,4% de erro por palavra e cerca de 4 s por turno; medium 3,1% mas 10 s por turno; large-v3-turbo 11 a 15 s
# por turno. Nesta CPU, só o small mantém a ligação fluida (o Whisper sempre processa uma janela de 30 s).
WHISPER_MODELO = os.getenv("WHISPER_MODELO", "small")
# Voz da atendente: Kokoro (kokoro-onnx 0.6.1, int8), voz feminina pt-BR "pf_dora", local como a transcrição.
# Troca autorizada pelo Jó em 2026-11-16 21:45 BRT, depois de ele achar a voz do Piper robótica. Medido em 5 frases do
# suporte: a transcrição errou 1,4% das palavras ditas pelo Kokoro contra 7,6% pelo Piper (pronúncia mais clara), mas
# o Kokoro gera em cerca de 0,55 s por segundo de fala contra 0,08 s do Piper; por isso a resposta toca frase a frase.
# O Piper (voz "faber") fica como reserva se o modelo do Kokoro faltar, e a voz "cadu" segue como cliente na bateria.
# Modelos fora do git (binários de 60 a 120 MB).
VOZ_PIPER = Path(os.getenv("VOZ_PIPER", REPO.parent / "dados/voz/pt_BR-faber-medium.onnx"))
VOZ_KOKORO = Path(os.getenv("VOZ_KOKORO", REPO.parent / "dados/voz/kokoro-v1.0.int8.onnx"))
VOZ_KOKORO_VOZES = VOZ_KOKORO.with_name("voices-v1.0.bin")
VOZ_KOKORO_NOME = os.getenv("VOZ_KOKORO_NOME", "pf_dora")
VOZ_MOTOR = os.getenv("VOZ_MOTOR", "kokoro")   # "kokoro" ou "piper"
# Fala longa demais não é turno de ligação; o limite também protege a CPU do link público.
MAX_SEGUNDOS_FALA = 60
