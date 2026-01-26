#!/bin/bash

# Destroy/cleanup script
# Usage: ./destroy.sh [namespace] [release-name]

set -e

NAMESPACE="${1:-rivka}"
RELEASE_NAME="${2:-simple-web}"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Destroying Helm Release"
echo "=========================================="
echo -e "${RED}Namespace: $NAMESPACE${NC}"
echo -e "${RED}Release: $RELEASE_NAME${NC}"
echo ""

# Confirmation
read -p "Are you sure you want to destroy this deployment? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Uninstall Helm release
echo "Uninstalling Helm release..."
helm uninstall $RELEASE_NAME --namespace $NAMESPACE --wait || echo "Release may not exist"

# Clean up any remaining resources
echo ""
echo "Cleaning up remaining resources..."
kubectl delete all -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME || true

echo ""
echo -e "${YELLOW}✓ Destruction complete${NC}"
echo ""
echo "Remaining resources in namespace $NAMESPACE:"
kubectl get all -n $NAMESPACE
