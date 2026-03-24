# Hermes - Sistema de Chamados de TI com IA

  Sistema inteligente de gestão de chamados de suporte de TI, com classificação automática por IA, sugestões de resolução e dashboard analítico em tempo real.

  ## Tecnologias

  - **Frontend:** React 18, TypeScript, Tailwind CSS, Shadcn UI, Recharts
  - **Backend:** Node.js, Express 5, TypeScript
  - **Banco de Dados:** PostgreSQL com Drizzle ORM
  - **IA:** OpenAI (GPT) para classificação, priorização e sugestões de resposta

  ## Pré-requisitos

  - [Node.js](https://nodejs.org/) v20 ou superior
  - [PostgreSQL](https://www.postgresql.org/) v14 ou superior
  - Chave de API da [OpenAI](https://platform.openai.com/)

  ## Instalação

  ### 1. Clone o repositório

  ```bash
  git clone https://github.com/renygrando/ai-master-challenge.git
  cd ai-master-challenge/submissions/renygrando/hermes-code
  ```

  ### 2. Instale as dependências

  ```bash
  npm install
  ```

  ### 3. Configure as variáveis de ambiente

  Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

  ```env
  DATABASE_URL=postgresql://usuario:senha@localhost:5432/hermes
  OPENAI_API_KEY=sk-sua-chave-aqui
  SESSION_SECRET=uma-chave-secreta-qualquer
  ```

  ### 4. Configure o banco de dados

  Execute as migrações para criar as tabelas:

  ```bash
  npm run db:push
  ```

  ### 5. Inicie o servidor

  **Modo desenvolvimento:**

  ```bash
  npm run dev
  ```

  **Modo produção:**

  ```bash
  npm run build
  npm start
  ```

  O servidor estará disponível em `http://localhost:5000`.

  ## Credenciais padrão

  Ao iniciar pela primeira vez, o sistema cria automaticamente um usuário administrador:

  - **Email:** admin@hermes.io
  - **Senha:** hermes123

  > Recomenda-se alterar a senha após o primeiro login.

  ## Funcionalidades

  - **Abertura de chamados** com classificação automática por IA (categoria, prioridade, equipe)
  - **Dashboard** com métricas em tempo real (SLA, volume, tempo de resolução)
  - **Sugestões de resposta** geradas por IA com base no histórico
  - **Base de conhecimento** com artigos de autoatendimento
  - **Painel administrativo** para gestão de chamados e equipes
  - **Analytics** com gráficos e indicadores de desempenho
  - **Autenticação** com controle de acesso por perfil (admin/usuário)

  ## Estrutura do Projeto

  ```
  ├── client/                  # Frontend React
  │   ├── src/
  │   │   ├── components/      # Componentes reutilizáveis (Shadcn UI)
  │   │   ├── context/         # Contextos (autenticação)
  │   │   ├── hooks/           # Hooks customizados
  │   │   ├── lib/             # Utilitários e configuração
  │   │   └── pages/           # Páginas da aplicação
  │   └── index.html
  ├── server/                  # Backend Express
  │   ├── db.ts                # Conexão com PostgreSQL
  │   ├── index.ts             # Entry point do servidor
  │   ├── routes.ts            # Rotas da API
  │   ├── storage.ts           # Camada de acesso a dados
  │   └── vite.ts              # Configuração do Vite (dev)
  ├── shared/                  # Código compartilhado
  │   ├── schema.ts            # Schema do banco (Drizzle ORM)
  │   └── routes.ts            # Definição de rotas tipadas
  ├── package.json
  ├── tsconfig.json
  ├── vite.config.ts
  ├── drizzle.config.ts
  └── tailwind.config.ts
  ```

  ## Scripts disponíveis

  | Comando | Descrição |
  |---------|-----------|
  | `npm run dev` | Inicia o servidor em modo desenvolvimento |
  | `npm run build` | Compila o projeto para produção |
  | `npm start` | Inicia o servidor em modo produção |
  | `npm run check` | Verifica tipos TypeScript |
  | `npm run db:push` | Sincroniza o schema com o banco de dados |

  ## Licença

  MIT
  