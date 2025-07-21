#!/bin/bash

set -e

MEMORY=4000 # in MB
CPUS=4
DISK_SIZE=50g

echo "Setting up Minikube with ${MEMORY}MB RAM, ${CPUS} CPUs, and ${DISK_SIZE} disk..."

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
    curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-darwin-arm64
    sudo install minikube-darwin-arm64 /usr/local/bin/minikube
    rm -f minikube-darwin-arm64 

fi

# Check if minikube is already running
if minikube status | grep -q "Running"; then
    echo "Minikube is already running. Stopping and restarting..."
    minikube stop
fi

# Start minikube with specified resources
minikube start --cpus $CPUS --memory $MEMORY --disk-size=$DISK_SIZE --driver=docker

# Enable necessary addons
minikube addons enable storage-provisioner
minikube addons enable default-storageclass

# Verify installation
kubectl get nodes
kubectl get pods -A

echo "Kubernetes setup complete."