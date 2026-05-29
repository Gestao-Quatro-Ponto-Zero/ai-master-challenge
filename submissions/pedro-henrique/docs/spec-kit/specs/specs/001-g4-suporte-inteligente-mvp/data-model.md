# Data Model - G4 Suporte Inteligente (MVP)

## Entity: Profile
- **Description**: Identidade do usuário autenticado e seu papel de acesso.
- **Fields**:
  - `id` (uuid, obrigatório)
  - `email` (texto, obrigatório)
  - `full_name` (texto, opcional)
  - `role` (`admin` | `customer`, obrigatório)
  - `created_at` (timestamp)
- **Relationships**:
  - 1:N com `Ticket` (um customer abre vários tickets)
  - 1:N com `DeflectionEvent`
- **Validation Rules**:
  - `role` deve respeitar domínio permitido
  - `email` não pode ser vazio

## Entity: KnowledgeBaseEntry
- **Description**: Registro histórico utilizado como fonte para busca semântica.
- **Fields**:
  - `id` (bigint)
  - `source_ticket_id` (texto)
  - `description` (texto, obrigatório)
  - `resolution` (texto)
  - `category` (texto)
  - `priority` (texto)
  - `channel` (texto)
  - `embedding` (vetor 1536)
  - `created_at` (timestamp)
- **Relationships**:
  - Referenciado em consultas de similaridade para sugestão
- **Validation Rules**:
  - `description` obrigatório
  - `embedding` presente para entradas indexadas

## Entity: Ticket
- **Description**: Chamado operacional criado quando deflexão não resolve.
- **Fields**:
  - `id` (bigint)
  - `customer_id` (uuid, obrigatório)
  - `source` (`text` | `audio`, obrigatório)
  - `audio_path` (texto, opcional)
  - `raw_text` (texto, obrigatório)
  - `category` (texto)
  - `priority` (`low` | `medium` | `high` | `critical`)
  - `status` (`open` | `pending` | `resolved` | `deflected`)
  - `rag_suggestion` (texto)
  - `rag_confidence` (numérico 0..1)
  - `resolved_by_ai` (boolean)
  - `created_at` (timestamp)
  - `resolved_at` (timestamp, opcional)
- **Relationships**:
  - N:1 com `Profile`
- **Validation Rules**:
  - `raw_text` obrigatório
  - `status` inicia como `open` quando houver criação de ticket
  - `audio_path` obrigatório quando `source=audio`

## Entity: DeflectionEvent
- **Description**: Registro de resolução sem criação de ticket.
- **Fields**:
  - `id` (bigint)
  - `customer_id` (uuid)
  - `raw_text` (texto)
  - `top_matches` (json)
  - `created_at` (timestamp)
- **Relationships**:
  - N:1 com `Profile`
- **Validation Rules**:
  - evento só deve existir quando usuário confirma "Resolveu"

## Entity: InsightSnapshot
- **Description**: Estrutura agregada para o dashboard executivo.
- **Fields**:
  - `generated_at` (timestamp)
  - `flow_bottlenecks` (objeto/lista)
  - `csat_drivers` (objeto/lista)
  - `waste_estimation` (objeto/lista)
  - `automation_patterns` (objeto/lista)
  - `deflection_metrics` (objeto/lista)
- **Relationships**:
  - Consumido por telas admin e API de insights
- **Validation Rules**:
  - arquivo deve ser válido em JSON
  - blocos mínimos obrigatórios para renderização do dashboard

## State Transitions: Ticket
- `open` -> `pending` (triagem inicial)
- `pending` -> `resolved` (resolução concluída)
- `open` -> `resolved` (resolução direta)
- `open|pending` -> `deflected` (uso excepcional quando ticket foi aberto e reclassificado como resolvido por autoatendimento)
