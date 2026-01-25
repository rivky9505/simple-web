# Deployment Challenges and Solutions

## Project Overview
Deployed a Helm chart for the `simple-web` application to Azure Kubernetes Service (AKS) with:
- **Namespace**: rivkak
- **Image**: acrinterview.azurecr.io/simple-web:latest
- **Ingress Path**: /rivka
- **KEDA Autoscaling**: CPU, Memory, and Schedule-based
- **Jenkins Pipeline**: Deploy/Destroy/Rollback options

---

## Challenge 1: RBAC Permission Denied for PodDisruptionBudget

### Issue
```
Error: INSTALLATION FAILED: poddisruptionbudgets.policy is forbidden: 
User "ec9066ee-58aa-4a40-b565-a6b6b117eee2" cannot create resource "poddisruptionbudgets"
```

### Root Cause
The managed identity used for deployment lacked permissions to create PodDisruptionBudget resources in the cluster.

### Solution
Disabled PodDisruptionBudget in the Helm deployment:
```bash
helm install simple-web helm-charts/simple-web/ \
  --set podDisruptionBudget.enabled=false
```

### Lesson Learned
Always verify RBAC permissions before deploying resources. For production environments, work with cluster administrators to grant necessary permissions.

---

## Challenge 2: Pods Crashing with CrashLoopBackOff (Exit Code 0)

### Issue
Pods continuously restarted with status `Completed` and Exit Code 0:
```
State:          Waiting
  Reason:       CrashLoopBackOff
Last State:     Terminated
  Reason:       Completed
  Exit Code:    0
```

### Root Cause
The Python application script (`index.py`) has a bare exception handler that silently exits:
```python
except:
    exit()
```

The script was failing to start properly but exiting cleanly, making debugging difficult.

### Investigation Steps
1. Checked pod logs: `kubectl logs pod/simple-web-xxx -n rivkak` (empty output)
2. Examined pod description: `kubectl describe pod simple-web-xxx -n rivkak`
3. Launched interactive debug pod: `kubectl run -it --rm debug --image=... -- sh`
4. Manually tested the script inside the pod: `python /code/index.py 0.0.0.0 80`

### Discovery
The script successfully ran when executed manually, indicating the issue was with the deployment configuration, not the application itself.

---

## Challenge 3: Port Binding and Security Context Conflicts

### Issue
The application needed to bind to port 80, but the security context prevented this:
- Security context set `runAsNonRoot: true` and `runAsUser: 1000`
- Non-root users cannot bind to privileged ports (< 1024)

### Root Cause
Conflicting requirements:
- Helm chart configured for port 8080 (`service.targetPort: 8080`)
- Application Dockerfile CMD runs on port 80: `CMD python index.py`
- Security context prevented binding to port 80

### Solution
1. Changed service target port to 80: `--set service.targetPort=80`
2. Disabled non-root requirement: `--set securityContext.runAsNonRoot=false`
3. Updated deployment template to conditionally apply security context

### Lesson Learned
Always check the application's default port configuration in the Dockerfile and ensure deployment manifests align with it.

---

## Challenge 4: Read-Only Filesystem Preventing Application Writes

### Issue
The Python application writes state files during operation:
- `index.html` - Generated HTML content
- `pickle_data.txt` - Request tracking data

The security context set `readOnlyRootFilesystem: true`, preventing these writes.

### Root Cause
The application needs write access to `/code` directory to create and update files, but the security hardening prevented this.

### Solution
Disabled read-only root filesystem:
```bash
--set securityContext.readOnlyRootFilesystem=false
```

Updated deployment template to conditionally apply this setting:
```yaml
{{- if .Values.securityContext.readOnlyRootFilesystem }}
securityContext:
  readOnlyRootFilesystem: {{ .Values.securityContext.readOnlyRootFilesystem }}
{{- end }}
```

### Lesson Learned
Balance security hardening with application requirements. If read-only filesystem is required, mount specific writable volumes for application data.

---

## Challenge 5: Volume Mount Overwriting Application Files

### Issue
Initial attempt to fix write permissions by mounting emptyDir volume at `/code`:
```yaml
volumeMounts:
  - name: code
    mountPath: /code
volumes:
  - name: code
    emptyDir: {}
```

This caused error:
```
python: can't open file 'index.py': [Errno 2] No such file or directory
```

### Root Cause
Mounting an emptyDir at `/code` overwrote the application files baked into the Docker image, leaving an empty directory.

### Solution
Removed the `/code` volume mount and relied on disabling `readOnlyRootFilesystem` instead:
```bash
sed -i '/- name: code/,+1d' deployment.yaml
```

### Lesson Learned
Never mount volumes over directories containing application code. Use volume mounts only for:
- Temporary files (`/tmp`)
- Cache directories
- User data directories
- Configuration overrides

---

## Challenge 6: Health Check Failures

### Issue
Health checks configured for `/health` and `/ready` endpoints, but the simple Python HTTP server doesn't provide these endpoints.

### Solution
Temporarily disabled health checks during initial deployment:
```bash
--set healthCheck.liveness.enabled=false \
--set healthCheck.readiness.enabled=false
```

### Future Enhancement
For production:
1. Modify the Python application to provide health check endpoints
2. Or change health checks to TCP socket checks on port 80
3. Re-enable with appropriate `initialDelaySeconds` to allow startup time

---

## Challenge 7: KEDA Autoscaling with Unhealthy Pods

### Issue
With KEDA autoscaling enabled, the HPA couldn't get metrics from unhealthy pods:
```
Warning  FailedGetResourceMetric  failed to get cpu utilization: unable to get metrics
```

### Solution
Temporarily disabled autoscaling during troubleshooting:
```bash
--set autoscaling.enabled=false
```

### Next Steps
Once pods are stable:
1. Re-enable autoscaling: `autoscaling.enabled=true`
2. Verify metrics-server is working: `kubectl top pods -n rivkak`
3. Test CPU/Memory scaling triggers
4. Verify schedule-based scaling (8AM-12PM)

---

## Challenge 8: Old ReplicaSets Not Being Cleaned Up

### Issue
After multiple failed deployments, old ReplicaSets remained active, causing pods to use outdated configurations even after Helm upgrade.

### Solution
Force cleanup and reinstall:
```bash
kubectl delete replicaset -n rivkak --all
helm uninstall simple-web -n rivkak
helm install simple-web helm-charts/simple-web/ ...
```

### Lesson Learned
When debugging deployment issues, sometimes a clean slate is needed. Use `helm uninstall` followed by `helm install` instead of repeated `helm upgrade` commands.

---

## Final Working Configuration

### Helm Install Command
```bash
helm install simple-web helm-charts/simple-web/ \
  --namespace rivkak \
  --set podDisruptionBudget.enabled=false \
  --set autoscaling.enabled=false \
  --set securityContext.readOnlyRootFilesystem=false \
  --set securityContext.runAsNonRoot=false \
  --set service.targetPort=80 \
  --set healthCheck.liveness.enabled=false \
  --set healthCheck.readiness.enabled=false
```

### Verification
```bash
# Check pods are running
kubectl get pods -n rivkak

# Verify logs show HTTP server started
kubectl logs -n rivkak -l app.kubernetes.io/name=simple-web

# Get Ingress IP
kubectl get ingress -n rivkak

# Find LoadBalancer external IP
kubectl get svc -A | grep LoadBalancer

# Test application
curl http://<EXTERNAL-IP>/rivka
```

---

## Remaining Tasks

### 1. Upload Helm Chart to GitHub
- [ ] Create private GitHub repository
- [ ] Push Helm charts to repository
- [ ] Verify access from Jenkins

### 2. Configure Jenkins Pipeline
- [ ] Set up GitHub credentials in Jenkins
- [ ] Configure pipeline to pull from GitHub
- [ ] Test deploy/destroy/rollback actions

### 3. Enable Production Features
- [ ] Re-enable KEDA autoscaling
- [ ] Add proper health check endpoints or use TCP checks
- [ ] Enable PodDisruptionBudget (after RBAC permissions granted)
- [ ] Restore security hardening (runAsNonRoot, readOnlyRootFilesystem)
- [ ] Configure proper ingress DNS with TLS

### 4. Testing
- [ ] Verify public IP access to /rivka path
- [ ] Test KEDA CPU scaling under load
- [ ] Test KEDA memory scaling
- [ ] Verify schedule-based scaling (8AM-12PM)
- [ ] Test Jenkins deploy/destroy/rollback

---

## Key Takeaways

1. **Start Simple**: Disable advanced features (security contexts, health checks, autoscaling) during initial debugging
2. **Understand the Application**: Review Dockerfile and application code to understand ports, file writes, and dependencies
3. **Debug Interactively**: Use `kubectl run -it` to test applications interactively before deploying
4. **Check Logs Carefully**: Silent failures (Exit Code 0) can be the hardest to debug
5. **Volume Mounts Are Dangerous**: Never mount volumes over application code directories
6. **RBAC Matters**: Verify permissions before deploying resources
7. **Clean Slate Approach**: Sometimes `uninstall` + `install` is faster than debugging failed upgrades

---

## Architecture Decisions

### Why Disable Security Features?
For this interview/demo environment, we prioritized getting the application running over security hardening. In production:
- Work with security team to allow necessary permissions
- Refactor application to run as non-root user on unprivileged port (>1024)
- Use init containers to prepare writable directories with proper ownership

### Why Disable Health Checks?
The legacy Python application doesn't provide health endpoints. Options for production:
1. Add health endpoints to the application
2. Use TCP socket checks instead of HTTP checks
3. Use `exec` probes to check process status

### Why Disable Autoscaling During Debugging?
KEDA requires healthy pods to collect metrics. Once base deployment is stable, re-enable autoscaling incrementally.

---

## Monitoring and Troubleshooting Commands

```bash
# Watch pod status
kubectl get pods -n rivkak -w

# View pod logs
kubectl logs -n rivkak <pod-name>
kubectl logs -n rivkak -l app.kubernetes.io/name=simple-web --tail=100

# Describe pod for events
kubectl describe pod -n rivkak <pod-name>

# Get namespace events
kubectl get events -n rivkak --sort-by='.lastTimestamp'

# Check deployment status
helm status simple-web -n rivkak
helm list -n rivkak

# Interactive debugging
kubectl exec -it -n rivkak <pod-name> -- bash

# Port forward for local testing
kubectl port-forward -n rivkak svc/simple-web 8080:80

# Check Ingress
kubectl get ingress -n rivkak
kubectl describe ingress simple-web -n rivkak

# Check KEDA ScaledObject (when enabled)
kubectl get scaledobject -n rivkak
kubectl describe scaledobject simple-web -n rivkak
```

---

*Document created: January 25-26, 2026*
*Last updated: January 26, 2026*
