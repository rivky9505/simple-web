# Simple Web Helm Deployment - Complete Implementation

![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white)
![Helm](https://img.shields.io/badge/helm-0F1689?style=for-the-badge&logo=helm&logoColor=white)
![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white)
![Jenkins](https://img.shields.io/badge/jenkins-%232C5263.svg?style=for-the-badge&logo=jenkins&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

A comprehensive DevOps solution featuring Kubernetes deployment with Helm, KEDA autoscaling, Jenkins CI/CD pipeline, and a Python API integration tool.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Components](#components)
- [Deployment Guide](#deployment-guide)
- [Jenkins Setup](#jenkins-setup)
- [Python Book Fetcher](#python-book-fetcher)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting](#troubleshooting)
- [Best Practices Implemented](#best-practices-implemented)

## 🎯 Overview

This project demonstrates enterprise-grade DevOps practices for deploying and managing a web application on Azure Kubernetes Service (AKS) with the following features:

### Key Features

- **Kubernetes Deployment**: Production-ready Helm chart with best practices
- **Auto-scaling**: KEDA-based autoscaling with CPU, memory, and schedule triggers
- **Ingress Management**: NGINX ingress with custom path routing (`/rivka`)
- **CI/CD Pipeline**: Jenkins pipeline with deploy/destroy/rollback capabilities
- **Infrastructure as Code**: Declarative Helm charts and Kubernetes manifests
- **Python Integration**: API client with Pydantic validation and extensible output formats
- **Security**: RBAC, security contexts, read-only filesystems, non-root containers
- **High Availability**: Pod Disruption Budgets, health checks, and resource limits

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Cloud                            │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           AKS Cluster (devops-interview-aks)          │ │
│  │                                                         │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │  Namespace: rivka                                │  │ │
│  │  │                                                   │  │ │
│  │  │  ┌──────────────┐      ┌──────────────┐         │  │ │
│  │  │  │  simple-web  │◄─────┤   Service    │         │  │ │
│  │  │  │  Deployment  │      │  ClusterIP   │         │  │ │
│  │  │  │   (2-10      │      └──────▲───────┘         │  │ │
│  │  │  │   replicas)  │             │                  │  │ │
│  │  │  └──────▲───────┘             │                  │  │ │
│  │  │         │                     │                  │  │ │
│  │  │         │              ┌──────┴───────┐          │  │ │
│  │  │  ┌──────┴───────┐      │    Ingress   │          │  │ │
│  │  │  │ KEDA Scaler  │      │  /rivka path │◄─────────┼──┼─── Public IP
│  │  │  │  - CPU (70%) │      └──────────────┘          │  │ │
│  │  │  │  - Mem (80%) │                                │  │ │
│  │  │  │  - Schedule  │                                │  │ │
│  │  │  └──────────────┘                                │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  │                                                         │ │
│  │  Container Registry: acrinterview.azurecr.io           │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
           ▲
           │
     ┌─────┴─────┐
     │  Jenkins  │
     │  Pipeline │
     │  on VM    │
     └───────────┘
```

## ✅ Prerequisites

### On Your Local Machine

- SSH client
- Git
- Text editor
- Private key file provided in the email

### On the Azure VM (Pre-installed)

- Azure CLI
- kubectl
- helm
- kubelogin
- Jenkins server

## 🚀 Quick Start

### 1. Connect to the VM

```powershell
# Windows (PowerShell)
ssh -i path\to\your\keyfile azureuser@108.143.33.48

# Linux/Mac
chmod 600 /path/to/keyfile
ssh -i /path/to/keyfile azureuser@108.143.33.48
```

### 2. Verify Tools

```bash
# Check installed tools
az --version
kubectl version --client
helm version
```

### 3. Authenticate with Azure

```bash
# Login using managed identity
az login -i

# Verify login
az account show
```

### 4. Connect to AKS Cluster

```bash
# Get cluster credentials
az aks get-credentials -n devops-interview-aks -g devops-interview-rg

# Configure kubelogin
export KUBECONFIG=~/.kube/config
kubelogin convert-kubeconfig -l msi

# Verify connection
kubectl cluster-info
kubectl get nodes
```

### 5. Clone This Repository

```bash
# Clone your repo (after pushing to GitHub)
git clone https://github.com/YOUR_USERNAME/devops-interview-task.git
cd devops-interview-task
```

### 6. Deploy with Helm

```bash
# Update namespace in values.yaml (change 'rivka' to deploymenter's name)
cd helm-charts/simple-web

# Lint the chart
helm lint .

# Deploy
helm install simple-web . \
  --namespace YOUR_NAMESPACE \
  --create-namespace \
  --wait

# Check deployment
kubectl get all -n YOUR_NAMESPACE
kubectl get ingress -n YOUR_NAMESPACE
```

### 7. Get Access URL

```bash
# Get the Ingress IP
INGRESS_IP=$(kubectl get ingress simple-web-simple-web \
  -n YOUR_NAMESPACE \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Access your application at: http://$INGRESS_IP/rivka"
```

## 📦 Components

### 1. Helm Chart (`helm-charts/simple-web/`)

The Helm chart is production-ready with the following components:

#### Core Resources

- **Deployment**: Manages application pods with health checks
- **Service**: ClusterIP service for internal communication
- **Ingress**: NGINX ingress with path `/rivka`
- **ConfigMap**: Application configuration
- **ScaledObject**: KEDA autoscaling configuration

#### Key Files

```
simple-web/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Configuration values
├── templates/
│   ├── deployment.yaml     # Pod template and deployment
│   ├── service.yaml        # Kubernetes service
│   ├── ingress.yaml        # Ingress rules
│   ├── scaledobject.yaml   # KEDA autoscaling
│   ├── configmap.yaml      # Configuration
│   ├── pdb.yaml            # Pod Disruption Budget
│   ├── _helpers.tpl        # Template helpers
│   └── NOTES.txt           # Post-install instructions
└── .helmignore             # Files to ignore
```

### 2. KEDA Autoscaling

#### Configured Triggers

```yaml
# CPU-based scaling
- Trigger: cpu
  Target: 70% utilization
  
# Memory-based scaling
- Trigger: memory
  Target: 80% utilization

# Schedule-based scaling (8 AM - 12 PM)
- Trigger: cron
  Scale Up: 8:00 AM → 5 replicas
  Scale Down: 12:00 PM → 2 replicas
  Timezone: Asia/Jerusalem
```

#### How It Works

1. **CPU/Memory Monitoring**: KEDA watches resource utilization
2. **Automatic Scaling**: Scales between 2-10 replicas based on load
3. **Schedule Override**: Proactively scales up during business hours
4. **Cool-down Period**: 5-minute cool-down prevents flapping

**Why This Matters**: Auto-scaling ensures your application can handle traffic spikes while minimizing costs during low-traffic periods.

### 3. Ingress Configuration

```yaml
Path: /rivka
Type: Prefix
Backend: simple-web service on port 80
Annotations:
  - nginx.ingress.kubernetes.io/rewrite-target: /
  - nginx.ingress.kubernetes.io/ssl-redirect: false
```

**Path Rewriting**: Requests to `/rivka` are rewritten to `/` for the application.

## 🔧 Deployment Guide

### Manual Deployment

```bash
# 1. Update values.yaml with your namespace
sed -i 's/namespace: rivka/namespace: YOUR_NAME/' helm-charts/simple-web/values.yaml

# 2. Validate chart
helm lint helm-charts/simple-web/

# 3. Dry-run deployment
helm install simple-web helm-charts/simple-web/ \
  --namespace YOUR_NAME \
  --dry-run --debug

# 4. Deploy
helm install simple-web helm-charts/simple-web/ \
  --namespace YOUR_NAME \
  --create-namespace \
  --wait \
  --timeout 10m

# 5. Verify deployment
kubectl get all -n YOUR_NAME
helm status simple-web -n YOUR_NAME
```

### Verify Application

```bash
# Check pods
kubectl get pods -n YOUR_NAME -w

# Check ingress
kubectl get ingress -n YOUR_NAME

# Get logs
kubectl logs -f deployment/simple-web-simple-web -n YOUR_NAME

# Test locally (port-forward)
kubectl port-forward svc/simple-web-simple-web 8080:80 -n YOUR_NAME
curl http://localhost:8080
```

### Verify KEDA

```bash
# Check ScaledObject
kubectl get scaledobject -n YOUR_NAME

# Describe ScaledObject
kubectl describe scaledobject simple-web-simple-web -n YOUR_NAME

# Watch HPA created by KEDA
kubectl get hpa -n YOUR_NAME -w
```

## 🤖 Jenkins Setup

### Access Jenkins

```bash
# Jenkins should be running on the VM
# Get Jenkins initial admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword

# Access Jenkins at:
http://108.143.33.48:8080
```

### Configure Jenkins Job

1. **Create New Pipeline Job**
   - Click "New Item"
   - Enter name: "simple-web-deploy"
   - Select "Pipeline"
   - Click OK

2. **Configure Pipeline**
   - Under "Pipeline" section
   - Definition: "Pipeline script from SCM"
   - SCM: Git
   - Repository URL: Your GitHub repo URL
   - Credentials: Add GitHub credentials if private repo
   - Branch: */main
   - Script Path: Jenkinsfile

3. **Configure Parameters** (Should auto-populate from Jenkinsfile)
   - ACTION: deploy/destroy/rollback
   - NAMESPACE: your-namespace
   - IMAGE_TAG: latest
   - etc.

4. **Save and Build**

### Run Pipeline

```bash
# From Jenkins UI:
1. Click "Build with Parameters"
2. Select ACTION: deploy
3. Enter NAMESPACE: YOUR_NAME
4. Click "Build"

# Monitor the pipeline execution
# Check console output for details
```

### Jenkins Credentials

**After setup, provide these credentials:**

```
Jenkins URL: http://108.143.33.48:8080
Username: admin
Password: [Initial admin password or your set password]
```

## 🐍 Python Book Fetcher

### Overview

A professional Python application that:
- Fetches book data from Open Library API
- Validates data using Pydantic v2
- Filters books by custom criteria
- Exports to JSON (extensible to CSV, YAML, etc.)

### Installation

```bash
cd python-book-fetcher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Run the book fetcher
python book_fetcher.py

# Output will be saved to: output/filtered_books.json
```

### Customization

Edit the `main()` function in `book_fetcher.py`:

```python
# Change search query
search_query = "python programming"

# Modify filters
filters = [
    TitleContainsFilter("python", case_sensitive=False),
    YearRangeFilter(min_year=2010, max_year=2024),
    AuthorFilter("Lutz")  # Add author filter
]
```

### Architecture Highlights

**Design Patterns Used:**
- **Strategy Pattern**: For output formatters (easy to add CSV, XML, YAML)
- **Repository Pattern**: API client abstraction
- **Filter Chain**: Composable book filters

**Key Features:**
- Type hints throughout
- Pydantic validation
- Retry logic with exponential backoff
- Comprehensive error handling
- Extensive documentation
- Unit tests included

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest test_book_fetcher.py -v

# Run with coverage
pytest test_book_fetcher.py --cov=book_fetcher --cov-report=html
```

## 📊 Monitoring and Observability

### Built-in Monitoring Features

#### 1. Resource Monitoring

```bash
# Watch pod resources
kubectl top pods -n YOUR_NAME

# Watch node resources
kubectl top nodes
```

#### 2. KEDA Metrics

```bash
# View KEDA metrics
kubectl get --raw /apis/external.metrics.k8s.io/v1beta1 | jq .

# Watch scaling events
kubectl get events -n YOUR_NAME --watch
```

#### 3. Application Logs

```bash
# Stream logs
kubectl logs -f deployment/simple-web-simple-web -n YOUR_NAME

# Logs from all pods
kubectl logs -f -l app.kubernetes.io/name=simple-web -n YOUR_NAME
```

#### 4. Health Checks

The application includes:
- **Liveness Probe**: `/health` - restarts unhealthy containers
- **Readiness Probe**: `/ready` - removes unready pods from service

### Prometheus Integration (Optional Enhancement)

The Helm chart includes Prometheus annotations:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/metrics"
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl describe pod POD_NAME -n YOUR_NAME

# Common issues:
# - ImagePullBackOff: Check ACR access
# - CrashLoopBackOff: Check logs
```

#### 2. Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress simple-web-simple-web -n YOUR_NAME

# Verify ingress controller
kubectl get pods -n ingress-nginx

# Check if IP is assigned
kubectl get ingress -n YOUR_NAME
```

#### 3. KEDA Not Scaling

```bash
# Check KEDA operator
kubectl get pods -n keda

# Check ScaledObject status
kubectl describe scaledobject simple-web-simple-web -n YOUR_NAME

# Verify HPA
kubectl get hpa -n YOUR_NAME
```

#### 4. Authentication Issues

```bash
# Re-authenticate with Azure
az login -i
az account show

# Refresh AKS credentials
az aks get-credentials -n devops-interview-aks -g devops-interview-rg --overwrite-existing
kubelogin convert-kubeconfig -l msi
```

### Debug Commands

```bash
# Get all resources
kubectl get all -n YOUR_NAME

# Check events
kubectl get events -n YOUR_NAME --sort-by='.lastTimestamp'

# Shell into pod
kubectl exec -it POD_NAME -n YOUR_NAME -- /bin/sh

# Check resource quotas
kubectl describe resourcequota -n YOUR_NAME

# View pod logs (previous container)
kubectl logs POD_NAME -n YOUR_NAME --previous
```
**Purpose**: DevOps Engineer Deployment Task

