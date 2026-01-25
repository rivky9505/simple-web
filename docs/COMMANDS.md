# Common Commands Reference

## Quick Access

```bash
# Source configuration
source ~/.devops-config

# Or set manually
export AKS_CLUSTER="devops-interview-aks"
export RESOURCE_GROUP="devops-interview-rg"
export NAMESPACE="YOUR_NAME"
export KUBECONFIG=~/.kube/config
```

## Azure Commands

### Authentication
```bash
# Login with managed identity
az login -i

# Show current account
az account show

# List subscriptions
az account list --output table
```

### AKS Operations
```bash
# Get AKS credentials
az aks get-credentials -n $AKS_CLUSTER -g $RESOURCE_GROUP

# Configure kubelogin
kubelogin convert-kubeconfig -l msi

# Show AKS cluster details
az aks show -n $AKS_CLUSTER -g $RESOURCE_GROUP

# List AKS clusters
az aks list --output table
```

### ACR Operations
```bash
# Show registry
az acr show --name acrinterview

# List repositories
az acr repository list --name acrinterview

# List image tags
az acr repository show-tags --name acrinterview --repository simple-web

# Login to ACR
az acr login --name acrinterview
```

## Kubernetes Commands

### Cluster Info
```bash
# Cluster information
kubectl cluster-info

# Get nodes
kubectl get nodes

# Get all namespaces
kubectl get namespaces
```

### Working with Your Namespace
```bash
# Create namespace
kubectl create namespace $NAMESPACE

# Get all resources in namespace
kubectl get all -n $NAMESPACE

# Get pods
kubectl get pods -n $NAMESPACE

# Watch pods
kubectl get pods -n $NAMESPACE -w

# Describe pod
kubectl describe pod POD_NAME -n $NAMESPACE

# Get logs
kubectl logs -f POD_NAME -n $NAMESPACE

# Get logs from all pods with label
kubectl logs -f -l app.kubernetes.io/name=simple-web -n $NAMESPACE

# Execute command in pod
kubectl exec -it POD_NAME -n $NAMESPACE -- /bin/sh
```

### Services and Ingress
```bash
# Get services
kubectl get svc -n $NAMESPACE

# Get ingress
kubectl get ingress -n $NAMESPACE

# Describe ingress
kubectl describe ingress simple-web-simple-web -n $NAMESPACE

# Get ingress IP
kubectl get ingress simple-web-simple-web -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### Port Forwarding (for testing)
```bash
# Forward service port to local
kubectl port-forward svc/simple-web-simple-web 8080:80 -n $NAMESPACE

# Then access: http://localhost:8080
```

### Events and Debugging
```bash
# Get events in namespace
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'

# Watch events
kubectl get events -n $NAMESPACE --watch

# Describe deployment
kubectl describe deployment simple-web-simple-web -n $NAMESPACE
```

## Helm Commands

### Basic Operations
```bash
# Install chart
helm install simple-web ./helm-charts/simple-web/ --namespace $NAMESPACE --create-namespace

# Upgrade chart
helm upgrade simple-web ./helm-charts/simple-web/ --namespace $NAMESPACE

# Install or upgrade
helm upgrade simple-web ./helm-charts/simple-web/ --install --namespace $NAMESPACE

# Uninstall release
helm uninstall simple-web --namespace $NAMESPACE
```

### Chart Management
```bash
# Lint chart
helm lint ./helm-charts/simple-web/

# Validate chart
helm template simple-web ./helm-charts/simple-web/ --namespace $NAMESPACE --validate

# Dry-run
helm install simple-web ./helm-charts/simple-web/ --namespace $NAMESPACE --dry-run --debug

# Show rendered templates
helm template simple-web ./helm-charts/simple-web/ --namespace $NAMESPACE
```

### Release Management
```bash
# List releases
helm list -n $NAMESPACE

# Show release status
helm status simple-web -n $NAMESPACE

# Show release history
helm history simple-web -n $NAMESPACE

# Rollback to previous version
helm rollback simple-web -n $NAMESPACE

# Rollback to specific revision
helm rollback simple-web 1 -n $NAMESPACE

# Get release values
helm get values simple-web -n $NAMESPACE

# Get release manifest
helm get manifest simple-web -n $NAMESPACE
```

### Override Values
```bash
# Install with custom values
helm install simple-web ./helm-charts/simple-web/ \
  --namespace $NAMESPACE \
  --set image.tag=v1.2.3 \
  --set replicaCount=5

# Install with values file
helm install simple-web ./helm-charts/simple-web/ \
  --namespace $NAMESPACE \
  --values custom-values.yaml
```

## KEDA Commands

### Check KEDA
```bash
# Check KEDA operator
kubectl get pods -n keda

# Get ScaledObjects
kubectl get scaledobject -n $NAMESPACE

# Describe ScaledObject
kubectl describe scaledobject simple-web-simple-web -n $NAMESPACE

# Get HPA (created by KEDA)
kubectl get hpa -n $NAMESPACE

# Describe HPA
kubectl describe hpa keda-hpa-simple-web-simple-web -n $NAMESPACE
```

### Watch Autoscaling
```bash
# Watch HPA
kubectl get hpa -n $NAMESPACE -w

# Watch pods (see scaling in action)
kubectl get pods -n $NAMESPACE -w
```

## Monitoring Commands

### Resource Usage
```bash
# Top nodes
kubectl top nodes

# Top pods in namespace
kubectl top pods -n $NAMESPACE

# Top specific pod
kubectl top pod POD_NAME -n $NAMESPACE
```

### Application Health
```bash
# Check deployment status
kubectl rollout status deployment/simple-web-simple-web -n $NAMESPACE

# Check replica status
kubectl get deployment simple-web-simple-web -n $NAMESPACE

# Check pod readiness
kubectl get pods -n $NAMESPACE -o wide
```

## Troubleshooting Commands

### Debug Pods
```bash
# Get pod details
kubectl describe pod POD_NAME -n $NAMESPACE

# Get logs
kubectl logs POD_NAME -n $NAMESPACE

# Get previous logs (if pod restarted)
kubectl logs POD_NAME -n $NAMESPACE --previous

# Stream logs
kubectl logs -f POD_NAME -n $NAMESPACE

# Logs from specific container
kubectl logs POD_NAME -c CONTAINER_NAME -n $NAMESPACE
```

### Debug Services
```bash
# Test service connectivity
kubectl run test-pod --image=busybox:1.28 --rm -it --restart=Never -n $NAMESPACE -- /bin/sh

# Inside the pod:
wget -O- http://simple-web-simple-web:80
```

### Debug Ingress
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress controller logs
kubectl logs -f deployment/ingress-nginx-controller -n ingress-nginx

# Test ingress from within cluster
kubectl run test-curl --image=curlimages/curl:7.85.0 --rm -it --restart=Never -n $NAMESPACE -- curl -v http://INGRESS_IP/rivka
```

## Useful One-Liners

```bash
# Get all pod names
kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}'

# Get all container images
kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].spec.containers[*].image}'

# Check if pods are ready
kubectl get pods -n $NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Get Ingress IP
INGRESS_IP=$(kubectl get ingress simple-web-simple-web -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "http://$INGRESS_IP/rivka"

# Delete all failed pods
kubectl delete pods --field-selector status.phase=Failed -n $NAMESPACE

# Force delete stuck pod
kubectl delete pod POD_NAME -n $NAMESPACE --grace-period=0 --force

# Get pod restart count
kubectl get pods -n $NAMESPACE -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[*].restartCount}{"\n"}{end}'
```

## Git Commands (for this project)

```bash
# Initial setup
git init
git add .
git commit -m "Initial commit: DevOps interview task"

# Create GitHub repo (via web UI), then:
git remote add origin https://github.com/YOUR_USERNAME/devops-interview-task.git
git branch -M main
git push -u origin main

# Update and push changes
git add .
git commit -m "Update deployment configuration"
git push

# Create a release tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Jenkins Commands (if using CLI)

```bash
# Get Jenkins CLI
wget http://108.143.33.48:8080/jnlpJars/jenkins-cli.jar

# Build job
java -jar jenkins-cli.jar -s http://108.143.33.48:8080/ build simple-web-deploy

# Build with parameters
java -jar jenkins-cli.jar -s http://108.143.33.48:8080/ build simple-web-deploy \
  -p ACTION=deploy \
  -p NAMESPACE=YOUR_NAME \
  -p IMAGE_TAG=latest
```
