# Animações do console Mesa de Suporte

Gravações do console rodando de verdade: build estático de `solution/app/out`, servido com `scripts/serve-prod.mjs` (mesmos cabeçalhos de produção do `vercel.json`), em Chrome headless. Nenhum arquivo do app foi alterado para gravar. O único acréscimo é visual e só existe na gravação: um ponteiro (círculo marinho com borda off-white e pulso dourado no clique) e, no celular, um indicador de toque, porque o headless não desenha cursor.

Cada animação tem três arquivos: `.mp4` (H.264, 30 fps, sem áudio, +faststart), `.gif` (loop infinito, para aparecer direto na descrição do PR) e `-poster.png` (o quadro mais representativo).

| Arquivo | O que mostra | Duração | Tamanho |
|---|---|---|---|
| `fila.mp4` / `fila.gif` | Home: rola até a tabela e para o mouse no "i" de Confiança, com a explicação aberta. Ordena por Confiança (da maior para a menor) e depois por Rota, primeiro com automático no topo e depois com humano no topo. Abre o T-10264 (Humano, que o roteador errou) e mostra a explicação de "Por que essa fila". Troca a fila dele para Diversos e aplica, confirma o T-10245 e termina em "Nesta sessão: 2 decisões, 1 correções humanas (taxa de override 50%)". | 20,6 s | MP4 2,2 MB · GIF 5,6 MB (1200 px, 12 fps) |
| `testar.mp4` / `testar.gif` | /testar/: clica nos 8 exemplos em sequência, com pausa para ler cada decisão. Hardware, Acesso e RH vão para Automático. Direito de administrador vai para Assistido ("Pedido de direito de administrador: uma pessoa sempre confirma"). Em português e Com erros de digitação vão para Humano (texto fora do vocabulário). Ataque: palavras coladas vai para Assistido ("Pode ter conteúdo de RH ou de acesso privilegiado"). Ataque: palavras intercaladas vai para Humano ("Sequência de palavras que não existe no histórico"), e a animação para cerca de 2 s nesse último. | 19,4 s | MP4 0,6 MB · GIF 1,7 MB (1200 px, 12 fps) |
| `diagnostico.mp4` / `diagnostico.gif` | /diagnostico/: as três perguntas do Diretor (52%, 0,005 e 87 h). Depois o business case: tickets por mês de 2.500 para 10.000 e minutos de triagem de 3 para 5. Os números grandes mudam ao vivo: de 87 h, 0,5 pessoa e R$ 3.911 por mês para 539 h, 3,4 pessoas e R$ 24.253 por mês. | 15,5 s | MP4 1,6 MB · GIF 4,3 MB (1200 px, 12 fps) |
| `estresse.mp4` / `estresse.gif` | /estresse/: rolagem pelas quatro severidades (extremamente crítico, crítico, médio, leve), parando na seção "Segurança · pentest": tabela S1 (antes e depois das travas novas) e tabela S2 (ataques ao console). | 12,5 s | MP4 3,1 MB · GIF 6,9 MB (1200 px, 10 fps) |
| `mobile.mp4` / `mobile.gif` | Celular 390 × 844: rola com o dedo até os cards da fila, toca no T-10243, a folha inferior abre com o detalhe, rola dentro dela até a decisão, toca em "Confirmar RH", a folha fecha e o card fica marcado como "confirmado". | 11,3 s | MP4 1,4 MB · GIF 3,5 MB (390 px, 12 fps) |

Pôsteres: `fila-poster.png` (tabela ordenada por rota e troca de fila registrada no T-10264), `testar-poster.png` (ataque de palavras intercaladas segurado em Humano), `diagnostico-poster.png` (business case com as premissas novas), `estresse-poster.png` (tabela S1 do pentest), `mobile-poster.png` (folha inferior aberta). Desktop em 1440 × 900, celular em 780 × 1688.

## Como foi gravado

- Desktop em 1440 × 900 com densidade 2x, reduzido para 1440 px no MP4 e 1200 px no GIF. Celular em 390 × 844, densidade 2x, com toque emulado (MP4 em 780 px, GIF em 390 px).
- Os quadros vêm do próprio compositor do Chrome com o horário de cada um e são reamostrados em taxa constante, então o tempo da tela é o tempo real.
- `fila` foi acelerada 1,35x, `testar` 1,2x e `diagnostico` 1,1x na montagem, para caber em cerca de 20 s. `estresse` e `mobile` estão em velocidade real.
- O GIF de `estresse` está em 10 fps porque a rolagem troca a tela inteira a cada quadro e, em 12 fps, passava de 8 MB.
- Os dados que aparecem são os do próprio protótipo: amostra de 43 tickets reais do conjunto de teste e o modelo rodando no navegador.
