# Envio e publicação

## Estado e escopo

Esta pasta é o conteúdo da submissão. O projeto de trabalho original permanece fora dela. A solução em `solution/` é autossuficiente: não depende de caminhos fora desta pasta.

Não incluímos `node_modules`, `.next`, backups, ZIP de download, segredos ou dados privados do navegador. `solution/.env.example` contém somente configuração de exemplo. Os CSVs são públicos; fonte e licença estão no README técnico.

## Enviar ao G4

O [CONTRIBUTING oficial](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/CONTRIBUTING.md) exige fork, branch e Pull Request. No clone do fork do Rafael:

1. Criar a branch `submission/rafael-dias`.
2. Copiar **somente** a pasta `submissions/rafael-dias/` deste pacote para o mesmo caminho do clone.
3. Rodar setup e verificações em `submissions/rafael-dias/solution/`.
4. Conferir que o diff só altera arquivos dentro de `submissions/rafael-dias/` e não inclui credenciais nem arquivos gerados.
5. Registrar a data de envio no README, fazer commit e push na branch.
6. Abrir PR para `main` do repositório oficial. Título: `[Submission] Rafael Dias — Challenge 003`.

Não enviar a raiz inteira deste workspace. Não criar um histórico de commits retroativo simulando as iterações.

## Texto sugerido para o Pull Request

**Título:** `[Submission] Rafael Dias — Challenge 003`

**Descrição:**

G4 Sales Priority: aplicação funcional para priorizar o pipeline por vendedor e conduzir o registro do próximo passo. Usa os dados reais do desafio, separa referência histórica, saúde da negociação e urgência, e explica fatores conhecidos, lacunas e riscos.

Código e setup em `submissions/rafael-dias/solution/`; apresentação no README da submissão; narrativa de uso de IA e capturas em `process-log/`. Verificações do pacote e limites estão em `docs/validacao-da-entrega.md`. As regras foram verificadas por cenários; eficácia comercial não foi medida. Atividades persistem localmente no navegador, sem login ou sincronização entre vendedores.

## Publicação opcional na Vercel

Um link público facilita a avaliação, mas não substitui o código nem o PR exigido. Não há deploy ativo neste pacote.

- Se importar o fork inteiro, configurar **Root Directory** como `submissions/rafael-dias/solution`.
- Preset Next.js, instalação `npm ci`, build `npm run build`; manter o comando de inicialização padrão da plataforma.
- Para demonstrar sem serviços externos, usar `DATA_SOURCE=local`, sem credenciais Supabase. O snapshot acompanha a solução.
- O modo local na Vercel mantém as atividades no navegador de cada visitante; não cria compartilhamento entre usuários.
- Se optar pelo Supabase, seguir o README técnico. A chave de serviço é exclusiva do servidor e não usa prefixo `NEXT_PUBLIC_`.
- Após publicar, conferir carregamento, persistência na mesma origem e atualizar o README com a URL realmente verificada.

## Checklist final

- [x] Identificação e LinkedIn informados pelo candidato.
- [x] README baseado no template oficial.
- [x] Código, dados públicos, documentação, narrativa e capturas incluídos.
- [ ] Reexecutar as verificações se houver mudanças após o empacotamento.
- [ ] Criar fork/branch e revisar o diff restrito à pasta da submissão.
- [ ] Abrir o PR e registrar URL e data reais.
- [ ] Opcional: publicar e adicionar URL verificada.
