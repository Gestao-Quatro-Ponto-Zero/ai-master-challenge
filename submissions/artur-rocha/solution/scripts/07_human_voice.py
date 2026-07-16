import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 - Passo 7: o FATOR HUMANO.
Ate aqui a analise foi so numero. Aqui eu leio a voz do cliente: o feedback_text
livre e os reason_code dos eventos de churn. E onde o 'porque' humano aparece
(ou nao) nos dados.
"""
import pandas as pd
pd.set_option('display.max_colwidth', 80); pd.set_option('display.width', 200)
DATA=os.path.join(_ROOT,'data')
chn=pd.read_csv(f'{DATA}/ravenstack_churn_events.csv')

print("="*80); print("REASON CODES (o 'porque' declarado)"); print("="*80)
rc=chn.reason_code.value_counts(dropna=False)
print(rc.to_string()); print(f"total eventos: {len(chn)}")

print("\n" + "="*80); print("FEEDBACK_TEXT (a voz do cliente, texto livre)"); print("="*80)
ft=chn.feedback_text
print(f"eventos com feedback preenchido: {ft.notna().sum()} de {len(chn)} ({ft.notna().mean():.0%})")
print(f"frases distintas: {ft.nunique()}")
print("\nfrases mais comuns:")
print(ft.value_counts().head(20).to_string())

print("\n" + "="*80); print("CRUZAMENTO reason_code x feedback (coerencia humana?)"); print("="*80)
ct=pd.crosstab(chn.reason_code, chn.feedback_text)
# para cada reason, o feedback dominante
for reason in chn.reason_code.dropna().unique():
    sub=chn[chn.reason_code==reason].feedback_text.value_counts().head(3)
    print(f"\n[{reason}] -> {dict(sub)}")

print("\n" + "="*80); print("SINAIS HUMANOS estruturados nos eventos"); print("="*80)
print(f"refunds concedidos (dinheiro de volta): {(chn.refund_amount_usd>0).sum()} eventos ({(chn.refund_amount_usd>0).mean():.0%})")
print(f"reativacoes (cliente que voltou e saiu de novo): {chn.is_reactivation.sum()}")
print(f"churn precedido de upgrade (comprou mais e saiu): {chn.preceding_upgrade_flag.sum()} ({chn.preceding_upgrade_flag.mean():.0%})")
print(f"churn precedido de downgrade: {chn.preceding_downgrade_flag.sum()} ({chn.preceding_downgrade_flag.mean():.0%})")
