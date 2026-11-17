# Como o vídeo de demonstração foi feito

O vídeo (`../../solution/demo/ravenstack-demo.mp4`, 1 min 51 s, 1080p) é uma gravação real da ferramenta rodando localmente sobre o banco do relatório. Os cliques não foram editados.

| Arquivo | O que faz |
|---|---|
| `roteiro.json` | O texto narrado, em nove blocos, com uma frase por legenda. |
| `tts.py` | Gera a narração frase a frase com a voz pt-BR do macOS (`say -v Luciana`) e mede a duração de cada uma. A pronúncia de palavras em inglês foi ajustada só na fala; a legenda mantém a grafia certa. |
| `video.ts` | Conduz a ferramenta num Chrome automatizado (puppeteer), um clipe por bloco. Faz login como avaliador, aplica filtro, abre o SQL, faz o recorte e desce mais um nível, pergunta ao analista, envia o gráfico para uma tela nova, marca um gráfico e monta a apresentação. As respostas da IA são reais, geradas na hora. |
| `legenda.ts` | Renderiza cada legenda como imagem transparente, porque o ffmpeg desta máquina não tem filtro de legenda. |
| `compor.py` | Corta cada clipe na duração da narração, posiciona cada frase no tempo, grava as legendas na imagem e inclui também uma faixa de legenda (SRT) desligável. |

Caminhos locais foram trocados por `<pasta_de_trabalho>` e `<app>`.
