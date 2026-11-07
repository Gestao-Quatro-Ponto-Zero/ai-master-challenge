# Validação da entrega

Pacote preparado em 06/11/2026 (horário de São Paulo). Resultado registrado na preparação local, antes de qualquer publicação ou Pull Request.

## Integridade e isolamento

- 108 arquivos de solução, totalizando 4.602.340 bytes nesta geração; SHA-256 de cada arquivo registrado em `../manifest.json` e conferido contra os bytes copiados.
- Inclusão por lista explícita. Dependências, builds, backups, ZIP original, arquivos de credenciais e registros privados do navegador excluídos do manifesto.
- Código, CSVs públicos, snapshot, testes, documentação e assets necessários acompanham a solução. A instalação deve ser feita dentro de `solution/`.
- O projeto original continua no lugar; nenhuma conta externa foi provisionada e nenhum repositório remoto foi alterado.

## Verificação independente

Executada dentro de `submissions/rafael-dias/solution/`, com dependências instaladas nessa pasta:

| Verificação | Resultado |
|---|---|
| `npm ci --no-audit --no-fund` | Instalação independente concluída: 31 pacotes |
| `npm run data` | Reconstrução dos CSVs: 8.800 totais, 2.089 abertas, 1.425 sem conta |
| Integridade após reconstruir os dados | Todos os hashes continuam idênticos ao manifesto |
| `npm run check` final | Formatação, 58 testes e build de produção aprovados |
| Configuração de raiz | Build final usa `next.config.mjs` da solução, sem aviso de raiz inferida da pasta-pai |
| `npm start -- --port 3004` | Servidor de produção iniciou com sucesso |
| Requisição HTTP à página inicial | 200; título G4 Sales Priority, ação Trabalhar oportunidade e dados presentes no HTML |
| Requisição HTTP ao SVG da marca | 200 |
| Links relativos Markdown | 29 links locais em 17 documentos conferidos, sem destinos ausentes |

Ambiente: Windows, Node.js v24.21.0. A tentativa offline inicial falhou por cache incompleto; a instalação com download concluiu. O acesso HTTP exigiu executar o servidor/verificação com acesso local adequado; isso não exigiu mudar a aplicação. A instância temporária de verificação foi encerrada ao finalizar, preservando a instância original de trabalho.

O pacote foi testado em pasta própria no mesmo computador, com raiz explicitamente configurada; isso não equivale à revisão por terceiro ou à instalação em outro sistema operacional. A navegação interativa completa não foi repetida nesta etapa de empacotamento.

## Evidências anteriores preservadas

Antes do empacotamento, a versão original passou em 58 testes, formatação e build de produção. A conferência de navegador, descrita no process log, incluiu registros fictícios, recarga, pausa, risco financeiro, tema escuro e formulário móvel. Essas verificações anteriores não são apresentadas como uma nova sessão de teste do navegador no pacote.

## Pendências externas

- Instalação e avaliação por outra pessoa em outro computador.
- Piloto com vendedores e medição de eficácia comercial.
- Fork, branch, revisão do diff e envio pelo Pull Request obrigatório.
- Publicação opcional na Vercel; integração de atividades compartilhadas para uso real.
