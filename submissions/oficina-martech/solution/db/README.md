# Banco de dados — Foco (Lead Scorer)

Camada de persistência **portável e reproduzível**: SQLite (zero-install, roda em qualquer máquina com Python) + migrations versionadas + seed dos dados reais. O avaliador instala e valida 100% em **3 comandos**.

## Instalar do zero

```bash
make setup        # = install + migrate + seed
# ou manualmente:
pip install -r requirements.txt
python -m db.migrate      # cria o schema (foco.db)
python -m db.seed         # carrega os 4 CSVs reais + valida
```

Saída esperada do seed:
```
✓ products            7
✓ accounts           85
✓ sales_teams        35
✓ sales_pipeline   8800
→ saúde: total=8800 abertos=2089 sem_conta=1425 ciclo_won=52d
Banco pronto para uso. ✅
```

## Estrutura

```
db/
├── migrations/
│   ├── 0001_init.sql     # tabelas, PKs/FKs, índices, CHECKs
│   └── 0002_views.sql    # views auditáveis (open deals, win-rate, saúde)
├── migrate.py            # runner: aplica migrations em ordem, 1x cada (idempotente)
├── seed.py               # carrega CSVs, aplica fix GTXPro→GTX Pro, valida counts
└── foco.db               # gerado (não versionado)
```

## Decisões

- **SQLite, não Postgres:** "instalar em qualquer lugar" = sem servidor. SQLite é stdlib do Python — o avaliador não precisa de Docker, container ou credencial. O mesmo SQL é ~portável para Postgres se um dia precisar escalar (ver roadmap no `../../docs/PLANO-DO-PROJETO.md`).
- **Migrations versionadas + `schema_migrations`:** cada `.sql` roda uma única vez, rastreado. `--reset` recria do zero. Profissional e auditável.
- **Seed idempotente:** limpa e recarrega — rodar 2x dá o mesmo estado. Aplica a limpeza da EDA (GTXPro, vazios→NULL) na carga, então o banco já nasce correto.
- **Views auditáveis:** a lógica de negócio (deals abertos, win-rate por vendedor, saúde) fica legível em SQL, para o avaliador conferir os números direto no banco. O scoring final (smoothing/pesos) é em Python, testado.

## Conferir no banco (opcional)
```bash
sqlite3 db/foco.db "SELECT * FROM v_pipeline_health;"
sqlite3 db/foco.db "SELECT * FROM v_agent_winrate ORDER BY win_rate DESC LIMIT 5;"
```
