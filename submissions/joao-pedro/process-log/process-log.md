# Process Log - Como usei IA
### Ferramentas usadas:
| Ferramenta | Para que usou |
|------------|--------------|
| _Claude Code_ | _Conversa inicial sobre o desafio + entendimento básico sobre os dados fornecidos_ |
| _Cursor_ | _Construção do protótipo web_ |
| _Claude code + Cursor_ | _Agente do claude dentro do cursor para auxílio no protótipo web_ |
### Workflow:
1. A primeira coisa que fiz foi recolher e juntar todo o material de contexto disponível do desafio.
2. Juntei a descrição da vaga + descrição do desafio + sumário resumido do escopo dos dados fornecidos.
3. Desde o princípio eu já tinha a ideia de trabalhar no desafio 03, mas mesmo assim enviei todas as descrições ao Claude para que - com base em um arquivo eu.md do meu ambiente -, ele pudesse me confirmar a escolha.
4. Feita a escolha do desafio e, com todo contexto dele "em mãos", abri o kaggle e começei a tirar as minhas primeiras conclusões.
5. Confesso que apenas visualizando os dados-base fornecidos, não estava conseguindo ir muito além de um modelo preditivo tradicional.
6. Foi quando finalmente comecei a utilizar o Claude para a análise de fato dos dados da data-base.
8. Contextualizei o Claude sobre algumas análises que eu havia feito e o instiguei a "pensarmos fora da caixa".
9. Foi ai que chegamos ao conceito de "features óbvias" vs "features imperdíveis".
10. O claude me gerou +20 features chamadas de "imperdíveis", mas a maioria esmagadora era pautada em modelos de ML complexos e detalhados.
11. Deixei claro a ele que o desafio não priorizava complexidade, e que a partir daquele momento nossa energia deveria estar concentrada em responder: "O que o vendedor precisa ver na tela segunda-feira de manhã?"
12. Com esse conceito batido, abri o cursor e criei um projeto com os 4 arquivos csv da data-base.
13. Utilizando o ploty criei uma view-base dos dados dos csvs fornecidos - nada demais, apenas tornar visual as métricas primárias.
14. Devo confessar novamente que apenas com as visualização das métricas primárias, não consegui enxergar nada demais além do óbvio.
15. Foi aí que pedi ao agente do claude, dentro do cursor, que criasse as views detalhadas das features "imperdíveis" - as páginas de "Analysis" do streamlit.
14. Com as métricas detalhadas em mãos, comecei a descartar algumas das 20 features imperdíveis.
15. Em uma primeira limpeza, as 20 métricas foram reduzidas para 10.
16. Até que em dado momento chegamos ao questionamento principal da tese: Por que vendedores com 0 prospects tem sobrecarga em engage?
17. Ao investigar a fundo o ponto, descobrimos correlações com outras métricas e definimos que seria essa a tese.
18. Com isso em mente, tratei de criar as documentações base da aplicação, que serviria posteriormente para um readme da vida mas principalmente que seriviria como ouro para a janela de contexto do agente Claude que eu conversava - criei vários arquivos .md dos conceitos discutidos e sempre que precisava recupera-los no contexto solicitava ao Claude.
19. Estimo que 70% do tempo investido no desafio foi na estruturação da página que pode ser visualizada no streamlit, eis o porque:
20. Pode-se inferir que a página do streamlit é o data-center de toda a aplicação.
21. Se observado com detalhe, todas as pontas que se derivam do projeto vem do que foi construído no streamlit: Documentações, teses, readme, gráficos, métricas, etc.
22. Com essa "base" pronta, o que fiz após foi somente destinar os resultados lá armazenados aos destinos corretos: Alguns pontos foram para documentações, outros foram para o frontend em react, outros para arquivos do desafio como esse.
23. Bom, eu nunca havia descrito um process log de utilização de IA em algum projeto, e não achei que seria tão difícil.
24. Mas se eu pudesse sintetizar todo o processo de utilização de IA nesse projeto, diria que foquei em utilizar a IA para fazer um arroz com feijão bem feito: Boas documentações e explicabilidade antes de modelos complexos ou lógicas revolucionárias.
# Onde a IA errou e como corrigi
### Devo adimitir que não lembro de erros muito expressivos das IAs que utilzei na elaboração e construção da tese.
### Um dos pontos nesse sentido claros e frescos para mim era que constantemente eu tinha que relembrar o contexto simples da tese, no sentido de rejeitar modelos complexos de ML ou coisas do tipo.
# Evidências:
Em anexo abaixo todo o conteúdo recuperado referente ao desenvolvimento da tese com IA:
>Me coloco a disposição para enviar maiores contextos de comprovação caso necessário
1. Chathistory da primeira conversa que tive com o Claude sobre o contexto inicialL:
https://claude.ai/share/07714d82-b304-43f4-b9b5-3c365b9d38c1
2. Screenshots de algumas sessões (Claude + Cursor):
<img width="1918" height="1044" alt="SS1-processlog" src="https://github.com/user-attachments/assets/11099a01-8a1f-41dd-9b8c-e0c7cb6594de" />
<img width="1710" height="1070" alt="SS4-processlog" src="https://github.com/user-attachments/assets/1bec9eec-d5c1-4189-8f12-693ea143b53e" />
<img width="1917" height="1047" alt="SS3-processlog" src="https://github.com/user-attachments/assets/ef2b0f5c-c6a0-43e1-bfff-e8c429f49b7b" />
<img width="544" height="1060" alt="SS5-processlog" src="https://github.com/user-attachments/assets/06c52eaa-c129-4a04-9310-c6b24806e6c7" />
<img width="538" height="1049" alt="SS6-processlog" src="https://github.com/user-attachments/assets/71c5897a-248c-4b21-a6f2-fb766f87a6f0" />
<img width="1920" height="1046" alt="SS2-processlog" src="https://github.com/user-attachments/assets/20b760d5-f9ab-460e-a795-da434d3e6f17" />
