"""Consolida os numeros reais do Dataset 1 usados no README.

So numeros que sao contagem direta (volume por categoria) — nao inclui
nada derivado de First Response Time / Time to Resolution / CSAT, porque
auditoria.py provou que essas colunas sao ruido sintetico incoerente.
"""
import json
from pathlib import Path

from auditoria import carregar_tickets, OUTPUTS


def diagnosticar() -> dict:
    df = carregar_tickets()
    n = len(df)

    vol_tipo = (df["Ticket Type"].value_counts(normalize=True) * 100).round(1).to_dict()
    vol_canal = (df["Ticket Channel"].value_counts(normalize=True) * 100).round(1).to_dict()
    vol_prioridade = (df["Ticket Priority"].value_counts(normalize=True) * 100).round(1).to_dict()
    vol_status = (df["Ticket Status"].value_counts(normalize=True) * 100).round(1).to_dict()

    autoatendimento_candidatos = df["Ticket Type"].isin(["Refund request", "Cancellation request"]).sum()

    resultado = {
        "total_tickets_dataset1": int(n),
        "obs": "README do challenge cita ~30k tickets; o CSV real tem 8469 linhas (wc -l conta quebras de linha dentro de campos multiline, nao registros — ver PROCESS_LOG).",
        "volume_pct_por_tipo": vol_tipo,
        "volume_pct_por_canal": vol_canal,
        "volume_pct_por_prioridade": vol_prioridade,
        "volume_pct_por_status": vol_status,
        "pct_refund_ou_cancelamento": round(autoatendimento_candidatos / n * 100, 1),
        "metricas_nao_utilizaveis": [
            "First Response Time / Time to Resolution: timestamps incoerentes, 49% dos casos fechados resolvem antes da 1a resposta — ver auditoria.py",
            "Customer Satisfaction Rating: sem correlacao estatistica com Priority/Channel/Type (ANOVA p>0.05 nos tres) — ver auditoria.py",
            "Ticket Description / Resolution: texto gerado (template com placeholder vazado / Faker), nao serve pra NLP de causa raiz",
        ],
    }

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "diagnostico.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado


def main() -> None:
    print(json.dumps(diagnosticar(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
