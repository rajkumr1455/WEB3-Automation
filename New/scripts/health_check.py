"""
Quick Health Check Script
Verify all services are running and responsive
"""

import asyncio
import httpx
from datetime import datetime


async def quick_check():
    """Quick health check of all services"""
    print("\n🏥 Web3 Bounty Hunter - Quick Health Check")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    services = [
        ("Web UI", "http://localhost:3001", "🌐"),
        ("Orchestrator", "http://localhost:8001/health", "🎯"),
        ("LLM Router", "http://localhost:8000/health", "🧠"),
        ("Recon Agent", "http://localhost:8002/health", "🔍"),
        ("Static Agent", "http://localhost:8003/health", "🔬"),
        ("Fuzzing Agent", "http://localhost:8004/health", "⚡"),
        ("Monitoring Agent", "http://localhost:8005/health", "👁️"),
        ("Triage Agent", "http://localhost:8006/health", "🎯"),
        ("Reporting Agent", "http://localhost:8007/health", "📝"),
        ("Qdrant", "http://localhost:6333", "💾"),
        ("Prometheus", "http://localhost:9090", "📊"),
        ("Grafana", "http://localhost:3000", "📈"),
    ]
    
    all_ok = True
    
    async with httpx.AsyncClient(timeout=5) as client:
        for name, url, emoji in services:
            try:
                response = await client.get(url)
                if response.status_code < 400:
                    print(f"{emoji} {name:<20} ✅ OK")
                else:
                    print(f"{emoji} {name:<20} ⚠️  HTTP {response.status_code}")
                    all_ok = False
            except Exception as e:
                print(f"{emoji} {name:<20} ❌ {str(e)[:30]}")
                all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ ALL SERVICES HEALTHY")
        print("\n🌐 Web UI: http://localhost:3001")
        print("📊 Grafana: http://localhost:3000")
    else:
        print("⚠️  SOME SERVICES NEED ATTENTION")
        print("Run: docker-compose logs -f")
    print("=" * 50 + "\n")
    
    return all_ok


if __name__ == "__main__":
    result = asyncio.run(quick_check())
    exit(0 if result else 1)
