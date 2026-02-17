#!/bin/bash
# Quick deployment script for Autonomous Artist

set -e

echo "════════════════════════════════════════════════════════════"
echo "  Autonomous Artist - Quick Deployment"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your API keys:"
        echo "   - HUGGINGFACE_API_KEY (required)"
        echo "   - FACEBOOK_PAGE_ACCESS_TOKEN (optional)"
        echo "   - IMGUR_CLIENT_ID (optional)"
        echo ""
        echo "Edit .env file now? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            ${EDITOR:-nano} .env
        fi
    else
        echo "❌ .env.example not found. Please create a .env file manually."
        exit 1
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Building Docker Image"
echo "════════════════════════════════════════════════════════════"
docker-compose build

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Starting Services"
echo "════════════════════════════════════════════════════════════"
docker-compose up -d

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Waiting for application to start..."
echo "════════════════════════════════════════════════════════════"
sleep 10

# Health check
echo "Running health check..."
if curl -f http://localhost:5001/health > /dev/null 2>&1; then
    echo "✅ Application is healthy!"
else
    echo "⚠️  Health check failed. Checking logs..."
    docker-compose logs --tail=50 app
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT SUCCESSFUL!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Application is running at:"
echo "  🌐 http://localhost:5001"
echo ""
echo "Available endpoints:"
echo "  - Health check: http://localhost:5001/health"
echo "  - Metrics: http://localhost:5001/metrics"
echo "  - Web UI: http://localhost:5001/"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f app"
echo "  - Stop: docker-compose down"
echo "  - Restart: docker-compose restart"
echo "  - Rebuild: docker-compose up -d --build"
echo ""
echo "For production deployment with SSL, see DEPLOYMENT.md"
echo "════════════════════════════════════════════════════════════"
