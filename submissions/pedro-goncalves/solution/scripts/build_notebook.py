from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks/challenge-002-analysis.ipynb"


def code(source: str):
    return nbf.v4.new_code_cell(source.strip())


def markdown(source: str):
    return nbf.v4.new_markdown_cell(source.strip())


def main() -> None:
    notebook = nbf.v4.new_notebook()
    notebook.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.cells = [
        markdown(
            """
# Challenge 002: diagnóstico e automação sob controle

## tl;dr

Este notebook executa o data audit e o experimento de classificação usados na solução. As conclusões são escritas somente após a execução:

- o Dataset 1 não permite medir FRT, TTR, touch time ou ROI observado;
- o Dataset 2 sustenta uma prova técnica de classificação com validação de threshold e teste final;
- o protótipo deve operar em shadow mode, com decisão humana como padrão.
"""
        ),
        markdown(
            """
## Context & Methods

### Key Assumptions

1. Os arquivos públicos são demonstrações, não dados da G4.
2. `First Response Time` e `Time to Resolution` precisam ser auditados antes de serem tratados como durações.
3. A taxonomia de suporte interno de TI não equivale à taxonomia de suporte ao cliente.
4. O threshold é escolhido na validação e avaliado uma vez no teste final.
"""
        ),
        code(
            """
from pathlib import Path
import json
import runpy
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd()
assert (ROOT / "scripts/data_audit.py").exists(), "Execute o notebook a partir da raiz do projeto."
"""
        ),
        markdown("## Data\n\n### 1. Auditar os dois datasets"),
        code(
            """
runpy.run_path(str(ROOT / "scripts/data_audit.py"), run_name="__main__")
audit = json.loads((ROOT / "artifacts/data_audit.json").read_text(encoding="utf-8"))
pd.DataFrame({
    "dataset": ["Suporte ao cliente", "Tickets de TI"],
    "linhas": [audit["dataset_1"]["rows"], audit["dataset_2"]["rows"]],
    "colunas": [audit["dataset_1"]["columns"], audit["dataset_2"]["columns"]],
})
"""
        ),
        markdown("### 2. Verificar a integridade temporal do Dataset 1"),
        code(
            """
d1 = audit["dataset_1"]
pd.DataFrame({
    "verificação": [
        "Pares com ambos os timestamps",
        "Resolução anterior à primeira resposta",
        "Descrições com placeholder",
        "CSAT disponível",
    ],
    "linhas": [
        d1["paired_timestamp_rows"],
        d1["negative_response_to_resolution_rows"],
        d1["placeholder_description_rows"],
        d1["rows"] - d1["null_counts"]["Customer Satisfaction Rating"],
    ],
})
"""
        ),
        markdown(
            """
**Interpretação:** não há timestamp de abertura. Quase metade dos pares possui ordem temporal impossível, e todas as descrições carregam placeholder. Portanto, qualquer número de horas economizadas extraído desses campos seria falsa precisão.
"""
        ),
        markdown("### 3. Treinar e avaliar o classificador no Dataset 2"),
        code(
            """
runpy.run_path(str(ROOT / "scripts/train_classifier.py"), run_name="__main__")
metrics = json.loads((ROOT / "artifacts/classifier_metrics.json").read_text(encoding="utf-8"))
pd.DataFrame([
    {"modelo": "Baseline majoritário", "accuracy": metrics["baseline_final_test"]["accuracy"], "macro_f1": metrics["baseline_final_test"]["macro_f1"]},
    {"modelo": "TF-IDF + LinearSVC calibrado", "accuracy": metrics["model_final_test"]["accuracy"], "macro_f1": metrics["model_final_test"]["macro_f1"]},
])
"""
        ),
        markdown("## Results\n\n### 4. Avaliar cobertura versus acurácia"),
        code(
            """
thresholds = pd.read_csv(ROOT / "artifacts/tables/classifier_coverage_accuracy.csv")
display(thresholds)

ax = thresholds.plot(
    x="coverage",
    y="accuracy_when_covered",
    marker="o",
    legend=False,
    figsize=(8, 4),
    color="#1463ff",
)
ax.set_title("Validação: cobertura versus acurácia no subconjunto coberto")
ax.set_xlabel("Cobertura")
ax.set_ylabel("Acurácia")
ax.grid(alpha=0.2)
plt.show()
"""
        ),
        markdown("### 5. Inspecionar desempenho por classe"),
        code(
            """
per_class = pd.read_csv(ROOT / "artifacts/tables/classifier_per_class_metrics.csv")
per_class[~per_class["class"].isin(["accuracy", "macro avg", "weighted avg"])].sort_values("f1-score")
"""
        ),
        markdown(
            """
## Takeaways

1. **O maior achado é uma limitação:** o Dataset 1 não mede os tempos solicitados de forma utilizável.
2. **A prova técnica é válida dentro do Dataset 2:** o threshold foi escolhido na validação e reportado uma vez no teste final.
3. **A melhor decisão é shadow mode:** mostrar classificação, confiança, abstenção e override sem executar ações externas.
4. **ROI permanece parametrizado:** volume elegível, touch time, adoção, revisão e custos precisam vir da operação real.
5. **Próximo gate:** validar o protótipo e submeter claims e limitações ao revisor independente.
"""
        ),
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    client = NotebookClient(
        notebook,
        timeout=180,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    executed = client.execute()
    nbf.write(executed, OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
