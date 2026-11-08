#!/bin/bash
# Cole este script em "Cloud-init script" ao criar a VM (Ubuntu 24.04; funciona na Micro AMD de 1 GB ou na Ampere A1).
# Ele instala o Docker, libera 80/443, clona o repositório e sobe a aplicação.
# Log: /var/log/g4-setup.log   (acompanhe com: sudo tail -f /var/log/g4-setup.log)
set -euxo pipefail
exec > >(tee -a /var/log/g4-setup.log) 2>&1

REPO=https://github.com/igor822/ai-master-challenge.git
BRANCH=submission/igor-carvalho
APP_DIR=/opt/g4
DEPLOY_DIR=$APP_DIR/submissions/igor-carvalho/solution/deploy/oracle

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git openssl iptables-persistent

# Swap de 4 GB (a VM Micro tem só 1 GB de RAM; o build e o treino precisam de folga)
if [ ! -f /swapfile ]; then
  fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl -w vm.swappiness=60
fi

# Docker (script oficial)
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu || true

# Firewall do Ubuntu da Oracle: libera 80/443 antes da regra REJECT padrão
for p in 80 443; do
  iptables -C INPUT -p tcp --dport $p -j ACCEPT 2>/dev/null || iptables -I INPUT 5 -p tcp --dport $p -m state --state NEW -j ACCEPT
done
iptables -C INPUT -p udp --dport 443 -j ACCEPT 2>/dev/null || iptables -I INPUT 5 -p udp --dport 443 -j ACCEPT
netfilter-persistent save

# Código
# Espera o deploy/oracle existir no GitHub (tenta de novo a cada 60 s)
until [ -d $DEPLOY_DIR ]; do
  rm -rf $APP_DIR
  git clone --depth 1 --branch $BRANCH $REPO $APP_DIR || true
  [ -d $DEPLOY_DIR ] || { echo 'deploy/oracle ainda não está no GitHub; tentando de novo em 60s'; sleep 60; }
done
chown -R ubuntu:ubuntu $APP_DIR

# Configuração (.env gerado uma única vez)
cd $DEPLOY_DIR
if [ ! -f .env ]; then
  IP=$(curl -fsS https://api.ipify.org || curl -fsS https://ifconfig.me)
  cat > .env <<ENV
SITE_ADDRESS=${IP//./-}.sslip.io
G4_JWT_SECRET=$(openssl rand -hex 32)
G4_SHOW_PROBABILITY=true
G4_RATE_LIMIT_PER_MINUTE=120
ENV
  chmod 600 .env
fi

# Builds um de cada vez (pouca memória), depois sobe
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml build web
docker compose -f docker-compose.prod.yml up -d
echo "PRONTO: https://$(grep ^SITE_ADDRESS= .env | cut -d= -f2)"
