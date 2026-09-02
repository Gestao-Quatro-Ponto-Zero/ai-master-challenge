# Arquitetura e contratos

## Visão geral

O G4 Focus é uma aplicação read-only, orientada a artefatos. O processamento acontece antes da inicialização do servidor; a camada web serve os mesmos JSONs para a interface e para a API.

```text
CSV brutos (imutáveis)
        |
        v
pipeline Python stdlib
  - validação
  - normalização
  - scoring e explicações
        |
        +--> data/normalized/
        |
        +--> generated/
               |-- dashboard.json
               |-- opportunities.json
               |-- model-report.json
               `-- data-quality.json
                         |
                         v
                 Next.js / API read-only
                         |
              navegador, gestor e vendedor
```

Esse desenho foi escolhido por quatro motivos: reproduzibilidade, deploy sem banco de dados, uma única fonte de verdade entre dashboard e API e isolamento entre transformação de dados e apresentação.

## Componentes

### `analytics/`

Pipeline determinístico em Python 3.11+ e biblioteca padrão. Ele recebe caminhos por argumento, não depende do diretório pessoal de quem executa e falha cedo em violações de schema.

Comando canônico:

```bash
python3 analytics/pipeline.py \
  --data-dir data/raw \
  --normalized-dir data/normalized \
  --output-dir generated
```

### `generated/`

Contrato de integração entre pipeline e web. Os arquivos são regeneráveis a partir de `data/raw/`; portanto, mudanças de scoring não exigem alterar a interface desde que o contrato permaneça compatível.

| Artefato | Responsabilidade |
|---|---|
| `opportunities.json` | Linhas priorizadas, componentes do score, fila, motivos, confiança e flags. |
| `dashboard.json` | KPIs e agregações necessários para a visão executiva. |
| `model-report.json` | Versão do método, parâmetros, distribuições e evidências de validação. |
| `data-quality.json` | Contagens, ausências, integridade de chaves e alertas de qualidade. |

### `web/`

Aplicação Next.js com renderização do dashboard e rotas JSON. A interface não recalcula scores; ela explica e filtra o resultado do pipeline.

Endpoints esperados:

| Método | Rota | Uso |
|---|---|---|
| `GET` | `/api/health` | Saúde do serviço e disponibilidade dos artefatos. |
| `GET` | `/api/v1/dashboard` | KPIs e agregações da visão executiva. |
| `GET` | `/api/v1/opportunities` | Carteira priorizada e filtros. |
| `GET` | `/api/v1/opportunities/{id}` | Explicação de uma oportunidade. |
| `GET` | `/api/v1/model-report` | Metodologia e diagnósticos gerados. |

O contrato efetivamente implementado e seus parâmetros devem ser conferidos no README de `solution/` e nos testes da aplicação.

## Fluxo de uma decisão

1. O vendedor abre a carteira e seleciona seu nome ou território.
2. A interface mostra a fila recomendada, score, valor e sinais principais.
3. O vendedor abre o detalhe para entender contribuições e alertas.
4. A decisão permanece humana: agir agora, acelerar, nutrir, resgatar/desqualificar ou qualificar.
5. Em uma evolução produtiva, a ação e o feedback voltariam ao CRM para medir utilidade e recalibrar o sistema.

## Empacotamento

O Dockerfile usa três responsabilidades isoladas:

1. **analytics:** roda o pipeline sobre os dados reais;
2. **web builder:** instala dependências e gera o build standalone;
3. **runner:** copia apenas os artefatos necessários e executa como usuário não-root.

No Railway, o diretório raiz do serviço é `/submissions/lucas-pardinho/solution`. O servidor respeita `PORT`, escuta em `0.0.0.0` e expõe `/api/health`.

## Limites operacionais e evolução

Esta versão deliberadamente não inclui autenticação, escrita em CRM, scheduler ou banco. Para produção, o próximo desenho deveria incluir:

- ingestão incremental e snapshots versionados;
- SSO e autorização por vendedor/manager;
- storage com trilha de auditoria;
- monitoramento de qualidade, drift, calibração e impacto por grupo;
- feedback da ação recomendada;
- rollout controlado e fallback para a fila convencional do CRM.
