from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.support_copilot.batch import CUSTOMER_SUPPORT, IT_SUPPORT
from src.support_copilot.customer_care import assess_customer_care
from src.support_copilot.memory import find_approved_lessons
from src.support_copilot.policy import Decision, OperatingMode, decide
from src.support_copilot.privacy import mask_pii


CASE_MATRIX = (
    {
        "case_id": "CLI-01",
        "context": CUSTOMER_SUPPORT,
        "scenario": "Reincidência com dano financeiro",
        "message": (
            "Já falei com o suporte várias vezes, continuo sem solução e fui "
            "cobrado duas vezes."
        ),
        "business_label": "Billing inquiry",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": (
            "UNRESOLVED_OR_REPEAT_CONTACT",
            "FINANCIAL_HARM",
        ),
        "source_basis": "Padrões observados no Dataset 1",
        "data_quality_rule": "Preservar como voz do cliente",
    },
    {
        "case_id": "CLI-02",
        "context": CUSTOMER_SUPPORT,
        "scenario": "Dúvida comum sobre produto",
        "message": "Como configuro o equipamento que acabei de comprar?",
        "business_label": "Product inquiry",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": (),
        "source_basis": "Tipo observado no Dataset 1",
        "data_quality_rule": "Manter classificação humana",
    },
    {
        "case_id": "CLI-03",
        "context": CUSTOMER_SUPPORT,
        "scenario": "Pedido de cancelamento",
        "message": "Quero cancelar o serviço porque não preciso mais dele.",
        "business_label": "Cancellation request",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": ("CANCELLATION_OR_CHURN",),
        "source_basis": "Tipo observado no Dataset 1",
        "data_quality_rule": "Preservar para decisão humana",
    },
    {
        "case_id": "CLI-04",
        "context": CUSTOMER_SUPPORT,
        "scenario": "Escalonamento público ou jurídico",
        "message": (
            "Se isso não for resolvido hoje, vou registrar no Procon e no "
            "Reclame Aqui."
        ),
        "business_label": "Technical issue",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": ("LEGAL_OR_PUBLIC_ESCALATION",),
        "source_basis": "Risco operacional derivado do Dataset 1",
        "data_quality_rule": "Preservar e priorizar",
    },
    {
        "case_id": "CLI-05",
        "context": CUSTOMER_SUPPORT,
        "scenario": "Fraude ou privacidade",
        "message": "Acredito que houve fraude e possível vazamento de dados.",
        "business_label": "Billing inquiry",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": ("SAFETY_PRIVACY_OR_ABUSE",),
        "source_basis": "Risco operacional derivado do Dataset 1",
        "data_quality_rule": "Preservar e restringir acesso",
    },
    {
        "case_id": "CLI-06",
        "context": CUSTOMER_SUPPORT,
        "scenario": "Insatisfação forte",
        "message": "O atendimento foi inaceitável e estou muito insatisfeito.",
        "business_label": "Technical issue",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": ("STRONG_DISSATISFACTION",),
        "source_basis": "Padrão observado no Dataset 1",
        "data_quality_rule": "Preservar para cuidado humano",
    },
    {
        "case_id": "CLI-07A",
        "context": CUSTOMER_SUPPORT,
        "scenario": "Contato repetido, primeiro registro",
        "message": "Já entrei em contato e o problema continua sem solução.",
        "business_label": "Technical issue",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": ("UNRESOLVED_OR_REPEAT_CONTACT",),
        "source_basis": "Padrão observado em 460 registros do Dataset 1",
        "data_quality_rule": "Preservar como evento distinto",
    },
    {
        "case_id": "CLI-07B",
        "context": CUSTOMER_SUPPORT,
        "scenario": "Contato repetido, segundo registro",
        "message": "Já entrei em contato e o problema continua sem solução.",
        "business_label": "Technical issue",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": ("UNRESOLVED_OR_REPEAT_CONTACT",),
        "source_basis": "Padrão observado em 460 registros do Dataset 1",
        "data_quality_rule": "Preservar: ID diferente não é duplicata técnica",
    },
    {
        "case_id": "ITI-01",
        "context": IT_SUPPORT,
        "scenario": "Equipamento com falha clara",
        "message": (
            "The company laptop overheats and shuts down during video calls."
        ),
        "business_label": "Hardware",
        "expected_action": "SHADOW_RECOMMENDATION",
        "expected_signals": (),
        "expected_model_category": "Hardware",
        "source_basis": "Taxonomia e padrão do Dataset 2",
        "data_quality_rule": "Testar sugestão em observação",
    },
    {
        "case_id": "ITI-02",
        "context": IT_SUPPORT,
        "scenario": "Permissão administrativa",
        "message": (
            "Please grant administrative rights to install software on the "
            "finance server."
        ),
        "business_label": "Administrative rights",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": (),
        "expected_model_category": "Administrative rights",
        "source_basis": "Categoria sensível do Dataset 2",
        "data_quality_rule": "Humano obrigatório",
    },
    {
        "case_id": "ITI-03",
        "context": IT_SUPPORT,
        "scenario": "Caixa de e-mail cheia",
        "message": "My shared mailbox is full and cannot receive new messages.",
        "business_label": "Storage",
        "expected_action": "SHADOW_RECOMMENDATION",
        "expected_signals": (),
        "expected_model_category": "Storage",
        "source_basis": "Taxonomia e padrão do Dataset 2",
        "data_quality_rule": "Testar sugestão em observação",
    },
    {
        "case_id": "ITI-04",
        "context": IT_SUPPORT,
        "scenario": "Erro conhecido de compra",
        "message": (
            "Please order two monitors and a keyboard for the new workstation."
        ),
        "business_label": "Purchase",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": (),
        "known_model_error": True,
        "source_basis": "Teste adversarial baseado na categoria Purchase",
        "data_quality_rule": "Memória aprovada força revisão",
    },
    {
        "case_id": "ITI-05",
        "context": IT_SUPPORT,
        "scenario": "Novo funcionário",
        "message": "A new employee starts Monday and needs onboarding support.",
        "business_label": "HR Support",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": (),
        "expected_model_category": "HR Support",
        "source_basis": "Categoria sensível do Dataset 2",
        "data_quality_rule": "Humano obrigatório",
    },
    {
        "case_id": "ITI-06",
        "context": IT_SUPPORT,
        "scenario": "Acesso a sistema",
        "message": "Please create access for the sales dashboard.",
        "business_label": "Access",
        "expected_action": "HUMAN_REVIEW",
        "expected_signals": (),
        "expected_model_category": "Access",
        "source_basis": "Categoria sensível do Dataset 2",
        "data_quality_rule": "Humano obrigatório",
    },
    {
        "case_id": "ITI-07",
        "context": IT_SUPPORT,
        "scenario": "Projeto interno pouco claro",
        "message": (
            "Please add a workstream to the internal migration project."
        ),
        "business_label": "Internal Project",
        "expected_action": "ABSTAIN",
        "expected_signals": (),
        "source_basis": "Teste de incerteza na taxonomia do Dataset 2",
        "data_quality_rule": "Pedir revisão quando faltar confiança",
    },
    {
        "case_id": "ITI-08",
        "context": IT_SUPPORT,
        "scenario": "Mensagem ambígua",
        "message": (
            "The service is not working as expected and I need help with my "
            "account."
        ),
        "business_label": "Needs clarification",
        "expected_action": "ABSTAIN",
        "expected_signals": (),
        "source_basis": "Teste adversarial de baixa especificidade",
        "data_quality_rule": "Não adivinhar",
    },
)


def matrix_frame() -> pd.DataFrame:
    rows = []
    for case in CASE_MATRIX:
        rows.append(
            {
                "ID": case["case_id"],
                "Fila": case["context"],
                "Cenário": case["scenario"],
                "Mensagem de teste": case["message"],
                "Rótulo de negócio": case["business_label"],
                "Comportamento esperado": case["expected_action"],
                "Sinais esperados": ", ".join(case["expected_signals"]),
                "Origem": case["source_basis"],
                "Regra de qualidade": case["data_quality_rule"],
            }
        )
    return pd.DataFrame(rows)


def evaluate_matrix(
    *,
    classifier,
    threshold: float,
    memory_path: str | Path,
    kill_switch: bool = False,
) -> pd.DataFrame:
    rows = []
    for case in CASE_MATRIX:
        masked_text, _ = mask_pii(case["message"])
        assessment = assess_customer_care(masked_text)
        memory_matches = []

        if case["context"] == CUSTOMER_SUPPORT:
            prediction = {"category": None, "confidence": None}
            if kill_switch or assessment.requires_human:
                decision = decide(
                    category="Customer support",
                    confidence=0.0,
                    threshold=threshold,
                    mode=OperatingMode.SHADOW,
                    kill_switch=kill_switch,
                    customer_care_required=assessment.requires_human,
                )
            else:
                decision = Decision(
                    action="HUMAN_REVIEW",
                    reason="A classificação da fila de clientes continua humana.",
                    requires_human=True,
                    simulated=False,
                )
        else:
            prediction = classifier.predict(masked_text)
            memory_matches = find_approved_lessons(
                memory_path,
                text=masked_text,
                predicted_category=prediction["category"],
            )
            decision = decide(
                category=prediction["category"],
                confidence=prediction["confidence"],
                threshold=threshold,
                mode=OperatingMode.SHADOW,
                kill_switch=kill_switch,
                memory_match=bool(memory_matches),
                customer_care_required=assessment.requires_human,
            )

        expected_signals = set(case["expected_signals"])
        observed_signals = set(assessment.signal_codes)
        signal_pass = expected_signals.issubset(observed_signals)
        action_pass = decision.action == case["expected_action"]

        expected_model_category = case.get("expected_model_category")
        category_pass = (
            True
            if expected_model_category is None
            else prediction["category"] == expected_model_category
        )
        memory_pass = True
        if case.get("known_model_error"):
            memory_pass = (
                prediction["category"] != case["business_label"]
                and bool(memory_matches)
                and decision.action == "HUMAN_REVIEW"
            )

        rows.append(
            {
                "ID": case["case_id"],
                "Cenário": case["scenario"],
                "Resultado": (
                    "PASS"
                    if action_pass
                    and signal_pass
                    and category_pass
                    and memory_pass
                    else "FAIL"
                ),
                "Rótulo de negócio": case["business_label"],
                "Sugestão observada": prediction["category"] or "Não aplicável",
                "Confiança": (
                    "Não aplicável"
                    if prediction["confidence"] is None
                    else f"{prediction['confidence']:.1%}"
                ),
                "Próximo passo": decision.action,
                "Memória acionada": "Sim" if memory_matches else "Não",
                "Sinais encontrados": ", ".join(assessment.signal_codes),
                "Regra de qualidade": case["data_quality_rule"],
            }
        )

    return pd.DataFrame(rows)
