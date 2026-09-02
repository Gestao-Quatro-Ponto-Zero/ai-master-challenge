# Proveniência e integridade dos dados

## Origem

O challenge referencia o dataset **CRM Sales Predictive Analytics**, publicado no Kaggle, e declara licença CC0. Os arquivos usados nesta submissão vieram do ZIP fornecido para o teste, sem download automatizado durante o build.

- Arquivo-fonte: `Predictive Analytics CRM Sales.zip`
- SHA-256 do ZIP: `74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c`
- Local no projeto: `solution/data/raw/`
- Regra: `raw/` é imutável; normalizações são gravadas separadamente em `data/normalized/`

O caminho original da máquina não é parte da proveniência versionada porque é específico do ambiente local.

## Manifesto de arquivos

As contagens abaixo excluem o cabeçalho.

| Arquivo | Registros | SHA-256 |
|---|---:|---|
| `accounts.csv` | 85 | `e5242324768a563fc632cddfed49a29acbbf2892b8a3c6453cc9650de9ae0358` |
| `metadata.csv` | 21 | `22b34e498d07e3d7f322afdbf81d70a5dc0a389792944e50ca2af86a3597f0af` |
| `products.csv` | 7 | `7c1c8cbbdb6d4c286902e1985eeb529a36366d6a43f43cd4a93c4b1da2a6eb84` |
| `sales_pipeline.csv` | 8.800 | `825ce8f6c32d4009548b468df3173d55a46fd73f2531f532c5459371dc52adf2` |
| `sales_teams.csv` | 35 | `aeff1272ebe196f5a27e3fc0578aa27abf48ed9ae461aa344fb95990e5ad8bd1` |

Para revalidar o manifesto no macOS ou Linux:

```bash
cd submissions/lucas-pardinho/solution
shasum -a 256 data/raw/*.csv
wc -l data/raw/*.csv
```

## Transformações controladas

O pipeline precisa ser determinístico e preserva os arquivos brutos. As principais regras são:

1. Remover espaços periféricos e interpretar strings vazias como ausência, sem inventar dados.
2. Converter datas e números com validação explícita; registros inválidos devem aparecer no relatório de qualidade.
3. Normalizar o alias de produto `GTXPro` para `GTX Pro` antes do relacionamento com o catálogo.
4. Preservar oportunidades sem conta e diminuir sua confiança, em vez de excluí-las.
5. Derivar a data de snapshot de forma reproduzível e registrá-la no relatório. Em produção, essa data precisa ser recebida explicitamente.
6. Nunca usar `close_date`, `close_value` ou `deal_stage` final como feature de uma oportunidade que estaria aberta no instante avaliado.

## Verificações de qualidade esperadas

- unicidade de `opportunity_id`;
- domínio de `deal_stage`;
- integridade dos relacionamentos com produto e equipe depois da normalização;
- contagem e concentração de campos ausentes;
- coerência cronológica entre engajamento e fechamento;
- valores não negativos;
- hashes e contagens do input;
- determinismo dos artefatos gerados.

Os resultados da execução ficam em `solution/generated/data-quality.json`. Este documento descreve o contrato; o arquivo gerado é a evidência da execução.
