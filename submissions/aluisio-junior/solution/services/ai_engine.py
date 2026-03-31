import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ask_ai(question: str, context: dict):
    """
    IA responde com base nos dados do sistema
    """

    prompt = f"""
    Você é um AI Master especialista em SaaS B2B.

    CONTEXTO DO NEGÓCIO:
    Plataforma SaaS com churn elevado.

    DADOS ANALÍTICOS:
    {context}

    PERGUNTA DO EXECUTIVO:
    {question}

    REGRAS:
    - Responda como consultor estratégico
    - Seja direto
    - Use linguagem executiva
    - Traga causa raiz (não superficial)
    - Sugira ações práticas

    FORMATO:
    1. Diagnóstico
    2. Evidência (dados)
    3. Recomendação
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text if hasattr(response, "text") else str(response)