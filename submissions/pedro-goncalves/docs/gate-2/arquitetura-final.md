# Arquitetura final: medir antes de automatizar

## Decisão

O sistema é um **copiloto de triagem em shadow mode**, não um agente autônomo. Ele demonstra classificação, confiança calibrada, abstenção e governança sem enviar respostas ou alterar sistemas externos. Aceita uma mensagem ou uma fila CSV e exporta apenas identificadores e resultados da triagem, sem copiar o texto.

```mermaid
flowchart LR
    A[Ticket recebido] --> B[Máscara local de PII]
    B --> R{Sinal de cuidado com o cliente?}
    R -->|Sim| H[Fila humana]
    R -->|Não| C[Classificador]
    C --> M[Consulta lições aprovadas]
    M --> D{Kill switch ativo?}
    D -->|Sim| H[Fila humana]
    D -->|Não| E{Categoria sensível?}
    E -->|Sim| H
    E -->|Não| Q{Erro anterior parecido?}
    Q -->|Sim| H
    Q -->|Não| F{Confiança acima do threshold?}
    F -->|Não| H
    F -->|Sim| G{Modo operacional}
    G -->|Shadow| I[Registra recomendação]
    G -->|Assistido| J[Humano aprova ou corrige]
    G -->|Simulação| K[Simula roteamento]
    I --> L[Log sem texto bruto]
    J --> L
    K --> L
    H --> L
```

## Componentes

| Componente | Função | Controle |
|---|---|---|
| `privacy.py` | Mascara padrões de PII | Executa localmente antes da inferência |
| `inference.py` | Retorna categoria e probabilidades | Modelo versionado e teste final documentado |
| `customer_care.py` | Identifica sinais explícitos de reclamação e possível dano | Qualquer sinal força decisão humana |
| `batch.py` | Processa DataFrames sem guardar texto bruto | O contexto escolhido, não o nome da coluna, define a fila |
| `policy.py` | Aplica gates de risco | Cliente, kill switch, human-only, memória e abstenção |
| `audit.py` | Gera registro rastreável | Sem texto e sem fingerprint do texto |
| `memory.py` | Registra correções e recupera lições aprovadas | SQLite local, sem texto bruto e com aprovação humana |
| `roi.py` | Simula capacidade e valor | Todas as premissas são entradas explícitas |
| `app.py` | Piloto de uso cotidiano | Apenas Triagem, Aprendizado e Ajuda |
| `cross_dataset_audit.py` | Aplica o modelo do Dataset 2 em todas as mensagens do Dataset 1 | Mede concentração e confiança sem alegar acurácia |

## Fronteira humano-IA

### IA pode

- mascarar padrões conhecidos de PII;
- identificar sinais explícitos de cuidado prioritário com o cliente;
- sugerir uma categoria;
- mostrar confiança e alternativas;
- abster-se;
- registrar a decisão e o estado da política;
- registrar correções e consultar lições aprovadas;
- mostrar o motivo do encaminhamento humano.

### IA não pode

- determinar prioridade sem dados adequados;
- enviar resposta;
- conceder reembolso;
- alterar acesso ou permissão;
- tratar casos de RH autonomamente;
- converter TTR em horas de trabalho;
- declarar ROI sem touch time e custos medidos;
- aprovar uma lição ou retreinar o modelo silenciosamente.

## Estado do protótipo

O protótipo é local e funcional. Ele contém apenas o fluxo cotidiano de triagem, aprendizado e
ajuda. Diagnóstico, evidências, matriz de decisão, plano e cenários permanecem nos documentos da
entrega. Nenhuma integração externa é executada.

## Caminho para produção

1. Instrumentar o fluxo real.
2. Definir taxonomia e risco com a operação.
3. Rotular amostra do domínio alvo.
4. Rodar shadow mode por janela suficiente.
5. Avaliar erro crítico, override, reabertura, touch time e CSAT.
6. Liberar canário apenas para ações reversíveis.
7. Manter revisão amostral, auditoria, rollback e kill switch.
