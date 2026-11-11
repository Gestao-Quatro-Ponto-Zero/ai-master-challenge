# Passo a passo: ligar a IA e publicar a demo

> **Estado desta submissão (11/11/2026):** a IA **não está ligada**. A conta da API da Anthropic não tem créditos, e a primeira chamada real foi recusada com `credit balance is too low`. Por isso, os textos publicados na demo são de **template validado**, e não de IA. O código de geração com Haiku 5.5 está pronto e testado com cliente falso (`tests/test_gerar_ia.py`), mas nunca rodou contra a API real.
>
> Para ir para produção com IA, é preciso um plano com API e orçamento de tokens. Os requisitos estão na seção "Para produção" no fim deste documento. Os passos abaixo valem quando houver saldo.

A demo é um site estático. A chave da Anthropic **não vai para a Vercel nem para o navegador**: ela fica no seu computador, só durante a geração dos briefings. A Vercel recebe apenas os arquivos já gerados em `app/data/`.

## 1. Guardar a chave na sua máquina, sem histórico de shell

```bash
cd ~/Documents/ai-master-challenge/submissions/diego-rodrigues/solution
read -s -p "Cole a chave da Anthropic e pressione Enter: " ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY
```

O `read -s` não mostra a chave na tela nem a grava no histórico do terminal. Ela vale só nesta sessão do shell; ao fechar o terminal, ela some.

Para não precisar repetir o passo, use o gerenciador de senhas ou um arquivo `.env` local. O `solution/.gitignore` já ignora `.env`; nunca faça commit de chave.

## 2. Conferir antes de gastar

```bash
.venv/bin/python3 -c "import os; print('chave presente:', bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

Deve imprimir `chave presente: True`. Não imprime a chave.

Recomendado: no console da Anthropic, defina um limite de gasto mensal para a chave. O código já limita cada execução a 60 chamadas, mas o limite do console protege de qualquer outro uso.

## 3. Gerar os briefings

```bash
.venv/bin/python3 run.py --hoje 2018-01-01
```

Quando aparecer `briefings gravados (origem: IA (Haiku 5.5), chamadas: ..., custo estimado: ..., recusas: ...)`, pressione `Ctrl+C` para parar o servidor local. Os textos ficam em `app/data/briefings.json`.

O custo esperado de uma execução completa (35 vendedores e 6 gestores) é de centavos de dólar. Se `recusas` vier maior que zero, os itens recusados usaram o template; a lista completa está no arquivo, com o motivo.

## 4. Conferir o resultado no navegador local

```bash
.venv/bin/python3 run.py --hoje 2018-01-01 --sem-build --sem-ia
```

`--sem-ia` não chama a API de novo: mantém o `briefings.json` que você acabou de gerar. Sem ele, a execução faria outra rodada de chamadas.

Abra `http://localhost:8000` e confira que o texto do vendedor aparece com "Texto escrito por IA e validado contra os fatos." quando a origem for `ia`.

## 5. Publicar a demo

```bash
cd app
vercel --prod --yes --name lead-scorer-diego
```

Não é preciso configurar nenhuma variável de ambiente na Vercel: a chave não é usada no site publicado.

## 6. Conferir a demo publicada

Abra https://lead-scorer-diego.vercel.app no celular e no desktop. O console do navegador não deve mostrar nenhum erro, e a faixa de demo deve aparecer.

## 7. Encerrar a sessão

```bash
unset ANTHROPIC_API_KEY
```

## Se algo falhar

| Sintoma | O que fazer |
|---|---|
| `chave presente: False` | o `export` do passo 1 não foi feito nesta sessão |
| `recusas` alto | abra `briefings.json`, veja o motivo de cada item; o template cobre os casos recusados |
| `custo estimado` acima do esperado | pare, confira o limite de gasto no console e revise `LIMITE_TOKENS` em `ia/briefing.py` |
| erro de autenticação da API | a chave foi copiada incompleta ou está revogada; gere outra no console |

## Para produção

Antes de ligar a IA para valer, estes itens precisam estar resolvidos. Hoje nenhum está:

1. **Plano com API e créditos suficientes** na conta da Anthropic, com faturamento ativo. Sem saldo, o produto cai no template, que é o comportamento esperado, mas não é "IA em produção".
2. **Orçamento de tokens definido por escrito**: teto mensal em US$, teto de tokens por execução (hoje 60 chamadas, 250 e 150 tokens de saída) e quem aprova um aumento.
3. **Limite de gasto mensal no console** da Anthropic, configurado antes de qualquer execução com chave de produção.
4. **Chave em gerenciador de segredos**, nunca em arquivo do repositório. O site publicado não usa chave.
5. **Monitoramento de custo**: a cada execução, `custo_estimado_usd`, `chamadas` e `recusas` precisam ser registrados, não só impressos.
6. **Avaliação de qualidade do texto** com pessoas reais da operação. O validador garante que os números e as promessas estão corretos; não garante que o texto seja útil.
7. **Plano de reversão**: se o custo ou a taxa de recusa passarem do limite, a geração volta a ser só template, sem mudança de código.
