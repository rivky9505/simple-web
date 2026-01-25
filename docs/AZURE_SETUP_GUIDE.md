# Azure Setup Guide for AWS Engineers

## Key Differences: AWS vs Azure

### Service Mapping

| AWS Service | Azure Service | Purpose |
|-------------|---------------|---------|
| EKS | AKS (Azure Kubernetes Service) | Managed Kubernetes |
| ECR | ACR (Azure Container Registry) | Container Registry |
| IAM Roles | Managed Identity | Identity Management |
| AWS CLI | Azure CLI (`az`) | Command-line tool |
| Route53 | Azure DNS | DNS Management |
| ALB/ELB | Azure Load Balancer / App Gateway | Load Balancing |

### Authentication Differences

#### AWS (What you know)
```bash
# AWS uses access keys
aws configure
# Enters: Access Key ID, Secret Access Key, Region

# For EKS
aws eks update-kubeconfig --name cluster-name
```

#### Azure (What you'll use)
```bash
# Azure uses Managed Identity on VM
az login -i  # -i means use managed identity (like IAM role for EC2)

# For AKS
az aks get-credentials -n cluster-name -g resource-group
kubelogin convert-kubeconfig -l msi  # msi = managed identity
```

**Why Managed Identity?**
- No credentials to manage (like assuming an IAM role)
- Automatic rotation
- Scoped permissions
- More secure than service principals

## Step-by-Step Azure Setup

### 1. Understanding Your Environment

```
Azure Resource Group (like AWS Account/Region)
    └── devops-interview-rg
        ├── AKS Cluster (like EKS)
        │   └── devops-interview-aks
        ├── Container Registry (like ECR)
        │   └── acrinterview.azurecr.io
        └── Virtual Machine (like EC2)
            └── Your Jenkins VM
```

### 2. Connecting to the VM

The VM is like an EC2 instance with an IAM role attached that gives it permissions to access AKS.

```powershell
# Windows PowerShell
ssh -i C:\path\to\your\keyfile azureuser@108.143.33.48

# If you get "bad permissions" error:
# Right-click key file → Properties → Security → Advanced
# Remove all users except yourself with Read permissions only
```

```bash
# Linux/Mac
chmod 600 /path/to/keyfile
ssh -i /path/to/keyfile azureuser@108.143.33.48
```

### 3. Azure Authentication (Like assuming IAM role)

```bash
# Login with managed identity (like EC2 instance profile)
az login -i

# Expected output:
[
  {
    "environmentName": "AzureCloud",
    "id": "subscription-id",
    "isDefault": true,
    "name": "subscription-name",
    "state": "Enabled",
    "tenantId": "tenant-id",
    "user": {
      "name": "systemAssignedIdentity",
      "type": "servicePrincipal"
    }
  }
]

# Verify your identity
az account show
```

**What's happening?**
- The VM has a "Managed Identity" (like an IAM role)
- This identity has permissions to access AKS
- No credentials needed - Azure handles it automatically

### 4. Connecting to AKS Cluster

```bash
# Get cluster credentials (like updating kubeconfig for EKS)
az aks get-credentials \
  --name devops-interview-aks \
  --resource-group devops-interview-rg \
  --overwrite-existing

# This creates/updates ~/.kube/config

# Configure authentication plugin
export KUBECONFIG=~/.kube/config
kubelogin convert-kubeconfig -l msi

# Verify connection
kubectl cluster-info
kubectl get nodes
kubectl get namespaces
```

**What's happening?**
- `az aks get-credentials`: Downloads cluster info to kubeconfig
- `kubelogin`: Converts kubeconfig to use managed identity for auth
- `-l msi`: Uses Managed Service Identity

### 5. Understanding Azure CLI Commands

#### Resource Groups (like AWS Accounts/Regions)

```bash
# List resource groups
az group list --output table

# Show specific resource group
az group show --name devops-interview-rg
```

#### AKS Commands (like EKS commands)

```bash
# List AKS clusters
az aks list --output table

# Show cluster details
az aks show --name devops-interview-aks --resource-group devops-interview-rg

# Get cluster credentials
az aks get-credentials --name devops-interview-aks --resource-group devops-interview-rg

# Scale node pool (like scaling EKS node group)
az aks scale --name devops-interview-aks --resource-group devops-interview-rg --node-count 3
```

#### Container Registry (like ECR)

```bash
# List registries
az acr list --output table

# Show registry
az acr show --name acrinterview

# Login to registry
az acr login --name acrinterview

# List images
az acr repository list --name acrinterview

# List tags for an image
az acr repository show-tags --name acrinterview --repository simple-web
```

### 6. Common Azure CLI Patterns

```bash
# Azure CLI follows this pattern:
az <service> <subgroup> <action> --parameters

# Examples:
az aks show --name cluster-name --resource-group rg-name
az acr login --name registry-name
az vm list --resource-group rg-name

# Get JSON output (default)
az aks show --name devops-interview-aks --resource-group devops-interview-rg

# Get table output (easier to read)
az aks show --name devops-interview-aks --resource-group devops-interview-rg --output table

# Get specific field with query
az aks show --name devops-interview-aks --resource-group devops-interview-rg --query "kubernetesVersion"
```

## Kubernetes on Azure vs AWS

### Similarities (95% the same!)

```bash
# All standard kubectl commands work the same
kubectl get pods
kubectl get services
kubectl apply -f deployment.yaml
kubectl logs pod-name
kubectl exec -it pod-name -- /bin/bash

# Helm works the same
helm install my-release ./chart
helm upgrade my-release ./chart
helm list
helm uninstall my-release
```

### Differences

#### 1. Load Balancer

**AWS EKS:**
```yaml
service:
  type: LoadBalancer  # Creates AWS ELB/ALB
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
```

**Azure AKS:**
```yaml
service:
  type: LoadBalancer  # Creates Azure Load Balancer
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "false"
```

#### 2. Ingress Controller

**AWS EKS:**
- Often use AWS ALB Ingress Controller
- Integrates with AWS ALB/ELB

**Azure AKS:**
- Often use NGINX Ingress Controller (already installed on your cluster)
- Can also use Application Gateway Ingress Controller (AGIC)

#### 3. Storage Classes

**AWS EKS:**
```yaml
storageClassName: gp2  # or gp3
# Uses AWS EBS
```

**Azure AKS:**
```yaml
storageClassName: managed-premium  # or managed, azurefile
# Uses Azure Disk
```

## Troubleshooting Common Issues

### Issue 1: Authentication Fails

```bash
# Problem: az login -i fails
# Solution: VM might not have managed identity enabled
az login -i

# If it fails, check VM identity
az vm identity show --name vm-name --resource-group rg-name
```

### Issue 2: kubectl Commands Fail with Auth Error

```bash
# Problem: "Unable to connect to the server: getting credentials"
# Solution: Re-configure kubelogin

export KUBECONFIG=~/.kube/config
kubelogin convert-kubeconfig -l msi

# Or refresh credentials
az aks get-credentials --name devops-interview-aks --resource-group devops-interview-rg --overwrite-existing
kubelogin convert-kubeconfig -l msi
```

### Issue 3: Permission Denied

```bash
# Problem: "cannot create resource in namespace"
# Solution: You only have permissions for specific namespace

# Check your permissions
kubectl auth can-i create pods --namespace YOUR_NAME

# Always use your assigned namespace
kubectl get pods --namespace YOUR_NAME
helm install app ./chart --namespace YOUR_NAME
```

### Issue 4: Image Pull Errors

```bash
# Problem: "Failed to pull image: acrinterview.azurecr.io/simple-web"
# Solution: AKS needs access to ACR

# Check if cluster has access to ACR
az aks show --name devops-interview-aks --resource-group devops-interview-rg --query "servicePrincipalProfile"

# Usually pre-configured, but you can attach if needed
az aks update --name devops-interview-aks --resource-group devops-interview-rg --attach-acr acrinterview
```

## Useful Azure CLI Commands Cheat Sheet

```bash
# Get help
az --help
az aks --help
az aks show --help

# Interactive mode (like AWS CLI wizard)
az interactive

# Login
az login -i  # With managed identity
az login     # Interactive browser login

# Account info
az account show
az account list

# AKS operations
az aks list --output table
az aks get-credentials --name CLUSTER --resource-group RG
az aks show --name CLUSTER --resource-group RG

# ACR operations
az acr login --name REGISTRY
az acr repository list --name REGISTRY
az acr repository show-tags --name REGISTRY --repository IMAGE

# Resource operations
az group list --output table
az resource list --resource-group RG --output table

# VM operations (if needed)
az vm list --output table
az vm show --name VM --resource-group RG
```

## Quick Reference: AWS to Azure Translation

| Task | AWS | Azure |
|------|-----|-------|
| CLI tool | `aws` | `az` |
| Login | `aws configure` | `az login -i` |
| K8s cluster type | EKS | AKS |
| Get K8s creds | `aws eks update-kubeconfig` | `az aks get-credentials` |
| Container registry | ECR | ACR |
| Registry login | `aws ecr get-login-password` | `az acr login` |
| Identity | IAM Role | Managed Identity |
| Resource group | Account + Region | Resource Group |
| Load balancer | ELB/ALB/NLB | Azure Load Balancer |

## Next Steps

Once connected, you can use standard Kubernetes/Helm commands:

```bash
# Deploy your Helm chart
cd helm-charts/simple-web
helm install simple-web . --namespace YOUR_NAME --create-namespace

# Monitor deployment
kubectl get pods --namespace YOUR_NAME --watch

# Check logs
kubectl logs -f deployment/simple-web-simple-web --namespace YOUR_NAME

# Get ingress
kubectl get ingress --namespace YOUR_NAME
```

The Kubernetes parts are identical to AWS EKS!
