from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import httpx
from enum import Enum
import os

app = FastAPI(
    title="Address-Only Scanner",
    description="Scan smart contracts by blockchain address without GitHub repository",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Chain(str, Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    SOLANA = "solana"
    APTOS = "aptos"
    SUI = "sui"
    STARKNET = "starknet"

class AddressScanRequest(BaseModel):
    """Request model for address scanning"""
    address: str = Field(..., description="Contract address to scan", min_length=20)
    chain: Optional[Chain] = Field(None, description="Blockchain (auto-detect if not provided)")
    rpc_url: Optional[str] = Field(None, description="Custom RPC endpoint")
    force_decompile: bool = Field(False, description="Force bytecode decompilation even if source available")

class AddressScanResponse(BaseModel):
    """Response model for address scanning"""
    scan_id: str
    address: str
    chain: str
    source_found: bool
    decompiled: bool
    findings: List[Dict]
    status: str
    contracts: List[Dict] = []  # For fuzzing compatibility
    source_code: Optional[Dict] = None  # Contract source code if available

class ChainDetector:
    """Auto-detect blockchain from address format"""
    
    @staticmethod
    def detect(address: str) -> Chain:
        """
        Detect blockchain from address format
        
        Args:
            address: Contract address
            
        Returns:
            Detected blockchain
            
        Raises:
            ValueError: If address format is unknown
        """
        # EVM chains (0x + 40 hex chars = 42 total)
        if address.startswith('0x') and len(address) == 42:
            try:
                int(address[2:], 16)  # Verify hex
                return Chain.ETHEREUM  # Default to Ethereum for EVM
            except ValueError:
                pass
        
        # Solana (32-44 base58 chars, no 0x prefix)
        if not address.startswith('0x') and 32 <= len(address) <= 44:
            # Solana addresses are base58 encoded
            if all(c in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz' for c in address):
                return Chain.SOLANA
        
        # Aptos/Sui (0x + 64 hex chars = 66 total)
        if address.startswith('0x') and len(address) == 66:
            try:
                int(address[2:], 16)  # Verify hex
                return Chain.APTOS
            except ValueError:
                pass
        
        # Starknet (0x + variable length, typically > 50)
        if address.startswith('0x') and len(address) > 50:
            try:
                int(address[2:], 16)  # Verify hex
                return Chain.STARKNET
            except ValueError:
                pass
        
        raise ValueError(f"Unknown address format: {address}. Supported: EVM (0x + 40 hex), Solana (32-44 base58), Aptos/Sui (0x + 64 hex), Starknet")

class ExplorerFetcher:
    """Fetch verified source code from block explorers"""
    
    EXPLORER_APIS = {
        Chain.ETHEREUM: "https://api.etherscan.io/v2/api",
        Chain.BSC: "https://api.bscscan.com/v2/api",
        Chain.POLYGON: "https://api.polygonscan.com/v2/api",
        Chain.ARBITRUM: "https://api.arbiscan.io/v2/api",
        Chain.OPTIMISM: "https://api-optimistic.etherscan.io/v2/api",
    }
    
    API_KEYS = {
        Chain.ETHEREUM: os.getenv("ETHERSCAN_API_KEY", ""),
        Chain.BSC: os.getenv("BSCSCAN_API_KEY", ""),
        Chain.POLYGON: os.getenv("POLYGONSCAN_API_KEY", ""),
        Chain.ARBITRUM: os.getenv("ARBISCAN_API_KEY", ""),
        Chain.OPTIMISM: os.getenv("OPTIMISM_API_KEY", ""),
    }
    
    # Chain IDs for API V2
    CHAIN_IDS = {
        Chain.ETHEREUM: "1",
        Chain.BSC: "56",
        Chain.POLYGON: "137",
        Chain.ARBITRUM: "42161",
        Chain.OPTIMISM: "10",
    }
    
    @classmethod
    async def fetch_source(cls, address: str, chain: Chain) -> Optional[Dict]:
        """
        Fetch verified source code from block explorer
        
        Args:
            address: Contract address
            chain: Blockchain network
            
        Returns:
            Dict containing source_code, abi, contract_name, compiler_version
            None if not found
        """
        if chain not in cls.EXPLORER_APIS:
            return None
        
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'chainid': cls.CHAIN_IDS.get(chain, '1'),
            'apikey': cls.API_KEYS.get(chain, '')
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    cls.EXPLORER_APIS[chain],
                    params=params,
                    timeout=15.0
                )
                data = response.json()
                
                if data.get('status') == '1' and data.get('result'):
                    result = data['result'][0]
                    source_code = result.get('SourceCode')
                    
                    if source_code and source_code != '':
                        return {
                            'source_code': source_code,
                            'abi': result.get('ABI', ''),
                            'contract_name': result.get('ContractName', 'Unknown'),
                            'compiler_version': result.get('CompilerVersion', ''),
                            'optimization_used': result.get('OptimizationUsed', '0'),
                            'runs': result.get('Runs', '200')
                        }
            except httpx.TimeoutException:
                print(f"Timeout fetching from {chain.value} explorer")
            except Exception as e:
                print(f"Error fetching from explorer: {e}")
                
        return None


class BytecodeDecompiler:
    """
    Simple bytecode decompiler for unverified contracts
    Generates pseudo-code from EVM bytecode for static analysis
    """
    
    @staticmethod
    async def fetch_bytecode(address: str, rpc_url: str) -> str:
        """
        Fetch contract bytecode from blockchain
        
        Args:
            address: Contract address
            rpc_url: RPC endpoint URL
            
        Returns:
            Hexadecimal bytecode string
            
        Raises:
            HTTPException: If RPC connection fails or no bytecode found
        """
        from web3 import Web3
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                raise HTTPException(500, f"Failed to connect to RPC endpoint: {rpc_url}")
            
            # Convert to checksum address (required by web3.py)
            checksum_address = Web3.to_checksum_address(address)
            
            bytecode = w3.eth.get_code(checksum_address)
            if not bytecode or bytecode == b'\x00' or len(bytecode) == 0:
                raise HTTPException(404, f"No bytecode found at {address}")
            
            return bytecode.hex()
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(500, f"Failed to fetch bytecode: {str(e)}")
    
    @staticmethod
    def decompile_to_pseudocode(bytecode: str, address: str) -> str:
        """
        Convert bytecode to pseudo-Solidity for static analysis
        
        Args:
            bytecode: Hexadecimal bytecode string
            address: Contract address (for comments)
            
        Returns:
            Pseudo-Solidity source code
        """
        # Remove 0x prefix if present
        if bytecode.startswith('0x'):
            bytecode = bytecode[2:]
        
        # Generate pseudo-code header
        pseudo_code = [
            "// Decompiled from bytecode",
            f"// Contract address: {address}",
            "// WARNING: This is machine-generated pseudo-code for static analysis",
            "pragma solidity ^0.8.0;",
            "",
            "contract DecompiledContract {",
            ""
        ]
        
        # Detect common function signatures
        if "a9059cbb" in bytecode:  # transfer(address,uint256)
            pseudo_code.append("    function transfer(address to, uint256 amount) public returns (bool);")
        
        if "23b872dd" in bytecode:  # transferFrom
            pseudo_code.append("    function transferFrom(address from, address to, uint256 amount) public returns (bool);")
        
        if "095ea7b3" in bytecode:  # approve
            pseudo_code.append("    function approve(address spender, uint256 amount) public returns (bool);")
        
        if "70a08231" in bytecode:  # balanceOf
            pseudo_code.append("    function balanceOf(address account) public view returns (uint256);")
        
        # Security warnings
        if "f4" in bytecode:  # DELEGATECALL
            pseudo_code.append("")
            pseudo_code.append("    // WARNING: DELEGATECALL detected - potential proxy or security risk")
        
        if "ff" in bytecode:  # SELFDESTRUCT
            pseudo_code.append( "    // WARNING: SELFDESTRUCT detected - contract can be destroyed")
        
        pseudo_code.append("}")
        
        return "\n".join(pseudo_code)


@app.post("/scan-address", response_model=AddressScanResponse)
async def scan_address(
    request: AddressScanRequest,
    background_tasks: BackgroundTasks
):
    """
    Scan a contract by address
    
    Workflow:
    1. Detect chain if not provided
    2. Fetch verified source from explorer
    3. If no source, attempt bytecode decompilation
    4. Run static analysis via static-agent
    5. Return findings
    """

    
    # Step 1: Detect chain
    chain = request.chain
    if not chain:
        try:
            chain = ChainDetector.detect(request.address)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Step 2: Fetch verified source
    source_data = await ExplorerFetcher.fetch_source(request.address, chain)
    
    source_found = source_data is not None
    decompiled = False
    
    if not source_data and not request.force_decompile:
        raise HTTPException(
            status_code=404,
            detail=f"No verified source found for {request.address} on {chain.value}. Set force_decompile=true to attempt decompilation."
        )
    
    
    if not source_data and request.force_decompile:
        # Step 3: Attempt bytecode decompilation
        try:
            # Determine RPC endpoint
            rpc_url = request.rpc_url
            if not rpc_url:
                # Use default RPC endpoints (public nodes)
                default_rpcs = {
                    Chain.ETHEREUM: "https://eth.llamarpc.com",
                    Chain.BSC: "https://bsc-dataseed.binance.org",
                    Chain.POLYGON: "https://polygon-rpc.com",
                    Chain.ARBITRUM: "https://arb1.arbitrum.io/rpc",
                    Chain.OPTIMISM: "https://mainnet.optimism.io"
                }
                rpc_url = default_rpcs.get(chain, "https://eth.llamarpc.com")
            
            # Fetch bytecode from blockchain
            bytecode = await BytecodeDecompiler.fetch_bytecode(
                request.address,
                rpc_url
            )
            
            # Decompile bytecode to pseudo-Solidity
            pseudo_code = BytecodeDecompiler.decompile_to_pseudocode(
                bytecode,
                request.address
            )
            
            # Create source_data format for static analysis
            source_data = {
                'source_code': pseudo_code,
                'contract_name': 'DecompiledContract',
                'compiler_version': 'bytecode-decompiled-v1.0',
                'abi': '[]'  # No ABI available from bytecode
            }
            
            decompiled = True
            source_found = True  # We have pseudo-code now
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Decompilation failed: {str(e)}"
            )
    
    # Step 4: Run static analysis
    # Integrate with existing static-agent
    try:
        # Generate scan ID first
        import uuid
        scan_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient() as client:
            analysis_response = await client.post(
                "http://static-agent:8003/analyze",
                json={
                    "scan_id": scan_id,
                    "contracts": [{
                        "name": source_data.get('contract_name', 'DecompiledContract'),
                        "source": source_data['source_code']
                    }]
                },
                timeout=120.0  # Static analysis can take time
            )
            
            if analysis_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Static analysis failed: {analysis_response.text}"
                )
            
            findings = analysis_response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Static analysis timed out")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Static analysis service unavailable")
    
    # Create contracts array for fuzzing compatibility
    contracts_array = []
    source_code_dict = {}
    
    if source_data:
        contract_name = source_data.get('contract_name', 'Contract')
        # Populate contracts array for orchestrator/fuzzing
        contracts_array.append({
            "name": contract_name,
            "address": request.address,
            "chain": chain.value,
            "language": "Solidity",
            "verified": source_found and not decompiled,
            "abi": source_data.get('abi', '')
        })
        
        # Create source_code dict for static analysis
        source_code_dict[contract_name] = {
            "source": source_data.get('source_code', ''),
            "abi": source_data.get('abi', ''),
            "compiler_version": source_data.get('compiler_version', '')
        }
    
    return AddressScanResponse(
        scan_id=scan_id,
        address=request.address,
        chain=chain.value,
        source_found=source_found,
        decompiled=decompiled,
        findings=findings.get('findings', []),
        status="completed",
        contracts=contracts_array,  # Populate for fuzzing
        source_code=source_code_dict  # Populate for static analysis
    )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "address-scanner",
        "version": "1.0.0"
    }

@app.get("/supported-chains")
async def supported_chains():
    """Get list of supported blockchain networks"""
    return {
        "chains": [chain.value for chain in Chain],
        "total": len(Chain)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)


