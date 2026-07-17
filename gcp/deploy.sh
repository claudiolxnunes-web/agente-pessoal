#!/bin/bash
# ============================================================
# deploy_gcp.sh — Deploy completo no Google Cloud
# Agente Pessoal v3.1
# ============================================================
# Pré-requisitos:
#   1. gcloud CLI instalado (https://cloud.google.com/sdk/docs/install)
#   2. Estar autenticado: gcloud auth login
#   3. Ter um projeto GCP criado
# ============================================================

set -euo pipefail

# ── Cores ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

info()    { echo -e "${CYAN}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()   { echo -e "${RED}❌ $1${NC}"; exit 1; }
step()    { echo -e "\n${BLUE}══ $1 ══${NC}"; }

# ── Configurações (EDITE AQUI) ─────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-meu-projeto-gcp}"
REGION="${GCP_REGION:-southamerica-east1}"      # São Paulo
REPO_NAME="agente-pessoal"
IMAGE_BASE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/agente"
DB_INSTANCE="agente-db"
DB_NAME="agente_pessoal"
DB_USER="agente_user"
SERVICE_ACCOUNT="agente-pessoal-sa"

echo -e """
${BLUE}╔══════════════════════════════════════════════╗
║   🤖 Agente Pessoal v3.1 — Deploy GCP       ║
║   Projeto : $PROJECT_ID
║   Região  : $REGION
╚══════════════════════════════════════════════╝${NC}
"""

# ── Verificações ───────────────────────────────────────────────────────────────
step "1/9 Verificações iniciais"

command -v gcloud >/dev/null 2>&1 || error "gcloud CLI não encontrado. Instale em: https://cloud.google.com/sdk/docs/install"
command -v docker  >/dev/null 2>&1 || error "Docker não encontrado. Instale em: https://docs.docker.com/get-docker/"

gcloud config set project "$PROJECT_ID" || error "Projeto '$PROJECT_ID' não encontrado. Defina GCP_PROJECT_ID="
success "Projeto configurado: $PROJECT_ID"

# ── Habilitar APIs ─────────────────────────────────────────────────────────────
step "2/9 Habilitando APIs do Google Cloud"

APIS=(
  run.googleapis.com
  cloudbuild.googleapis.com
  artifactregistry.googleapis.com
  sqladmin.googleapis.com
  secretmanager.googleapis.com
  vpcaccess.googleapis.com
  cloudresourcemanager.googleapis.com
)

for api in "${APIS[@]}"; do
  info "Habilitando $api..."
  gcloud services enable "$api" --quiet
done
success "APIs habilitadas"

# ── Service Account ─────────────────────────────────────────────────────────────
step "3/9 Criando Service Account"

if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" &>/dev/null; then
  gcloud iam service-accounts create "$SERVICE_ACCOUNT" \
    --display-name="Agente Pessoal SA" \
    --description="Service account do Agente Pessoal"
  success "Service account criada"
else
  info "Service account já existe"
fi

# Permissões necessárias
ROLES=(
  roles/run.invoker
  roles/cloudsql.client
  roles/secretmanager.secretAccessor
  roles/storage.objectAdmin
  roles/logging.logWriter
)
for role in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$role" --quiet
done
success "Permissões configuradas"

# ── Artifact Registry ──────────────────────────────────────────────────────────
step "4/9 Configurando Artifact Registry"

if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &>/dev/null; then
  gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Imagens do Agente Pessoal"
  success "Repositório criado: $REPO_NAME"
else
  info "Repositório já existe"
fi

gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
success "Docker autenticado no Artifact Registry"

# ── Cloud SQL ──────────────────────────────────────────────────────────────────
step "5/9 Configurando Cloud SQL (PostgreSQL)"

if ! gcloud sql instances describe "$DB_INSTANCE" &>/dev/null; then
  info "Criando instância PostgreSQL (pode levar alguns minutos)..."
  gcloud sql instances create "$DB_INSTANCE" \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region="$REGION" \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --availability-type=zonal

  # Banco de dados
  gcloud sql databases create "$DB_NAME" --instance="$DB_INSTANCE"

  # Usuário
  DB_PASSWORD=$(openssl rand -base64 24)
  gcloud sql users create "$DB_USER" \
    --instance="$DB_INSTANCE" \
    --password="$DB_PASSWORD"

  # Salva a connection string no Secret Manager
  DB_URL="postgresql+psycopg2://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE"
  echo -n "$DB_URL" | gcloud secrets create "DATABASE_URL" \
    --data-file=- --replication-policy=automatic
  success "Cloud SQL criado. Connection string salva no Secret Manager."
else
  info "Cloud SQL já existe"
fi

# ── Secret Manager ─────────────────────────────────────────────────────────────
step "6/9 Configurando Secrets"

create_secret() {
  local name="$1"
  local value="$2"
  if ! gcloud secrets describe "$name" &>/dev/null; then
    echo -n "$value" | gcloud secrets create "$name" \
      --data-file=- --replication-policy=automatic
    success "Secret criado: $name"
  else
    echo -n "$value" | gcloud secrets versions add "$name" --data-file=-
    info "Secret atualizado: $name"
  fi
}

# Lê do .env se existir
if [ -f ".env" ]; then
  source .env
  [ -n "${OPENAI_API_KEY:-}" ]        && create_secret "OPENAI_API_KEY"        "$OPENAI_API_KEY"
  [ -n "${GMAIL_ENABLED:-}" ]         && create_secret "GMAIL_ENABLED"         "$GMAIL_ENABLED"
  [ -n "${OUTLOOK_ACCESS_TOKEN:-}" ]  && create_secret "OUTLOOK_ACCESS_TOKEN"  "$OUTLOOK_ACCESS_TOKEN"
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ]    && create_secret "TELEGRAM_BOT_TOKEN"    "$TELEGRAM_BOT_TOKEN"
  [ -n "${WHATSAPP_ACCESS_TOKEN:-}" ] && create_secret "WHATSAPP_ACCESS_TOKEN" "$WHATSAPP_ACCESS_TOKEN"
  [ -n "${NOTION_TOKEN:-}" ]          && create_secret "NOTION_TOKEN"          "$NOTION_TOKEN"
  success "Secrets carregados do .env"
else
  warn ".env não encontrado. Configure os secrets manualmente no Secret Manager."
  warn "Acesse: https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
fi

# ── Build e Push da Imagem ────────────────────────────────────────────────────
step "7/9 Build e Push da imagem Docker"

IMAGE_TAG="$IMAGE_BASE:$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"
IMAGE_LATEST="$IMAGE_BASE:latest"

info "Fazendo build da imagem..."
docker build -f docker/Dockerfile -t "$IMAGE_TAG" -t "$IMAGE_LATEST" .

info "Fazendo push para Artifact Registry..."
docker push "$IMAGE_TAG"
docker push "$IMAGE_LATEST"
success "Imagem publicada: $IMAGE_LATEST"

# ── Deploy dos Serviços no Cloud Run ─────────────────────────────────────────
step "8/9 Deploy no Cloud Run"

CLOUDSQL_CONN="$PROJECT_ID:$REGION:$DB_INSTANCE"

# Função de deploy genérica
deploy_service() {
  local name="$1"
  local cmd="$2"
  local port="$3"
  local memory="${4:-512Mi}"
  local cpu="${5:-1}"

  info "Fazendo deploy: $name..."
  gcloud run deploy "$name" \
    --image="$IMAGE_LATEST" \
    --region="$REGION" \
    --platform=managed \
    --port="$port" \
    --command="$cmd" \
    --memory="$memory" \
    --cpu="$cpu" \
    --min-instances=0 \
    --max-instances=3 \
    --service-account="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
    --add-cloudsql-instances="$CLOUDSQL_CONN" \
    --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
    --set-env-vars="PYTHONPATH=/app,REGION=$REGION" \
    --allow-unauthenticated \
    --quiet
  success "✅ $name online"
}

# API REST
deploy_service "agente-api" \
  "python,api/main.py" \
  "8000" "512Mi" "1"

# Interface Web (Streamlit)
gcloud run deploy "agente-web" \
  --image="$IMAGE_LATEST" \
  --region="$REGION" \
  --platform=managed \
  --port=8501 \
  --command="streamlit" \
  --args="run,ui/streamlit_app.py,--server.port=8501,--server.address=0.0.0.0,--server.headless=true" \
  --memory="1Gi" --cpu="1" \
  --min-instances=0 --max-instances=2 \
  --service-account="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --add-cloudsql-instances="$CLOUDSQL_CONN" \
  --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
  --allow-unauthenticated --quiet
success "✅ agente-web online"

# Dashboard Analytics
gcloud run deploy "agente-dashboard" \
  --image="$IMAGE_LATEST" \
  --region="$REGION" \
  --platform=managed \
  --port=8502 \
  --command="streamlit" \
  --args="run,ui/dashboard.py,--server.port=8502,--server.address=0.0.0.0,--server.headless=true" \
  --memory="1Gi" --cpu="1" \
  --min-instances=0 --max-instances=2 \
  --service-account="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --add-cloudsql-instances="$CLOUDSQL_CONN" \
  --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
  --allow-unauthenticated --quiet
success "✅ agente-dashboard online"

# Webhook WhatsApp
deploy_service "agente-whatsapp" \
  "python,ui/bot_whatsapp.py" \
  "8001" "512Mi" "1"

# ── URLs dos Serviços ─────────────────────────────────────────────────────────
step "9/9 Resumo do Deploy"

API_URL=$(gcloud run services describe agente-api --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "N/A")
WEB_URL=$(gcloud run services describe agente-web --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "N/A")
DASH_URL=$(gcloud run services describe agente-dashboard --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "N/A")
WA_URL=$(gcloud run services describe agente-whatsapp --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "N/A")

echo -e """
${GREEN}╔══════════════════════════════════════════════════════╗
║   🎉 Deploy concluído com sucesso!                   ║
╠══════════════════════════════════════════════════════╣
║  🔌 API REST    : $API_URL
║  🖥️  Interface  : $WEB_URL
║  📊 Dashboard  : $DASH_URL
║  📱 WhatsApp   : $WA_URL/webhook
╠══════════════════════════════════════════════════════╣
║  📋 Próximos passos:                                 ║
║  1. Configure o Telegram bot com longa execução      ║
║     → veja: gcp/deploy_telegram.sh                  ║
║  2. Configure o webhook do WhatsApp com a URL acima  ║
║  3. Acesse o Console GCP para monitorar os logs      ║
╚══════════════════════════════════════════════════════╝${NC}
"""

# Salva as URLs em arquivo
cat > gcp/urls_deploy.txt << EOF
API_URL=$API_URL
WEB_URL=$WEB_URL
DASHBOARD_URL=$DASH_URL
WHATSAPP_WEBHOOK_URL=$WA_URL/webhook
DEPLOY_DATE=$(date)
EOF

success "URLs salvas em gcp/urls_deploy.txt"
