# Molecular Dynamics Pipeline

This project implements a Kubeflow Pipeline for molecular dynamics simulations using AmberTools and BioContainers.

## Project Structure

- `pipelines/`: Contains compiled pipeline YAML files
- `scripts/`: Contains setup scripts for Kubernetes and Kubeflow
- `src/`: Contains the pipeline source code

## Dependencies

- Minikube (for local Kubernetes cluster)
- kubectl
- Python 3.8+
- Python packages:
  - kfp (v2.13.0)
  - kfp-pipeline-spec (v0.6.0)
  - kfp-server-api (v2.4.0)

## Setup Instructions

### Option 1 using startup script

```bash
chmod +x setup.sh
bash setup.sh
```

### Option 2 Manually

#### 1. Set up Kubernetes with Minikube

Run the following script to install and configure Minikube:

```bash
chmod +x scripts/setup_k8s.sh
bash scripts/setup_k8s.sh
```

#### 2. Install kubeflow pipeline on minikube cluster

Run following to setup kubeflow

```bash
chmod +x scripts/install_kubeflow.sh
bash scripts/install_kubeflow.sh
```

#### 3. Install kfp dependencies

Run Following to install dependencies

```bash
pip install -r requirements.txt
```

## Troubleshooting

If port forwarding stops, restart it with:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80 &
```

Check Kubeflow Pipelines pods with:

```bash
kubectl get pods -n kubeflow
```

Check pod logs:

```bash
kubectl logs -n kubeflow pod-name
```

## Run pipeline

```bash
python src/iso_pipeline.py
```
