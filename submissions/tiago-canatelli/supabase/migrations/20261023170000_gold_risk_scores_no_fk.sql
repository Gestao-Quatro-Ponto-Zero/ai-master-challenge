-- gold.risk_scores é derivado e reconstruído depois do silver; a FK para silver.accounts impedia
-- o TRUNCATE do silver.refresh() num reprocessamento ("cannot truncate a table referenced in a
-- foreign key constraint"). Encontrado ao testar a ingestão disparada pelo painel.
alter table gold.risk_scores drop constraint if exists risk_scores_account_id_fkey;
