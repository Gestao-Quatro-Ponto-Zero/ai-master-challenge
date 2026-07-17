# Contrato de serving do dashboard

## Fonte

O dashboard lê `data/processed/posts_analytical.csv`, validado pelo contrato analítico. Não acessa raw, nomes, URLs ou texto de comentários.

## Campos consumidos

- filtros: plataforma, tipo, categoria, creator size e patrocínio;
- dimensões adicionais: faixa etária e localização agregadas;
- métricas: `engagement_rate_views`, `views` e contagem de posts;
- `is_sponsored` apenas para proporção/contraste descritivo.

## Regras

- filtros vazios significam “todos”;
- `n` é sempre exibido;
- conjunto vazio mostra estado de dados insuficientes;
- eixo de engagement usa faixa fixa 19%–21% para não dramatizar diferenças mínimas;
- nenhuma métrica nova pode ser calculada fora do registry;
- dashboard não estima causalidade ou ROI.
