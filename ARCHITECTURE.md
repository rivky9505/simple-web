# Architecture Diagrams

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Internet                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ HTTPS (Public IP)
                         │
            ┌────────────▼────────────┐
            │   Azure Load Balancer   │
            │    (Ingress Managed)    │
            └────────────┬────────────┘
                         │
        ┌────────────────┴────────────────┐
        │    NGINX Ingress Controller     │
        │      Path: /rivka → /           │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │   Kubernetes Service            │
        │   (ClusterIP: simple-web)       │
        │   Port: 80 → 8080               │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────────────────┐
        │         Deployment: simple-web              │
        │    ┌──────────┬──────────┬──────────┐      │
        │    │  Pod 1   │  Pod 2   │  Pod N   │      │
        │    │ (8080)   │ (8080)   │ (8080)   │      │
        │    └──────────┴──────────┴──────────┘      │
        │         Replicas: 2-10 (KEDA)              │
        └─────────────────────────────────────────────┘
                         ▲
                         │ Scales based on:
                         │
        ┌────────────────┴────────────────┐
        │      KEDA ScaledObject          │
        │  • CPU: 70%                     │
        │  • Memory: 80%                  │
        │  • Schedule: 8AM-12PM           │
        └─────────────────────────────────┘
```

## Component Interaction Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ 1. HTTP Request
       │    http://<IP>/rivka
       ▼
┌──────────────────┐
│  Azure Ingress   │
│  (Public IP)     │
└──────┬───────────┘
       │ 2. Route to
       │    Ingress Controller
       ▼
┌──────────────────┐
│  NGINX Ingress   │
│  Controller      │
└──────┬───────────┘
       │ 3. Path rewrite
       │    /rivka → /
       ▼
┌──────────────────┐
│  K8s Service     │
│  (simple-web)    │
└──────┬───────────┘
       │ 4. Load balance
       │    across pods
       ▼
┌──────────────────┐
│  Pod(s)          │
│  Port 8080       │
└──────┬───────────┘
       │ 5. Return
       │    response
       ▼
    [User]
```

## KEDA Autoscaling Flow

```
┌─────────────────────────────────────────────────────┐
│              KEDA Operator                          │
│  (Watches metrics and creates/updates HPA)          │
└───────┬────────────┬────────────┬───────────────────┘
        │            │            │
        │            │            │
    ┌───▼───┐   ┌────▼────┐  ┌───▼────┐
    │  CPU  │   │ Memory  │  │Schedule│
    │ 70%   │   │  80%    │  │8AM-12PM│
    └───┬───┘   └────┬────┘  └───┬────┘
        │            │            │
        └────────────┴────────────┘
                     │
                     │ Creates/Updates
                     ▼
        ┌────────────────────────┐
        │  HPA (Horizontal Pod   │
        │   Autoscaler)          │
        └────────────┬───────────┘
                     │
                     │ Scales
                     ▼
        ┌────────────────────────┐
        │  Deployment            │
        │  Replicas: 2-10        │
        └────────────────────────┘
```

## CI/CD Pipeline Flow

```
┌──────────────┐
│  Developer   │
│  git push    │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│   GitHub Repository  │
└──────┬───────────────┘
       │
       │ Webhook/Poll
       │
       ▼
┌──────────────────────────────────────────────────┐
│           Jenkins Pipeline                       │
│                                                  │
│  1. Checkout Code                                │
│       ↓                                          │
│  2. Validate & Lint Helm Chart                   │
│       ↓                                          │
│  3. Authenticate with Azure (Managed Identity)   │
│       ↓                                          │
│  4. Connect to AKS Cluster                       │
│       ↓                                          │
│  5. Deploy/Upgrade with Helm                     │
│       ↓                                          │
│  6. Wait for Rollout                             │
│       ↓                                          │
│  7. Run Smoke Tests                              │
│       ↓                                          │
│  8. Success! ✓                                   │
│                                                  │
│  (If failure: Automatic Rollback)               │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│   AKS Cluster                │
│   Namespace: <interviewer>   │
│   - Deployment                │
│   - Service                   │
│   - Ingress                   │
│   - ScaledObject             │
└──────────────────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────┐
│          Security Layers (Defense in Depth)     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Layer 1: Network                               │
│  ├── Namespace isolation                        │
│  ├── Ingress path-based routing                 │
│  └── Service mesh ready                         │
│                                                 │
│  Layer 2: Kubernetes RBAC                       │
│  ├── Namespace-scoped permissions               │
│  ├── Least privilege principle                  │
│  └── Managed identity (no credentials)          │
│                                                 │
│  Layer 3: Pod Security                          │
│  ├── Security contexts                          │
│  ├── Non-root user (UID 1000)                   │
│  ├── Read-only root filesystem                  │
│  └── Pod Disruption Budget                      │
│                                                 │
│  Layer 4: Container Security                    │
│  ├── Dropped capabilities                       │
│  ├── Private registry (ACR)                     │
│  ├── Resource limits                            │
│  └── Health checks                              │
│                                                 │
│  Layer 5: Application                           │
│  ├── Input validation                           │
│  ├── Error handling                             │
│  └── Logging (no sensitive data)                │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Resource Flow

```
┌─────────────────────────────────────────────────┐
│              Kubernetes Resources               │
├─────────────────────────────────────────────────┤
│                                                 │
│  Helm Chart                                     │
│     │                                           │
│     ├──► Deployment                             │
│     │      ├── Pods (2-10 replicas)             │
│     │      ├── Resource Limits                  │
│     │      │   ├── CPU: 500m                    │
│     │      │   └── Memory: 512Mi                │
│     │      ├── Security Context                 │
│     │      │   ├── runAsUser: 1000              │
│     │      │   ├── readOnlyRootFilesystem       │
│     │      │   └── capabilities: drop ALL       │
│     │      └── Health Checks                    │
│     │           ├── Liveness: /health           │
│     │           └── Readiness: /ready           │
│     │                                           │
│     ├──► Service (ClusterIP)                    │
│     │      ├── Port: 80                         │
│     │      └── TargetPort: 8080                 │
│     │                                           │
│     ├──► Ingress                                │
│     │      ├── Path: /rivka                     │
│     │      ├── Rewrite: /                       │
│     │      └── Backend: Service:80              │
│     │                                           │
│     ├──► ScaledObject (KEDA)                    │
│     │      ├── Min: 2                           │
│     │      ├── Max: 10                          │
│     │      └── Triggers:                        │
│     │          ├── CPU: 70%                     │
│     │          ├── Memory: 80%                  │
│     │          └── Schedule: 8AM-12PM           │
│     │                                           │
│     ├──► ConfigMap                              │
│     │      └── App configuration                │
│     │                                           │
│     └──► PodDisruptionBudget                    │
│            └── minAvailable: 1                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Python Application Architecture

```
┌─────────────────────────────────────────────────┐
│        Python Book Fetcher Architecture         │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────┐                              │
│  │  Main (CLI)   │                              │
│  └───────┬───────┘                              │
│          │                                      │
│          ▼                                      │
│  ┌────────────────────┐                         │
│  │   BookFetcher      │  (Orchestrator)         │
│  └────┬───────────┬───┘                         │
│       │           │                             │
│       │           │                             │
│   ┌───▼───┐   ┌───▼────────┐                   │
│   │Client │   │ Formatter  │  (Strategy)        │
│   │       │   │            │                    │
│   │ ┌─────▼───┴─┐  ┌──────▼────┐               │
│   │ │OpenLibrary│  │JSONFormat │               │
│   │ │  Client   │  │           │               │
│   │ └─────┬─────┘  └───────────┘               │
│   │       │                                     │
│   │       │ Uses                                │
│   │       ▼                                     │
│   │  ┌─────────────┐                            │
│   │  │  Pydantic   │  (Validation)              │
│   │  │   Models    │                            │
│   │  │  - Book     │                            │
│   │  │  - Author   │                            │
│   │  └─────────────┘                            │
│   │                                             │
│   │  ┌─────────────┐                            │
│   └─►│   Filters   │  (Chain of Resp.)          │
│      │  - Title    │                            │
│      │  - Year     │                            │
│      │  - Author   │                            │
│      └─────────────┘                            │
│                                                 │
│  Design Patterns Used:                          │
│  • Strategy Pattern: Output formatters          │
│  • Repository Pattern: API client               │
│  • Chain of Responsibility: Filters             │
│  • Dependency Injection: Client & formatter     │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Deployment States

```
Initial State:
┌──────────────┐
│  No Resources│
└──────────────┘

After "helm install":
┌────────────────────────────────────────┐
│  Namespace Created                     │
│  ├── Deployment (2 replicas)           │
│  ├── Service                            │
│  ├── Ingress (IP pending)              │
│  ├── ScaledObject                       │
│  ├── ConfigMap                          │
│  └── PodDisruptionBudget               │
└────────────────────────────────────────┘

Steady State (Normal Traffic):
┌────────────────────────────────────────┐
│  Replicas: 2-3                          │
│  CPU: 30-50%                            │
│  Memory: 40-60%                         │
│  Status: Healthy ✓                      │
└────────────────────────────────────────┘

Peak Hours (8 AM - 12 PM):
┌────────────────────────────────────────┐
│  Replicas: 5 (schedule-triggered)      │
│  CPU: 50-70%                            │
│  Memory: 50-70%                         │
│  Status: Scaling ⚡                     │
└────────────────────────────────────────┘

High Load (Auto-scaled):
┌────────────────────────────────────────┐
│  Replicas: 8-10                         │
│  CPU: 70%+ (trigger threshold)         │
│  Memory: 80%+ (trigger threshold)      │
│  Status: Maximum capacity ⚠             │
└────────────────────────────────────────┘

After "helm uninstall":
┌──────────────┐
│  Cleaned Up  │
│  (Resources  │
│   removed)   │
└──────────────┘
```

## Data Flow - Python Application

```
1. User Runs: python book_fetcher.py
                    │
                    ▼
2. BookFetcher.fetch_and_filter()
                    │
                    ▼
3. OpenLibraryClient.search_books()
                    │
                    ├──► API Request
                    │    https://openlibrary.org/search.json?q=python
                    │
                    ◄──┤ API Response (JSON)
                    │
                    ▼
4. Parse & Validate with Pydantic
                    │
                    ├──► APIResponse model
                    │    ├── numFound
                    │    ├── start
                    │    └── docs[]
                    │
                    ├──► Book models (for each doc)
                    │    ├── title
                    │    ├── authors[]
                    │    ├── first_publish_year
                    │    └── ...
                    │
                    ▼
5. Apply Filters
                    │
                    ├──► TitleContainsFilter("python")
                    │    100 books → 75 books
                    │
                    ├──► YearRangeFilter(2010-2024)
                    │    75 books → 45 books
                    │
                    ▼
6. Format Output
                    │
                    ├──► JSONFormatter.format()
                    │    ├── Add metadata
                    │    ├── Convert to dict
                    │    └── Pretty print JSON
                    │
                    ▼
7. Write to File
                    │
                    └──► output/filtered_books.json
                          {
                            "metadata": {...},
                            "books": [...]
                          }
```

## Monitoring & Observability

```
┌─────────────────────────────────────────────────┐
│          Observability Stack (Ready)            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Metrics (Prometheus Ready)                     │
│  ├── Pod annotations:                           │
│  │   prometheus.io/scrape: "true"               │
│  │   prometheus.io/port: "8080"                 │
│  │   prometheus.io/path: "/metrics"             │
│  └── Available metrics:                         │
│      ├── CPU usage                              │
│      ├── Memory usage                           │
│      ├── Request rate                           │
│      └── Response time                          │
│                                                 │
│  Logs (kubectl logs)                            │
│  ├── Structured logging                         │
│  ├── Log levels: INFO, WARNING, ERROR           │
│  └── No sensitive data                          │
│                                                 │
│  Health Checks                                  │
│  ├── Liveness: /health (restart if fails)       │
│  └── Readiness: /ready (remove from service)    │
│                                                 │
│  Events (kubectl get events)                    │
│  ├── Pod lifecycle                              │
│  ├── Scaling events                             │
│  └── Error events                               │
│                                                 │
└─────────────────────────────────────────────────┘
```

These diagrams help visualize:
- System architecture
- Component interactions
- Data flow
- Security layers
- Deployment states
- Autoscaling behavior

Use them during your interview to explain your solution visually!
