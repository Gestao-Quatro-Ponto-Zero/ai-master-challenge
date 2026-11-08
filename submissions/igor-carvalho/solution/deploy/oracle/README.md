# Deploy na Oracle Cloud (Always Free)

Uma VM Ampere A1 (ARM) roda tudo com Docker Compose:
- `api`: backend FastAPI (treina no build; cron diário às 02:00; SQLite em volume persistente)
- `web`: Caddy servindo o frontend (modo API real) e repassando `/api/*` para a API, com HTTPS automático via `<ip-com-traços>.sslip.io`

## 1. Publicar estes arquivos
Faça commit e push de `deploy/oracle/` no branch `submission/igor-carvalho` (a VM clona de lá).

## 2. Criar a VM (Console → Compute → Instances → Create instance)
- Image: **Canonical Ubuntu 24.04**
- Shape: **Ampere → VM.Standard.A1.Flex**, 2 OCPU / 12 GB (Always Free)
- Networking: VCN e sub-rede **pública** novas; **Assign a public IPv4 address** marcado
- SSH keys: gere e **baixe a chave privada**
- Advanced options → Management → **Cloud-init script**: cole o conteúdo de `cloud-init.sh`

"Out of capacity"? Tente outro Availability Domain, ou 1 OCPU / 6 GB.

## 3. Abrir as portas na rede da Oracle
Networking → Virtual Cloud Networks → (sua VCN) → Subnet pública → Security List padrão → **Add Ingress Rules**:
- Source `0.0.0.0/0`, TCP, porta **80**
- Source `0.0.0.0/0`, TCP, porta **443**

## 4. Acessar
Leva ~10–15 min no primeiro boot (Docker + build + treino). Depois:
`https://<IP-com-traços>.sslip.io`  (ex.: IP 140.238.1.2 → https://140-238-1-2.sslip.io)

Acompanhar / diagnosticar:
    ssh -i chave.key ubuntu@<IP> 'sudo tail -f /var/log/g4-setup.log'
    ssh -i chave.key ubuntu@<IP> 'cd /opt/g4/submissions/igor-carvalho/solution/deploy/oracle && sudo docker compose -f docker-compose.prod.yml ps'

## Atualizar após novos commits
    ssh -i chave.key ubuntu@<IP> 'sudo bash /opt/g4/submissions/igor-carvalho/solution/deploy/oracle/update.sh'
