#!/bin/bash
# Build script for AWS Lambda Docker image

set -e

echo "=================================="
echo "Building AWS Lambda Docker Image"
echo "=================================="

# Configuration
IMAGE_NAME="xbrl-validator"
IMAGE_TAG="latest"
DOCKERFILE="Dockerfile.lambda"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Build the image
echo ""
echo "Building Docker image..."
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Dockerfile: ${DOCKERFILE}"
echo ""

docker build -f "${DOCKERFILE}" -t "${IMAGE_NAME}:${IMAGE_TAG}" .

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "Build completed successfully!"
    echo "=================================="
    echo ""
    echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "Next steps:"
    echo "1. Test locally:"
    echo "   docker run -p 9000:8080 ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "2. Tag for ECR:"
    echo "   docker tag ${IMAGE_NAME}:${IMAGE_TAG} <account-id>.dkr.ecr.<region>.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "3. Push to ECR:"
    echo "   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "See AWS_LAMBDA_DEPLOYMENT.md for complete deployment instructions."
else
    echo ""
    echo "=================================="
    echo "Build failed!"
    echo "=================================="
    exit 1
fi
