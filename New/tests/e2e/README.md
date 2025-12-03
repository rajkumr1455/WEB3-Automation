# End-to-End Test Plan

## Overview

This comprehensive test suite validates the entire Web3 Bug Bounty Automation Platform including backend microservices, orchestration pipeline, and Next.js 16 UI.

**Test Coverage:**
- ✅ Happy paths for all major workflows
- ✅ Edge cases and error handling
- ✅ Failure/retry flows with exponential backoff
- ✅ Security controls (no mainnet writes)
- ✅ Safety checks (admin tokens, fork mode)
- ✅ Multi-chain support validation
- ✅ LLM integration flows
- ✅ Real-time monitoring & alerting

**Environment:**
- Next.js 16.0.3 LTS + React 19
- Node 20+
- Docker Desktop (Linux containers)
- Ollama @ http://host.docker.internal:11434
- Claude 4.5 for verification (optional)
- Windows PowerShell (primary) / bash (alternative)

---

## Test Matrix

| Feature | Backend Tests | UI Tests | Fixtures | Status |
|---------|--------------|----------|----------|--------|
| Repo Import | test_repo_import_flow.py | repo_import.spec.ts | test-repo.tar.gz | ✅ |
| Address Scan | test_address_scan_flow.py | address_scan.spec.ts | explorer-mocks | ✅ |
| Guardrail Simulate | test_guardrail_simulation.py | guardrail_panel.spec.ts | tx-fixtures | ✅ |
| Validator Repro | test_validator_repro.py | validator_queue.spec.ts | sample-findings | ✅ |
| Remediator PR | test_remediator_pr_generation.py | remediator_panel.spec.ts | github-mock | ✅ |
| Reporting | test_reporting_formats.py | report_download.spec.ts | report-templates | ✅ |
| Metrics | test_metrics_emission.py | - | - | ✅ |
| ML-Ops Training | test_mlops_training.py | - | validated-findings | ✅ |
| Signature Export | test_signature_export.py | - | - | ✅ |
| Streaming Events | test_streaming_indexer.py | - | event-fixtures | ✅ |

---

## Acceptance Criteria

### 1. Repo Import Flow
**Pass Conditions:**
- POST `/import` returns `{"status": "queued", "import_id": "<uuid>"}`
- Status transitions: `queued` → `processing` → `completed` within 60s
- UI shows progress bar (0% → 100%)
- Index page displays imported items with correct metadata
- RAG embeddings created in Qdrant

**Fail Conditions:**
- Import stuck in `processing` > 120s
- Missing required fields in API response
- UI displays error message
- No embeddings in vector DB

### 2. Address Scan Flow
**Pass Conditions:**
- POST `/address-scanner/scan-address` with address only returns scan_id
- Auto-detection identifies correct chain
- Status becomes `completed` with findings array
- Findings have required fields: `type`, `severity`, `title`, `description`
- UI displays findings with severity badges

**Fail Conditions:**
- Invalid address returns 400 with clear message
- Missing API keys handled gracefully (not 500)
- Findings missing required schema fields

### 3. Guardrail Simulation
**Pass Conditions:**
- POST `/guardrail/monitor/start` creates monitor
- Simulated transaction analyzed within 5s
- Response includes `economic_impact`, `risk_score`, `verdict`
- POST `/guardrail/pause/request` creates DB entry (status: pending)
- Admin approval workflow works

**Fail Conditions:**
- Simulation timeout > 10s
- Missing required response fields
- Non-admin can approve pause request

### 4. Validator Reproduction
**Pass Conditions:**
- POST `/validator/validate` creates job with job_id
- Job status transitions: `queued` → `running` → `completed`
- Result includes `is_valid`, `confidence`, `execution_trace`
- Foundry sandbox created and cleaned up
- PoC template generated if not provided

**Fail Conditions:**
- Job stuck in queue > 300s
- Sandbox fails to create
- Invalid PoC crashes worker

### 5. Remediator PR Generation
**Pass Conditions:**
- POST `/remediator/remediate` generates fix
- Fix has `confidence` ≥ 0.7
- GitHub PR created (or mocked) with proper diff
- Branch created: `fix/<type>-<id>`
- PR body includes vulnerability description + fix explanation

**Fail Conditions:**
- Low confidence fix (< 0.5) not flagged
- Invalid GitHub credentials handled gracefully
- PR creation failure logged properly

### 6. Report Generation
**Pass Conditions:**
- GET `/reports/immunefi/<finding_id>` returns valid JSON
- Required fields: `title`, `severity`, `description`, `poc`, `impact`
- Markdown format includes all sections
- HackenProof format validates against schema

**Fail Conditions:**
- Missing required fields
- Invalid severity values
- Malformed JSON

### 7. Metrics Emission
**Pass Conditions:**
- GET `:9090/metrics` returns Prometheus format
- Required metrics exist:
  - `bugbot_findings_total{severity="<level>"}`
  - `bugbot_scan_duration_seconds`
  - `bugbot_service_health{service="<name>"}`
- Labels are valid and consistent

**Fail Conditions:**
- Metrics endpoint not responding
- Missing critical metrics
- Invalid label values

### 8. ML-Ops Training
**Pass Conditions:**
- POST `/mlops/ingest` accepts validated finding
- POST `/mlops/train` returns trained models
- Accuracy metrics calculated
- POST `/mlops/generate-rules` creates detection rules
- Rules have confidence scores

**Fail Conditions:**
- Training fails with insufficient data
- Invalid finding schema crashes ingestion
- Generated rules have errors

### 9. Signature Export
**Pass Conditions:**
- POST `/signatures/generate` creates 4 formats (YARA, Sigma, Suricata, Custom)
- Each format validates against schema
- POST `/signatures/export` returns combined content
- Downloaded file is valid

**Fail Conditions:**
- Invalid finding type crashes generator
- Malformed signature output
- Export endpoint errors

### 10. Streaming Indexer
**Pass Conditions:**
- POST `/indexer/index/start` begins indexing
- WebSocket connection established @ `/ws`
- Events streamed in real-time
- POST `/indexer/query` returns filtered events
- Backfill completes within timeout

**Fail Conditions:**
- WebSocket disconnects unexpectedly
- Events not indexed
- Query returns wrong data

---

## Security & Safety Checks

### Mainnet Protection
```powershell
# All tests MUST set this
$env:SCAN_MODE = "fork"
$env:ALLOW_LIVE = "0"
```

**Assertions:**
- No test broadcasts to mainnet
- All contract interactions use forked RPCs
- Fuzzing limited to 5 minutes in CI
- Validator sandboxes are isolated

### Authentication
**Assertions:**
- Guardrail pause requires `ADMIN_TOKEN`
- Remediator PR creation requires `GITHUB_TOKEN`
- Metrics endpoints open (Prometheus standard)
- Health endpoints open (monitoring)

### Rate Limiting
**Assertions:**
- Explorer API calls respect rate limits
- Mock servers used for deterministic testing
- Retry logic with exponential backoff

---

## Test Reliability

### Retry Strategy
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def wait_for_completion(scan_id: str):
    response = await client.get(f"/scans/{scan_id}")
    assert response.json()["status"] == "completed"
```

### Timeouts
- Service health checks: 120s max
- Scan completion: 180s max
- UI interactions: 30s max
- WebSocket connections: 60s max

### Flakiness Mitigation
- Deterministic mock data
- Fixed timestamps in fixtures
- Isolated test environments
- Cleanup between tests

---

## Local Execution

### Prerequisites
```powershell
# Install dependencies
npm install
pip install -r tests/backend/requirements.txt
npx playwright install chromium

# Start services
.\tests\e2e\bootstrap.ps1
```

### Run All Tests
```powershell
# Backend tests
pytest tests/backend -v --tb=short

# UI tests
npx playwright test --project=chromium

# Teardown
docker compose -f docker-compose.yml down --volumes
```

### Run Specific Test
```powershell
# Single backend test
pytest tests/backend/test_address_scan_flow.py -v

# Single UI test
npx playwright test tests/ui/address_scan.spec.ts
```

---

## CI Execution

Tests run automatically on push/PR via GitHub Actions:
- Matrix: Node 20, Python 3.11
- Services: Docker Compose
- Artifacts: Screenshots, traces, logs
- Reports: JUnit XML, HTML

See `.github/workflows/e2e.yml` for configuration.

---

## Debugging Failed Tests

### Collect Logs
```powershell
# Get service logs
docker logs --tail 500 address-scanner > address-scanner.log
docker logs --tail 500 guardrail > guardrail.log

# Get all logs
docker compose logs > all-services.log
```

### View Playwright Traces
```powershell
npx playwright show-trace tests/ui/test-results/address_scan-chromium/trace.zip
```

### Check Service Health
```powershell
curl http://localhost:8008/health
curl http://localhost:8009/health
```

---

## Test Coverage Summary

### Covered (✅)
- All 7 Phase 3 features
- All 6 original agents
- Orchestrator pipeline
- LLM routing
- Vector DB operations
- Metrics emission
- Report generation
- UI interactions

### Not Covered (Future)
- Load testing (concurrent scans)
- Stress testing (resource limits)
- Chaos engineering (service failures)
- Performance benchmarks
- Browser compatibility (Firefox, Safari)
- Mobile responsiveness
- Accessibility (WCAG)

---

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Services won't start | Check Docker Desktop running, ports not in use |
| Health checks timeout | Increase timeout, check service logs |
| Tests fail locally but pass in CI | Check environment variables, file paths |
| Playwright can't connect | Verify UI server running on :3001 |
| Mock server errors | Check fixtures directory exists |
| Flaky WebSocket tests | Increase connection timeout |

---

**Last Updated:** 2024-11-30  
**Test Suite Version:** 1.0.0  
**Platform Version:** 0.92.0
