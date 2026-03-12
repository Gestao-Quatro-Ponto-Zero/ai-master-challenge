*Idéia Central* - lead scorer parecido com o rating bancário

*Plano Lógico*  - Discussão com o ChatGPT para descobrir os melhores modelos matematicos/algoritno, tecnicas para desenvolvimento do projeto. Ao final gerar um prompt para o Claude Code gerar um plano técnico.

*Problema técnico encontrado*
- Os dados históricos são antigos, o cálculo está sendo feito comparando com a data atual. Solução: Em vez de usar a data de hoje, usar a data do snapshot do deal, exemplo: days_since_engage = data_do_deal - ultimo_engajamento.
- O close_value foi removido como feature — um Lead Lost tem sempre close_value=0 e um Won tem valor positivo, o que causava leakage perfeito (AUC=0.98 artificial). Com a correção, o modelo usa sales_price (preço de lista) para todas as linhas, e o close_value real só é usado no cálculo de expected_revenue de saída.
- Os 6711 tem deals com outcome definido (Won/Lost). Os outros ~1.588 não entraram no treino porque estão em stages intermediários (sem close_value definido, filtrados durante o build_features). Os 501 são os deals abertos que recebem score. O restante pode ter sido descartado por dados faltantes na feature engineering.

*Dúvidas/Bugs*
- [x] Crie filtros dependentes (cascata) em uma aplicação de dashboard.
- [x] Lógica: Criar, documento "critérios de scoring você usou e por quê"
- [x] Planilha inteligente com fórmulas de scoring, onde está?
- [ ] Bot que envia prioridades por Slack/email, onde está?
- [x] Porque somente 6711 deals treinados? cade o resto?

*Melhorias Futuro*
- [ ] Criar um endpoint onde o CRM pode enviar os dados de uma oportunidade de venda (deal) e receber de volta,score de prioridade, probabilidade de fechamento, etc. Ou seja, a aplicação funcionaria como um serviço de scoring. Hoje os arquivos de dataset estão estáticos em uma pasta /data
- [ ] padronize as cores do ratting, na sidebar devem ser as mesma cores dos gráficos e na sidebar direita
- [ ] Fazer o envio de e-mails através de APIs ou provedores como SendGrid, Resend, Mailgun. E para mais controle substituir a cron por um painel que programmo quando enviar.






cd /Users/jessicacastro/claudecode/ai-master-challenge/submissions/jessica-castro/solution/dealsignal
python3 run_pipeline.py


cd /Users/jessicacastro/claudecode/ai-master-challenge/submissions/jessica-castro/solution/dealsignal
streamlit run app/streamlit_app.py
