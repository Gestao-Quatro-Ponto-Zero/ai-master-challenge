# Política do repositório

## Escopo único permitido

Somente caminhos abaixo de `submissions/carlos-henrique/` podem ser criados, alterados, removidos ou versionados por esta submissão. Arquivos da raiz, challenges, templates e submissões de terceiros são somente leitura.

## Contexto Git autorizado

- **Branch:** `submission/carlos-henrique`
- **Origin:** `https://github.com/acarloshenrique/ai-master-challenge.git`
- **Upstream:** `https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge.git`
- **Política atual:** commits locais são permitidos; push e Pull Request exigem autorização explícita posterior.

Não configurar tracking remoto nesta fase. Force push é proibido. Commits devem ser pequenos, intencionais, revisados e conter exclusivamente arquivos do caminho permitido.

## Segredos e dados pessoais

- nunca versionar credenciais, tokens, chaves, cookies, arquivos `.env` ou identificadores de acesso;
- usar variáveis de ambiente e um gerenciador de segredos em fases futuras;
- aplicar minimização, controle de acesso, mascaramento ou anonimização quando a auditoria identificar dados pessoais;
- evitar registrar conteúdo sensível em logs, prompts, screenshots ou mensagens de erro;
- interromper a execução se um segredo for detectado no staging.

## Datasets e arquivos grandes

- os cinco CSVs oficiais devem permanecer fora do Git;
- nenhum dataset sintético substituirá silenciosamente uma fonte ausente;
- dados brutos são imutáveis;
- arquivos derivados grandes somente serão versionados quando houver necessidade justificada;
- todo artefato derivado deverá possuir script gerador, linhagem e validação;
- formatos binários, modelos e bancos não devem ser adicionados por conveniência.

## Regra de ignore e solução adotada

O `.gitignore` da raiz ignora `submissions/`. Esse arquivo oficial não pode ser alterado. A solução autorizada é usar `git add -f` seletivamente, um arquivo revisado por vez. O ignore reduz staging acidental, mas exige disciplina para que arquivos válidos da submissão sejam incluídos.

São proibidos staging amplo, staging da pasta inteira e qualquer comando que possa capturar caminhos não revisados.

## Procedimento de staging seguro

1. Listar todos os arquivos criados dentro da submissão.
2. Revisar cada caminho e confirmar que começa por `submissions/carlos-henrique/`.
3. Adicionar individualmente cada arquivo aprovado com `git add -f <caminho-do-arquivo>`.
4. Executar `git diff --cached --name-only`.
5. Rejeitar qualquer caminho fora de `submissions/carlos-henrique/`.
6. Revisar o conteúdo completo com `git diff --cached`.
7. Somente então criar o commit local autorizado.

Após o commit, validar status, hash, conteúdo e ausência de tracking ou push.
