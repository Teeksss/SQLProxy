#!/bin/bash

# Exit on error
set -e

# Variables
ENVIRONMENT=$1
TAG=$2
CONFIG_FILE=".env.${ENVIRONMENT}"

# Validate input
if [ -z "$ENVIRONMENT" ] || [ -z "$TAG" ]; then
    echo "Usage: $0 <environment> <tag>"
    echo "Example: $0 staging v1.0.0"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file $CONFIG_FILE not found!"
    exit 1
fi

# Load environment variables
set -a
source "$CONFIG_FILE"
set +a

# Pull latest image
docker pull ghcr.io/teeksss/sqlproxy:$TAG

# Deploy with docker-compose
TAG=$TAG docker-compose -f docker-compose.yml up -d

# Wait for health checks
echo "Waiting for services to be healthy..."
sleep 10

# Verify deployment
if docker-compose ps | grep -q "unhealthy"; then
    echo "Deployment failed - unhealthy containers detected!"
    docker-compose logs
    exit 1
fi

echo "Deployment successful!"