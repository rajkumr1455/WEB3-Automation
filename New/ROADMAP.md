# Web3 Security Platform - Complete Roadmap

## ✅ CURRENT STATUS (As of Nov 29, 2024)

Your platform is **100% operational** with:
- 12 Docker services running
- Web UI accessible at http://localhost:3001
- API working (tested successfully)
- All 6 core agents functional

**Issue:** UI doesn't provide adequate feedback after scan submission

---

## 📋 PHASE 1: Fix UI Feedback (1-2 hours)

### Issue
After clicking "Launch Scan", users don't see:
- Success confirmation
- Scan progress
- Error messages
- Navigation to results

### Solution

#### 1. Add Toast Notifications
Install: `npm install react-hot-toast`

Update `ScanForm.tsx`:
```typescript
import toast from 'react-hot-toast';

const { mutate: startScan, isPending } = useMutation({
    mutationFn: (data: ScanRequest) => scanAPI.startScan(data),
    onSuccess: (data) => {
        toast.success(`Scan ${data.scan_id} started successfully!`);
        router.push(`/scan/${data.scan_id}`); // Navigate to scan page
        queryClient.invalidateQueries({ queryKey: ['scans'] });
        setFormData({ target_url: '', contract_address: '', chain: 'ethereum' });
    },
    onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to start scan');
    },
 });
```

Add to `app/layout.tsx`:
```typescript
import { Toaster } from 'react-hot-toast';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <Navigation />
          <main className="ml-64 p-8">
            {children}
          </main>
          <Toaster position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
```

#### 2. Create Scan Detail Page
Create `web-ui/app/scan/[id]/page.tsx`:
```typescript
'use client';

import { use } from 'react';
import { useQuery } from '@tanstack/react-query';
import { scanAPI } from '@/lib/api';

export default function ScanDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params); // Next.js 16 async params
  
  const { data: scan, isLoading } = useQuery({
    queryKey: ['scan', id],
    queryFn: () => scanAPI.getScanStatus(id),
    refetchInterval: (data) => {
      // Poll every 3 seconds while running
      return data?.status === 'running' || data?.status === 'pending' ? 3000 : false;
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (!scan) return <div>Scan not found</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Scan {scan.scan_id}</h1>
      
      {/* Progress bar */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex justify-between mb-2">
          <span>Progress</span>
          <span>{scan.progress}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-4">
          <div 
            className="bg-primary-500 h-4 rounded-full transition-all duration-300"
            style={{ width: `${scan.progress}%` }}
          />
        </div>
        <p className="mt-2 text-sm text-gray-400">
          Current stage: {scan.current_stage || 'Initializing'}
        </p>
      </div>

      {/* Results */}
      {scan.status === 'completed' && (
        <div className="bg-gray-800  rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Results</h2>
          <pre className="text-sm overflow-auto">
            {JSON.stringify(scan.results, null, 2)}
          </pre>
        </div>
      )}

      {/* Error */}
      {scan.status === 'failed' && (
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-6">
          <h2 className="text-xl font-bold text-red-500 mb-2">Scan Failed</h2>
          <p>{scan.error}</p>
        </div>
      )}
    </div>
  );
}
```

---

## 🚀 PHASE 2: Upgrade to Next.js 16 (3-4 hours)

### Prerequisites
- Ensure Node.js 20+ installed
- Backup current working code

### Steps

#### 1. Update Dependencies
```bash
cd web-ui
npm install next@latest react@latest react-dom@latest
npm install @types/react@latest @types/react-dom@latest
```

#### 2. Enable Next.js 16 Features
Update `next.config.js`:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable Cache Components (Next.js 16)
  cacheComponents: true,
  
  // Enable Turbopack for dev (stable in Next.js 16)
  turbopack: true,
  
  // React Compiler (optional but recommended)
  experimental: {
    reactCompiler: true,
  },
  
  // ... rest of config
};

export default nextConfig;
```

#### 3. Update Caching APIs
Replace old caching:
```typescript
// OLD (deprecated)
revalidateTag('blog-posts');

// NEW (Next.js 16)
import { revalidateTag } from 'next/cache';
revalidateTag('blog-posts', 'max'); // Add cacheLife profile
```

#### 4. Convert middleware.ts → proxy.ts
Rename `middleware.ts` to `proxy.ts`:
```typescript
// proxy.ts
import { NextRequest, NextResponse } from 'next/server';

export default function proxy(request: NextRequest) {
  // Your middleware logic here
  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*',
};
```

#### 5. Add "use cache" Directives
For cacheable components:
```typescript
'use cache';

export default async function CachedComponent() {
  // This component will be cached
  const data = await fetch('...');
  return <div>{data}</div>;
}
```

#### 6. Update Async Request APIs
Next.js 16 requires awaiting params:
```typescript
// OLD
export default function Page({ params }: { params: { id: string } }) {
  const { id } = params;
}

// NEW (Next.js 16)
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
}
```

#### 7. Test Everything
```bash
npm run build
npm run dev
```

---

## 🌟 PHASE 3: Advanced Features (40-50 hours)

### 3.1 Address-Only Scanner (8 hours)

**Scope:** Scan contracts by address alone (no GitHub repo)

**New Service:** `services/address-scanner/`

**Features:**
- Multi-chain support (EVM, Solana, Aptos, Sui, Starknet)
- Auto-detect chain from address format
- Fetch verified source from explorers
- Bytecode decompilation if no source
- Unified vulnerability output

**Implementation:**
```python
# services/address-scanner/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from typing import Optional, List

app = FastAPI()

class AddressScanRequest(BaseModel):
    address: str
    chain: Optional[str] = None  # Auto-detect if not provided

class ChainDetector:
    @staticmethod
    def detect_chain(address: str) -> str:
        if address.startswith('0x') and len(address) == 42:
            return 'evm'  # Ethereum / EVM chains
        elif len(address) == 44 and address.isalnum():
            return 'solan' # Solana
        elif address.startswith('0x') and len(address) == 66:
            return 'aptos'  # Aptos/Sui
        elif address.startswith('stark'):
            return 'starknet'
        else:
            raise ValueError(f"Unknown address format: {address}")

async def fetch_verified_source(address: str, chain: str) -> Optional[str]:
    """Fetch verified source from block explorer"""
    explorers = {
        'ethereum': f'https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}',
        'bsc': f'https://api.bscscan.com/api?module=contract&action=getsourcecode&address={address}',
        'polygon': f'https://api.polygonscan.com/api?module=contract&action=getsourcecode&address={address}',
    }
    
    if chain not in explorers:
        return None
    
    async with httpx.AsyncClient() as client:
        response = await client.get(explorers[chain])
        data = response.json()
        
        if data['status'] == '1' and data['result'][0].get('SourceCode'):
            return data['result'][0]['SourceCode']
    
    return None

async def decompile_bytecode(address: str, chain: str) -> str:
    """Decompile bytecode using Panoramix or similar"""
    # Implementation for EVM decompilation
    # Would integrate with tools like:
    # - Panoramix (EVM)
    # - Solana decompilers
    # - Move decompilers (Aptos/Sui)
    pass

@app.post("/scan-address")
async def scan_address(request: AddressScanRequest):
    # Detect chain
    chain = request.chain or ChainDetector.detect_chain(request.address)
    
    # Fetch source
    source = await fetch_verified_source(request.address, chain)
    
    if not source:
        # Attempt decompilation
        source = await decompile_bytecode(request.address, chain)
    
    # Run static analysis
    # ...
    
    return {"address": request.address, "chain": chain, "findings": []}
```

### 3.2 Guardrail Auto-Pause System (6 hours)

**Scope:** Real-time transaction simulation + contract pausing

**New Service:** `services/guardrail/`

**Features:**
- Monitor mempool for contract calls
- Simulate transactions on fork
- Detect exploit patterns
- Generate pause requests (manual approve by default)
- Optional auto-pause with governance

**Key Files:**
- `services/guardrail/app.py` - Main service
- `services/guardrail/simulator.py` - Tenderly/Hardhat fork integration
- `services/guardrail/policies.yaml` - Pause rules configuration
- `web-ui/app/guardrail/page.tsx` - Management UI

### 3.3 Validator Worker (4 hours)

**Scope:** Reproduce and validate findings

**New Service:** `services/validator-worker/`

**Features:**
- Queue-based reproduction system
- Sandbox execution (Docker in Docker)
- Capture traces & state diffs
- Mark findings as verified/false-positive
- Feed to ML-Ops engine

### 3.4 ML-Ops Engine (10 hours)

**Scope:** Continuous learning & rule generation

**New Services:**
- `services/mlops-engine/` - Training & inference
- `web-ui/app/mlops/` - Dataset labeling UI

**Features:**
- Human-in-the-loop labeling
- Fine-tune local models (Qwen, Mistral)
- Generate Semgrep rules from patterns
- A/B test rule effectiveness
- Model versioning & rollback

### 3.5 Remediator (6 hours)

**Scope:** Automated code fix PR generation

**New Service:** `services/remediator/`

**Features:**
- Accept vulnerability + location
- Generate minimal safe patch
- Run tests in sandbox
- Create GitHub Draft PR
- Review UI panel

### 3.6 Streaming Indexer (8 hours)

**Scope:** High-throughput on-chain event indexing

**New Service:** `services/streaming-indexer/`

**Features:**
- WebSocket subscriptions to chains
- Event log ingestion
- Time-series storage (TimescaleDB)
- Embed events in Qdrant for RAG
- Real-time dashboards

### 3.7 Signature Generator (4 hours)

**Scope:** Convert findings → monitoring rules

**New Service:** `services/signature-generator/`

**Features:**
- Fuzz crash → detection signature
- Require human approval
- Deploy to monitoring-agent
- Metric tracking

---

## 📊 PRIORITY MATRIX

| Feature | Impact | Effort | Priority | Timeline |
|---------|--------|--------|----------|----------|
| UI Feedback Fix | HIGH | LOW | **P0** | 1-2 hours |
| Next.js 16 Upgrade | MEDIUM | MEDIUM | **P1** | 3-4 hours |
| Address Scanner | HIGH | HIGH | **P2** | 8 hours |
| Guardrail | HIGH | MEDIUM | **P2** | 6 hours |
| ML-Ops | MEDIUM | HIGH | P3 | 10 hours |
| Validator Worker | MEDIUM | LOW | P3 | 4 hours |
| Remediator | MEDIUM | MEDIUM | P4 | 6 hours |
| Streaming Indexer | LOW | HIGH | P4 | 8 hours |
| Signature Generator | LOW | LOW | P5 | 4 hours |

---

## 🎯 RECOMMENDED EXECUTION PLAN

### Week 1: Core Fixes
- Day 1: Phase 1 (UI fixes)
- Day 2-3: Phase 2 (Next.js 16 upgrade)
- Day 4-5: Testing & documentation

### Week 2: Address Scanner
- Day 1-3: Build address-scanner service
- Day 4: Multi-chain integration
- Day 5: Testing & UI

### Week 3: Guardrail System
- Day 1-2: Simulation engine
- Day 3: Pause mechanism
- Day 4-5: UI & testing

### Week 4+: Advanced Features
- Week 4: Validator + ML-Ops
- Week 5: Remediator + Streaming
- Week 6: Integration testing & optimization

---

## 📝 CURRENT SYSTEM INVENTORY

### Services Running ✅
1. web-ui (Next.js 14) - Port 3001
2. orchestrator - Port 8001
3. llm-router - Port 8000
4. recon-agent - Port 8002
5. static-agent - Port 8003 (Slither only currently)
6. fuzzing-agent - Port 8004
7. monitoring-agent - Port 8005
8. triage-agent - Port 8006
9. reporting-agent - Port 8007
10. qdrant - Ports 6333-6334
11. prometheus - Port 9090
12. grafana - Port 3000

### What's Built
- ✅ Complete Web UI (9 pages)
- ✅ 6 functional AI agents
- ✅ Hybrid LLM routing
- ✅ RAG infrastructure
- ✅ Monitoring stack
- ✅ Docker orchestration
- ✅ Comprehensive documentation

### What's Missing
- ⏸️ UI user feedback (Phase 1)
- ⏸️ Next.js 16 features (Phase 2)
- ⏸️ 7 advanced services (Phase 3)

---

## 🔧 QUICK FIXES FOR IMMEDIATE USE

### Fix 1: Environment Variables
Create `.env` file:
```env
CLAUDE_API_KEY=sk-ant-your-key-here
GITHUB_TOKEN=ghp_your-token  # Optional
ETH_RPC_URL=https://eth.llamarpc.com
```

Restart services:
```powershell
docker-compose restart
```

### Fix 2: Test Scan Submission
```powershell
$body = @{
    target_url = 'https://github.com/OpenZeppelin/openzeppelin-contracts'
    chain = 'ethereum'
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://localhost:8001/scan' -Method Post -Body $body -ContentType 'application/json'
```

### Fix 3: Monitor Scan Progress
```powershell
# Replace SCAN_ID with actual ID from above
Invoke-RestMethod -Uri 'http://localhost:8001/scan/SCAN_ID'
```

---

## 📚 ADDITIONAL RESOURCES

### Documentation
- [Next.js 16 Blog Post](https://nextjs.org/blog/next-16)
- [React 19 Release](https://react.dev/blog/2024/04/25/react-19)
- [Turbopack Docs](https://nextjs.org/docs/architecture/turbopack)

### Multi-Chain References
- [Solana Web3.js](https://solana-labs.github.io/solana-web3.js/)
- [Aptos SDK](https://aptos.dev/sdks/ts-sdk/)
- [Starknet.js](https://www.starknetjs.com/)

### Security Tools
- [Slither](https://github.com/crytic/slither)
- [Mythril](https://github.com/ConsenSys/mythril)
- [Foundry](https://book.getfoundry.sh/)

---

## ✅ VERIFICATION CHECKLIST

Before deploying to production:

- [ ] UI feedback implemented
- [ ] Next.js 16 upgrade complete
- [ ] All tests passing
- [ ] Error handling comprehensive
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Load testing complete
- [ ] Security audit performed
- [ ] Backup strategy in place
- [ ] Rollback plan documented

---

**Ready to start Phase 1? Let me know what you'd like to tackle first!** 🚀
