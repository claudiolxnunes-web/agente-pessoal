# ☁️ Deploy no Google Cloud — Agente Pessoal v3.1

Guia completo para subir o agente no Google Cloud usando **Cloud Run**, **Cloud SQL**, **Secret Manager** e **Artifact Registry**.

---

## 🏗️ Arquitetura GCP

```
┌─────────────────────────────────────────────────────────┐
│                    Google Cloud                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Cloud Run   │  │  Cloud Run   │  │   Cloud Run   │  │
│  │  agente-api  │  │  agente-web  │  │agente-dashboard│ │
│  │  (FastAPI)   │  │ (Streamlit)  │  │   (Plotly)    │  │
│  │   :8000      │  │   :8501      │  │    :8502      │  │
│  └──────┬───────┘  └──────────────┘  └───────────────┘  │
│         │                                                 │
│  ┌──────▼───────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Cloud SQL   │  │   Secret     │  │   Artifact    │  │
│  │ (PostgreSQL) │  │   Manager    │  │   Registry    │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                      │
│  │  Cloud Run   │  │  Cloud Run   │                      │
│  │agente-whatsapp│ │agente-telegram│                     │
│  │  (Webhook)   │  │ (min=1 ativo)│                      │
│  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Pré-requisitos

### 1. Instalar gcloud CLI
```bash
# Linux/macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Ou via Homebrew (macOS)
brew install --cask google-cloud-sdk
```

### 2. Autenticar
```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Criar projeto GCP (se ainda não tiver)
```bash
gcloud projects create meu-agente-pessoal --name="Agente Pessoal"
gcloud config set project meu-agente-pessoal

# Ativar faturamento (obrigatório para Cloud Run)
# https://console.cloud.google.com/billing
```

---

## 🚀 Deploy Rápido (Automático)

```bash
# 1. Configure as variáveis
export GCP_PROJECT_ID="meu-agente-pessoal"
export GCP_REGION="southamerica-east1"   # São Paulo

# 2. Preencha o .env com suas chaves
cp .env.example .env
nano .env   # ou code .env

# 3. Torne os scripts executáveis
chmod +x gcp/*.sh

# 4. Configure os secrets
./gcp/setup_secrets.sh .env

# 5. Faça o deploy completo
./gcp/deploy.sh
```

> ⏱️ O primeiro deploy leva ~15-20 minutos (criação do Cloud SQL).

---

## 🔧 Deploy Manual (Passo a Passo)

### Passo 1 — Habilitar APIs
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

### Passo 2 — Criar Artifact Registry
```bash
gcloud artifacts repositories create agente-pessoal \
  --repository-format=docker \
  --location=southamerica-east1
```

### Passo 3 — Build e Push da Imagem
```bash
# Autenticar Docker
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# Build
IMAGE="southamerica-east1-docker.pkg.dev/meu-agente-pessoal/agente-pessoal/agente:latest"
docker build -f docker/Dockerfile -t $IMAGE .
docker push $IMAGE
```

### Passo 4 — Cloud SQL (PostgreSQL)
```bash
gcloud sql instances create agente-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=southamerica-east1

gcloud sql databases create agente_pessoal --instance=agente-db
gcloud sql users create agente_user --instance=agente-db --password=SENHA_SEGURA
```

### Passo 5 — Secrets
```bash
# OPENAI_API_KEY
echo -n "sk-sua-chave" | gcloud secrets create OPENAI_API_KEY --data-file=-

# DATABASE_URL
DB_URL="postgresql+psycopg2://agente_user:SENHA@/agente_pessoal?host=/cloudsql/meu-agente-pessoal:southamerica-east1:agente-db"
echo -n "$DB_URL" | gcloud secrets create DATABASE_URL --data-file=-
```

### Passo 6 — Deploy no Cloud Run
```bash
PROJECT="meu-agente-pessoal"
REGION="southamerica-east1"
IMAGE="southamerica-east1-docker.pkg.dev/$PROJECT/agente-pessoal/agente:latest"

# API REST
gcloud run deploy agente-api \
  --image=$IMAGE \
  --region=$REGION \
  --port=8000 \
  --command=python --args=api/main.py \
  --memory=512Mi --cpu=1 \
  --min-instances=0 --max-instances=5 \
  --add-cloudsql-instances=$PROJECT:$REGION:agente-db \
  --set-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest \
  --allow-unauthenticated

# Interface Web
gcloud run deploy agente-web \
  --image=$IMAGE \
  --region=$REGION \
  --port=8501 \
  --command=streamlit \
  --args="run,ui/streamlit_app.py,--server.port=8501,--server.address=0.0.0.0,--server.headless=true" \
  --memory=1Gi \
  --allow-unauthenticated
```

---

## 🔄 CI/CD com Cloud Build

### Configurar trigger automático
```bash
# Conectar repositório GitHub
gcloud builds triggers create github \
  --repo-name=agente-pessoal \
  --repo-owner=seu-usuario-github \
  --branch-pattern="^main$" \
  --build-config=gcp/cloudbuild.yaml \
  --name=deploy-main
```

A partir daí, cada push na `main` dispara o pipeline automaticamente.

---

## 📊 Monitoramento

```bash
# Ver status de todos os serviços
./gcp/logs_gcp.sh status

# Ver logs da API
./gcp/logs_gcp.sh logs agente-api 100

# Via Console GCP
# https://console.cloud.google.com/run?project=meu-agente-pessoal
```

---

## 💰 Estimativa de Custo (GCP)

| Serviço | Configuração | Custo/mês |
|---------|-------------|-----------|
| Cloud Run (API + Web + Dashboard) | 0 min-instances | **~$0–5** |
| Cloud Run (Telegram, min=1) | 512Mi, sempre ativo | **~$7–12** |
| Cloud SQL | db-f1-micro, 10GB | **~$8–10** |
| Artifact Registry | ~500MB imagens | **~$0.50** |
| Secret Manager | < 10k acessos | **~$0** |
| **Total estimado** | | **~$15–28/mês** |

> 💡 Use o [GCP Pricing Calculator](https://cloud.google.com/products/calculator) para simular seu caso específico.

---

## 🌎 Regiões Disponíveis

| Região | Localização | Latência BR |
|--------|------------|-------------|
| `southamerica-east1` | **São Paulo** ⭐ | ~10ms |
| `us-central1` | Iowa, EUA | ~150ms |
| `us-east1` | Carolina do Sul, EUA | ~130ms |

---

## 🐛 Solução de Problemas

### Erro: "Permission denied" no Cloud SQL
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:agente-pessoal-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### Erro: "Secret not found"
```bash
# Verifique se o secret existe
gcloud secrets list --project=$PROJECT_ID

# Recrie se necessário
./gcp/setup_secrets.sh .env
```

### Container não inicia (erro 500)
```bash
# Veja os logs detalhados
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=agente-api" \
  --project=$PROJECT_ID --limit=50 --format=json | jq '.[].textPayload'
```

### Streamlit não carrega
O Cloud Run tem timeout de 60s para cold start. Adicione:
```bash
gcloud run services update agente-web \
  --timeout=300 --region=$REGION
```

---

## 🔒 Boas Práticas de Segurança

- ✅ **Nunca** coloque chaves de API no código — use Secret Manager
- ✅ Use uma Service Account dedicada com o mínimo de permissões
- ✅ Ative VPC para comunicação interna entre serviços
- ✅ Configure alertas de faturamento no GCP
- ✅ Revise os logs regularmente no Cloud Logging
