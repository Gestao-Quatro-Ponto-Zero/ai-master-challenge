"""
Protótipo: AI Ticket Assistant
Challenge 002 — Redesign de Suporte (G4 AI Master Challenge)

Recebe o texto de um ticket e retorna:
- Categoria prevista
- Confiança
- Prioridade sugerida
- Se deve ir para agente sênior
- Resposta sugerida (quando aplicável)
- Flags de risco
"""

import joblib
from typing import Dict, Any, Optional
import re

# Carrega o modelo treinado (TF-IDF + Logistic Regression)
# Acurácia de validação: ~85.3%
clf = joblib.load('ticket_classifier.joblib')

# ====================== REGRAS DE NEGÓCIO ======================
CATEGORY_RULES = {
    "Hardware": {
        "default_priority": "High",
        "auto_suggest": False,
        "send_to_senior": True,
        "reason": "Problemas de hardware geralmente exigem diagnóstico técnico e possíveis substituições."
    },
    "Access": {
        "default_priority": "Medium",
        "auto_suggest": True,
        "send_to_senior": False,
        "reason": "Solicitações de acesso são frequentemente padronizadas e de baixo risco."
    },
    "HR Support": {
        "default_priority": "Medium",
        "auto_suggest": False,
        "send_to_senior": True,
        "reason": "Assuntos de RH envolvem dados sensíveis e julgamento humano."
    },
    "Miscellaneous": {
        "default_priority": "Low",
        "auto_suggest": True,
        "send_to_senior": False,
        "reason": "Categoria residual — muitos casos simples podem receber resposta sugerida."
    },
    "Storage": {
        "default_priority": "Medium",
        "auto_suggest": True,
        "send_to_senior": False,
        "reason": "Alertas de storage (mailbox full etc.) costumam ter procedimentos claros."
    },
    "Purchase": {
        "default_priority": "Medium",
        "auto_suggest": False,
        "send_to_senior": True,
        "reason": "Compras envolvem orçamento e aprovação — melhor com humano."
    },
    "Internal Project": {
        "default_priority": "Low",
        "auto_suggest": True,
        "send_to_senior": False,
        "reason": "Demandas internas de projeto geralmente são de baixo risco externo."
    },
    "Administrative rights": {
        "default_priority": "High",
        "auto_suggest": False,
        "send_to_senior": True,
        "reason": "Direitos administrativos são sensíveis do ponto de vista de segurança."
    }
}

RESPONSE_TEMPLATES = {
    "Access": (
        "Olá,\n\n"
        "Recebemos sua solicitação de acesso. Para prosseguirmos, por favor confirme:\n"
        "1. O sistema/aplicação desejada\n"
        "2. O nível de acesso necessário\n"
        "3. A justificativa de negócio\n\n"
        "Assim que tivermos essas informações, a liberação será analisada em até 1 dia útil.\n\n"
        "Atenciosamente,\nEquipe de Suporte"
    ),
    "Storage": (
        "Olá,\n\n"
        "Identificamos que seu espaço de armazenamento está próximo do limite.\n\n"
        "Recomendamos:\n"
        "- Excluir arquivos temporários e e-mails antigos\n"
        "- Mover arquivos grandes para o drive corporativo\n"
        "- Verificar a lixeira\n\n"
        "Se precisar de aumento de cota, responda este ticket com a justificativa.\n\n"
        "Atenciosamente,\nEquipe de Suporte"
    ),
    "Miscellaneous": (
        "Olá,\n\n"
        "Obrigado por entrar em contato. Analisamos sua mensagem e, para podermos ajudar da melhor forma, "
        "poderia fornecer um pouco mais de detalhes sobre o problema?\n\n"
        "Ficamos no aguardo.\n\n"
        "Atenciosamente,\nEquipe de Suporte"
    ),
    "Internal Project": (
        "Olá,\n\n"
        "Recebemos sua solicitação relacionada ao projeto interno. Ela foi registrada e será encaminhada "
        "para o responsável.\n\n"
        "Você receberá um retorno em breve.\n\n"
        "Atenciosamente,\nEquipe de Suporte"
    )
}

EMOTION_KEYWORDS = [
    "furious", "angry", "unacceptable", "lawsuit", "lawyer", "cancel", "refund now",
    "worst", "terrible", "disgusted", "hate", "scam", "fraud", "urgent!!!", "asap!!!",
    "raiva", "absurdo", "inaceitável", "processar", "cancelar agora", "péssimo", "horrível",
    "lixo", "vergonha", "incompetente"
]


def detect_high_emotion(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EMOTION_KEYWORDS)


def classify_ticket(text: str) -> Dict[str, Any]:
    """
    Função principal do protótipo.
    
    Parâmetros:
        text (str): texto completo do ticket
        
    Retorna:
        dict com category, confidence, suggested_priority, send_to_senior,
        can_auto_suggest, suggested_response, high_emotion_detected, reasoning, top_3
    """
    if not text or len(str(text).strip()) < 10:
        return {"error": "Texto do ticket muito curto ou vazio."}
    
    text = str(text).strip()
    
    # Predição
    proba = clf.predict_proba([text])[0]
    classes = clf.classes_
    pred_idx = proba.argmax()
    category = classes[pred_idx]
    confidence = float(proba[pred_idx])
    
    rules = CATEGORY_RULES.get(category, {
        "default_priority": "Medium",
        "auto_suggest": False,
        "send_to_senior": True,
        "reason": "Categoria não mapeada com regras específicas."
    })
    
    high_emotion = detect_high_emotion(text)
    
    # Lógica de decisão
    send_to_senior = bool(rules["send_to_senior"] or high_emotion or confidence < 0.70)
    can_suggest_response = bool(rules["auto_suggest"] and not high_emotion and confidence >= 0.75)
    
    suggested_response = RESPONSE_TEMPLATES.get(category) if can_suggest_response else None
    
    priority = rules["default_priority"]
    if high_emotion:
        priority = "Critical"
    elif confidence < 0.55:
        priority = "High"  # baixa confiança → sobe prioridade para humano olhar logo
    
    return {
        "category": category,
        "confidence": round(confidence, 3),
        "suggested_priority": priority,
        "send_to_senior": send_to_senior,
        "can_auto_suggest": can_suggest_response,
        "suggested_response": suggested_response,
        "high_emotion_detected": high_emotion,
        "reasoning": rules["reason"],
        "top_3_categories": sorted(
            [(str(classes[i]), round(float(proba[i]), 3)) for i in range(len(classes))],
            key=lambda x: x[1], reverse=True
        )[:3]
    }


def print_result(result: Dict[str, Any], ticket_text: str = None):
    """Pretty print do resultado."""
    if "error" in result:
        print(f"Erro: {result['error']}")
        return
    
    if ticket_text:
        print(f"Ticket: {ticket_text[:120]}{'...' if len(ticket_text) > 120 else ''}")
        print()
    
    print(f"Categoria:              {result['category']}")
    print(f"Confiança:              {result['confidence']:.1%}")
    print(f"Prioridade sugerida:    {result['suggested_priority']}")
    print(f"Enviar para sênior:     {'SIM' if result['send_to_senior'] else 'Não'}")
    print(f"Pode sugerir resposta:  {'SIM' if result['can_auto_suggest'] else 'Não'}")
    print(f"Emoção alta detectada:  {'SIM' if result['high_emotion_detected'] else 'Não'}")
    print(f"Motivo da regra:        {result['reasoning']}")
    print(f"Top 3 categorias:       {result['top_3_categories']}")
    
    if result.get("suggested_response"):
        print("\n--- Resposta sugerida ---")
        print(result["suggested_response"])
        print("-------------------------")


if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("AI Ticket Assistant — Protótipo Challenge 002")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        # Uso via linha de comando: python ticket_ai_assistant.py "texto do ticket"
        text = " ".join(sys.argv[1:])
        result = classify_ticket(text)
        print_result(result, text)
    else:
        # Demo interativa rápida
        examples = [
            "My mailbox is almost full and I cannot receive new emails. Please increase my quota.",
            "I need access to the Salesforce system for the new project. My manager already approved.",
            "The laptop screen is completely black after the last update. Nothing works. Critical.",
            "I want a full refund now! This is a scam and I will call my lawyer.",
            "Please setup the new printer in the marketing department."
        ]
        
        for i, ex in enumerate(examples, 1):
            print(f"\n{'─'*70}")
            print(f"Exemplo {i}")
            result = classify_ticket(ex)
            print_result(result, ex)
