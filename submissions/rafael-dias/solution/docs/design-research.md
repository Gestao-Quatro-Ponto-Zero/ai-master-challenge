# Pesquisa e redesenho da experiência — 06/11/2026

## Dor observada pelo usuário

A primeira versão era uma tabela explicável, mas exigia que o vendedor decidisse o que fazer. O usuário pediu uma ferramenta com foco, contexto do cliente, score, próxima ação, passos posteriores e visão de funil pessoal/empresa. A média de 251 oportunidades inclui encerradas; as 2.089 abertas equivalem a aproximadamente 60 por vendedor cadastrado (distribuição não uniforme). A revisão detalhada encontrou 27 vendedores com oportunidades abertas e oito sem abertas neste snapshot: cerca de 77 por vendedor com carteira aberta, com variação de 31 a 194. O seletor inclui os 35 cadastrados, com estado vazio para carteiras sem oportunidades.

## Referências encontradas no Behance

- [Track x CRM — Sales CRM & UI/UX Dashboard Design](https://www.behance.net/gallery/244656771/Track-x-CRM-Sales-CRM-UIUX-Dashboard-Design): descrição pública aborda inteligência comercial, progresso de pipeline e gestão de atividades. Referência de organização por execução, não só análise.
- [Smart CRM Analytics Dashboard](https://www.behance.net/gallery/241526897/Smart-CRM-Analytics-Dashboard): descrição pública cita perfis centralizados, status de negociação, tarefas, follow-ups e reuniões. Referência de conexão entre cliente, ação e progresso.

As páginas completas retornaram 403. A pesquisa se baseou nas descrições indexadas e resultados de busca; não afirmamos ter inspecionado todos os layouts ou testado esses conceitos. Behance oferece inspiração, não evidência de ganho comercial. Nenhuma tela foi copiada.

## Paleta

Consulta do HTML público do [site oficial do G4](https://g4business.com/) identificou #B9915B (dourado), #F5F4F3 (fundo), #031A26 e #001F35 (azuis escuros). A [página institucional](https://g4business.com/sobre) descreve a identidade atual com dourado editorial. Aplicação usa esses tons e neutros auxiliares; não é reprodução certificada de manual de marca nem produto oficial.

## Decisões aplicadas

1. Carteira individual por padrão; empresa acessível em Resultados.
2. Meu dia: cinco prioridades, uma oportunidade em destaque, motivo e botão de trabalho.
3. Cadastro sem conta separado da lista de negociações identificadas, sem alterar o score por ausência.
4. Perfil do cliente, composição de score e roteiro no mesmo contexto da ação.
5. Registro de contato exige resultado e próximo compromisso com data/hora. Retornos vencidos sobem no foco; agendados aguardam na agenda.
6. SQL confirmado somente mediante evidências de necessidade, decisor e prazo. Proposta e venda exigem SQL confirmado.
7. Pipeline visual com avanço por atividades. Sem arrastar arbitrariamente para SQL ou venda sem justificativa.
8. Resultados separados: execução registrada nesta demo e distribuição histórica do CRM. Taxas têm denominador explícito; ausência de resultados aparece como zero ou sem denominador, nunca dado inventado.
9. Saúde operacional separada do score histórico. Não afirmar propensão de compra, intenção ou contato recente sem evidência.
10. Persistência local transparente. Não apresentar a visão da empresa como sincronização de 35 pessoas quando ainda não há acesso por usuário nem banco compartilhado para atividades.

## Critérios de aceitação

- Em poucos segundos o vendedor identifica uma conta, um motivo e uma ação.
- Registrar atividade produz mudança observável em histórico, agenda e/ou etapa.
- Recarregar preserva os registros neste navegador.
- Qualificar e fechar altera resultados pessoais e da empresa neste navegador.
- Dados ausentes e limites da demonstração são compreensíveis.

Testes de utilidade com vendedores e medição de impacto comercial continuam pendentes.

## Refinamento pontual — contraste e navegação

Nova consulta pública a [G4 Skills](https://g4business.com/g4-skills), [CRM System concept — Dark dashboard](https://www.behance.net/gallery/91298083/CRM-System-concept-Dark-dashboard) e [SaaS CRM Dashboard — Light and Dark Mode](https://www.behance.net/gallery/181318331/SaaS-CRM-Dashboard-Light-and-Dark-Mode). As páginas completas do Behance voltaram a bloquear acesso; as descrições indexadas foram usadas como referência temática, sem alegar inspeção de todos os layouts.

A aplicação preserva a estrutura aprovada. Mudanças focam alinhamento simétrico, transição curta de largura, contraste explícito também em pseudo-elementos e badges, busca uniforme e perguntas frequentes apresentadas como cartões. Não reintroduzimos referências na interface.


## Rodadas compactas e registro previsível

Consulta a [Track x CRM](https://www.behance.net/gallery/244656771/Track-x-CRM-Sales-CRM-UIUX-Dashboard-Design) e [CRM System / UX/UI](https://www.behance.net/gallery/210777021/CRM-System-Dashboard-UXUI-design): resultados indexados descrevem acompanhamento de atividades e tarefas. Páginas completas retornaram 403, portanto não foi possível inspecionar seus layouts ou interações. São referências temáticas, não pesquisa de campo nem validação com vendedores.

Decisão própria: preservar o destaque inicial e a fila de clientes; progresso secundário em quatro checkpoints compactos abaixo da fila, chamados Rodadas do dia (termo de interface, sem alegar padrão comercial). Eliminar a lista duplicada de tarefas. No card, um único seletor nativo O que aconteceu? escolhe o registro; somente os campos de preenchimento mudam. O roteiro e o SPIN permanecem estáveis, sem rolagem automática na escolha. Registro altera pipeline apenas ao salvar, mantendo validações de SQL e venda.
