# CRP-000 prompt file discussion
_Exported on 3/21/2026 at 07:35:34 GMT-3 from Cursor (2.6.19)_

---

**User**

@focus-score-challenge-gap-closure-pack/crps/CRP-REAL-06-clean-repo-noise-and-isolate-legacy.md 

@focus-score-challenge-gap-closure-pack/crps/CRP-REAL-07-rewrite-readme-as-final-submission.md 

@focus-score-challenge-gap-closure-pack/crps/CRP-REAL-08-upgrade-tests-to-real-dataset-path.md 

@focus-score-challenge-gap-closure-pack/crps/CRP-REAL-09-refresh-demo-and-evidence-on-real-flow.md 

@focus-score-challenge-gap-closure-pack/crps/CRP-REAL-10-final-audit-against-challenge-readme.md 

execute esse@focus-score-ux-competition-pack/prompts/CURSOR_MASTER_PROMPT_UX.md e, já passe para esses demais:

@focus-score-ux-competition-pack/crps/CRP-UX-01.md @focus-score-ux-competition-pack/crps/CRP-UX-02.md @focus-score-ux-competition-pack/crps/CRP-UX-03.md @focus-score-ux-competition-pack/crps/CRP-UX-04.md @focus-score-ux-competition-pack/crps/CRP-UX-05.md @focus-score-ux-competition-pack/crps/CRP-UX-06.md @focus-score-ux-competition-pack/crps/CRP-UX-07.md @focus-score-ux-competition-pack/crps/CRP-UX-08.md @focus-score-ux-competition-pack/crps/CRP-UX-09.md @focus-score-ux-competition-pack/crps/CRP-UX-10.md  

bota tudo no ar, por favor

@focus-score-combobox-crps-pack/cursor-master-prompt.md @focus-score-combobox-crps-pack/crps execute todos! na sequencia.

faça um  belo commit

CRP-CBX-08 — Transformar “Gestor Comercial” em combobox funcional com autocomplete

Objetivo
Converter o campo “Gestor Comercial” de input texto para um combobox digitável real, com autocomplete a partir de 3 letras, usando a lista real de gestores vinda da API.

Contexto
A tela atual já mostra:
- “Escritório Regional” como select
- “Gestor Comercial” ainda como textbox com placeholder “Digite 3 letras para buscar”
Ou seja: o comportamento esperado ainda não foi implementado de verdade.

A aplicação roda no frontend atual em `public/` com HTML + CSS + JavaScript, servida pelo backend. Não migrar stack. Não trazer React. Resolver na stack atual.

Escopo
Implementar apenas o combobox de “Gestor Comercial”, sem mexer nos outros filtros além do necessário para integração.

Requisitos funcionais
1. Carregar a lista real de gestores a partir do endpoint de opções de filtro já usado pela UI.
2. Ordenar alfabeticamente os gestores.
3. Remover nulos, vazios e duplicados.
4. Transformar o campo em combobox real:
   - campo digitável
   - dropdown de sugestões
   - seleção por clique
   - seleção por teclado
5. Comportamento mínimo:
   - com menos de 3 letras: não listar resultados; mostrar dica “Digite 3 letras para buscar”
   - com 3 letras ou mais: filtrar gestores em tempo real
   - busca case-insensitive
   - preferir match por prefixo; se simples de implementar, aceitar contains
6. Estados obrigatórios:
   - vazio inicial
   - carregando, se aplicável
   - nenhum resultado encontrado
   - valor selecionado
7. Teclado:
   - seta para baixo / cima navega nas opções
   - Enter seleciona
   - Esc fecha
   - Tab não quebra o fluxo do formulário
8. Ao selecionar um gestor:
   - o valor deve preencher o filtro corretamente
   - a submissão de filtros deve enviar esse gestor no payload normal da tela
9. Ao limpar filtros:
   - o campo deve voltar ao estado inicial
10. O componente deve fechar ao clicar fora.

Requisitos de UX
- Não mostrar JSON, IDs internos ou estrutura técnica.
- O campo precisa parecer parte do cockpit atual.
- O dropdown deve ficar visualmente alinhado com os outros controles.
- A mensagem “Digite 3 letras para buscar” pode aparecer como helper text antes do filtro ativar.
- Se não houver resultado, mostrar “Nenhum gestor encontrado”.

Requisitos técnicos
1. Não duplicar lógica de opções se já houver utilitário de carregamento/normalização.
2. Se necessário, criar função utilitária pequena e reutilizável para:
   - normalizar lista
   - ordenar
   - filtrar opções
3. Não espalhar listeners de forma caótica.
4. Manter o código legível e pequeno.
5. Se houver necessidade, adicionar atributos semânticos mínimos de acessibilidade para combobox/listbox.

Arquivos esperados para revisão
- frontend shell em `public/` ou arquivos equivalentes usados pela tela atual
- qualquer utilitário de filtros relacionado
- documentação curta se necessário

Atualizações obrigatórias
1. Atualizar `PROCESS_LOG.md` com:
   - objetivo do CRP
   - ferramenta de IA usada
   - prompt relevante
   - o que a IA propôs
   - qualquer erro ou ajuste feito manualmente
   - evidência gerada
2. Atualizar `LOG.md`
3. Se houver documentação de UI/filtros, atualizar também

Evidências obrigatórias
- screenshot do campo “Gestor Comercial” funcionando como combobox
- evidência com busca por 3 letras
- evidência com “Nenhum gestor encontrado”
- evidência com seleção aplicada ao filtro
- evidência com “Limpar filtros” resetando o campo

Definition of Done
- “Gestor Comercial” deixou de ser textbox simples
- existe combobox funcional com autocomplete real
- lista vem da API real
- resultados são ordenados alfabeticamente
- filtro só começa a sugerir a partir de 3 letras
- mouse e teclado funcionam
- seleção é aplicada corretamente no filtro
- limpar filtros reseta o campo
- process log e evidências foram atualizados

Validação manual obrigatória
Testar pelo menos estes casos:
1. Digitar menos de 3 letras → não listar resultados
2. Digitar 3 letras válidas de um gestor real → listar sugestões
3. Selecionar com mouse
4. Selecionar com Enter
5. Pressionar Esc para fechar
6. Buscar valor inexistente → mostrar “Nenhum gestor encontrado”
7. Aplicar filtro com gestor selecionado
8. Limpar filtros e confirmar reset do campo

Restrições
- Não migrar framework
- Não reescrever a tela inteira
- Não mexer em outros filtros além do necessário
- Não criar overengineering

Saída esperada
Editar os arquivos reais do projeto e, ao final, entregar um resumo curto em markdown com:
- arquivos alterados
- como o combobox foi implementado
- evidências geradas
- pendências ou limitações, se houver

