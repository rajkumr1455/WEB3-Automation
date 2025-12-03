#!/bin/bash
# Bootstrap E2E Test Environment (Bash)
# Starts Docker services and waits for health

HEALTH_TIMEOUT=120
RETRY_INTERVAL=5

echo "🚀 Starting E2E Test Environment..."

# Check Docker is running
echo "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker."
    exit 1
fi

# Start services
echo "Starting Docker Compose services..."
docker compose -f docker-compose.yml up -d \
    qdrant \
    llm-router \
    orchestrator \
    recon-agent \
    static-agent \
    fuzzing-agent \
    monitoring-agent \
    triage-agent \
    reporting-agent \
    address-scanner \
    guardrail \
    validator-worker \
    mlops-engine \
    signature-generator \
    remediator \
    streaming-indexer \
    web-ui

if [ $? -ne 0 ]; then
    echo "❌ Failed to start services"
    exit 1
fi

# Wait for services to be healthy
echo "Waiting for services to be healthy (timeout: ${HEALTH_TIMEOUT}s)..."

declare -A services=(
    ["qdrant"]="6333:/"
    ["llm-router"]="8000:/health"
    ["orchestrator"]="8001:/health"
    ["address-scanner"]="8008:/health"
    ["guardrail"]="8009:/health"
    ["validator-worker"]="8010:/health"
    ["mlops-engine"]="8011:/health"
    ["signature-generator"]="8012:/health"
    ["remediator"]="8013:/health"
    ["streaming-indexer"]="8014:/health"
    ["web-ui"]="3001:/"
)

start_time=$(date +%s)
all_healthy=false

while [ "$all_healthy" = false ] && [ $(($(date +%s) - start_time)) -lt $HEALTH_TIMEOUT ]; do
    all_healthy=true
    
    for service in "${!services[@]}"; do
        IFS=':' read -r port path <<< "${services[$service]}"
        url="http://localhost:${port}${path}"
        
        if curl -sf -m 2 "$url" > /dev/null 2>&1; then
            echo "✓ $service is healthy"
        else
            echo "⏳ Waiting for $service..."
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = false ]; then
        sleep $RETRY_INTERVAL
    fi
done

if [ "$all_healthy" = false ]; then
    echo "❌ Services failed to become healthy within ${HEALTH_TIMEOUT}s"
    echo "Check logs with: docker compose logs"
    exit 1
fi

echo "✅ All services are healthy!"
echo ""
echo "Run tests with:"
echo "  pytest tests/backend -v"
echo "  npx playwright test"
echo ""
echo "Teardown with:"
echo "  docker compose down --volumes"
