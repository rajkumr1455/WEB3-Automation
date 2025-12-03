# Contributing to Web3 Bounty Hunter

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn
- Prioritize security and quality

## Getting Started

### 1. Set Up Development Environment

```powershell
# Clone repository
git clone <repo-url>
cd web3_hunter/New

# Install Ollama and models
ollama pull deepseek-r1:32b-q4_K_M
ollama pull qwen2.5:14b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M
ollama pull nomic-embed-text

# Set up environment
copy .env.example .env

# Start services
docker-compose up -d
```

### 2. Development Workflow

```powershell
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# Test changes

# Commit
git commit -m "feat: add new feature"

# Push
git push origin feature/your-feature-name

# Create Pull Request
```

## Project Structure

```
web3_hunter/New/
├── services/           # Microservices (FastAPI)
│   ├── llm-router/    # LLM routing
│   ├── orchestrator/  # Pipeline coordination
│   ├── *-agent/       # Individual agents
│   └── */app.py       # Main service file
├── web-ui/            # Next.js frontend
│   ├── app/           # Pages
│   ├── components/    # React components
│   └── lib/           # Utilities
├── src/               # Shared utilities
│   └── rag/           # RAG utilities
├── scripts/           # Utility scripts
├── docs/              # Documentation
└── configs/           # Configuration files
```

## Contribution Guidelines

### Code Style

**Python (Backend):**
- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions under 50 lines
- Use meaningful variable names

```python
async def analyze_contract(
    contract_code: str,
    chain: str = "ethereum"
) -> Dict[str, Any]:
    """
    Analyze smart contract for vulnerabilities.
    
    Args:
        contract_code: Solidity source code
        chain: Blockchain network name
        
    Returns:
        Dictionary with analysis results
    """
    # Implementation
```

**TypeScript (Frontend):**
- Follow Next.js conventions
- Use TypeScript strict mode
- Add JSDoc comments
- Use functional components
- Keep components under 200 lines

```typescript
interface ScanResult {
  scan_id: string;
  status: ScanStatus;
  results: FindingsData;
}

async function fetchScanStatus(scanId: string): Promise<ScanResult> {
  // Implementation
}
```

### Testing

**Add tests for new features:**

```python
# tests/test_static_agent.py
import pytest

async def test_run_slither():
    result = await run_slither(contract_path)
    assert result["findings"]
    assert "slither" in result["tool"]
```

**Run tests before submitting:**

```powershell
# Python tests
pytest tests/

# E2E tests
python scripts/test_e2e.py

# Health check
python scripts/health_check.py
```

### Documentation

**Update documentation for:**
- New features
- API changes
- Configuration options
- Breaking changes

**Documentation locations:**
- API changes → `docs/API.md`
- Architecture → `docs/ARCHITECTURE.md`
- Deployment → `docs/DEPLOYMENT.md`
- Main README → `README.md`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new vulnerability detection pattern
fix: correct Slither JSON parsing
docs: update API documentation
chore: update dependencies
test: add fuzzing agent tests
refactor: simplify triage logic
```

## Areas for Contribution

### High Priority

1. **Additional Security Tools**
   - Integrate new static analyzers
   - Add more fuzzing engines
   - Expand monitoring capabilities

2. **Knowledge Base Expansion**
   - Add more vulnerability patterns
   - Index additional CVEs
   - Create custom Semgrep rules

3. **UI Enhancements**  
   - Add vulnerability visualization
   - Improve scan progress indicators
   - Create comparison views

4. **Performance Optimization**
   - Optimize Docker builds
   - Reduce memory usage
   - Speed up analysis pipeline

### Medium Priority

1. **Integration Support**
   - Add more bug bounty platforms
   - Support additional chains
   - Add CI/CD integrations

2. **Authentication**
   - JWT authentication
   - OAuth providers
   - API key management

3. **Advanced Features**
   - Historical trend analysis
   - ML-based false positive filtering
   - Automated exploit generation

### Good First Issues

Look for issues labeled `good-first-issue`:
- Documentation improvements
- UI polish
- Test coverage
- Error message improvements

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Run all tests** locally
4. **Update CHANGELOG** if applicable
5. **Request review** from maintainers

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No new warnings/errors
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

## Security Vulnerabilities

**DO NOT** create public issues for security vulnerabilities.

Instead:
1. Email: security@yourproject.com
2. Include detailed description
3. Provide reproduction steps
4. We'll respond within 48 hours

## Questions?

- **GitHub Discussions**: Ask questions
- **GitHub Issues**: Report bugs
- **Documentation**: Check docs/ first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Web3 security! 🔒🎯**
