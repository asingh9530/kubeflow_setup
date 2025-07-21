### 4. Optional startup script for the root directory

You could also create a single startup script in the root directory that runs both setup scripts:

```bash
#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up environment for Molecular Dynamics Pipeline...${NC}"

# installing dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Make scripts executable
chmod +x scripts/setup_k8s.sh
chmod +x scripts/install_kubeflow.sh

# Run setup scripts
echo -e "${YELLOW}Setting up Kubernetes...${NC}"
./scripts/setup_k8s.sh

echo -e "${YELLOW}Installing Kubeflow Pipelines...${NC}"
./scripts/install_kubeflow.sh

echo -e "${GREEN}Setup complete! You can now run the pipeline.${NC}"
echo -e "${YELLOW}Access the Kubeflow Pipelines UI at: http://localhost:8080${NC}"