#!/bin/bash
# ============================================================
# logs_gcp.sh — Monitora logs e status dos serviços GCP
# ============================================================

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-southamerica-east1}"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

SERVICOS=(agente-api agente-web agente-dashboard agente-whatsapp agente-telegram)

show_status() {
  echo -e "\n${CYAN}══ Status dos Serviços Cloud Run ══${NC}\n"
  for svc in "${SERVICOS[@]}"; do
    URL=$(gcloud run services describe "$svc" \
      --region="$REGION" --project="$PROJECT_ID" \
      --format='value(status.url)' 2>/dev/null || echo "não encontrado")
    READY=$(gcloud run services describe "$svc" \
      --region="$REGION" --project="$PROJECT_ID" \
      --format='value(status.conditions[0].status)' 2>/dev/null || echo "?")
    EMOJI="🟢"
    [ "$READY" != "True" ] && EMOJI="🔴"
    printf "${EMOJI} %-22s %s\n" "$svc" "$URL"
  done
}

show_logs() {
  local svc="${1:-agente-api}"
  local linhas="${2:-50}"
  echo -e "\n${CYAN}══ Logs: $svc (últimas $linhas linhas) ══${NC}\n"
  gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=$svc" \
    --project="$PROJECT_ID" \
    --limit="$linhas" \
    --format="value(timestamp,textPayload)" \
    --order=asc 2>/dev/null || echo "Nenhum log encontrado"
}

show_metricas() {
  echo -e "\n${CYAN}══ Métricas rápidas ══${NC}\n"
  for svc in "${SERVICOS[@]}"; do
    COUNT=$(gcloud run services describe "$svc" \
      --region="$REGION" --project="$PROJECT_ID" \
      --format='value(status.observedGeneration)' 2>/dev/null || echo "?")
    echo "  📊 $svc — revisão: $COUNT"
  done
}

# Menu
case "${1:-status}" in
  status)   show_status ;;
  logs)     show_logs "${2:-agente-api}" "${3:-50}" ;;
  metricas) show_metricas ;;
  all)
    show_status
    show_metricas
    echo -e "\n${YELLOW}Use: ./logs_gcp.sh logs agente-api 100${NC}"
    ;;
  *)
    echo "Uso: $0 [status|logs <servico> <linhas>|metricas|all]"
    echo ""
    echo "Serviços: ${SERVICOS[*]}"
    ;;
esac
