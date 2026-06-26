# RUN_ME — como testar a submissão

## 1. Instalar dependências

Na raiz do projeto:

```bash
pip install -r requirements.txt
```

## 2. Rodar a API

```bash
cd solution
uvicorn app:app --reload
```

Abra no navegador:

```text
http://127.0.0.1:8000/docs
```

Teste o endpoint `POST /triage`.

## 3. Payloads de teste

### B2E/IT — candidato a automação

```json
{
  "text": "Please reset my password. I cannot login to my account or access the internal system.",
  "priority": "Medium",
  "channel": "Internal portal",
  "source_context": "b2e_it"
}
```

### B2C externo — agent assist

```json
{
  "text": "I need help setting up my Philips Hue lights with the mobile app.",
  "priority": "Medium",
  "channel": "Chat",
  "source_context": "b2c_external"
}
```

### B2C externo com risco — escalação humana

```json
{
  "text": "I want a refund because my GoPro is not working and I am very angry.",
  "priority": "High",
  "channel": "Email",
  "source_context": "b2c_external"
}
```

## 4. Rodar teste em batch

```bash
cd solution
python test_batch.py
```

O resultado é salvo em:

```text
solution/outputs/batch/batch_triage_results.csv
```

## 5. Reproduzir treinamento

Coloque os CSVs em uma pasta `data/` na raiz:

```text
data/customer_support_tickets.csv
data/all_tickets_processed_improved_v3.csv
```

Depois rode:

```bash
cd solution
python train_models.py
```

Isso recria os modelos em `solution/models/` e as métricas em `solution/outputs/`.

## 6. Antes de abrir PR

Editar no `README.md`:

```text
Sara Andrade
26/06/26
```

Opcional: adicionar prints em `process-log/screenshots/`.
