# Support Triage AI — Setup do Protótipo

## Requisitos

- Node.js 18+
- Conta Anthropic com API key

## Rodar localmente

```bash
# 1. Criar projeto React
npx create-react-app support-triage
cd support-triage

# 2. Substituir src/App.js pelo conteúdo de support_triage_v3.jsx

# 3. Rodar
npm start
```

## Variável de ambiente

O protótipo chama `https://api.anthropic.com/v1/messages` diretamente do browser.  
No claude.ai Artifacts, a autenticação é injetada automaticamente.  
Para rodar localmente, configure um proxy ou use a API via backend.

## Modelo usado

`claude-sonnet-4-20250514` — max_tokens: 1024
