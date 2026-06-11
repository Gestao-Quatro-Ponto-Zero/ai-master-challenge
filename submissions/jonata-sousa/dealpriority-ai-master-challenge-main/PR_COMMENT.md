Ajustes realizados conforme revisão:

1. Tornei a lógica de scoring reproduzível:
* adicionado `scripts/generate\_scores.py`;
* adicionada documentação em `docs/scoring-methodology.md`;
* incluídos os CSVs originais em `data/raw/`;
* explicitadas variáveis, pesos, penalidade de aging, percentis e lógica de `recommended\_action`;
* documentado o tratamento da inconsistência `GTXPro` vs. `GTX Pro`;
* adicionadas validações para preservar unicidade de `opportunity\_id` e contagem de linhas após os joins.
2. Facilitei a execução/avaliação do app:
* README atualizado com URL pública da demo;
* instruções de setup local com `npm install` e `npm run dev`;
* instruções de reprodução do CSV final;
* adicionado `scripts/seed\_from\_csv.py`;
* incluído `supabase/seed.sql` para recriar a tabela `public.deals` a partir do CSV final.

Demo pública:
https://opportunity-focus-hub.lovable.app/auth

Credenciais:

* E-mail: jonatamarinssousa@gmail.com
* Senha: Jojuan22@

Obrigado pela revisão.

