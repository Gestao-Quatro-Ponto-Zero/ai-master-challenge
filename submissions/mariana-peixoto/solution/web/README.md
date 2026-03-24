# Antigravity Kit

> Templates de Agentes de IA com Skills, Agentes e Workflows

<div  align="center">
    <a href="https://unikorn.vn/p/antigravity-kit?ref=unikorn" target="_blank"><img src="https://unikorn.vn/api/widgets/badge/antigravity-kit?theme=dark" alt="Antigravity Kit - Destaque em Unikorn.vn" style="width: 210px; height: 54px;" width="210" height="54" /></a>
    <a href="https://unikorn.vn/p/antigravity-kit?ref=unikorn" target="_blank"><img src="https://unikorn.vn/api/widgets/badge/antigravity-kit/rank?theme=dark&type=daily" alt="Antigravity Kit - Diário" style="width: 250px; height: 64px;" width="250" height="64" /></a>
    <a href="https://launch.j2team.dev/products/antigravity-kit" target="_blank"><img src="https://launch.j2team.dev/badge/antigravity-kit/dark" alt="Antigravity Kit on J2TEAM Launch" width="250" height="54" /></a>
</div>

## Instalação Rápida

```bash
npx @vudovn/ag-kit init
```

Ou instalar globalmente:

```bash
npm install -g @vudovn/ag-kit
ag-kit init
```

Isso instala a pasta `.agent` contendo todos os templates em seu projeto.

## Uso

### Usando Agentes

**Não é necessário mencionar os agentes explicitamente!** O sistema detecta e aplica automaticamente os especialistas corretos:

```
Você: "Adicionar autenticação JWT"
IA: 🤖 Aplicando @security-auditor + @backend-specialist...

Você: "Corrigir o botão de modo escuro"
IA: 🤖 Usando @frontend-specialist...

Você: "Login retorna erro 500"
IA: 🤖 Usando @debugger para análise sistemática...
```

**Como funciona:**

- Analisa sua solicitação silenciosamente
- Detecta domínios automaticamente (frontend, backend, segurança, etc.)
- Seleciona os melhores especialistas
- Informa qual expertise está sendo aplicada
- Você recebe respostas de nível especialista sem precisar conhecer a arquitetura do sistema

**Benefícios:**

- ✅ Curva de aprendizado zero - apenas descreva o que você precisa
- ✅ Sempre obtenha respostas de especialistas
- ✅ Transparente - mostra qual agente está sendo usado
- ✅ Ainda pode sobrescrever mencionando o agente explicitamente

### Usando Workflows

Invoque workflows com comandos de barra (/):

| Comando          | Descrição                             |
| ---------------- | ------------------------------------- |
| `/brainstorm`    | Explore opções antes da implementação |
| `/create`        | Crie novos recursos ou apps           |
| `/debug`         | Depuração sistemática                 |
| `/deploy`        | Implantar aplicação                   |
| `/enhance`       | Melhorar código existente             |
| `/orchestrate`   | Coordenação multi-agente              |
| `/plan`          | Criar detalhamento de tarefas         |
| `/preview`       | Visualizar alterações localmente      |
| `/status`        | Verificar status do projeto           |
| `/test`          | Gerar e executar testes               |
| `/ui-ux-pro-max` | Design com 50 estilos                 |

Exemplo:

```
/brainstorm sistema de autenticação
/create landing page com seção hero
/debug por que o login falha
```

### Usando Skills

As skills foram carregadas automaticamente com base no contexto da tarefa. A IA lê as descrições das skills e aplica o conhecimento relevante.

## Ferramenta CLI

| Comando         | Descrição                                 |
| --------------- | ----------------------------------------- |
| `ag-kit init`   | Instala a pasta `.agent` em seu projeto |
| `ag-kit update` | Atualiza para a versão mais recente       |
| `ag-kit status` | Verifica o status da instalação           |

### Opções

```bash
ag-kit init --force        # Sobrescrever pasta .agent existente
ag-kit init --path ./myapp # Instalar em diretório específico
ag-kit init --branch dev   # Usar branch específica
ag-kit init --quiet        # Suprimir saída (para CI/CD)
ag-kit init --dry-run      # Prévia das ações sem executar
```

## Documentação

- **[Exemplo de Web App](https://antigravity-kit.vercel.app//docs/guide/examples/web-app)** - Guia passo a passo para criar uma aplicação web
- **[Docs Online](https://antigravity-kit.vercel.app//docs)** - Navegue por toda a documentação online

## Licença

MIT © Vudovn
