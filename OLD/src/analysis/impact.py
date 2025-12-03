"""
Impact Calculator
Calculates financial impact, severity scores, and exploitation costs
"""
import asyncio
import json
from typing import Dict, Optional
from web3 import Web3
import requests

class ImpactCalculator:
    """Calculate vulnerability impact metrics"""
    
    def __init__(self):
        self.eth_price = self._get_eth_price()
        self.severity_matrix = {
            'Critical': {'cvss_base': 9.0, 'multiplier': 1.0},
            'High': {'cvss_base': 7.0, 'multiplier': 0.7},
            'Medium': {'cvss_base': 5.0, 'multiplier': 0.4},
            'Low': {'cvss_base': 3.0, 'multiplier': 0.2}
        }
    
    def _get_eth_price(self) -> float:
        """Get current ETH price in USD"""
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                price = data['ethereum']['usd']
                print(f"📊 Current ETH price: ${price:,.2f}")
                return price
        except Exception as e:
            print(f"⚠️  Failed to fetch ETH price: {e}")
        
        # Default fallback
        return 2000.0
    
    def calculate_financial_impact(
        self,
        funds_at_risk_eth: float,
        attack_cost_eth: float = 0.0001  # ~$0.20 at $2000/ETH
    ) -> Dict:
        """
        Calculate financial impact of vulnerability
        
        Returns:
            {
                'funds_at_risk_usd': float,
                'funds_at_risk_eth': float,
                'attack_cost_usd': float,
                'attack_cost_eth': float,
                'potential_profit_usd': float,
                'profit_ratio': float
            }
        """
        funds_at_risk_usd = funds_at_risk_eth * self.eth_price
        attack_cost_usd = attack_cost_eth * self.eth_price
        potential_profit_usd = funds_at_risk_usd - attack_cost_usd
        profit_ratio = potential_profit_usd / attack_cost_usd if attack_cost_usd > 0 else 0
        
        return {
            'funds_at_risk_usd': round(funds_at_risk_usd, 2),
            'funds_at_risk_eth': round(funds_at_risk_eth, 6),
            'attack_cost_usd': round(attack_cost_usd, 2),
            'attack_cost_eth': round(attack_cost_eth, 6),
            'potential_profit_usd': round(potential_profit_usd, 2),
            'profit_ratio': round(profit_ratio, 2)
        }
    
    def calculate_cvss_score(
        self,
        vulnerability_type: str,
        severity: str,
        exploitability: str = 'high',  # high, medium, low
        scope_changed: bool = True,
        user_interaction: bool = False,
        privileges_required: bool = False
    ) -> float:
        """
        Calculate CVSS 3.1 score
        
        Formula components:
        - Base: from severity matrix
        - Exploitability: how easy to exploit
        - Scope: does it affect other contracts
        - Impact: financial/operational damage
        """
        base_score = self.severity_matrix.get(severity, {'cvss_base': 5.0})['cvss_base']
        
        # Exploitability adjustment
        exploit_scores = {'high': 1.0, 'medium': 0.8, 'low': 0.5}
        exploit_modifier = exploit_scores.get(exploitability, 0.8)
        
        # Scope change bonus
        scope_modifier = 1.2 if scope_changed else 1.0
        
        # User interaction penalty (easier if no interaction needed)
        interaction_modifier = 0.9 if user_interaction else 1.0
        
        # Privileges penalty
        privileges_modifier = 0.85 if privileges_required else 1.0
        
        # Calculate final score
        cvss = base_score * exploit_modifier * scope_modifier * interaction_modifier * privileges_modifier
        
        # Cap at 10.0
        cvss = min(10.0, cvss)
        
        return round(cvss, 1)
    
    def estimate_attack_cost(
        self,
        num_transactions: int = 1,
        gas_per_tx: int = 200000,
        gas_price_gwei: int = 30
    ) -> Dict:
        """
        Estimate cost to execute attack
        
        Returns:
            {
                'total_gas': int,
                'gas_price_gwei': int,
                'cost_eth': float,
                'cost_usd': float
            }
        """
        total_gas = num_transactions * gas_per_tx
        cost_wei = total_gas * gas_price_gwei * 1e9  # Convert gwei to wei
        cost_eth = Web3.from_wei(int(cost_wei), 'ether')
        cost_usd = float(cost_eth) * self.eth_price
        
        return {
            'total_gas': total_gas,
            'gas_price_gwei': gas_price_gwei,
            'cost_eth': round(float(cost_eth), 6),
            'cost_usd': round(cost_usd, 2)
        }
    
    def calculate_severity_tier(
        self,
        financial_impact_usd: float,
        cvss_score: float,
        exploitability: str
    ) -> str:
        """
        Determine bug bounty severity tier
        Based on typical bounty platform criteria
        """
        # Critical: >$1M or CVSS 9.0+
        if financial_impact_usd > 1_000_000 or cvss_score >= 9.0:
            return 'Critical'
        
        # High: $100K-$1M or CVSS 7.0-8.9
        elif financial_impact_usd > 100_000 or cvss_score >= 7.0:
            return 'High'
        
        # Medium: $10K-$100K or CVSS 4.0-6.9
        elif financial_impact_usd > 10_000 or cvss_score >= 4.0:
            return 'Medium'
        
        # Low: <$10K or CVSS <4.0
        else:
            return 'Low'
    
    def generate_full_impact_report(
        self,
        vulnerability_type: str,
        funds_at_risk_eth: float,
        num_transactions: int = 1,
        gas_per_tx: int = 200000,
        exploitability: str = 'high',
        scope_changed: bool = True,
        affected_users: int = 0
    ) -> Dict:
        """
        Generate comprehensive impact report
        """
        # Financial impact
        financial = self.calculate_financial_impact(funds_at_risk_eth)
        
        # Attack cost
        attack_cost = self.estimate_attack_cost(num_transactions, gas_per_tx)
        
        # Update financial with attack cost
        financial['attack_cost_eth'] = attack_cost['cost_eth']
        financial['attack_cost_usd'] = attack_cost['cost_usd']
        financial['potential_profit_usd'] = financial['funds_at_risk_usd'] - attack_cost['cost_usd']
        financial['profit_ratio'] = (
            financial['potential_profit_usd'] / attack_cost['cost_usd']
            if attack_cost['cost_usd'] > 0 else 0
        )
        
        # Determine severity from financial impact
        if financial['funds_at_risk_usd'] > 1_000_000:
            severity = 'Critical'
        elif financial['funds_at_risk_usd'] > 100_000:
            severity = 'High'
        elif financial['funds_at_risk_usd'] > 10_000:
            severity = 'Medium'
        else:
            severity = 'Low'
        
        # CVSS score
        cvss = self.calculate_cvss_score(
            vulnerability_type,
            severity,
            exploitability,
            scope_changed
        )
        
        # Final severity tier (may differ from initial)
        final_severity = self.calculate_severity_tier(
            financial['funds_at_risk_usd'],
            cvss,
            exploitability
        )
        
        # Estimated bounty reward (typical percentages)
        bounty_percentages = {
            'Critical': 0.10,  # 10% of TVL at risk
            'High': 0.05,      # 5%
            'Medium': 0.02,    # 2%
            'Low': 0.005       # 0.5%
        }
        
        estimated_bounty = (
            financial['funds_at_risk_usd'] * 
            bounty_percentages.get(final_severity, 0.02)
        )
        
        return {
            'vulnerability_type': vulnerability_type,
            'severity': final_severity,
            'cvss_score': cvss,
            'financial_impact': financial,
            'attack_cost': attack_cost,
            'exploitability': exploitability,
            'affected_users': affected_users,
            'estimated_bounty': round(estimated_bounty, 2),
            'difficulty': self._get_difficulty_label(exploitability),
            'summary': self._generate_summary(
                vulnerability_type,
                final_severity,
                financial,
                cvss
            )
        }
    
    def _get_difficulty_label(self, exploitability: str) -> str:
        """Convert exploitability to difficulty"""
        mapping = {
            'high': 'Easy',
            'medium': 'Medium',
            'low': 'Hard'
        }
        return mapping.get(exploitability, 'Medium')
    
    def _generate_summary(
        self,
        vuln_type: str,
        severity: str,
        financial: Dict,
        cvss: float
    ) -> str:
        """Generate human-readable summary"""
        return (
            f"{severity} severity {vuln_type} vulnerability with CVSS score {cvss}. "
            f"Potential loss: ${financial['funds_at_risk_usd']:,.2f} "
            f"({financial['funds_at_risk_eth']:.4f} ETH). "
            f"Attack cost: ${financial['attack_cost_usd']:.2f}. "
            f"ROI: {financial['profit_ratio']:.0f}x"
        )


if __name__ == "__main__":
    # Test impact calculator
    calc = ImpactCalculator()
    
    print("\n" + "="*70)
    print("Testing Impact Calculator")
    print("="*70)
    
    # Example: Critical Reentrancy on DeFi protocol
    report = calc.generate_full_impact_report(
        vulnerability_type="Reentrancy",
        funds_at_risk_eth=50.0,  # 50 ETH at risk
        num_transactions=3,       # 3 transactions to exploit
        gas_per_tx=250000,        # 250k gas each
        exploitability='high',
        scope_changed=True,
        affected_users=200
    )
    
    print("\n📊 Impact Report:")
    print(json.dumps(report, indent=2))
    
    print(f"\n📌 Summary:")
    print(f"   {report['summary']}")
    print(f"\n💰 Estimated Bug Bounty: ${report['estimated_bounty']:,.2f}")
