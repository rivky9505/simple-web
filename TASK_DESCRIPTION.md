# DevOps Interview Task

## Overview

Following the last interview, this is the technical task assignment.

> If you encounter any issues, feel free to ask for help to release any blockers.

---

## 🖥️ VM Remote Access

| Property | Value |
|----------|-------|
| **IP Address** | 108.143.33.48 |
| **Username** | azureuser |
| **Key file** | attached to the mail |

> **NOTE**: Your user has sudo permissions

---

## 🔧 Environment Setup

### 1. Connect to the VM

Connect by SSH to the VM with the key file:

```bash
ssh -i rivkak.pem azureuser@108.143.33.48
```

The VM already has the following tools installed:
- Jenkins server
- az CLI
- helm
- kubectl
- kubelogin

### 2. Login to Azure

Login to Azure using "managed identity":

```bash
az login -i
```

### 3. Connect to Kubernetes Cluster

| Property | Value |
|----------|-------|
| **AKS name** | devops-interview-aks |
| **Resource group** | devops-interview-rg |

```bash
az aks get-credentials -n devops-interview-aks -g devops-interview-rg
export KUBECONFIG=~/.kube/config
kubelogin convert-kubeconfig -l msi
```

---

## 📋 TASK

### Task 1: Helm Chart & Deployment

Create and deploy a helm chart for the following application:

| Property | Value |
|----------|-------|
| **Image** | simple-web |
| **Registry** | acrinterview.azurecr.io |
| **Namespace** | `<Interviewer Name>` (you will have permission to create resources only for this namespace) |

**Requirements:**
- ✅ Add the Helm chart to your own private GitHub repo
- ✅ Check that the access is working from the public IP to the simple-web

### Task 2: Ingress & KEDA Autoscaling

Add to the helm charts:
- **Ingress rule** (Ingress deployment is already installed on the cluster)
- **KEDA auto-scaler** (KEDA deployment is already installed on the cluster)

**KEDA should auto-scale by:**
1. Memory + CPU metrics
2. Schedule between **8:00 AM - 12:00 PM**

**Ingress Configuration:**
- The ingress rule path should be `/rivka`

### Task 3: Jenkins Pipeline

Create a Jenkins pipeline for deploying the helm chart from the GitHub repo with:
- Deploy option
- Destroy option

---

## 🐍 Python Task – Small Book Fetcher (Pydantic + API Call)

Create a small Python script or module that performs the following:

### 1. API Integration

Call a public API that returns book-related data.

**Example:** Open Library API
```
https://openlibrary.org/search.json?q=python
```

> You may choose a different public API if you prefer.

### 2. Pydantic Model

Define a Pydantic model (or models) that represents the relevant part of the response.

Choose the fields you consider important:
- title
- author
- year
- etc.

### 3. Implementation Requirements

Implement code that:
1. Fetches the data from the API
2. Validates/parses it into Pydantic models
3. Returns a filtered list of books based on **2 criteria of your choice**
   - e.g., title contains a keyword
   - e.g., books from a specific year

### 4. Output

- Write the filtered results to a **JSON file**
- Structure the code in a way that makes it easy to add additional output formats in the future
  - For example: separating the output logic, or designing a small formatter interface
- **Note:** You only need to implement JSON output for this task

---

## 📤 Submission

Once finished, please send:
1. ✅ Link to your GitHub repo
2. ✅ Login credentials for accessing your created Jenkins

---

## 📞 Contact

If you have any questions or concerns, feel free to reach out.

---

**Good luck!!!**

--  
*Best Regards,*  
*Omri Ziner | DevOps Engineer | omrizi@etoro.com*  
*eToro - Your Social Investment Network*
