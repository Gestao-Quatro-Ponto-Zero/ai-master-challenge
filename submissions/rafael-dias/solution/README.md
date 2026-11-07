# G4 Sales Priority

Aplicação do Challenge 003 do G4 Educação. Transforma 2.089 oportunidades abertas em uma rotina de execução por vendedor, com cinco prioridades do dia, contexto do cliente, pontuação explicada, registro de ações, qualificação SQL, agenda e acompanhamento de resultados. Usa dados públicos reais, sem login na demonstração.

## Experimentar o fluxo comercial

1. Em **Meu dia**, escolha a carteira de um vendedor no topo. A tela abre com cinco oportunidades identificadas; contas ausentes ficam em uma fila separada.
2. Clique em **Trabalhar oportunidade** para ver dados da conta, motivos do score e um roteiro de abordagem.
3. Cadastre um contato verificado. O dataset não tem telefone, e-mail ou nome do comprador; não inventamos esses dados. Os atalhos abrem o aplicativo de telefone/e-mail do computador, sem envio automático.
4. Registre se houve resposta, quando a ação ocorreu e se o cliente aceitou o próximo passo. Compromissos futuros ficam na agenda; quando vencem, entram no foco mesmo fora da rodada atual. Bloqueio financeiro pode gerar revisão interna antes do retorno, sem antecipar contato.
5. Confirme um SQL somente com evidências de necessidade, decisor e prazo. Registre proposta, follow-ups e venda (valor real) ou perda (motivo).
6. Na proposta, informe valor total em USD e condições financeiras quando conhecidos. Se o cliente pedir pausa, registre a data para retomar. Acompanhe as etapas em **Meu pipeline** e as contagens/conversões em **Resultados**, para a carteira ou empresa.
7. Abaixo das oportunidades, **Rodadas do dia** mostra quatro checkpoints de até cinco ações, sem repetir clientes na tela. A próxima rodada entra no foco ao concluir a atual; o pipeline continua livre. Até vinte oportunidades reais por dia e vendedor, sem inventar tarefas em carteiras menores. Conclusões anteriores são preservadas. Notas e simples reagendamentos não concluem tarefas de contato.

O detalhe traz fatos históricos da conta, lacunas e um roteiro comercial. No seletor **O que aconteceu?**, escolha a ação executada e preencha o formulário correspondente. A escolha não altera o roteiro nem confirma atividades. Após salvar, aparecem o próximo passo sugerido e o compromisso combinado.

O logo em `public/brand/g4-original-white.svg` é o arquivo original publicado no [site oficial](https://g4business.com/wp-content/uploads/2026/01/logo-g4-completa-branca.svg), usado sem redesenho. O projeto demonstrativo independente usa o nome **G4 Sales Priority**, escolhido pelo usuário. Pesquisa e referências ficam somente na documentação.

**Persistência da demonstração:** atividades, contatos e tarefas ficam no armazenamento deste navegador e continuam após recarregar a página. São compartilhados entre as carteiras selecionadas neste navegador, mas não sincronizam com outros computadores. O painel da empresa agrega esses registros locais. A base pública pode ser lida do Supabase; as atividades ainda não são gravadas nele. Para uso simultâneo por 35 vendedores, faltam autenticação e armazenamento compartilhado de atividades. Exporte atividades em Resultados para ter uma cópia JSON; ainda não há importação/restauração pela interface.

O score original é uma referência histórica. **Saúde comercial v2** considera qualificação (40), participação e atualidade da resposta do comprador (25), aceite/data do próximo passo (25) e viabilidade financeira (10). Sem evidência suficiente, aparece “Em validação”; riscos prevalecem sobre uma soma alta. A fila operacional considera urgência e avanço atual antes do potencial. São regras de piloto, sem probabilidade calibrada ou ganho de vendas comprovado. Veja [política ativa](docs/health-v2-implementation.md).

## Interface e conversa comercial

- Prioridade: 80–100 verde, 60–79 âmbar, abaixo de 60 vermelho, com rótulo textual. Saúde e etapas também têm indicação própria; cor não representa probabilidade de venda.
- Perguntas SPIN de situação, problema, implicação e valor da solução usam conta, produto e histórico disponível. São sugestões de investigação; não presumem dores ou respostas. A referência é a [metodologia da Huthwaite](https://www.huthwaiteinternational.com/spin-methodology), sem afirmar adoção oficial pelo G4.
- O card mostra dados, passos e formulário sem seções escondidas. O SPIN é compacto, com abas Situação, Problema, Implicação e Valor da solução; as perguntas mantêm a linguagem revisada. O atalho “Registrar resultado” leva diretamente ao formulário, que permanece visível.
- No Kanban, arraste para avançar ou registrar perda. Soltar abre somente uma janela de registro da etapa, sem o card completo. O card muda após salvar e cumprir os critérios, e a janela fecha. Cancelar não altera a etapa. Retorno a etapas anteriores e reabertura de encerrados não são suportados nesta versão. No celular ou teclado, abra o card e selecione a ação correspondente.
- Menu mais largo, opção de recolher, controle de tema com ícones de sol/lua e busca de vendedor por nome, gestor ou região. Preferências visuais ficam neste navegador, preservando atividades e planos. Textos secundários, formulários e roteiros têm cores específicas de contraste no modo escuro.
- O funil tem cores por etapa e contagens cumulativas. A largura é ilustrativa; não representa taxas entre etapas.
- O seletor de vendedor ordena carteiras por quantidade de oportunidades abertas. A distribuição foi preservada do CRM, sem redistribuir leads; detalhes do diagnóstico ficam na documentação.

## Rodar localmente

Requer Node.js 20.9+ e npm. Na pasta do projeto:

```sh
npm ci
npm run data
npm test
npm run dev
```

Abra http://127.0.0.1:3000 **no navegador**. Deixe o terminal aberto. No PowerShell do Windows, use `npm.cmd` se a execução de `npm.ps1` estiver bloqueada; não é necessário mudar políticas do Windows. Mantenha o mesmo host e porta para recuperar os registros do navegador. Não é necessário configurar contas externas para experimentar: o modo local usa o mesmo snapshot público preparado para o Supabase.

```sh
npm run build
npm start
```

## Supabase: projeto novo

1. Crie um projeto no seu Supabase e execute `supabase/schema.sql` no SQL Editor.
2. Copie `.env.example` para `.env.local`. Preencha `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` com os valores do projeto. A chave secreta fica exclusivamente no servidor e nunca deve receber prefixo `NEXT_PUBLIC_` ou entrar no Git.
3. Execute `npm run db:import` para importar 2.089 oportunidades. A importação faz upsert por ID e pode ser repetida para este snapshot.
4. Defina `DATA_SOURCE=supabase` e reinicie o servidor. A interface passa a mostrar “Supabase conectado”. Erros de conexão ou importação incompleta são explícitos; não há fallback silencioso para dados locais.

A tabela usa RLS sem acesso anônimo. O servidor lê o dataset público com a chave de serviço. A tabela guarda o snapshot enriquecido das oportunidades abertas; CSVs completos e preparação reproduzível ficam no projeto. A versão inicial não é um CRM transacional nem sincroniza alterações em tempo real.

## Publicar na Vercel

Importe este projeto por um repositório seu na Vercel, usando o preset Next.js e o comando `npm run build`. Para o modo Supabase, configure as três variáveis de `.env.example` no ambiente do servidor antes de publicar. Para demonstração local na nuvem, `DATA_SOURCE=local` dispensa credenciais. O projeto remoto e a publicação dependem do acesso às contas do proprietário; não são criados pelo código local.

## Dados e método

- Fonte: [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics), licença CC0 conforme o [README do desafio](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/challenges/build-003-lead-scorer/README.md).
- 8.800 oportunidades; 4.238 ganhas; 2.473 perdidas; 1.589 em negociação; 500 em prospecção.
- Data de referência explícita: **31/12/2017**, escolhida a partir do último fechamento disponível, sem afirmar que é a data certificada de extração.
- 1.425 oportunidades abertas não têm conta. A ausência aparece como tarefa, não penalização de perfil.
- Normalização documentada: `GTXPro` → `GTX Pro`, em 1.480 registros do pipeline completo.

Leia [metodologia](docs/methodology.md), [process log](docs/process-log.md) e o perfil reproduzível em `docs/data-profile.json`. A tela “Entenda as prioridades” também explica as regras dentro da aplicação.

## Limitações

É um índice heurístico, não probabilidade calibrada ou garantia de aumento de conversão. A base original não tem data de criação, histórico de estágio, último contato, proposta, quantidade ou previsão de receita. Atividades e qualificações novas são registros manuais da demonstração, não dados históricos descobertos. Não é possível reconstruir integralmente um backtest point-in-time. O ciclo histórico dos encerrados sofre viés de seleção: negócios ainda abertos não entram na média. Filtros não são autorização de acesso. Para dados privados, adicionar autenticação, autorização por equipe, auditoria e sincronização antes do uso real.

## Manutenção e continuidade

Comece pelo [guia de manutenção](docs/maintenance.md): mapa de telas, regras, armazenamento, contratos dos registros, pontos de extensão e limites. O [roteiro de verificação](docs/refactor-validation.md) descreve a conferência dos fluxos e a comparação visual.

- `app/`: entradas Next.js, composição e índice de estilos.
- `components/`: interface compartilhada e estrutura da aplicação.
- `features/`: telas e funcionalidades comerciais separadas por área.
- `lib/`: regras e projeções puras, formatação, contratos e acesso aos dados.
- `tests/`: verificações automatizadas.

Execute `npm run check` (no PowerShell, `npm.cmd run check`) com o servidor parado: formatação, testes e build. A refatoração manteve as chaves do armazenamento e os registros existentes. Não há migração de banco ou publicação nesta etapa.

## Entrega

O [guia de submissão](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/submission-guide.md) exige solução e process log via Pull Request. Nenhum PR ou publicação é criado automaticamente por este projeto.

No workspace de desenvolvimento, o pacote fica em `submissions/rafael-dias/`, com README do candidato, `solution/`, `process-log/` e `docs/`. Para gerá-lo novamente a partir do código de trabalho, execute `node scripts/prepare-submission.mjs` na raiz original. O gerador usa uma lista explícita de arquivos e recusa sobrescrever alterações feitas diretamente na solução empacotada. Não edite as duas cópias em paralelo. Esse utilitário de preparação não integra o aplicativo entregue.
