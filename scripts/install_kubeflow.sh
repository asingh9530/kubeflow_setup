#!/bin/bash

set -e

KFP_VERSION=2.5.0 # Specify the Kubeflow Pipelines version to install

echo "Installing Kubeflow Pipelines version ${KFP_VERSION}..."

# Install Kubeflow Pipelines
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$KFP_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic?ref=$KFP_VERSION"

# Wait for KFP to be ready
echo "Waiting for Kubeflow Pipelines to be ready..."
kubectl wait --for=condition=ready pod -l app=ml-pipeline -n kubeflow --timeout=300s || true

# Wait a bit more to ensure all pods are running
echo "Waiting for all Kubeflow components to be ready..."
sleep 30

# Check the status of pods
kubectl get pods -n kubeflow

# Set up port forwarding in the background
echo "Setting up port forwarding for the Kubeflow UI to http://localhost:8080"
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80 &
PF_PID=$!

# Save the port forwarding PID to a file so we can terminate it later if needed
echo $PF_PID > .port_forward_pid

echo "Kubeflow Pipelines installation complete."
echo "If the UI is not accessible, you may need to manually run:"
echo "kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80"