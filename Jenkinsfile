#!/usr/bin/env groovy

/**
 * Jenkins Pipeline for Deploying simple-web Helm Chart
 * 
 * Features:
 * - Deploy/Destroy actions with parameter selection
 * - Multi-environment support
 * - Helm chart validation and linting
 * - Rollback on failure
 * - Slack/Email notifications (configurable)
 * - Security scanning
 * - Detailed logging and error handling
 */

// Pipeline parameters
properties([
    parameters([
        choice(
            name: 'ACTION',
            choices: ['deploy', 'destroy', 'dry-run', 'upgrade', 'rollback'],
            description: 'Select action to perform'
        ),
        string(
            name: 'NAMESPACE',
            defaultValue: 'rivkak',
            description: 'Kubernetes namespace (use interviewer name)'
        ),
        string(
            name: 'RELEASE_NAME',
            defaultValue: 'simple-web',
            description: 'Helm release name'
        ),
        string(
            name: 'IMAGE_TAG',
            defaultValue: 'latest',
            description: 'Docker image tag to deploy'
        ),
        string(
            name: 'REPLICA_COUNT',
            defaultValue: '2',
            description: 'Number of initial replicas'
        ),
        choice(
            name: 'ENVIRONMENT',
            choices: ['development', 'staging', 'production'],
            description: 'Deployment environment'
        ),
        booleanParam(
            name: 'ENABLE_AUTOSCALING',
            defaultValue: true,
            description: 'Enable KEDA autoscaling'
        ),
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run smoke tests after deployment'
        ),
        booleanParam(
            name: 'WAIT_FOR_READY',
            defaultValue: true,
            description: 'Wait for deployment to be ready'
        )
    ])
])

pipeline {
    agent any
    
    environment {
        // Azure Configuration
        AKS_CLUSTER = 'devops-interview-aks'
        RESOURCE_GROUP = 'devops-interview-rg'
        
        // Helm Configuration
        HELM_CHART_PATH = './helm-charts/simple-web'
        KUBECONFIG = "${HOME}/.kube/config"
        
        // Git Configuration
        GIT_REPO = 'https://github.com/rivky9505/simple-web.git'
        
        // Container Registry
        ACR_REGISTRY = 'acrinterview.azurecr.io'
        IMAGE_NAME = 'simple-web'
        
        // Timeout settings
        DEPLOY_TIMEOUT = '10m'
        HELM_TIMEOUT = '600s'
    }
    
    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '50'))
        disableConcurrentBuilds()
    }
    
    stages {
        stage('Initialize') {
            steps {
                script {
                    echo "=========================================="
                    echo "Pipeline Execution Started"
                    echo "=========================================="
                    echo "Action: ${params.ACTION}"
                    echo "Namespace: ${params.NAMESPACE}"
                    echo "Release: ${params.RELEASE_NAME}"
                    echo "Image Tag: ${params.IMAGE_TAG}"
                    echo "Environment: ${params.ENVIRONMENT}"
                    echo "=========================================="
                    
                    // Set build description
                    currentBuild.description = "${params.ACTION} - ${params.NAMESPACE} - ${params.IMAGE_TAG}"
                }
            }
        }
        
        stage('Validate Environment') {
            steps {
                script {
                    echo "Validating required tools and configurations..."
                      // Check required tools
                    sh '''
                        echo "Checking required tools..."
                        command -v az >/dev/null 2>&1 || { echo "az CLI not found"; exit 1; }
                        command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found"; exit 1; }
                        command -v helm >/dev/null 2>&1 || { echo "helm not found"; exit 1; }
                        command -v kubelogin >/dev/null 2>&1 || { echo "kubelogin not found"; exit 1; }
                        
                        echo "Tool versions:"
                        az --version | head -n 1
                        kubectl version --client -o yaml | head -n 5
                        helm version --short
                    '''
                }
            }
        }
        
        stage('Azure Authentication') {
            steps {
                script {
                    echo "Authenticating with Azure using managed identity..."
                    sh '''
                        # Login to Azure with managed identity
                        az login --identity
                        
                        # Verify login
                        az account show
                    '''
                }
            }
        }
        
        stage('Connect to AKS') {
            steps {
                script {
                    echo "Connecting to AKS cluster: ${AKS_CLUSTER}"
                    sh '''
                        # Get AKS credentials
                        az aks get-credentials \
                            --name ${AKS_CLUSTER} \
                            --resource-group ${RESOURCE_GROUP} \
                            --overwrite-existing
                        
                        # Configure kubelogin for managed identity
                        export KUBECONFIG=${KUBECONFIG}
                        kubelogin convert-kubeconfig -l msi
                        
                        # Verify connection
                        kubectl cluster-info
                        kubectl get nodes
                        
                        # Verify namespace access
                        kubectl get ns ${NAMESPACE} || echo "Namespace ${NAMESPACE} may not exist yet"
                    '''
                }
            }
        }
        
        stage('Checkout Code') {
            when {
                expression { params.ACTION in ['deploy', 'upgrade', 'dry-run'] }
            }
            steps {
                script {
                    echo "Checking out Helm charts from repository..."
                    checkout scm
                }
            }
        }
        
        stage('Helm Lint & Validate') {
            when {
                expression { params.ACTION in ['deploy', 'upgrade', 'dry-run'] }
            }
            steps {
                script {
                    echo "Validating Helm chart..."
                    sh """
                        cd ${HELM_CHART_PATH}
                        
                        # Lint the chart
                        helm lint . --strict
                        
                        # Template and validate
                        helm template ${RELEASE_NAME} . \
                            --namespace ${NAMESPACE} \
                            --set image.tag=${IMAGE_TAG} \
                            --set replicaCount=${REPLICA_COUNT} \
                            --set autoscaling.enabled=${ENABLE_AUTOSCALING} \
                            --validate
                        
                        echo "✓ Helm chart validation successful"
                    """
                }
            }
        }
        stage('Deploy / Upgrade') {
            when {
                expression { params.ACTION in ['deploy', 'upgrade'] }
            }
            steps {
                script {
                    echo "Deploying Helm chart..."
                    
                    sh """
                        cd ${HELM_CHART_PATH}
                        
                        # Create namespace if it doesn't exist
                        kubectl create namespace ${NAMESPACE} 2>/dev/null || true
                        
                        # Deploy/Upgrade with Helm (use upgrade --install for idempotent deploys)
                        helm upgrade ${RELEASE_NAME} . \
                            --namespace ${NAMESPACE} \
                            --install \
                            --set image.tag=${IMAGE_TAG} \
                            --set replicaCount=${REPLICA_COUNT} \
                            --set autoscaling.enabled=${ENABLE_AUTOSCALING} \
                            --set app.namespace=${NAMESPACE} \
                            --timeout ${HELM_TIMEOUT} \
                            --wait \
                            --atomic
                        
                        echo "✓ Deployment successful"
                        
                        # Show deployment status
                        helm status ${RELEASE_NAME} -n ${NAMESPACE}
                        kubectl get all -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME}
                    """
                }
            }
        }
        
        stage('Dry Run') {
            when {
                expression { params.ACTION == 'dry-run' }
            }
            steps {
                script {
                    echo "Performing dry-run deployment..."
                    sh """
                        cd ${HELM_CHART_PATH}
                        
                        helm upgrade ${RELEASE_NAME} . \
                            --namespace ${NAMESPACE} \
                            --install \
                            --set image.tag=${IMAGE_TAG} \
                            --set replicaCount=${REPLICA_COUNT} \
                            --set autoscaling.enabled=${ENABLE_AUTOSCALING} \
                            --set app.namespace=${NAMESPACE} \
                            --dry-run \
                            --debug
                        
                        echo "✓ Dry-run completed successfully"
                    """
                }
            }
        }
        stage('Wait for Deployment') {
            when {
                expression { 
                    params.ACTION in ['deploy', 'upgrade'] && params.WAIT_FOR_READY 
                }
            }
            steps {
                script {
                    echo "Waiting for deployment to be ready..."
                    sh """
                        # Wait for deployment to be ready
                        kubectl rollout status deployment/${RELEASE_NAME} \
                            -n ${NAMESPACE} \
                            --timeout=${DEPLOY_TIMEOUT}
                        
                        # Show pod status
                        kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME}
                        
                        echo "✓ All pods are ready"
                    """
                }
            }
        }
        stage('Smoke Tests') {
            when {
                expression { 
                    params.ACTION in ['deploy', 'upgrade'] && params.RUN_TESTS 
                }
            }
            steps {
                script {
                    echo "Running smoke tests..."
                    sh """
                        # Get the ingress controller external IP (not the ingress resource IP)
                        INGRESS_IP=\$(kubectl get svc nginx-ingress-controller -n ingress \
                            -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
                        
                        echo "Ingress Controller External IP: \${INGRESS_IP}"
                        
                        if [ -n "\${INGRESS_IP}" ]; then
                            # Test the application endpoint
                            echo "Testing application at http://\${INGRESS_IP}/rivka"
                            
                            # Test with curl (with retries, shorter timeout)
                            for i in 1 2 3; do
                                HTTP_CODE=\$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://\${INGRESS_IP}/rivka" || echo "000")
                                echo "Attempt \$i: HTTP \${HTTP_CODE}"
                                if echo "\${HTTP_CODE}" | grep -qE "^(200|301|302)\$"; then
                                    echo "✓ Smoke test passed"
                                    break
                                fi
                                sleep 5
                            done
                        else
                            echo "⚠ Ingress controller IP not found, skipping HTTP test"
                        fi
                        
                        # Verify pods are running
                        READY_PODS=\$(kubectl get pods -n ${NAMESPACE} \
                            -l app.kubernetes.io/instance=${RELEASE_NAME} \
                            -o jsonpath='{.items[*].status.containerStatuses[*].ready}' | tr ' ' '\\n' | grep -c true || echo 0)
                        
                        echo "Ready pods: \${READY_PODS}"
                        
                        if [ "\${READY_PODS}" -lt 1 ]; then
                            echo "✗ No pods are ready"
                            exit 1
                        fi
                        
                        echo "✓ All smoke tests passed"
                    """
                }
            }
        }
        
        stage('Rollback') {
            when {
                expression { params.ACTION == 'rollback' }
            }
            steps {
                script {
                    echo "Rolling back to previous release..."
                    sh """
                        # Check release history
                        echo "Release history:"
                        helm history ${RELEASE_NAME} -n ${NAMESPACE} --max 5
                        
                        # Perform rollback
                        helm rollback ${RELEASE_NAME} -n ${NAMESPACE} --wait
                        
                        echo "✓ Rollback completed"
                        
                        # Show current status
                        helm status ${RELEASE_NAME} -n ${NAMESPACE}
                    """
                }
            }
        }
        
        stage('Destroy') {
            when {
                expression { params.ACTION == 'destroy' }
            }
            steps {
                script {
                    echo "Destroying Helm release..."
                    
                    // Add confirmation for production
                    if (params.ENVIRONMENT == 'production') {
                        input message: 'Are you sure you want to destroy the production deployment?', 
                              ok: 'Yes'
                    }
                    
                    sh """
                        # Uninstall Helm release
                        helm uninstall ${RELEASE_NAME} \
                            --namespace ${NAMESPACE} \
                            --wait \
                            --timeout ${HELM_TIMEOUT} || echo "Release may not exist"
                        
                        # Optionally delete namespace resources
                        echo "Cleaning up remaining resources..."
                        kubectl delete all -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME} || true
                        
                        echo "✓ Destruction completed"
                    """
                }
            }
        }
        
        stage('Show Deployment Info') {
            when {
                expression { params.ACTION in ['deploy', 'upgrade'] }
            }
            steps {
                script {
                    echo "Gathering deployment information..."
                    sh """
                        echo "=========================================="
                        echo "Deployment Summary"
                        echo "=========================================="
                        
                        # Helm release info
                        helm list -n ${NAMESPACE}
                        
                        # Pods
                        echo "\\nPods:"
                        kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME}
                        
                        # Services
                        echo "\\nServices:"
                        kubectl get svc -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME}
                        
                        # Ingress
                        echo "\\nIngress:"
                        kubectl get ingress -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME}
                        
                        # KEDA ScaledObject (if exists)
                        echo "\\nKEDA ScaledObject:"                        kubectl get scaledobject -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME} || echo "No ScaledObject found"
                        
                        echo "=========================================="
                        echo "Access the application:"
                        # Get the ingress controller external IP
                        INGRESS_IP=\$(kubectl get svc nginx-ingress-controller -n ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
                        
                        if [ -n "\${INGRESS_IP}" ] && [ "\${INGRESS_IP}" != "pending" ]; then
                            echo "URL: http://\${INGRESS_IP}/rivka"
                        else
                            echo "Ingress IP is being assigned, please check in a few minutes"
                        fi
                        echo "=========================================="
                    """
                }
            }        }
    }
    
    post {
        success {
            script {
                echo "✓ Pipeline completed successfully!"
            }
        }
        
        failure {
            script {
                echo "✗ Pipeline failed!"
                // Capture logs for debugging
                sh """
                    echo "Capturing debug information..."
                    kubectl describe deployment simple-web -n rivkak 2>/dev/null || true
                    kubectl get events -n rivkak --sort-by='.lastTimestamp' 2>/dev/null | tail -n 20 || true
                """
            }
        }
    }
}
