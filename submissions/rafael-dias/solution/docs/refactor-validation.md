# Verificação da reorganização

## Escopo

Separação estrutural do código, mantendo regras e aparência. Nenhuma alteração de score ou publicação externa faz parte desta etapa.

## Evidências automatizadas

- Base anterior: 24 testes aprovados.
- Base reorganizada: 32 testes aprovados, incluindo oito novos para compatibilidade, falha de armazenamento e filtros/projeção de carteiras.
- Compilação de produção aprovada. Um bloqueio de criação de pasta de build no Windows foi resolvido ao executar a compilação com acesso adequado; não foi necessário alterar regras da aplicação.
- Formatação cobre `app`, `components`, `features`, `lib`, `scripts` e `tests`.

## Roteiro de interface

1. Reabrir o mesmo endereço e verificar vendedor, atividades e progresso anteriores.
2. Abrir uma oportunidade: dados da conta, score, roteiro e SPIN permanecem disponíveis.
3. Selecionar cada tipo de registro: os campos correspondentes aparecem sem mudar o roteiro ou executar uma transição antes de salvar.
4. Cadastrar contato fictício; conferir histórico e próximo passo.
5. Registrar conversa com contexto e data futura; conferir agenda e etapa.
6. Confirmar SQL com necessidade, decisor e prazo; conferir saúde e histórico.
7. Registrar proposta e venda fictícia com valor positivo; conferir resultados e fechamento.
8. Em outra oportunidade, conferir perda com motivo, nota e reagendamento.
9. Arrastar no Kanban: deve abrir registro resumido, cancelar deve preservar a etapa.
10. Buscar por ID e trocar vendedor; conferir isolamento e carteiras vazias.
11. Alternar claro/escuro, recolher/expandir menu, verificar ajuda e filtros de resultados.
12. Recarregar e verificar persistência. Conferir layout de 390 px sem rolagem horizontal na página inicial.

Não simular retorno vencido alterando o relógio do computador ou adulterando armazenamento. Regras temporais são cobertas pelos testes de domínio.

## Comparação inicial/final

Na carteira de Boris, os registros existentes e o progresso 1/20 foram mantidos. No desktop de 1440 × 1000, largura, altura, fonte, cor e fundo de menu, destaque, fila, checkpoints, indicadores e seletor de tema foram comparados antes/depois e permaneceram iguais.

As capturas ficam em `docs/screenshots/refactor-before.png` e `refactor-after.png`. Medidas equivalentes nesses elementos não garantem equivalência visual de todos os estados; a conferência dos demais fluxos complementa essa comparação.


## Execução no navegador

Em origem de QA separada (`localhost:3003`, distinta de `127.0.0.1:3003`), cadastro fictício, contato, SQL, proposta e venda fictícia de USD 100 foram registrados; depois nota, reagendamento e perda em outra oportunidade. Cancelar um arraste preservou a etapa. Recarregar preservou cinco eventos na venda e três no segundo negócio; Resultados mostrou 1 contato, 1 SQL, 1 venda e 1 perda, com histórico de 2017 separado. Filtro de outro gestor retornou zero atividades dessa carteira. Nenhuma comunicação ou transação real foi realizada.

Conferidos também: tema escuro, recolher/expandir menu, ajuda, versão de 390 px (largura de conteúdo 380 px, sem transbordamento horizontal) e execução final completa de npm run check, aprovada com 32 testes. Hashes SHA-256 de scoring.mjs, workflow.mjs, sales-guide.mjs e prepared.json permaneceram iguais aos da cópia anterior.
