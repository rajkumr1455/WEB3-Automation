"""
Test configuration - Service URLs
"""
import os

# Determine if running in Docker or locally
IS_DOCKER = os.path.exists('/.dockerenv')

# Service URLs - use Docker service names in containers, localhost locally
if IS_DOCKER:
    ADDRESS_SCANNER_URL = "http://address-scanner:8008"
    GUARDRAIL_URL = "http://guardrail:8009"
    VALIDATOR_URL = "http://validator-worker:8010"
    MLOPS_URL = "http://mlops-engine:8011"
    SIGNATURE_URL = "http://signature-generator:8012"
    REMEDIATOR_URL = "http://remediator:8013"
    INDEXER_URL = "http://streaming-indexer:8014"
    REPORTING_URL = "http://reporting-agent:8007"
    PROMETHEUS_URL = "http://prometheus:9090"
else:
    ADDRESS_SCANNER_URL = "http://localhost:8008"
    GUARDRAIL_URL = "http://localhost:8009"
    VALIDATOR_URL = "http://localhost:8010"
    MLOPS_URL = "http://localhost:8011"
    SIGNATURE_URL = "http://localhost:8012"
    REMEDIATOR_URL = "http://localhost:8013"
    INDEXER_URL = "http://localhost:8014"
    REPORTING_URL = "http://localhost:8007"
    PROMETHEUS_URL = "http://localhost:9090"
