#!/bin/bash
# ============================================================
# setup_secrets.sh — Configura todos os secrets no
# Google Secret Manager a partir do arquivo .env
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()   { echo -e "${RED}❌ $1${NC}"; exit 1; }

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
[ -z "$PROJECT_ID" ] && error "GCP_PROJECT_ID não definido. Execute: export GCP_PROJECT_ID=meu-projeto"

ENV_FILE="${1:-.env}"
[ ! -f "$ENV_FILE" ] && error "Arquivo $ENV_FILE não encontrado. Copie .env.example para .env e preencha."

echo "📋 Configurando secrets do projeto: $PROJECT_ID"
echo "📄 Lendo de: $ENV_FILE"
echo ""

# Secrets que devem ir para o Secret Manager (dados sensíveis)
SECRETS_PARA_GCP=(
  OPENAI_API_KEY
  GMAIL_ENABLED
  OUTLOOK_CLIENT_ID
  OUTLOOK_CLIENT_SECRET
  OUTLOOK_TENANT_ID
  OUTLOOK_ACCESS_TOKEN
  YAHOO_EMAIL
  YAHOO_APP_PASSWORD
  PROTONMAIL_API_TOKEN
  NOTION_TOKEN
  NOTION_DATABASE_ID
  WHATSAPP_ACCESS_TOKEN
  WHATSAPP_VERIFY_TOKEN
  WHATSAPP_PHONE_NUMBER_ID
  TELEGRAM_BOT_TOKEN
  SERPAPI_KEY
)

create_or_update_secret() {
  local name="$1"
  local value="$2"

  if [ -z "$value" ]; then
    warn "Pulando $name (valor vazio)"
    return
  fi

  if gcloud secrets describe "$name" --project="$PROJECT_ID" &>/dev/null; then
    echo -n "$value" | gcloud secrets versions add "$name" \
      --data-file=- --project="$PROJECT_ID" --quiet
    success "Atualizado: $name"
  else
    echo -n "$value" | gcloud secrets create "$name" \
      --data-file=- \
      --replication-policy=automatic \
      --project="$PROJECT_ID" \
      --quiet
    success "Criado: $name"
  fi
}

# Lê o .env e processa
while IFS='=' read -r chave valor; do
  # Ignora comentários e linhas vazias
  [[ "$chave" =~ ^#.*$ || -z "$chave" ]] && continue
  # Remove aspas do valor
  valor="${valor%\"}"
  valor="${valor#\"}"
  valor="${valor%\'}"
  valor="${valor#\'}"

  # Verifica se é um secret que deve ir para o GCP
  for secret in "${SECRETS_PARA_GCP[@]}"; do
    if [ "$chave" = "$secret" ]; then
      create_or_update_secret "$chave" "$valor"
      break
    fi
  done
done < "$ENV_FILE"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗"
echo -e "║  ✅ Secrets configurados com sucesso!            ║"
echo -e "╠══════════════════════════════════════════════════╣"
echo -e "║  🔗 Acesse o Secret Manager:                     ║"
echo -e "║  https://console.cloud.google.com/security/      ║"
echo -e "║  secret-manager?project=$PROJECT_ID"
echo -e "╚══════════════════════════════════════════════════╝${NC}"
