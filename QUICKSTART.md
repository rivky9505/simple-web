# 🚀 Quick Start Guide

Get your deployment running in 15 minutes!

## Prerequisites
- SSH key file from email
- GitHub account
- 15 minutes of focused time

## Step 1: Setup GitHub (5 minutes)

```bash
# 1. Create a new private repository on GitHub named: devops-interview-task

# 2. On your local machine, navigate to this directory
cd d:\task

# 3. Initialize git and push
git init
git add .
git commit -m "Initial commit: DevOps interview task"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/devops-interview-task.git
git push -u origin main

# 4. Verify your repository is accessible on GitHub
```

## Step 2: Connect to Azure VM (2 minutes)

```powershell
# Windows PowerShell
ssh -i C:\path\to\your\keyfile.pem azureuser@108.143.33.48
```

```bash
# Linux/Mac
chmod 600 /path/to/keyfile.pem
ssh -i /path/to/keyfile.pem azureuser@108.143.33.48
```

## Step 3: Setup Azure (3 minutes)

```bash
# Once connected to VM, run these commands:

# Authenticate with Azure
az login -i

# Connect to Kubernetes cluster
az aks get-credentials -n devops-interview-aks -g devops-interview-rg
export KUBECONFIG=~/.kube/config
kubelogin convert-kubeconfig -l msi

# Verify connection
kubectl cluster-info
kubectl get nodes

# Note: Replace "rivka" with your actual interviewer's name in the next steps
```

## Step 4: Deploy Application (5 minutes)

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/devops-interview-task.git
cd devops-interview-task

# IMPORTANT: Update the namespace
# Edit helm-charts/simple-web/values.yaml
# Change "namespace: rivka" to "namespace: YOUR_INTERVIEWER_NAME"
nano helm-charts/simple-web/values.yaml
# or
vim helm-charts/simple-web/values.yaml

# Deploy with Helm
helm install simple-web helm-charts/simple-web/ \
  --namespace YOUR_INTERVIEWER_NAME \
  --create-namespace \
  --wait

# Check deployment
kubectl get all -n YOUR_INTERVIEWER_NAME
```

## Step 5: Get Application URL

```bash
# Wait for Ingress IP (may take 2-5 minutes)
kubectl get ingress -n YOUR_INTERVIEWER_NAME -w

# Once you see an IP address, press Ctrl+C

# Get the URL
INGRESS_IP=$(kubectl get ingress simple-web-simple-web -n YOUR_INTERVIEWER_NAME -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Your application is at: http://$INGRESS_IP/rivka"

# Test in browser or curl
curl http://$INGRESS_IP/rivka
```

## ✅ Success Checklist

After deployment, verify:
- [ ] Pods are running: `kubectl get pods -n YOUR_NAME`
- [ ] Service is created: `kubectl get svc -n YOUR_NAME`
- [ ] Ingress has IP: `kubectl get ingress -n YOUR_NAME`
- [ ] Application is accessible via browser
- [ ] KEDA is configured: `kubectl get scaledobject -n YOUR_NAME`

## 🎯 Next Steps

### Setup Jenkins (Optional but Recommended)

```bash
# Get Jenkins URL
echo "http://108.143.33.48:8080"

# Get initial admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword

# Follow CHECKLIST.md section "Jenkins Setup" for complete instructions
```

### Test Python Application

```bash
cd python-book-fetcher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install and run
pip install -r requirements.txt
python book_fetcher.py

# Check output
cat output/filtered_books.json
```

## 🆘 Troubleshooting

### Pods not starting?
```bash
kubectl describe pod POD_NAME -n YOUR_NAME
kubectl logs POD_NAME -n YOUR_NAME
```

### Ingress IP still pending?
```bash
# Wait 5-10 minutes - it takes time
# Check ingress controller
kubectl get pods -n ingress-nginx
```

### Permission denied?
```bash
# Verify namespace
kubectl auth can-i create pods --namespace YOUR_NAME

# Re-authenticate if needed
az login -i
az aks get-credentials -n devops-interview-aks -g devops-interview-rg --overwrite-existing
kubelogin convert-kubeconfig -l msi
```

## 📚 Full Documentation

For detailed information:
- **Main README**: [README.md](README.md)
- **Azure Guide**: [docs/AZURE_SETUP_GUIDE.md](docs/AZURE_SETUP_GUIDE.md)
- **Commands**: [docs/COMMANDS.md](docs/COMMANDS.md)
- **Complete Checklist**: [CHECKLIST.md](CHECKLIST.md)
- **Interview Prep**: [docs/INTERVIEW_PREP.md](docs/INTERVIEW_PREP.md)

## 🎉 You're Done!

Your application is now running on Azure Kubernetes Service with:
- ✅ Helm deployment
- ✅ KEDA autoscaling
- ✅ Ingress routing
- ✅ Production-ready configuration

Prepare for your interview with [docs/INTERVIEW_PREP.md](docs/INTERVIEW_PREP.md)!
