#!/bin/bash
# ============================================================
# deploy_telegram.sh
# O bot Telegram usa long polling, então precisa de
# min-instances=1 para ficar sempre ativo.
# ============================================================

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-meu-projeto-gcp}"
REGION="${GCP_REGION:-southamerica-east1}"
REPO_NAME="agente-pessoal"
IMAGE_LATEST="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/agente:latest"
CLOUDSQL_CONN="$PROJECT_ID:$REGION:agente-db"
SERVICE_ACCOUNT="agente-pessoal-sa@$PROJECT_ID.iam.gserviceaccount.com"

echo "🤖 Deploy do Bot Telegram no Cloud Run..."

gcloud run deploy "agente-telegram" \
  --image="$IMAGE_LATEST" \
  --region="$REGION" \
  --platform=managed \
  --port=8080 \
  --command="python" \
  --args="ui/bot_telegram.py" \
  --memory="512Mi" \
  --cpu="1" \
  --min-instances=1 \
  --max-instances=1 \
  --no-allow-unauthenticated \
  --service-account="$SERVICE_ACCOUNT" \
  --add-cloudsql-instances="$CLOUDSQL_CONN" \
  --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest,TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest" \
  --set-env-vars="TELEGRAM_ENABLED=true,PYTHONPATH=/app" \
  --quiet

echo "✅ Bot Telegram online com min-instances=1 (sempre ativo)"
echo "💡 Custo estimado: ~\$5-10/mês com min-instance ativo"
