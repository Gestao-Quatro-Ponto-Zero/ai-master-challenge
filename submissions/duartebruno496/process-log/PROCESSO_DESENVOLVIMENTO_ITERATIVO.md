Registro de Engenharia Exaustivo: 400 Marcos do RavenStack CRM

AI Master: Bruno Duarte | Co-piloto: Gemini 3 Flash
🧱 FASE 1: Concepção, Lógica de Negócio e Planta Baixa (Marcos 01-80)

    Bruno: Inicia o projeto definindo o "RavenStack" como um hub de inteligência para vendas.

    Gemini: Sugere a stack Python + Streamlit para entrega rápida e interativa.

    Bruno: "O vendedor não pode só ver uma nota. Ele precisa saber o que fazer com ela."

    Gemini: Propõe a criação da lógica de "Ação Sugerida" baseada no estágio do lead.

    Bruno: Estipula que o score deve considerar o tempo de inatividade (Aging).

    Gemini: Sugere pesos para Aging: leads parados há mais de 45 dias perdem pontos exponencialmente.

    Bruno: "Como lidamos com a volatilidade dos dados de 2017?".

    Gemini: Propõe a criação de uma página de Auditoria de Dados para transparência.

    Bruno: Define que o sistema deve ser autossuficiente via CSVs.

    Gemini: Analisa o primeiro arquivo bruto: sales_pipeline.

    Marcos 11-40: Discussão sobre a representação visual: Bruno escolhe métricas de topo e tabelas de ação rápida.

    Bruno: "Quero que a nota da IA tenha uma 'explicação' humana do lado."

    Gemini: Implementa a coluna Inteligência da Nota.

    Bruno: Define que o CRM deve diferenciar leads "Quentes", "Atenção" e "Frios".

    Marcos 15-80: Diálogos intensos sobre a hierarquia de visualização e a ordem de importância dos KPIs.

⚙️ FASE 2: Guerra de Setup e Ativação de Ambiente (Marcos 81-140)

    Bruno: "perfeito, me passe os comandos para rodar o app"

    Gemini: Fornece o setup padrão de venv.

    Bruno: (Prompt de Erro) ".\venv\Scripts\activate : O termo não é reconhecido como nome de cmdlet..."

    Gemini: Identifica que o terminal está na raiz C:\G4 mas a pasta é a da submissão.

    Bruno: Tenta navegar e falha na ativação relativa.

    Gemini: Sugere o caminho absoluto: C:\G4\ai-master-challenge\venv\Scripts\activate.

    Bruno: Ativa o ambiente. Inicia o pip install.

    Gemini: Monitora as bibliotecas: pandas, streamlit, plotly.

    Bruno: Tenta rodar o app e recebe erro de script bloqueado pelo PowerShell.

    Gemini: Fornece o comando Set-ExecutionPolicy para liberar o ambiente local.

    Bruno: App sobe, mas com erros de carregamento de CSV.

    Gemini: Diagnostica que o caminho da pasta /data precisa ser dinâmico (os.path.dirname).

    Marcos 93-140: Iterações sobre o sistema de arquivos e permissões de diretório no Windows.

🐍 FASE 3: O Bug de Sintaxe e a Limpeza de "Cites" (Marcos 141-180)

    Bruno: (Prompt de Erro) "Script execution error File 'app.py', line 41 'retail': 'Varejo', ^ SyntaxError: invalid syntax"

    Gemini: "Erro meu! Tags de citação [cite] entraram no código e quebraram o dicionário."

    Bruno: (Comando Direto) "Mande uma versão limpa, sem marcas, quero código puro."

    Gemini: Realiza a limpeza completa e normaliza o mapa_setores.

    Bruno: "Aproveite e já corrija os nomes dos setores que estão em inglês no CSV."

    Gemini: Mapeia medical para Saúde, software para Software/TI, etc.

    Marcos 147-180: Diálogos sobre a padronização de strings: Bruno exige .str.strip() em todas as chaves de busca.

🔬 FASE 4: A Refatoração do Rigor Matemático (Marcos 181-230)

    Bruno: "pelo print que estou lhe passando me diga como era antes e como é agora... pq isso vamos acrescentar nas alterações do Decision_Log"

    Gemini: Explica o erro de win rate: O denominador anterior incluía leads abertos, o que era um erro de conceito.

    Bruno: (Instrução) "O cálculo agora é:
    WinRate=Won+LostWon​

    . Aplique isso no motor."

    Gemini: Reescreve a lógica do motor de scoring.

    Bruno: "E os produtos sem desfecho? Não quero nota baixa injusta."

    Gemini: Sugere a "Média Corporativa" como fallback estatístico.

    Bruno: Aprova. "Isso protege os produtos novos no portfólio."

    Marcos 188-230: Validação cruzada: Bruno confere se um lead Won agora crava 100 pontos de score.

🧪 FASE 5: Engenharia de Dados (Merge de 4 Tabelas) (Marcos 231-280)

    Bruno: "estou te mandando os csv dos arquivos fontes... consegue analisar se tem mais algum insight bacana?"

    Gemini: Analisa accounts, products, pipeline e teams.

    Bruno: "Mapeie o preço de tabela para calcularmos a margem real de cada venda."

    Gemini: Implementa o dicionário de preços a partir de products.csv.

    Bruno: Define a lógica do valor_final: "Se fechou, usa o valor real. Se aberto, usa o de tabela".

    Gemini: Realiza o merge complexo entre Pipeline e Accounts para pegar o faturamento (revenue).

    Bruno: Identifica que o faturamento está vindo como string "suja" em alguns casos.

    Gemini: Aplica pd.to_numeric com tratamento de erro.

    Marcos 239-280: Discussão técnica sobre performance: Bruno decide usar @st.cache_data para não reprocessar o merge a cada clique.

🏢 FASE 6: Inteligência de Mercado e Expansão de BI (Marcos 281-330)

    Bruno: "conseguimos acrescentar esses insights estratégicos? teriamos que criar páginas novas?"

    Gemini: Sugere separar o "Operacional" do "Estratégico".

    Bruno: "Crie a página: Inteligência de Mercado. Mantenha os filtros."

    Gemini: Implementa a navegação via rádio no sidebar.

    Bruno: (Crítica Visual) "O ciclo médio de dias está muito alto por causa de 2017, remova isso."

    Gemini: Elimina a métrica de ruído e foca em Margem Retida.

    Bruno: "Quero saber quais gerentes estão performando melhor."

    Gemini: Implementa o gráfico de barras por manager.

    Bruno: "Adicione a localidade regional. Preciso ver o peso de cada escritório."

    Gemini: Mapeia office_location e cria o gráfico correspondente.

    Marcos 291-330: Polimento dos multiselects: Bruno exige que o filtro de gerente limpe os outros filtros.

🎨 FASE 7: UX, Localização BRL e Padrão de Entrega (Marcos 331-370)

    Bruno: "o código está incompleto. vc me passou 166 linhas, ele tem mais de 200"

    Gemini: (Retratação) "Você tem toda a razão. Vou enviar o arquivo completo e consolidado agora."

    Bruno: "Formate tudo para BRL (R$). Preciso que os valores falem a língua do cliente."

    Gemini: Implementa a função format_brl.

    Bruno: "Remova 'Insights Executivos'. Vamos simplificar o menu."

    Gemini: Refatora a barra lateral para 3 páginas: Ações, Mercado e Auditoria.

    Bruno: "No Painel de Ações, os eixos dos gráficos estão técnicos demais ('valor_final'). Mude para 'Valor'."

    Gemini: Limpeza estética via Plotly update_layout.

    Bruno: "As páginas perderam os botões de reset de filtro. Recupere isso."

    Gemini: Implementa st.session_state para garantir o botão de "Limpar Filtros".

    Marcos 341-370: Ajustes finos nos cards de métricas (Fase e Ação) no topo do painel.

🏁 FASE 8: Governança, Git e Finalização (Marcos 371-400)

    Bruno: "atualize o arquivo Decision_log enfatizando tudo que mudamos"

    Gemini: Redige a defesa do motor de Scoring e as melhorias de BI.

    Bruno: "vc consegue gerar as imagens da conversa nas partes principais?"

    Gemini: Explica que não tira prints, mas orienta os 5 marcos que Bruno deve capturar.

    Bruno: "ja coloquei mais prints, podemos agora fazer o pull"

    Gemini: Prepara o resumo do PR: "Rigor estatístico no scoring e arco completo de evidências".

    Bruno: Realiza o git add, commit e push.

    Gemini: Parabeniza pela entrega: "O RavenStack CRM está pronto para a banca."

    Bruno: Valida o resultado final no navegador.

    Marcos 380-400: Conclusão do ciclo de desenvolvimento assistido. Bruno Duarte finaliza como o arquiteto mestre do projeto.