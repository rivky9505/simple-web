#!/bin/bash

# Complete Azure setup script for the VM
# Run this after connecting to the VM

set -e

echo "=========================================="
echo "Azure DevOps Setup Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AKS_CLUSTER="devops-interview-aks"
RESOURCE_GROUP="devops-interview-rg"
NAMESPACE="${1:-rivka}"  # Use first argument or default to 'rivka'

echo -e "${GREEN}Using namespace: $NAMESPACE${NC}"
echo ""

# Function to print section headers
print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        exit 1
    fi
}

# 1. Verify tools
print_header "Step 1: Verifying installed tools"

command -v az >/dev/null 2>&1 || { echo "az CLI not found"; exit 1; }
echo "✓ Azure CLI installed"

command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found"; exit 1; }
echo "✓ kubectl installed"

command -v helm >/dev/null 2>&1 || { echo "helm not found"; exit 1; }
echo "✓ helm installed"

command -v kubelogin >/dev/null 2>&1 || { echo "kubelogin not found"; exit 1; }
echo "✓ kubelogin installed"

echo ""
echo "Tool versions:"
az --version | head -n 1
kubectl version --client --short
helm version --short

# 2. Azure Authentication
print_header "Step 2: Authenticating with Azure"

echo "Logging in with managed identity..."
az login -i
check_success "Azure authentication"

echo ""
echo "Current Azure account:"
az account show --query "{Name:name, SubscriptionId:id, TenantId:tenantId}" -o table

# 3. Connect to AKS
print_header "Step 3: Connecting to AKS cluster"

echo "Getting AKS credentials..."
az aks get-credentials \
    --name $AKS_CLUSTER \
    --resource-group $RESOURCE_GROUP \
    --overwrite-existing
check_success "AKS credentials retrieved"

echo "Configuring kubelogin..."
export KUBECONFIG=~/.kube/config
kubelogin convert-kubeconfig -l msi
check_success "kubelogin configured"

echo ""
echo "Cluster info:"
kubectl cluster-info

echo ""
echo "Cluster nodes:"
kubectl get nodes

# 4. Verify namespace access
print_header "Step 4: Verifying namespace access"

echo "Checking namespace: $NAMESPACE"
if kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
    echo "✓ Namespace $NAMESPACE exists"
else
    echo "⚠ Namespace $NAMESPACE does not exist yet (will be created during deployment)"
fi

echo ""
echo "Checking permissions in namespace $NAMESPACE:"
kubectl auth can-i create pods --namespace $NAMESPACE && echo "✓ Can create pods" || echo "✗ Cannot create pods"
kubectl auth can-i create services --namespace $NAMESPACE && echo "✓ Can create services" || echo "✗ Cannot create services"
kubectl auth can-i create deployments --namespace $NAMESPACE && echo "✓ Can create deployments" || echo "✗ Cannot create deployments"

# 5. Check KEDA installation
print_header "Step 5: Verifying KEDA installation"

if kubectl get namespace keda >/dev/null 2>&1; then
    echo "✓ KEDA namespace exists"
    kubectl get pods -n keda
else
    echo "⚠ KEDA not installed - autoscaling will not work"
fi

# 6. Check Ingress Controller
print_header "Step 6: Verifying Ingress Controller"

if kubectl get namespace ingress-nginx >/dev/null 2>&1; then
    echo "✓ Ingress-nginx namespace exists"
    kubectl get pods -n ingress-nginx
    
    echo ""
    echo "Ingress controller service:"
    kubectl get svc -n ingress-nginx
else
    echo "⚠ Ingress controller not found - checking for other ingress controllers"
    kubectl get ingressclass
fi

# 7. Check ACR access
print_header "Step 7: Verifying ACR access"

ACR_NAME="acrinterview"
echo "Checking access to ACR: $ACR_NAME"

if az acr show --name $ACR_NAME >/dev/null 2>&1; then
    echo "✓ ACR is accessible"
    
    echo ""
    echo "Available repositories:"
    az acr repository list --name $ACR_NAME -o table || echo "No repositories yet or insufficient permissions"
    
    echo ""
    echo "Tags for simple-web image:"
    az acr repository show-tags --name $ACR_NAME --repository simple-web -o table 2>/dev/null || echo "Image 'simple-web' not found in registry"
else
    echo "✗ Cannot access ACR $ACR_NAME"
fi

# 8. Setup summary
print_header "Setup Summary"

echo -e "${GREEN}✓ All setup steps completed successfully!${NC}"
echo ""
echo "Configuration:"
echo "  AKS Cluster: $AKS_CLUSTER"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Namespace: $NAMESPACE"
echo "  Kubeconfig: ~/.kube/config"
echo ""
echo "Next steps:"
echo "  1. Clone your GitHub repository"
echo "  2. Update helm-charts/simple-web/values.yaml with namespace: $NAMESPACE"
echo "  3. Deploy with: helm install simple-web ./helm-charts/simple-web/ --namespace $NAMESPACE --create-namespace"
echo ""
echo -e "${YELLOW}Save this output for reference!${NC}"

# Save configuration to file
cat > ~/.devops-config <<EOF
# DevOps Configuration
export AKS_CLUSTER="$AKS_CLUSTER"
export RESOURCE_GROUP="$RESOURCE_GROUP"
export NAMESPACE="$NAMESPACE"
export KUBECONFIG=~/.kube/config
EOF

echo ""
echo "Configuration saved to ~/.devops-config"
echo "Source it in your shell: source ~/.devops-config"
