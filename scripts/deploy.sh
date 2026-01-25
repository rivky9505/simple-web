#!/bin/bash

# Quick deployment script
# Usage: ./deploy.sh [namespace] [release-name]

set -e

NAMESPACE="${1:-rivka}"
RELEASE_NAME="${2:-simple-web}"
CHART_PATH="./helm-charts/simple-web"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Deploying simple-web Helm Chart"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Release: $RELEASE_NAME"
echo ""

# Check if chart exists
if [ ! -d "$CHART_PATH" ]; then
    echo "Error: Chart not found at $CHART_PATH"
    exit 1
fi

# Update namespace in values.yaml
echo "Updating namespace in values.yaml..."
sed -i.bak "s/namespace: .*/namespace: $NAMESPACE/" "$CHART_PATH/values.yaml"

# Lint chart
echo "Linting Helm chart..."
helm lint $CHART_PATH

# Create namespace if it doesn't exist
echo "Creating namespace (if not exists)..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy with Helm
echo ""
echo "Deploying Helm chart..."
helm upgrade $RELEASE_NAME $CHART_PATH \
    --install \
    --namespace $NAMESPACE \
    --wait \
    --timeout 10m \
    --atomic \
    --cleanup-on-fail

echo ""
echo -e "${GREEN}✓ Deployment successful!${NC}"
echo ""

# Show status
echo "=========================================="
echo "Deployment Status"
echo "=========================================="

helm status $RELEASE_NAME -n $NAMESPACE

echo ""
echo "Pods:"
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo ""
echo "Services:"
kubectl get svc -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo ""
echo "Ingress:"
kubectl get ingress -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo ""
echo "Getting Ingress IP (this may take a few minutes)..."
sleep 10

INGRESS_IP=$(kubectl get ingress ${RELEASE_NAME}-simple-web -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

if [ "$INGRESS_IP" != "pending" ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "Application is accessible at:"
    echo "http://$INGRESS_IP/rivka"
    echo "==========================================${NC}"
else
    echo ""
    echo -e "${YELLOW}Ingress IP is being assigned..."
    echo "Check again in a few minutes with:"
    echo "kubectl get ingress ${RELEASE_NAME}-simple-web -n $NAMESPACE${NC}"
fi

# Show KEDA status
if kubectl get scaledobject -n $NAMESPACE ${RELEASE_NAME}-simple-web >/dev/null 2>&1; then
    echo ""
    echo "KEDA ScaledObject:"
    kubectl get scaledobject ${RELEASE_NAME}-simple-web -n $NAMESPACE
fi
