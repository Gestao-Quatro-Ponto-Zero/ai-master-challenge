"""Configurações centrais do Lead Scorer — tudo que um dev pode querer ajustar sem
mexer na lógica de scoring/alertas (caminhos, data de referência, pesos, limites).

Os limites de TEMPO (zona de risco, teto do ciclo) não ficam aqui de propósito: são
calculados a partir do histórico em scoring.calcular_benchmarks, pra que o score
continue fazendo sentido se o dataset for trocado por um pipeline real."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Credenciais próprias deste projeto, num .env só dele (ver .env.example). Nada aqui
# lê variáveis genéricas do ambiente (ex.: OPENAI_API_KEY / SMTP_*) — todas as
# variáveis têm o prefixo LEAD_SCORER_.
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = Path(os.getenv("LEAD_SCORER_DATA_DIR", BACKEND_DIR / "data"))

# O dataset é um snapshot que termina em 2017-12-31. Sem override, "hoje" para o
# vendedor é a data do último fechamento registrado (ver dados.carregar). A interface
# também deixa simular qualquer segunda-feira anterior (ver motor.datas_disponiveis).
DATA_REFERENCIA = os.getenv("LEAD_SCORER_DATA_REFERENCIA")

# ── Score de prioridade ───────────────────────────────────────────────────────
# Pesos dos 3 pilares (somam 100). "chance" = probabilidade calibrada de ganhar até
# o fim do horizonte (ver scoring.py e calibracao.py). Histórico da conta, afinidade
# do vendedor, ICP e produto×porte foram testados e ficaram de fora: AUC 0,49–0,52.
PESOS = {"chance": 60, "valor": 25, "dados": 15}

# Horizonte da chance: fim do trimestre atual, ou do próximo se faltar menos que isso
HORIZONTE_MIN_DIAS = 7

# Suavização bayesiana das taxas de ganho (afinidade usada na redistribuição): k deals
# "fictícios" na média — evita que 3 deals e 3 ganhos apareçam como 100%.
SUAVIZACAO_K = 20

# Faixas de score → ação recomendada, por PERCENTIL entre os deals vivos (Engaging dentro
# do ciclo) da data. Corte fixo não serve: a curva de calibração muda com a data
# (rolling-origin) e, com 85/70 fixos, "Atacar agora" variava de 82 a 893 deals.
# Top 15% ≈ 5 a 7 deals por vendedor numa semana típica — uma lista que dá pra trabalhar.
PERCENTIL_ATACAR = 0.85
PERCENTIL_NUTRIR = 0.60

# Deal fora do ciclo (chance zero como está) com preço de tabela a partir disso →
# Requalificar = perguntar ao cliente e, se continuar, reabrir como oportunidade nova
# (relógio zerado). Abaixo disso → Encerrar.
REQUALIFICAR_PRECO_MIN = 1000

# ── Alertas ───────────────────────────────────────────────────────────────────
# "Valor relevante" para um alerta virar crítico: preço no quartil superior dos abertos
QUANTIL_VALOR_RELEVANTE = 0.75
# "Deal grande" do gatilho de esfriamento: top 10% de valor
QUANTIL_DEAL_GRANDE = 0.90
# Teto de críticos por vendedor — acima disso o alerta é rebaixado pra atenção
MAX_CRITICOS_POR_VENDEDOR = 3

# ── Pressão de fechamento / emergência ───────────────────────────────────────
# Janela de emergência antes do fim do trimestre. 30 dias = o último mês do
# trimestre, que é onde os ganhos se concentram no histórico (ver /benchmarks).
JANELA_EMERGENCIA_DIAS = 30
# Meta = média trimestral fechada × fator (1.10 = média + 10%)
META_FATOR = float(os.getenv("LEAD_SCORER_META_FATOR", "1.0"))
# Comparação com o score de N dias atrás pra detectar deal "caindo de faixa"
DIAS_COMPARACAO_SCORE = 7

# ── Capacidade ────────────────────────────────────────────────────────────────
# Throughput medido nos últimos N dias (deals fechados, ganhos + perdidos)
JANELA_THROUGHPUT_DIAS = 90
# Carga ≥ N× a capacidade (lei de Little: throughput × ciclo médio) → sobrecarga
FATOR_SOBRECARGA = 3.0
# Carga abaixo disso = vendedor com folga, candidato a receber deals
FATOR_FOLGA = 1.0

ORIGENS_CORS = os.getenv("LEAD_SCORER_CORS", "http://localhost:3001").split(",")
URL_APP = os.getenv("LEAD_SCORER_URL_APP", "http://localhost:3001")

# ── Camada de IA (OpenAI) ─────────────────────────────────────────────────────
# A IA só INTERPRETA e escreve sobre os números do motor — nunca calcula score/chance.
# Sem chave, toda função cai no texto-template e a ferramenta continua funcionando.
OPENAI_API_KEY = os.getenv("LEAD_SCORER_OPENAI_API_KEY")  # chave exclusiva deste projeto
LLM_MODELO = os.getenv("LEAD_SCORER_LLM_MODEL", "gpt-4o")
LLM_TIMEOUT_S = float(os.getenv("LEAD_SCORER_LLM_TIMEOUT", "60"))
IA_MAX_PERGUNTAS_DIA = int(os.getenv("LEAD_SCORER_IA_MAX_PERGUNTAS_DIA", "200"))
IA_CACHE_DIR = BACKEND_DIR / ".cache_ia"
IA_LOG = BACKEND_DIR / "logs" / "ia.jsonl"

# ── E-mails (equipe e gestão) ─────────────────────────────────────────────────
# 'arquivo' (padrão): gera os HTMLs em saida_emails/ sem enviar nada.
# 'enviar': manda via SMTP — exige config/destinatarios.json e LEAD_SCORER_SMTP_*.
EMAIL_MODO = os.getenv("LEAD_SCORER_EMAIL_MODO", "arquivo")
# Se definido, TODO e-mail vai para este endereço (teste/demo sem atingir ninguém)
EMAIL_REDIRECIONAR = os.getenv("LEAD_SCORER_EMAIL_REDIRECIONAR")
SMTP_HOST = os.getenv("LEAD_SCORER_SMTP_HOST")
SMTP_PORT = int(os.getenv("LEAD_SCORER_SMTP_PORT", "587"))
SMTP_USER = os.getenv("LEAD_SCORER_SMTP_USER")
SMTP_PASSWORD = os.getenv("LEAD_SCORER_SMTP_PASSWORD")
SMTP_FROM = os.getenv("LEAD_SCORER_SMTP_FROM", SMTP_USER or "")
DESTINATARIOS = BACKEND_DIR / "config" / "destinatarios.json"
DESTINATARIOS_EXEMPLO = BACKEND_DIR / "config" / "destinatarios.exemplo.json"
EMAIL_SAIDA = BACKEND_DIR / "saida_emails"
