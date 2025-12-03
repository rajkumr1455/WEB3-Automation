#!/bin/bash
# Run Tests in Isolated Docker Environment

# Build test image
echo "Building test Docker image..."
docker build -t web3-tests:latest -f tests/Dockerfile .

if [ $? -ne 0 ]; then
    echo "Failed to build test image"
    exit 1
fi

# Start test services
echo "Starting test services..."
docker-compose -f tests/docker-compose.test.yml up -d \
    address-scanner \
    guardrail \
    validator-worker \
    mlops-engine \
    signature-generator \
    remediator \
    streaming-indexer

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 15

# Run tests
echo "Running backend tests..."
docker-compose -f tests/docker-compose.test.yml run --rm backend-tests

testExitCode=$?

# Cleanup
echo "Cleaning up test environment..."
docker-compose -f tests/docker-compose.test.yml down --volumes

if [ $testExitCode -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed with exit code $testExitCode"
fi

exit $testExitCode
