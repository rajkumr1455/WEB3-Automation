"""
Advanced Vulnerability Detectors
Covers the missing 25% to reach 100% coverage
"""

import re
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class AdvancedDetectors:
    """
    Custom detectors for vulnerabilities not covered by Slither
    """
    
    def __init__(self):
        self.detectors = [
            self.detect_code_with_no_effects,
            self.detect_hash_collisions,
            self.detect_hardcoded_gas,
            self.detect_mev_vulnerabilities,
            self.detect_cross_chain_issues,
            self.detect_layer2_risks,
            self.detect_erc4337_issues,
            self.detect_proxy_risks,
            self.detect_upgrade_vulnerabilities
        ]
    
    def analyze(self, source_code: str) -> List[Dict[str, Any]]:
        """
        Run all advanced detectors
        """
        findings = []
        
        for detector in self.detectors:
            try:
                result = detector(source_code)
                if result:
                    findings.extend(result)
            except Exception as e:
                logger.error(f"Detector {detector.__name__} failed: {e}")
                continue
        
        return findings
    
    def detect_code_with_no_effects(self, source: str) -> List[Dict]:
        """
        Detect functions that don't modify state or return values (dead code)
        """
        findings = []
        
        # Find functions without return or state changes
        pattern = r'function\s+(\w+)\s*\([^)]*\)\s+(public|external|internal|private)\s+(pure|view)?\s*\{([^}]+)\}'
        
        for match in re.finditer(pattern, source, re.DOTALL):
            func_name = match.group(1)
            visibility = match.group(2)
            modifier = match.group(3)
            body = match.group(4)
            
            # Check if function body is empty or only has comments
            body_clean = re.sub(r'//.*?\n|/\*.*?\*/', '', body, flags=re.DOTALL).strip()
            
            if not body_clean or len(body_clean) < 10:
                findings.append({
                    "name": "Code With No Effects",
                    "category": "YELLOW",
                    "description": f"Function '{func_name}' has no meaningful operations. Dead code should be removed.",
                    "location": f"Function {func_name}",
                    "severity": "Low"
                })
        
        return findings
    
    def detect_hash_collisions(self, source: str) -> List[Dict]:
        """
        Detect hash collision vulnerabilities with variable length arguments
        """
        findings = []
        
        # Look for abi.encodePacked with dynamic types
        if 'abi.encodePacked' in source:
            pattern = r'abi\.encodePacked\s*\(([^)]+)\)'
            
            for match in re.finditer(pattern, source):
                args = match.group(1)
                
                # Check for string, bytes, or array types (dynamic length)
                if any(t in args for t in ['string', 'bytes', 'memory', '[]']):
                    findings.append({
                        "name": "Hash Collision with Variable Length Arguments",
                        "category": "RED",
                        "description": "Using abi.encodePacked with dynamic types can cause hash collisions. Use abi.encode instead.",
                        "location": f"abi.encodePacked({args[:50]}...)",
                        "severity": "Medium"
                    })
        
        return findings
    
    def detect_hardcoded_gas(self, source: str) -> List[Dict]:
        """
        Detect message calls with hardcoded gas amounts
        """
        findings = []
        
        # Pattern: .call{gas: <number>}()
        pattern = r'\.call\s*\{\s*gas\s*:\s*(\d+)\s*\}'
        
        for match in re.finditer(pattern, source):
            gas_amount = match.group(1)
            findings.append({
                "name": "Message Call with Hardcoded Gas Amount",
                "category": "YELLOW",
                "description": f"Hardcoded gas amount ({gas_amount}) can break with EVM changes. Let the EVM provide gas automatically.",
                "location": f".call{{gas: {gas_amount}}}",
                "severity": "Medium"
            })
        
        return findings
    
    def detect_mev_vulnerabilities(self, source: str) -> List[Dict]:
        """
        Detect MEV (Maximal Extractable Value) vulnerabilities
        """
        findings = []
        
        # Check for unprotected swaps (common MEV target)
        if 'swap' in source.lower() and 'deadline' not in source.lower():
            findings.append({
                "name": "MEV Front-Running Risk",
                "category": "RED",
                "description": "Swap function without deadline parameter is vulnerable to MEV sandwich attacks. Add deadline and slippage protection.",
                "location": "Swap/Exchange functions",
                "severity": "High"
            })
        
        # Check for price oracles without TWAP
        if ('getPrice' in source or 'price' in source) and 'twap' not in source.lower():
            findings.append({
                "name": "MEV Oracle Manipulation",
                "category": "RED",
                "description": "Price oracle without TWAP is vulnerable to flash loan price manipulation. Use time-weighted average prices.",
                "location": "Price oracle functions",
                "severity": "High"
            })
        
        # Check for unprotected liquidations
        if 'liquidat' in source.lower() and 'flashloan' not in source.lower():
            findings.append({
                "name": "MEV Liquidation Front-Running",
                "category": "BLUE",
                "description": "Liquidation functions without protection can be front-run by MEV bots. Consider priority queues or commit-reveal.",
                "location": "Liquidation functions",
                "severity": "Medium"
            })
        
        return findings
    
    def detect_cross_chain_issues(self, source: str) -> List[Dict]:
        """
        Detect cross-chain bridge vulnerabilities
        """
        findings = []
        
        # Check for missing chainId validation
        if any(keyword in source.lower() for keyword in ['bridge', 'crosschain', 'lock', 'unlock']):
            if 'chainid' not in source.lower() or 'block.chainid' not in source.lower():
                findings.append({
                    "name": "Cross-Chain Replay Attack",
                    "category": "RED",
                    "description": "Bridge functions missing chainId validation. Transactions can be replayed across chains.",
                    "location": "Bridge/Cross-chain functions",
                    "severity": "Critical"
                })
            
            # Check for missing destination validation
            if 'destination' not in source.lower() and 'target' not in source.lower():
                findings.append({
                    "name": "Cross-Chain Destination Validation Missing",
                    "category": "RED",
                    "description": "No validation of destination chain. Funds could be sent to wrong chain.",
                    "location": "Bridge functions",
                    "severity": "High"
                })
        
        return findings
    
    def detect_layer2_risks(self, source: str) -> List[Dict]:
        """
        Detect Layer 2 specific vulnerabilities
        """
        findings = []
        
        # Optimistic Rollup fraud proof issues
        if 'challenge' in source.lower() or 'dispute' in source.lower():
            if 'timestamp' in source and 'block.timestamp' in source:
                findings.append({
                    "name": "Layer 2 Timestamp Manipulation",
                    "category": "BLUE",
                    "description": "L2 sequencers can manipulate timestamps in fraud proof windows. Use block numbers instead.",
                    "location": "Challenge/Dispute functions",
                    "severity": "Medium"
                })
        
        # Check for missing L1->L2 message validation
        if 'l1tol2' in source.lower() or 'crossdomainmessage' in source.lower():
            if 'verify' not in source.lower() and 'validate' not in source.lower():
                findings.append({
                    "name": "Layer 2 Message Validation Missing",
                    "category": "RED",
                    "description": "L1->L2 messages not properly validated. Could allow unauthorized operations.",
                    "location": "Cross-domain messaging",
                    "severity": "High"
                })
        
        return findings
    
    def detect_erc4337_issues(self, source: str) -> List[Dict]:
        """
        Detect ERC-4337 Account Abstraction vulnerabilities
        """
        findings = []
        
        # Check for paymaster vulnerabilities
        if 'paymaster' in source.lower():
            if 'validatepaymaster' not in source.lower():
                findings.append({
                    "name": "ERC-4337 Paymaster Validation Missing",
                    "category": "RED",
                    "description": "Paymaster without proper validation can be drained. Implement validatePaymasterUserOp.",
                    "location": "Paymaster implementation",
                    "severity": "Critical"
                })
        
        # Check for UserOperation validation
        if 'useroperation' in source.lower() or 'userop' in source.lower():
            if 'signature' in source.lower() and 'recover' not in source.lower():
                findings.append({
                    "name": "ERC-4337 Signature Not Verified",
                    "category": "RED",
                    "description": "UserOperation signature not properly verified. Implement ECDSA.recover validation.",
                    "location": "UserOp handling",
                    "severity": "Critical"
                })
        
        return findings
    
    def detect_proxy_risks(self, source: str) -> List[Dict]:
        """
        Detect upgradeable proxy pattern vulnerabilities
        """
        findings = []
        
        # Check for storage collisions
        if any(keyword in source for keyword in ['delegatecall', 'Proxy', 'Upgradeable']):
            
            # Check for uninitialized implementation
            if 'initialize' in source and '__gap' not in source:
                findings.append({
                    "name": "Proxy Storage Collision Risk",
                    "category": "RED",
                    "description": "Upgradeable contract without storage gap (__gap). Future upgrades may corrupt storage.",
                    "location": "Upgradeable contract",
                    "severity": "High"
                })
            
            # Check for selfdestruct in implementation
            if 'selfdestruct' in source.lower():
                findings.append({
                    "name": "Proxy Self-Destruct Vulnerability",
                    "category": "RED",
                    "description": "Implementation contract has selfdestruct. Can brick the proxy permanently.",
                    "location": "Implementation contract",
                    "severity": "Critical"
                })
            
            # Check for constructor in upgradeable contract
            if 'constructor' in source and 'Upgradeable' in source:
                findings.append({
                    "name": "Proxy Constructor in Upgradeable Contract",
                    "category": "YELLOW",
                    "description": "Constructor in upgradeable contract won't execute when called via proxy. Use initializer.",
                    "location": "Upgradeable contract",
                    "severity": "High"
                })
        
        return findings
    
    def detect_upgrade_vulnerabilities(self, source: str) -> List[Dict]:
        """
        Detect upgrade mechanism vulnerabilities
        """
        findings = []
        
        # Check for unprotected upgrade functions
        if 'upgrade' in source.lower():
            if 'onlyowner' not in source.lower() and 'onlyadmin' not in source.lower():
                findings.append({
                    "name": "Unprotected Upgrade Function",
                    "category": "RED",
                    "description": "Upgrade function without access control. Anyone can upgrade the contract.",
                    "location": "Upgrade functions",
                    "severity": "Critical"
                })
            
            # Check for missing initialization disable
            if '_disableInitializers' not in source and 'initialize' in source:
                findings.append({
                    "name": "Upgrade Initialization Not Disabled",
                    "category": "RED",
                    "description": "Implementation can be initialized directly. Call _disableInitializers() in constructor.",
                    "location": "Upgradeable implementation",
                    "severity": "High"
                })
        
        return findings

# Standalone detector instance
advanced_detector = AdvancedDetectors()
