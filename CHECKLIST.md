# Simple Web Helm Deployment - Deployment Checklist

## Pre-Deployment Checklist

### 1. Repository Setup
- [ ] Create private GitHub repository: `devops-interview-task`
- [ ] Clone this code to your repository
- [ ] Update README.md with your GitHub username
- [ ] Push all code to GitHub
- [ ] Verify repository is accessible

### 2. Update Configuration Files
- [ ] Update `helm-charts/simple-web/values.yaml`:
  - [ ] Change `namespace: rivka` to deploymenter's name
  - [ ] Verify image registry: `acrinterview.azurecr.io`
  - [ ] Verify image name: `simple-web`
- [ ] Update `Jenkinsfile`:
  - [ ] Change `GIT_REPO` URL to your GitHub repository
  - [ ] Verify namespace default value
- [ ] Update scripts with correct namespace if needed

### 3. Local Machine Setup
- [ ] Download SSH key file from email
- [ ] Save key file securely (e.g., `C:\keys\azure-key.pem`)
- [ ] Test SSH connection to VM:
  ```powershell
  # Windows
  ssh -i C:\path\to\keyfile azureuser@108.143.33.48
  ```
  ```bash
  # Linux/Mac
  chmod 600 /path/to/keyfile
  ssh -i /path/to/keyfile azureuser@108.143.33.48
  ```

## VM Setup Checklist

### 4. Initial VM Connection
- [ ] Connect to VM via SSH
- [ ] Verify you're logged in as `azureuser`
- [ ] Check home directory: `pwd` → should show `/home/azureuser`

### 5. Azure Authentication
- [ ] Run: `az login -i`
- [ ] Verify successful login
- [ ] Check account: `az account show`
- [ ] Note subscription ID for reference

### 6. AKS Cluster Connection
- [ ] Get AKS credentials:
  ```bash
  az aks get-credentials -n devops-interview-aks -g devops-interview-rg
  ```
- [ ] Configure kubelogin:
  ```bash
  export KUBECONFIG=~/.kube/config
  kubelogin convert-kubeconfig -l msi
  ```
- [ ] Test connection: `kubectl cluster-info`
- [ ] View nodes: `kubectl get nodes`
- [ ] Check namespaces: `kubectl get namespaces`

### 7. Verify Tools
- [ ] Check az CLI: `az --version`
- [ ] Check kubectl: `kubectl version --client`
- [ ] Check helm: `helm version`
- [ ] Check kubelogin: `kubelogin --version`

### 8. Verify Cluster Components
- [ ] Check KEDA: `kubectl get pods -n keda`
- [ ] Check Ingress: `kubectl get pods -n ingress-nginx` or `kubectl get ingressclass`
- [ ] Check ACR access: `az acr show --name acrinterview`
- [ ] Check permissions:
  ```bash
  kubectl auth can-i create pods --namespace YOUR_NAME
  kubectl auth can-i create deployments --namespace YOUR_NAME
  kubectl auth can-i create services --namespace YOUR_NAME
  ```

## Deployment Checklist

### 9. Clone Repository on VM
- [ ] Generate SSH key on VM (if using SSH): `ssh-keygen -t ed25519 -C "your_email@example.com"`
- [ ] Add SSH key to GitHub account
- [ ] Clone repository:
  ```bash
  git clone git@github.com:YOUR_USERNAME/devops-interview-task.git
  cd devops-interview-task
  ```
- [ ] Or use HTTPS if preferred:
  ```bash
  git clone https://github.com/YOUR_USERNAME/devops-interview-task.git
  cd devops-interview-task
  ```

### 10. Deploy with Helm
- [ ] Navigate to project: `cd devops-interview-task`
- [ ] Validate Helm chart: `helm lint helm-charts/simple-web/`
- [ ] Dry-run deployment:
  ```bash
  helm install simple-web helm-charts/simple-web/ \
    --namespace YOUR_NAME \
    --dry-run --debug
  ```
- [ ] Deploy application:
  ```bash
  helm install simple-web helm-charts/simple-web/ \
    --namespace YOUR_NAME \
    --create-namespace \
    --wait \
    --timeout 10m
  ```
- [ ] Check deployment status: `helm status simple-web -n YOUR_NAME`

### 11. Verify Deployment
- [ ] Check pods: `kubectl get pods -n YOUR_NAME`
- [ ] Check services: `kubectl get svc -n YOUR_NAME`
- [ ] Check ingress: `kubectl get ingress -n YOUR_NAME`
- [ ] Check KEDA: `kubectl get scaledobject -n YOUR_NAME`
- [ ] Check logs: `kubectl logs -f deployment/simple-web-simple-web -n YOUR_NAME`
- [ ] Wait for pods to be ready (may take 2-5 minutes)

### 12. Get Application URL
- [ ] Get Ingress IP:
  ```bash
  kubectl get ingress simple-web-simple-web -n YOUR_NAME -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
  ```
- [ ] Wait for IP to be assigned (may take 5-10 minutes)
- [ ] Test URL in browser: `http://[INGRESS_IP]/rivka`
- [ ] Verify application is accessible

## Jenkins Setup Checklist

### 13. Access Jenkins
- [ ] Get Jenkins URL: `http://108.143.33.48:8080`
- [ ] Get initial admin password:
  ```bash
  sudo cat /var/lib/jenkins/secrets/initialAdminPassword
  ```
- [ ] Login to Jenkins
- [ ] Complete initial setup wizard (if first time)
- [ ] Install suggested plugins

### 14. Configure Jenkins Pipeline
- [ ] Click "New Item"
- [ ] Name: `simple-web-deploy`
- [ ] Type: "Pipeline"
- [ ] Under "Pipeline" section:
  - [ ] Definition: "Pipeline script from SCM"
  - [ ] SCM: Git
  - [ ] Repository URL: Your GitHub repository
  - [ ] Branch: `*/main`
  - [ ] Script Path: `Jenkinsfile`
- [ ] Save configuration

### 15. Test Jenkins Pipeline
- [ ] Click "Build with Parameters"
- [ ] Set parameters:
  - ACTION: `deploy`
  - NAMESPACE: `YOUR_NAME`
  - RELEASE_NAME: `simple-web`
  - IMAGE_TAG: `latest`
  - ENVIRONMENT: `development`
- [ ] Click "Build"
- [ ] Monitor console output
- [ ] Verify successful deployment

### 16. Test Destroy Action
- [ ] Build with parameters:
  - ACTION: `destroy`
  - NAMESPACE: `YOUR_NAME`
- [ ] Verify resources are cleaned up
- [ ] Re-deploy with ACTION: `deploy`

## Python Application Checklist

### 17. Python Book Fetcher Setup
- [ ] On VM or locally, navigate to: `cd python-book-fetcher`
- [ ] Create virtual environment:
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run application: `python book_fetcher.py`
- [ ] Verify output file: `output/filtered_books.json`
- [ ] Check JSON file contains filtered books

### 18. Run Python Tests
- [ ] Install test dependencies: `pip install pytest pytest-cov`
- [ ] Run tests: `pytest test_book_fetcher.py -v`
- [ ] Verify all tests pass
- [ ] Generate coverage report: `pytest test_book_fetcher.py --cov=book_fetcher --cov-report=html`

## Final Verification Checklist

### 19. Complete System Test
- [ ] Application accessible via Ingress
- [ ] Pods running and healthy
- [ ] KEDA autoscaling configured
- [ ] Jenkins pipeline working (deploy/destroy)
- [ ] Python script running and producing output
- [ ] All tests passing

### 20. Documentation Check
- [ ] README.md is complete and accurate
- [ ] All scripts are executable (`chmod +x scripts/*.sh`)
- [ ] Commands work as documented
- [ ] GitHub repository is well-organized

### 21. Monitoring and Observability
- [ ] Check pod metrics: `kubectl top pods -n YOUR_NAME`
- [ ] View KEDA status: `kubectl describe scaledobject -n YOUR_NAME`
- [ ] Check events: `kubectl get events -n YOUR_NAME --sort-by='.lastTimestamp'`
- [ ] Verify health checks are working

## Submission Checklist

### 22. Prepare Submission
- [ ] GitHub repository URL
- [ ] Jenkins credentials:
  - URL: `http://108.143.33.48:8080`
  - Username: `admin`
  - Password: [Your Jenkins password]
- [ ] Application URL: `http://[INGRESS_IP]/rivka`
- [ ] Namespace used: [YOUR_NAME]
- [ ] Any additional notes or instructions

### 23. Create Submission Document
Create a file `SUBMISSION.md` with:
```markdown
# Simple Web Helm Deployment Submission

## Repository
- GitHub URL: https://github.com/YOUR_USERNAME/devops-interview-task

## Jenkins Access
- URL: http://108.143.33.48:8080
- Username: admin
- Password: [YOUR_PASSWORD]
- Pipeline Name: simple-web-deploy

## Application Access
- URL: http://[INGRESS_IP]/rivka
- Namespace: YOUR_NAME
- Cluster: devops-interview-aks
- Resource Group: devops-interview-rg

## Deployment Status
- Helm Release: simple-web
- Pods Running: X/X
- KEDA Autoscaling: Enabled
- Ingress: Configured

## Python Application
- Location: python-book-fetcher/
- Output: output/filtered_books.json
- Tests: All passing

## Additional Notes
[Any additional information, challenges faced, or improvements made]
```

### 24. Final Review
- [ ] All checklist items completed
- [ ] Application working correctly
- [ ] Documentation is clear
- [ ] Code is clean and well-commented
- [ ] Ready for presentation

## Troubleshooting

If you encounter issues, refer to:
- `docs/AZURE_SETUP_GUIDE.md` - Azure-specific help
- `docs/COMMANDS.md` - Command reference

Common issues:
- **Pods not starting**: Check `kubectl describe pod POD_NAME -n YOUR_NAME`
- **Ingress IP pending**: Wait 5-10 minutes, it takes time to provision
- **Permission denied**: Verify you're using the correct namespace
- **Authentication failed**: Re-run `az login -i` and kubelogin setup

## Time Estimates

- Repository setup: 15 minutes
- VM connection and Azure setup: 15 minutes
- Helm deployment: 20 minutes
- Jenkins setup: 30 minutes
- Python application: 15 minutes
- Testing and verification: 30 minutes
- Documentation: 15 minutes

**Total estimated time: 2-3 hours**

---

Good luck with deployment! 🚀
