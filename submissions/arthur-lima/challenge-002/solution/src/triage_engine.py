"""Calibrated 3-Tier Support Triage Engine with Precedent Retrieval & Guardrail Isolation.

Implements H2 (Selective 3-Tier Automation via Calibrated Confidence),
H3 (Guardrail & Domain-Shift Preemption), and H5 (Batch/Single Parity & Analyst Overrides).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.guardrails import GuardrailAssessment, evaluate_guardrails, mask_pii


CATEGORY_RUNBOOKS: Dict[str, Dict[str, str]] = {
    "Hardware": {
        "queue": "N2 Field & Endpoint Engineering",
        "sla_hours": "8h úteis",
        "checklist": "1) Validar asset tag no CMDB; 2) Verificar garantia do fabricante; 3) Emitir equipamento de empréstimo se indisponibilidade total.",
        "draft_response": "Olá! Seu chamado foi classificado em **Hardware** e encaminhado à fila de Endpoint Engineering. Já iniciamos a verificação do equipamento no inventário; caso haja falha física impeditiva, providenciaremos substituição conforme política de ativos.",
    },
    "HR Support": {
        "queue": "People Ops & Payroll Service Desk",
        "sla_hours": "12h úteis",
        "checklist": "1) Conferir matrícula ativa no HCM; 2) Validar período de folha/férias/benefícios; 3) Anexar comprovante no prontuário.",
        "draft_response": "Olá! Sua solicitação foi direcionada para **HR Support (People Ops)**. Os dados do colaborador estão em conferência no sistema de gestão de pessoas e retornaremos dentro do SLA de 12h úteis.",
    },
    "Access": {
        "queue": "IAM & Identity Provisioning",
        "sla_hours": "2h úteis",
        "checklist": "1) Verificar aprovação do gestor do recurso; 2) Validar grupo RBAC/Active Directory; 3) Conceder acesso com princípio de menor privilégio.",
        "draft_response": "Olá! Identificamos uma solicitação de **Access (IAM)**. Confirmada a aprovação da liderança responsável pelo sistema, o perfil de acesso será provisionado automaticamente via Active Directory/SSO.",
    },
    "Storage": {
        "queue": "Cloud & Storage Operations",
        "sla_hours": "4h úteis",
        "checklist": "1) Checar utilização atual da cota; 2) Verificar política de retenção/arquivamento; 3) Expandir volume após validação de centro de custo.",
        "draft_response": "Olá! Seu chamado foi roteado para **Storage Operations**. Estamos verificando a utilização atual da cota de armazenamento e a política de retenção aplicável ao seu diretório/mailbox.",
    },
    "Purchase": {
        "queue": "IT Procurement & Licensing",
        "sla_hours": "24h úteis",
        "checklist": "1) Conferir aprovação do centro de custo (PO); 2) Checar disponibilidade em contrato corporativo; 3) Emitir requisição de compra.",
        "draft_response": "Olá! Sua requisição foi encaminhada ao time de **Purchase (IT Procurement)**. Assim que o vínculo de centro de custo e aprovação do aprovador financeiro forem validados, seguiremos com a alocação do item/licença.",
    },
    "Internal Project": {
        "queue": "PMO & Project Systems Support",
        "sla_hours": "12h úteis",
        "checklist": "1) Verificar código do projeto e status no sistema; 2) Validar janela de forecast/alocação; 3) Ajustar parâmetros com o PMO.",
        "draft_response": "Olá! Seu chamado sobre **Internal Project** foi direcionado à equipe de suporte a sistemas de projetos/PMO para verificação de código, forecast e permissões de cronograma.",
    },
    "Administrative rights": {
        "queue": "SecOps & Privileged Access (PAM)",
        "sla_hours": "4h úteis (Revisão Humana)",
        "checklist": "1) Validar justificativa técnica temporária (JIT); 2) Checar conformidade de endpoint (EDR ativo); 3) Exigir aprovação humana de Segurança.",
        "draft_response": "Olá! Solicitações de **Administrative rights** passam por revisão de privilégio mínimo (PAM/SecOps). Um analista validará a justificativa técnica para liberação temporária segura.",
    },
    "Miscellaneous": {
        "queue": "General Service Desk Triage (N1/N2)",
        "sla_hours": "8h úteis",
        "checklist": "1) Inspecionar contexto complementar do chamado; 2) Confirmar sistema impactado com o solicitante; 3) Direcionar ao grupo especialista.",
        "draft_response": "Olá! Recebemos seu chamado na fila **General Service Desk**. Um analista está revisando os detalhes para concluir o atendimento ou direcionar à equipe especialista.",
    },
    "Human_Escalation_Guardrail": {
        "queue": "Fila Prioritária de Supervisão Humana / SecOps / Consumidor",
        "sla_hours": "1h útil (Crítico)",
        "checklist": "1) Inspecionar motivo do bloqueio (Guardrail / Domain Shift / Risco Financeiro ou Jurídico); 2) Nunca emitir estorno ou resposta automática sem alçada humana.",
        "draft_response": "[BLOQUEIO DE AUTOMAÇÃO] Este chamado acionou uma barreira determinística de segurança, política financeira/jurídica ou mudança de domínio e requer tratamento 100% humano.",
    },
}


@dataclass(frozen=True)
class TicketTriageResult:
    ticket_id: str
    raw_text: str
    sanitized_text: str
    pred_category: str
    confidence: float
    top2_category: str
    top2_confidence: float
    margin_top1_top2: float
    centroid_similarity: float
    base_tier: str
    effective_tier: str
    effective_category: str
    override_status: str
    guardrail_triggered: bool
    guardrail_reasons: str
    pii_count: int
    assigned_queue: str
    sla_target: str
    recommended_action: str
    draft_response: str
    precedent_snippet: str
    precedent_similarity: float


class SupportTriageEngine:
    """
    Calibrated TF-IDF + LinearSVC Triage Engine with:
    - Strict train/test separation and per-fold TF-IDF calibration (zero out-of-fold IDF leakage)
    - Mandatory PII redaction before indexing vocabulary and precedent bank
    - Class centroid cosine specificity for Domain-Shift / OOD detection
    - Precedent retrieval over sanitized training corpus (grounded runbook assistance)
    - 3-Tier routing policy + guardrail-safe human overrides
    """

    def __init__(
        self,
        tier1_threshold: float = 0.80,
        tier2_threshold: float = 0.55,
        min_domain_similarity: float = 0.065,
        max_features: int = 20000,
        random_state: int = 42,
    ):
        if not (0.0 < tier2_threshold < tier1_threshold <= 1.0):
            raise ValueError(
                "Os limiares devem satisfazer 0 < tier2_threshold < tier1_threshold <= 1."
            )
        self.tier1_threshold = float(tier1_threshold)
        self.tier2_threshold = float(tier2_threshold)
        self.min_domain_similarity = float(min_domain_similarity)
        self.max_features = int(max_features)
        self.random_state = int(random_state)

        self.vectorizer: Optional[TfidfVectorizer] = None
        self.classifier: Optional[CalibratedClassifierCV] = None
        self.classes_: Optional[np.ndarray] = None
        self.centroids_: Optional[np.ndarray] = None
        self.precedent_texts_: Optional[np.ndarray] = None
        self.precedent_labels_: Optional[np.ndarray] = None
        self.precedent_matrix_ = None
        self.is_fitted_: bool = False

    def fit(
        self, texts: np.ndarray | pd.Series, labels: np.ndarray | pd.Series
    ) -> "SupportTriageEngine":
        """Fits per-fold calibrated pipeline, domain centroids, and sanitized precedent index on training data ONLY."""
        raw_x = pd.Series(texts).fillna("").to_numpy(dtype=str)
        y_arr = pd.Series(labels).fillna("Miscellaneous").to_numpy(dtype=str)

        if len(raw_x) == 0:
            raise ValueError("Conjunto de treino vazio.")

        # Sanitize PII on all training texts before fitting vectorizer, classifier, or precedent bank
        x_arr = np.array(
            [str(mask_pii(t)["sanitized_text"]) for t in raw_x],
            dtype=str,
        )

        fold_pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=self.max_features,
                        ngram_range=(1, 2),
                        sublinear_tf=True,
                        min_df=2,
                        stop_words="english",
                    ),
                ),
                ("svc", LinearSVC(C=0.5, random_state=self.random_state)),
            ]
        )
        self.classifier = CalibratedClassifierCV(fold_pipeline, cv=3)
        self.classifier.fit(x_arr, y_arr)
        self.classes_ = np.asarray(self.classifier.classes_, dtype=str)

        # Fit training-set vectorizer strictly on sanitized training texts for centroid & precedent similarity
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            stop_words="english",
        )
        x_mat = self.vectorizer.fit_transform(x_arr)

        # Compute normalized class centroids in TF-IDF space (strictly from training data)
        centroid_list = []
        for cls in self.classes_:
            cls_mask = y_arr == cls
            mean_vec = np.asarray(x_mat[cls_mask].mean(axis=0)).ravel()
            norm = np.linalg.norm(mean_vec) + 1e-12
            centroid_list.append(mean_vec / norm)
        self.centroids_ = np.vstack(centroid_list)

        # Build compact sanitized precedent bank (up to 150 highest-centroid-affinity examples per class)
        prec_indices: List[int] = []
        for idx_c, cls in enumerate(self.classes_):
            cls_indices = np.where(y_arr == cls)[0]
            if len(cls_indices) == 0:
                continue
            sims = np.asarray(x_mat[cls_indices] @ self.centroids_[idx_c]).ravel()
            top_local = cls_indices[np.argsort(sims)[::-1][:150]]
            prec_indices.extend(top_local.tolist())

        prec_idx_arr = np.array(prec_indices, dtype=int)
        self.precedent_texts_ = x_arr[prec_idx_arr]
        self.precedent_labels_ = y_arr[prec_idx_arr]
        self.precedent_matrix_ = x_mat[prec_idx_arr]
        self.is_fitted_ = True
        return self

    def _check_fitted(self) -> None:
        if not self.is_fitted_ or self.vectorizer is None or self.classifier is None:
            raise RuntimeError(
                "SupportTriageEngine precisa ser ajustado com .fit() antes do uso."
            )

    # H2 & H3 — Decisão de roteamento em 3 Tiers combinando probabilidades calibradas
    # e bloqueio determinístico (Guardrail, Administrative rights sensível ou Domain Shift).
    def _determine_base_tier(
        self,
        pred_category: str,
        confidence: float,
        guardrail: GuardrailAssessment,
        tier1_threshold: float,
        tier2_threshold: float,
    ) -> Tuple[str, str]:
        if guardrail.force_human_tier3:
            return (
                "Tier 3 — Escalação Humana (Guardrail)",
                "Bloqueado por Guardrail: " + "; ".join(guardrail.guardrail_reasons),
            )
        # Privileged administrative rights require human approval in Tier 2/3 even if high confidence
        if pred_category == "Administrative rights":
            return (
                "Tier 2 — Copilot Assist (Aprovação PAM)",
                "Categoria de privilégio administrativo exige validação humana de alçada (PAM/SecOps).",
            )
        if confidence >= tier1_threshold:
            return (
                "Tier 1 — Auto-Route (Alta Confiança)",
                f"Confiança calibrada ({confidence:.1%}) >= limiar Tier 1 ({tier1_threshold:.0%}) e domínio validado.",
            )
        if confidence >= tier2_threshold:
            return (
                "Tier 2 — Copilot Assist (Revisão Rápida)",
                f"Confiança intermediária ({confidence:.1%}); apresenta Top-2 hipóteses e rascunho ao analista.",
            )
        return (
            "Tier 3 — Escalação Humana (Baixa Confiança)",
            f"Confiança ({confidence:.1%}) abaixo do piso de assistência ({tier2_threshold:.0%}); requer triagem humana.",
        )

    def triage_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str = "Document",
        id_col: Optional[str] = None,
        overrides: Optional[Dict[str, Dict[str, str]]] = None,
        tier1_threshold: Optional[float] = None,
        tier2_threshold: Optional[float] = None,
        include_precedents: bool = True,
    ) -> pd.DataFrame:
        """
        Canonical batch triage pipeline. Preserves exact parity with `triage_single_ticket`
        and is invariant to input row order when sorted by `ticket_id`.
        """
        self._check_fitted()
        t1_thr = float(
            tier1_threshold if tier1_threshold is not None else self.tier1_threshold
        )
        t2_thr = float(
            tier2_threshold if tier2_threshold is not None else self.tier2_threshold
        )
        if not (0.0 < t2_thr < t1_thr <= 1.0):
            raise ValueError(
                "Os limiares devem satisfazer 0 < tier2_threshold < tier1_threshold <= 1."
            )

        if len(df) == 0:
            return pd.DataFrame()

        raw_texts = df[text_col].fillna("").to_numpy(dtype=str)
        if id_col and id_col in df.columns:
            ticket_ids = df[id_col].astype(str).to_numpy(dtype=str)
        else:
            ticket_ids = np.array([f"TKT-{i:05d}" for i in range(len(df))], dtype=str)

        # First pass: sanitize PII before vectorization so PII tokens never distort or leak
        pre_guards = [
            evaluate_guardrails(t, centroid_similarity=None) for t in raw_texts
        ]
        sanitized_texts = np.array([g.sanitized_text for g in pre_guards], dtype=str)

        x_vec = self.vectorizer.transform(sanitized_texts)
        probs = self.classifier.predict_proba(sanitized_texts)
        centroid_sims = np.asarray((x_vec @ self.centroids_.T).max(axis=1)).ravel()

        # Sort probabilities to get Top-1 and Top-2 deterministically
        order = np.argsort(probs, axis=1)
        top1_idx = order[:, -1]
        top2_idx = order[:, -2]
        top1_cats = self.classes_[top1_idx]
        top2_cats = self.classes_[top2_idx]
        top1_probs = probs[np.arange(len(df)), top1_idx]
        top2_probs = probs[np.arange(len(df)), top2_idx]
        margins = top1_probs - top2_probs

        # Precedent retrieval over sanitized precedent bank (computed whenever include_precedents=True)
        prec_snippets = np.full(len(df), "", dtype=object)
        prec_sims = np.zeros(len(df), dtype=float)
        if include_precedents and self.precedent_matrix_ is not None:
            sim_mat = (x_vec @ self.precedent_matrix_.T).toarray()
            best_p_idx = sim_mat.argmax(axis=1)
            prec_sims = sim_mat[np.arange(len(df)), best_p_idx]
            prec_snippets = np.array(
                [
                    f"[{self.precedent_labels_[idx]}] {self.precedent_texts_[idx][:180]}..."
                    for idx in best_p_idx
                ],
                dtype=object,
            )

        overrides_map = overrides or {}
        rows: List[Dict[str, Any]] = []

        for i in range(len(df)):
            tid = str(ticket_ids[i])
            raw_t = str(raw_texts[i])
            c_sim = float(centroid_sims[i])
            guard = evaluate_guardrails(
                raw_t,
                centroid_similarity=c_sim,
                min_domain_similarity=self.min_domain_similarity,
            )
            pred_cat = str(top1_cats[i])
            conf = float(top1_probs[i])
            top2_cat = str(top2_cats[i])
            top2_conf = float(top2_probs[i])
            margin = float(margins[i])

            base_tier, rationale = self._determine_base_tier(
                pred_cat, conf, guard, t1_thr, t2_thr
            )

            eff_tier = base_tier
            eff_cat = pred_cat
            override_status = "Original (Sem Override)"

            if tid in overrides_map:
                ov = overrides_map[tid]
                act = ov.get("override_action", "")
                ov_cat = ov.get("override_category", "") or pred_cat
                reason = ov.get("reason", "Revisão manual")

                if act == "approve_tier1":
                    if guard.force_human_tier3:
                        # Hard guardrail blocks cannot be promoted to automated Tier 1 dispatch
                        eff_tier = "Tier 3 — Escalação Humana (Guardrail Irrevogável p/ Auto-Route)"
                        eff_cat = ov_cat
                        override_status = (
                            f"⛔ Bloqueado: Guardrail impede Auto-Route Tier 1 ({reason})"
                        )
                    else:
                        eff_tier = "Tier 1 — Auto-Route (Homologado por Analista)"
                        eff_cat = ov_cat
                        override_status = f"✅ Homologado Tier 1 ({reason})"
                elif act == "escalate_tier3":
                    eff_tier = "Tier 3 — Escalação Humana (Override Analista)"
                    eff_cat = ov_cat
                    override_status = f"🛑 Escalado Tier 3 ({reason})"
                elif act == "reclassify":
                    if guard.force_human_tier3:
                        eff_tier = "Tier 3 — Escalação Humana (Guardrail + Reclassificado)"
                        eff_cat = ov_cat
                        override_status = (
                            f"✏️ Categoria {eff_cat} anotada; retido no Tier 3 por Guardrail ({reason})"
                        )
                    else:
                        eff_tier = "Tier 2 — Copilot Assist (Reclassificado)"
                        eff_cat = ov_cat
                        override_status = f"✏️ Reclassificado para {eff_cat} ({reason})"

            # Any ticket triggered by Guardrail OR explicitly escalated to Tier 3 uses the Human Escalation runbook
            use_escalation_runbook = guard.force_human_tier3 or (
                tid in overrides_map
                and overrides_map[tid].get("override_action") == "escalate_tier3"
            )
            runbook_key = (
                "Human_Escalation_Guardrail" if use_escalation_runbook else eff_cat
            )
            rb = CATEGORY_RUNBOOKS.get(runbook_key, CATEGORY_RUNBOOKS["Miscellaneous"])

            # Priority rank for operational sorting: Tier 3 urgent human attention first, then Tier 2 Copilot, then Tier 1 Auto
            if eff_tier.startswith("Tier 3"):
                tier_sort_order = 1
            elif eff_tier.startswith("Tier 2"):
                tier_sort_order = 2
            else:
                tier_sort_order = 3

            rows.append(
                {
                    "ticket_id": tid,
                    "raw_text": raw_t,
                    "sanitized_text": guard.sanitized_text,
                    "pred_category": pred_cat,
                    "confidence": conf,
                    "top2_category": top2_cat,
                    "top2_confidence": top2_conf,
                    "margin_top1_top2": margin,
                    "centroid_similarity": c_sim,
                    "base_tier": base_tier,
                    "effective_tier": eff_tier,
                    "effective_category": eff_cat,
                    "override_status": override_status,
                    "guardrail_triggered": guard.force_human_tier3,
                    "guardrail_reasons": "; ".join(guard.guardrail_reasons)
                    if guard.guardrail_reasons
                    else "Limpo (Nenhum bloqueio)",
                    "pii_count": guard.pii_count,
                    "assigned_queue": rb["queue"],
                    "sla_target": rb["sla_hours"],
                    "recommended_action": rationale,
                    "runbook_checklist": rb["checklist"],
                    "draft_response": rb["draft_response"],
                    "precedent_snippet": str(prec_snippets[i]),
                    "precedent_similarity": float(prec_sims[i]),
                    "tier_sort_order": tier_sort_order,
                }
            )

        out = pd.DataFrame(rows)
        out = out.sort_values(
            by=["tier_sort_order", "confidence", "ticket_id"],
            ascending=[True, True, True],
            kind="mergesort",
        ).reset_index(drop=True)
        return out

    def triage_single_ticket(
        self,
        text: str,
        ticket_id: str = "SIM-00001",
        overrides: Optional[Dict[str, Dict[str, str]]] = None,
        tier1_threshold: Optional[float] = None,
        tier2_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Single-ticket wrapper calling `triage_dataframe` to guarantee exact mathematical parity."""
        single_df = pd.DataFrame({"ticket_id": [ticket_id], "Document": [text]})
        res_df = self.triage_dataframe(
            single_df,
            text_col="Document",
            id_col="ticket_id",
            overrides=overrides,
            tier1_threshold=tier1_threshold,
            tier2_threshold=tier2_threshold,
            include_precedents=True,
        )
        return res_df.iloc[0].to_dict()


def split_dataset2_train_test(
    df_d2: pd.DataFrame, test_size: float = 0.20, random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Deterministic stratified train/test split on Dataset 2 with deterministic `ticket_id`."""
    df = df_d2.copy().reset_index(drop=True)
    if "ticket_id" not in df.columns:
        df["ticket_id"] = [f"IT-{i:05d}" for i in range(len(df))]
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df["Topic_group"],
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def fit_triage_engine_from_dataframe(
    df_d2: pd.DataFrame,
    *,
    test_size: float = 0.20,
    random_state: int = 42,
    tier1_threshold: float = 0.80,
    tier2_threshold: float = 0.55,
    max_train_per_class: Optional[int] = None,
) -> Tuple[SupportTriageEngine, pd.DataFrame, pd.DataFrame]:
    """
    Canonical anti-leakage pipeline entrypoint: accepts the full Dataset 2 DataFrame,
    performs the deterministic stratified train/test split, and fits `SupportTriageEngine`
    exclusively on the training partition (`train_df`).
    """
    train_df, test_df = split_dataset2_train_test(
        df_d2, test_size=test_size, random_state=random_state
    )
    fit_df = train_df
    if max_train_per_class is not None:
        fit_df = (
            train_df.groupby("Topic_group", as_index=False)
            .head(int(max_train_per_class))
            .reset_index(drop=True)
        )
    engine = SupportTriageEngine(
        tier1_threshold=tier1_threshold,
        tier2_threshold=tier2_threshold,
        random_state=random_state,
    ).fit(fit_df["Document"], fit_df["Topic_group"])
    return engine, fit_df, test_df
