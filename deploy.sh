#!/bin/bash

# Safe Python Execution Service - Google Cloud Run Deployment Script
# This script builds and deploys the service to Google Cloud Run

set -e

# Configuration - Set these environment variables or edit as needed
PROJECT_ID=${PROJECT_ID:-"python-executor-20250901"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="safe-python-executor"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Deploying Safe Python Execution Service to Google Cloud Run"
echo "================================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    echo "   Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set the project
echo "Setting project to: ${PROJECT_ID}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Configure Docker to use gcloud as a credential helper
echo "Configuring Docker authentication..."
gcloud auth configure-docker

# Build the Docker image
echo "Building Docker image..."
docker build --platform linux/amd64 -t ${IMAGE_NAME} .

# Push the image to Google Container Registry
echo "Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 10 \
    --max-instances 10 \
    --set-env-vars "ENVIRONMENT=production" \
    --description "Safe Python Script Execution Service using nsjail"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo "Deployment completed successfully!"
echo "================================================================"
echo "Service URL: ${SERVICE_URL}"
echo "Health Check: ${SERVICE_URL}/health"
echo "Execute Endpoint: ${SERVICE_URL}/execute"
echo ""

# Test the deployment
echo "Testing the deployment..."
echo "Testing health check..."
curl -s "${SERVICE_URL}/health" | jq '.' || echo "Health check failed or jq not installed"

echo ""
echo "Example cURL commands:"
echo "================================================================"
echo "# Health check"
echo "curl ${SERVICE_URL}/health"
echo ""
echo "# Execute simple script"
echo 'curl -X POST '${SERVICE_URL}'/execute \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"script": "def main():\n    return {\"message\": \"Hello from Cloud Run!\"}"}'"'"''
echo ""
echo "# Test with pandas/numpy"
echo 'curl -X POST '${SERVICE_URL}'/execute \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"script": "import numpy as np\ndef main():\n    data = np.random.randn(10)\n    return {\"mean\": float(np.mean(data)), \"data\": data.tolist()}"}'"'"''
echo ""

echo ""
echo "Security Features:"
echo "- nsjail sandboxing with strict resource limits"
echo "- Memory limit: 1GB per execution"
echo "- CPU limit: 300 seconds per execution"
echo "- Seccomp filtering for system calls"
echo "- Non-root execution"
echo ""
echo "Documentation: ${SERVICE_URL}/health"
echo "================================================================" 