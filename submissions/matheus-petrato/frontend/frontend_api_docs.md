# Documentação da API e Fluxo de Onboarding — Datapus

Este documento serve como referência definitiva para a integração do Frontend com o Backend do Datapus. Ele detalha todos os endpoints disponíveis, seus contratos (payloads e respostas) e descreve o fluxo ideal de experiência do usuário (UX) para o Onboarding.

---

## 🚀 O Fluxo "Perfeito" de Onboarding (UX B2B)

Para que o cliente B2B alcance o momento "Aha!" o mais rápido possível e justifique o Product-Market Fit, o frontend deve guiar o usuário em **3 passos mágicos** logo após o registro:

### Passo 1: O Engate (Conexão)
*O usuário acabou de criar a conta, mas o chat está bloqueado/invisível.*
- **Tela:** Limpa, focada em um único componente central. O título deve ser provocativo: *"Onde estão os seus dados?"*
- **Componentes:**
  - Card para selecionar o tipo de banco (Ex: Supabase, Postgres).
  - Um campo de input grande para colar a `Connection URI`.
  - Um campo opcional para um "Apelido" (Ex: "Loja Principal").
- **Ação:** O usuário clica em "Conectar". O frontend dispara a chamada para `POST /api/v1/datasources`.

### Passo 2: O Escaneamento (A Mágica da IA)
*O banco conectou. Agora o Datapus assume o protagonismo.*
- **Tela:** O botão de "Conectar" se transforma num *loader state* com micro-animações. Aparece um texto dinâmico estilo hacker: *"Iniciando tentáculos... Lendo tabelas... Pedindo pro Mercury analisar contextos de negócio..."*
- **Ação:** Em background (sem ação do usuário), o frontend faz uma chamada imediatamente para `POST /api/v1/datasources/:id/scan`.
- *Wait time esperado:* ~2 a 4 segundos.

### Passo 3: A Curadoria (Treinando o Polvo)
*O backend retorna o payload do `/scan` com o rascunho de como ele entendeu a empresa.*
- **Tela:** "Ajude o Datapus a ter 100% de precisão". 
- **O que exibir:** O frontend pega o objeto `.draft` retornado pela API e monta um formulário onde as chaves são lidas do JSON.
  - **Exemplo de UI:** 
    - 🗄️ Tabela: `users`
      - *Sugestão da IA:* "Tabela contendo o cadastro de clientes." [Input Field com esse valor pré-preenchido para ele alterar se quiser].
- **Ação:** O usuário clica em "Concluir Onboarding". O frontend dispara uma chamada silenciosa (se precisar atualizar via PUT no futuro, ou guarda localmente), e em seguida... liberta o usuário na tela de Chat!

---

## 📡 Contratos da API (REST & WS)

Todas as chamadas à API (exceto `/auth`) exigem o token JWT no cabeçalho:
`Authorization: Bearer <seu_token>`

### 1. Autenticação

#### 1.1 Registrar Usuário
- **URL:** `POST /api/auth/register`
- **Payload:**
  ```json
  {
    "name": "Matheus Teodoro",
    "org_name": "Datapus Inc",
    "email": "matheus@empresa.com",
    "password": "senha_segura123"
  }
  ```
- **Resposta (201 Created):**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "uuid-do-usuario",
      "org_id": "uuid-da-organizacao",
      "name": "Matheus Teodoro",
      "email": "matheus@empresa.com"
    }
  }
  ```

#### 1.2 Login de Usuário
- **URL:** `POST /api/auth/login`
- **Payload:**
  ```json
  {
    "email": "matheus@empresa.com",
    "password": "senha_segura123"
  }
  ```
- **Resposta (200 OK):** *(Mesmo formato do Register)*

---

### 2. Gestão de Fontes de Dados (Data Sources)

#### 2.1 Criar Conexão (Início do Onboarding)
- **URL:** `POST /api/v1/datasources`
- **Payload:**
  - *Nota:* O campo `semantic_schema` pode ser enviado como uma string de JSON vazio `{}` na etapa 1.
  ```json
  {
    "name": "Supabase Vendas",
    "type": "supabase",
    "config": "{\"connection_uri\": \"postgresql://postgres:senha@db.exemplo.co:5432/postgres\"}",
    "semantic_schema": "{}"
  }
  ```
- **Resposta (201 Created):**
  ```json
  {
    "id": "uuid-do-datasource",
    "org_id": "uuid-da-organizacao",
    "name": "Supabase Vendas",
    "type": "supabase",
    "config": "{\"connection_uri\": \"...\"}",
    "semantic_schema": "{}"
  }
  ```

#### 2.2 Escaneamento Inteligente (A Mágica)
- **URL:** `POST /api/v1/datasources/:id/scan`
  - *(Onde `:id` é a string retornada na rota de criação).*
- **Payload:** *(Não precisa de Body. O Backend usa o banco já cadastrado e a config interna).*
- **Resposta (200 OK):**
  - **`raw`**: Lista de tabelas e colunas fiéis ao banco. Use para montar selects ou sidebars.
  - **`draft`**: É o objeto mastigado pela IA. Use ele para montar o formulário de "treinamento" (Passo 3 do Onboarding).
  ```json
  {
    "raw": [
      {
        "table_name": "vendas",
        "columns": ["id", "produto_id", "valor"]
      }
    ],
    "draft": {
      "tables": {
        "vendas": "Registros históricos de todas as transações da loja."
      },
      "columns": {
        "vendas.valor": "Faturamento bruto expresso na moeda local do sistema."
      }
    }
  }
  ```

#### 2.3 Listar Conexões Ativas
- **URL:** `GET /api/v1/datasources`
- **Resposta (200 OK):**
  ```json
  [
    {
      "id": "uuid-do-datasource",
      "org_id": "uuid-da-organizacao",
      "name": "Supabase Vendas",
      ...
    }
  ]
  ```

---

### 3. A Central de Chat (WebSocket via Streaming)

O Chat do Datapus não usa chamadas REST POST comuns. Para conseguir a sensação de "Digitação da IA em tempo real", usamos WebSockets nativos.

#### 3.1 Conectar
- **URL:** `ws://localhost:8080/ws/chat` *(ajuste o host em prod)*
- **Autenticação no WS:** Você deve enviar o JWT na query da requisição, já que browsers não suportam header de auth nativamente em WS em todas as situações:
  - `ws://localhost:8080/ws/chat?token=eyJ...`

#### 3.2 Cliente Envia Mensagem (JSON IN)
Quando o usuário clica em Enviar (Texto) ou Grava o Áudio, você emite este JSON via socket:
- **Exemplo de Texto:**
  ```json
  {
    "content": "Mostre as vendas do mês",
    "session_id": "seu-user-id",
    "type": "text"
  }
  ```
- **Exemplo de Áudio (Base64):**
  ```json
  {
    "audio_data": "data:audio/webm;base64,GkXf...",
    "session_id": "seu-user-id",
    "type": "audio"
  }
  ```

#### 3.3 Backend Responde (JSON OUT / Streaming)
Você escutará os eventos (`onMessage`). O backend vai vomitar pedaços de texto conforme a IA vai pensando e escrevendo. É responsabilidade do Frontend ir **somando (concatenando)** esses pedaços na bolha do chat.
- **Formato (Chunking Mode):**
  ```json
  {
    "channel": "web",
    "chat_id": "seu-user-id",
    "content": "Neste mês ti",
    "stream_state": "chunk"
  }
  ```
  *(...milissegundos depois...)*
  ```json
  {
    "channel": "web",
    "chat_id": "seu-user-id",
    "content": "vemos um to",
    "stream_state": "chunk"
  }
  ```
  *(Quando a IA finalizar a resposta completamente):*
  ```json
  {
    "channel": "web",
    "chat_id": "seu-user-id",
    "content": "",
    "stream_state": "done"
  }
  ```
*O evento `done` é o seu sinal para liberar o input do usuário e parar a animação de "digitando..."*.
