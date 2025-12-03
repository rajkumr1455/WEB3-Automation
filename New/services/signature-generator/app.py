from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import json
import yaml

app = FastAPI(
    title="Signature Generator",
    description="Convert security findings into monitoring signatures and detection rules",
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


# In-memory storage for generated signatures
generated_signatures: Dict[str, List[Dict]] = {
    "yara": [],
    "sigma": [],
    "suricata": [],
    "custom": []
}

class SignatureFormat(str, Enum):
    """Supported signature formats"""
    YARA = "yara"
    SIGMA = "sigma"
    SURICATA = "suricata"
    CUSTOM = "custom"

class FindingType(str, Enum):
    """Types of security findings"""
    REENTRANCY = "reentrancy"
    INTEGER_OVERFLOW = "integer_overflow"
    ACCESS_CONTROL = "access_control"
    UNCHECKED_CALL = "unchecked_call"
    FLASH_LOAN = "flash_loan"
    PRICE_MANIPULATION = "price_manipulation"
    FRONT_RUNNING = "front_running"
    DOS = "dos"

class Finding(BaseModel):
    """Security finding to convert to signature"""
    id: str
    type: FindingType
    severity: str
    title: str
    description: str
    contract_address: Optional[str] = None
    function_name: Optional[str] = None
    patterns: List[str] = Field(default_factory=list)
    bytecode_patterns: List[str] = Field(default_factory=list)

class SignatureRequest(BaseModel):
    """Request to generate signatures"""
    finding: Finding
    formats: List[SignatureFormat] = Field(
        default=[SignatureFormat.YARA, SignatureFormat.CUSTOM]
    )
    include_metadata: bool = Field(default=True)

class Signature(BaseModel):
    """Generated signature"""
    signature_id: str
    format: SignatureFormat
    finding_id: str
    finding_type: FindingType
    content: str
    metadata: Dict[str, Any]
    created_at: datetime

class YARAGenerator:
    """
    Generate YARA rules for bytecode pattern matching
    """
    
    @staticmethod
    def generate(finding: Finding) -> str:
        """
        Generate YARA rule from finding
        
        YARA rules can detect:
        - Bytecode patterns
        - Function signatures
        - Opcode sequences
        """
        rule_name = f"{finding.type.value}_{finding.id.replace('-', '_')}"
        
        # Create condition strings from patterns
        strings_section = []
        for i, pattern in enumerate(finding.bytecode_patterns[:10]):  # Max 10 patterns
            strings_section.append(f'        $pattern{i} = {{ {pattern} }}')
        
        # If no bytecode patterns, use function name
        if not strings_section and finding.function_name:
            # Convert function name to hex pattern
            func_hex = finding.function_name.encode().hex()
            strings_section.append(f'        $func = {{ {func_hex} }}')
        
        strings = '\n'.join(strings_section) if strings_section else '        // No patterns available'
        
        # Build condition
        if strings_section:
            condition = ' or '.join([f'$pattern{i}' for i in range(len(strings_section))])
        else:
            condition = 'false'
        
        yara_rule = f'''rule {rule_name} {{
    meta:
        description = "{finding.title}"
        severity = "{finding.severity}"
        type = "{finding.type.value}"
        generated = "{datetime.utcnow().isoformat()}"
        
    strings:
{strings}
        
    condition:
        {condition}
}}'''
        
        return yara_rule

class SigmaGenerator:
    """
    Generate Sigma rules for transaction monitoring
    """
    
    @staticmethod
    def generate(finding: Finding) -> str:
        """
        Generate Sigma rule from finding
        
        Sigma rules can detect:
        - Transaction patterns
        - Event signatures
        - Parameter patterns
        """
        sigma_rule = {
            "title": finding.title,
            "id": finding.id,
            "status": "experimental",
            "description": finding.description,
            "references": [],
            "author": "Web3 Security Platform",
            "date": datetime.utcnow().strftime("%Y/%m/%d"),
            "modified": datetime.utcnow().strftime("%Y/%m/%d"),
            "tags": [
                f"attack.{finding.type.value}",
                f"severity.{finding.severity}"
            ],
            "logsource": {
                "category": "blockchain",
                "product": "ethereum",
                "service": "transaction_monitor"
            },
            "detection": {
                "selection": {
                    "to": finding.contract_address if finding.contract_address else "*",
                    "function": finding.function_name if finding.function_name else "*"
                },
                "condition": "selection"
            },
            "falsepositives": [
                "Legitimate usage of similar patterns"
            ],
            "level": finding.severity,
            "fields": [
                "transaction.hash",
                "transaction.from",
                "transaction.to",
                "transaction.value"
            ]
        }
        
        # Add pattern-based detection if available
        if finding.patterns:
            sigma_rule["detection"]["patterns"] = finding.patterns[:5]
        
        return yaml.dump(sigma_rule, default_flow_style=False)

class SuricataGenerator:
    """
    Generate Suricata rules for network-level detection
    """
    
    @staticmethod
    def generate(finding: Finding) -> str:
        """
        Generate Suricata rule from finding
        
        Suricata rules can detect:
        - RPC call patterns
        - Transaction payloads
        - Network-level exploit attempts
        """
        # Suricata rule format:
        # alert <protocol> <source> <source_port> -> <dest> <dest_port> (rule_options)
        
        sid = abs(hash(finding.id)) % 1000000  # Generate unique SID
        
        # Build content patterns
        content_patterns = []
        if finding.contract_address:
            content_patterns.append(f'content:"{finding.contract_address}";')
        
        if finding.function_name:
            content_patterns.append(f'content:"{finding.function_name}";')
        
        content_str = ' '.join(content_patterns) if content_patterns else 'content:"eth_sendTransaction";'
        
        suricata_rule = f'''alert http any any -> any any (
    msg:"Possible {finding.type.value} attack on {finding.contract_address or 'contract'}";
    flow:established,to_server;
    {content_str}
    http.method; content:"POST";
    http.uri; content:"/";
    classtype:attempted-admin;
    sid:{sid};
    rev:1;
    metadata:
        severity {finding.severity},
        type {finding.type.value},
        created {datetime.utcnow().isoformat()};
)'''
        
        return suricata_rule

class CustomGenerator:
    """
    Generate custom platform-specific rules
    """
    
    @staticmethod
    def generate(finding: Finding) -> str:
        """
        Generate custom JSON-based detection rule
        
        Custom format allows maximum flexibility for
        integration with various monitoring platforms
        """
        custom_rule = {
            "id": finding.id,
            "name": finding.title,
            "type": finding.type.value,
            "severity": finding.severity,
            "description": finding.description,
            "detection": {
                "contract_address": finding.contract_address,
                "function_name": finding.function_name,
                "patterns": finding.patterns,
                "bytecode_patterns": finding.bytecode_patterns
            },
            "alert": {
                "enabled": True,
                "channels": ["email", "slack", "webhook"],
                "threshold": 1,
                "window": "5m"
            },
            "response": {
                "auto_pause": finding.severity in ["critical", "high"],
                "notify_team": True,
                "create_ticket": True
            },
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "platform": "web3-security",
                "version": "1.0"
            }
        }
        
        return json.dumps(custom_rule, indent=2)

@app.post("/generate", response_model=List[Signature])
async def generate_signatures(request: SignatureRequest):
    """
    Generate monitoring signatures from a security finding
    
    Converts findings into platform-specific detection rules:
    - YARA: Bytecode pattern matching
    - Sigma: Transaction monitoring
    - Suricata: Network-level detection
    - Custom: Platform-agnostic JSON rules
    """
    import uuid
    
    signatures = []
    
    for format_type in request.formats:
        # Generate signature content
        if format_type == SignatureFormat.YARA:
            content = YARAGenerator.generate(request.finding)
        elif format_type == SignatureFormat.SIGMA:
            content = SigmaGenerator.generate(request.finding)
        elif format_type == SignatureFormat.SURICATA:
            content = SuricataGenerator.generate(request.finding)
        elif format_type == SignatureFormat.CUSTOM:
            content = CustomGenerator.generate(request.finding)
        else:
            continue
        
        # Create signature object
        signature = Signature(
            signature_id=str(uuid.uuid4()),
            format=format_type,
            finding_id=request.finding.id,
            finding_type=request.finding.type,
            content=content,
            metadata={
                "severity": request.finding.severity,
                "contract": request.finding.contract_address,
                "function": request.finding.function_name,
                "patterns_count": len(request.finding.patterns)
            } if request.include_metadata else {},
            created_at=datetime.utcnow()
        )
        
        signatures.append(signature)
        
        # Store signature
        generated_signatures[format_type.value].append(signature.dict())
    
    return signatures

@app.get("/signatures")
async def get_signatures(
    format: Optional[SignatureFormat] = None,
    finding_type: Optional[FindingType] = None
):
    """Get all generated signatures with optional filtering"""
    all_sigs = []
    
    # Collect signatures from all formats
    for fmt, sigs in generated_signatures.items():
        if format and fmt != format.value:
            continue
        all_sigs.extend(sigs)
    
    # Filter by finding type
    if finding_type:
        all_sigs = [s for s in all_sigs if s["finding_type"] == finding_type.value]
    
    return {
        "signatures": all_sigs,
        "total": len(all_sigs),
        "by_format": {
            fmt: len([s for s in all_sigs if s["format"] == fmt])
            for fmt in SignatureFormat
        }
    }

@app.get("/signatures/{signature_id}")
async def get_signature(signature_id: str):
    """Get a specific signature by ID"""
    for sigs in generated_signatures.values():
        for sig in sigs:
            if sig["signature_id"] == signature_id:
                return sig
    
    raise HTTPException(404, "Signature not found")

@app.post("/export")
async def export_signatures(
    format: SignatureFormat,
    finding_ids: Optional[List[str]] = None
):
    """
    Export signatures in bulk
    
    Returns all signatures in the specified format,
    optionally filtered by finding IDs
    """
    sigs = generated_signatures[format.value]
    
    # Filter by finding IDs if provided
    if finding_ids:
        sigs = [s for s in sigs if s["finding_id"] in finding_ids]
    
    # Combine all signature content
    combined_content = "\n\n".join([s["content"] for s in sigs])
    
    return {
        "format": format.value,
        "count": len(sigs),
        "content": combined_content,
        "exported_at": datetime.utcnow().isoformat()
    }

@app.delete("/signatures")
async def clear_signatures():
    """Clear all generated signatures"""
    for fmt in generated_signatures:
        generated_signatures[fmt].clear()
    
    return {
        "status": "cleared",
        "message": "All signatures cleared"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    total_sigs = sum(len(sigs) for sigs in generated_signatures.values())
    
    return {
        "status": "healthy",
        "service": "signature-generator",
        "version": "1.0.0",
        "total_signatures": total_sigs,
        "by_format": {
            fmt: len(sigs)
            for fmt, sigs in generated_signatures.items()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
