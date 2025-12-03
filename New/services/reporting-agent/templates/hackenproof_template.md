# HackenProof Security Report

**Scan ID:** {{ scan_id }}  
**Target:** {{ target_url }}  
**Contract Address:** {{ contract_address or "N/A" }}  
**Report Date:** {{ timestamp }}

---

## Summary

Automated security analysis identified **{{ vulnerabilities|length }}** security issues requiring attention.

### Priority Distribution

{% set critical = vulnerabilities | selectattr("severity", "equalto", "critical") | list %}
{% set high = vulnerabilities | selectattr("severity", "equalto", "high") | list %}
{% set medium = vulnerabilities | selectattr("severity", "equalto", "medium") | list %}
{% set low = vulnerabilities | selectattr("severity", "equalto", "low") | list %}

| Priority | Count |
|----------|-------|
| P1 - Critical | {{ critical|length }} |
| P2 - High | {{ high|length }} |
| P3 - Medium | {{ medium|length }} |
| P4 - Low | {{ low|length }} |

---

{% for vuln in vulnerabilities %}
## Issue #{{ loop.index }}: {{ vuln.title }}

**Priority:** {{ vuln.hackenproof_severity }}  
**Confidence Level:** {{ vuln.confidence|upper }}

### Technical Details

{{ vuln.description }}

### Business Impact

{{ vuln.impact }}

### Steps to Reproduce

{% if vuln.reproduction_steps %}
```
{% for step in vuln.reproduction_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}
```
{% else %}
Detailed reproduction available in full report.
{% endif %}

### Remediation

{{ vuln.recommendation }}

{% if vuln.cvss_score %}
**CVSS v3.1 Score:** {{ vuln.cvss_score }}
{% endif %}

---

{% endfor %}

## Methodology

This report was generated using a multi-tier automated security analysis pipeline:

1. **Reconnaissance** - Repository mapping and surface analysis
2. **Static Analysis** - Slither, Mythril, Semgrep
3. **Dynamic Testing** - Foundry fuzz testing
4. **Runtime Monitoring** - Mempool and oracle monitoring
5. **AI-Powered Triage** - Multi-model classification and validation

## Notes

- All findings have been validated through multiple analysis stages
- Reproduction steps are designed for safe verification only
- Additional technical details available upon request

**Scan Reference:** `{{ scan_id }}`
