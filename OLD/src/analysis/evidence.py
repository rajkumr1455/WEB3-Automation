"""
Evidence Generator
Creates visual evidence for vulnerabilities (diagrams, charts, screenshots)
"""
import os
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
from datetime import datetime
from src.database.models import db, Vulnerability, Evidence

class EvidenceGenerator:
    """Generate visual evidence for vulnerability reports"""
    
    def __init__(self, output_dir: str = "reports/evidence"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        sns.set_theme(style="darkgrid")
        plt.rcParams['figure.facecolor'] = '#1a1a1a'
        plt.rcParams['axes.facecolor'] = '#2d2d2d'
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'
    
    def generate_state_transition_diagram(
        self,
        vulnerability_id: int,
        before_state: Dict,
        after_state: Dict,
        title: str = "Contract State Transition"
    ) -> str:
        """
        Generate before/after state diagram
        
        Args:
            before_state: {'vault_balance': 100, 'attacker_balance': 0}
            after_state: {'vault_balance': 0, 'attacker_balance': 100}
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Before state
        accounts = list(before_state.keys())
        balances_before = list(before_state.values())
        
        colors_before = ['#ff6b6b' if 'attacker' in acc.lower() else '#4ecdc4' for acc in accounts]
        
        ax1.barh(accounts, balances_before, color=colors_before)
        ax1.set_xlabel('Balance (ETH)', color='white')
        ax1.set_title('Before Exploit', color='white', fontsize=14, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        # After state
        balances_after = list(after_state.values())
        colors_after = ['#ff6b6b' if 'attacker' in acc.lower() else '#4ecdc4' for acc in accounts]
        
        ax2.barh(accounts, balances_after, color=colors_after)
        ax2.set_xlabel('Balance (ETH)', color='white')
        ax2.set_title('After Exploit', color='white', fontsize=14, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        # Add delta annotations
        for i, (acc, before, after) in enumerate(zip(accounts, balances_before, balances_after)):
            delta = after - before
            if delta != 0:
                symbol = '📈' if delta > 0 else '📉'
                ax2.text(after, i, f'  {symbol} {delta:+.2f}', va='center', color='#ffe66d', fontweight='bold')
        
        fig.suptitle(title, color='white', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        # Save
        filename = f"state_transition_{vulnerability_id}_{int(datetime.now().timestamp())}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
        plt.close()
        
        # Save to database
        self._save_evidence_record(vulnerability_id, filepath, 'state_diagram', 'State transition visualization')
        
        print(f"   ✓ Generated state diagram: {filename}")
        return filepath
    
    def generate_transaction_flow(
        self,
        vulnerability_id: int,
        steps: List[Dict],
        title: str = "Exploit Transaction Flow"
    ) -> str:
        """
        Generate transaction flow diagram
        
        Args:
            steps: [
                {'from': 'Attacker', 'to': 'Vault', 'action': 'deposit()', 'value': '0.5 ETH'},
                {'from': 'Vault', 'to': 'Attacker', 'action': 'withdraw()', 'value': '0.5 ETH'},
                ...
            ]
        """
        fig, ax = plt.subplots(figsize=(12, max(8, len(steps) * 0.8)))
        
        # Draw timeline
        y_positions = list(range(len(steps), 0, -1))
        
        for i, step in enumerate(steps):
            y = y_positions[i]
            
            # Step number
            ax.text(0, y, f"Step {i+1}", 
                   bbox=dict(boxstyle='circle', facecolor='#4ecdc4', edgecolor='white'),
                   ha='center', va='center', fontweight='bold', fontsize=10)
            
            # Arrow
            ax.annotate('', xy=(3.5, y), xytext=(0.5, y),
                       arrowprops=dict(arrowstyle='->', lw=2, color='#ffe66d'))
            
            # Action details
            action_text = f"{step['from']} → {step['to']}\n{step['action']}"
            if step.get('value'):
                action_text += f"\nValue: {step['value']}"
            
            ax.text(2, y, action_text,
                   bbox=dict(boxstyle='round', facecolor='#2d2d2d', edgecolor='#4ecdc4'),
                   ha='center', va='center', fontsize=9, color='white')
        
        ax.set_xlim(-0.5, 4)
        ax.set_ylim(0, len(steps) + 1)
        ax.axis('off')
        ax.set_title(title, color='white', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Save
        filename = f"transaction_flow_{vulnerability_id}_{int(datetime.now().timestamp())}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
        plt.close()
        
        # Save to database
        self._save_evidence_record(vulnerability_id, filepath, 'transaction_flow', 'Exploit transaction sequence')
        
        print(f"   ✓ Generated transaction flow: {filename}")
        return filepath
    
    def generate_impact_chart(
        self,
        vulnerability_id: int,
        impact_data: Dict,
        title: str = "Vulnerability Impact Analysis"
    ) -> str:
        """
        Generate impact visualization
        
        Args:
            impact_data: {
                'funds_drained': 50000,
                'attack_cost': 45,
                'profit': 49955,
                'affected_users': 150
            }
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # Financial Impact
        categories = ['Funds Drained', 'Attacker Profit', 'Attack Cost']
        values = [
            impact_data.get('funds_drained', 0),
            impact_data.get('profit', 0),
            impact_data.get('attack_cost', 0)
        ]
        colors = ['#ff6b6b', '#ffe66d', '#4ecdc4']
        
        ax1.bar(categories, values, color=colors, edgecolor='white', linewidth=1.5)
        ax1.set_ylabel('USD ($)', color='white', fontweight='bold')
        ax1.set_title('Financial Impact', color='white', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='x', rotation=15)
        ax1.grid(axis='y', alpha=0.3)
        
        # Profit Ratio
        if impact_data.get('attack_cost', 0) > 0:
            profit_ratio = impact_data.get('profit', 0) / impact_data.get('attack_cost', 1)
            ax2.pie([profit_ratio, 1], labels=['Profit', 'Cost'], colors=['#4ecdc4', '#ff6b6b'],
                   autopct='%1.0f%%', startangle=90, textprops={'color': 'white', 'fontweight': 'bold'})
            ax2.set_title(f'ROI: {profit_ratio:.0f}x', color='white', fontsize=12, fontweight='bold')
        
        # Severity Distribution
        severity = impact_data.get('severity', 'High')
        severity_color = {'Critical': '#ff6b6b', 'High': '#ff9f1c', 'Medium': '#ffe66d', 'Low': '#4ecdc4'}
        
        ax3.barh(['Severity'], [1], color=severity_color.get(severity, '#ffe66d'))
        ax3.set_xlim(0, 1)
        ax3.set_title(f'Severity: {severity}', color='white', fontsize=12, fontweight='bold')
        ax3.axis('off')
        
        # Affected Users (if provided)
        if impact_data.get('affected_users'):
            users = impact_data['affected_users']
            ax4.text(0.5, 0.5, f"{users:,}\nAffected Users",
                    ha='center', va='center', fontsize=20, fontweight='bold',
                    color='#ff6b6b',
                    bbox=dict(boxstyle='round', facecolor='#2d2d2d', edgecolor='white', linewidth=2))
            ax4.axis('off')
        else:
            ax4.axis('off')
        
        fig.suptitle(title, color='white', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        # Save
        filename = f"impact_analysis_{vulnerability_id}_{int(datetime.now().timestamp())}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
        plt.close()
        
        # Save to database
        self._save_evidence_record(vulnerability_id, filepath, 'impact_chart', 'Vulnerability impact visualization')
        
        print(f"   ✓ Generated impact chart: {filename}")
        return filepath
    
    def _save_evidence_record(self, vulnerability_id: int, filepath: str, evidence_type: str, description: str):
        """Save evidence record to database"""
        session = db.get_session()
        
        try:
            evidence = Evidence(
                vulnerability_id=vulnerability_id,
                evidence_type=evidence_type,
                file_path=filepath,
                description=description
            )
            
            session.add(evidence)
            session.commit()
            
        except Exception as e:
            print(f"   ⚠️  Failed to save evidence record: {e}")
            session.rollback()
        
        finally:
            session.close()


if __name__ == "__main__":
    # Test evidence generator
    gen = EvidenceGenerator()
    
    # Test state transition diagram
    before = {
        'Vault': 10.0,
        'Attacker': 0.5,
        'User1': 2.0,
        'User2': 1.5
    }
    
    after = {
        'Vault': 0.0,
        'Attacker': 14.0,
        'User1': 0.0,
        'User2': 0.0
    }
    
    state_diagram = gen.generate_state_transition_diagram(
        vulnerability_id=999,
        before_state=before,
        after_state=after,
        title="Reentrancy Attack - State Transition"
    )
    
    # Test transaction flow
    flow_steps = [
        {'from': 'Attacker', 'to': 'Vault', 'action': 'deposit()', 'value': '0.5 ETH'},
        {'from': 'Attacker', 'to': 'Vault', 'action': 'withdraw()', 'value': ''},
        {'from': 'Vault', 'to': 'Attacker', 'action': 'transfer', 'value': '0.5 ETH'},
        {'from': 'Attacker', 'to': 'Vault', 'action': 'withdraw() [REENTRANT]', 'value': ''},
        {'from': 'Vault', 'to': 'Attacker', 'action': 'transfer', 'value': '0.5 ETH'},
        {'from': 'Vault', 'to': 'Attacker', 'action': 'repeat until drained', 'value': '13.5 ETH'},
    ]
    
    flow_diagram = gen.generate_transaction_flow(
        vulnerability_id=999,
        steps=flow_steps,
        title="Reentrancy Exploit - Transaction Flow"
    )
    
    # Test impact chart
    impact = {
        'funds_drained': 50000,
        'attack_cost': 45,
        'profit': 49955,
        'affected_users': 150,
        'severity': 'Critical'
    }
    
    impact_chart = gen.generate_impact_chart(
        vulnerability_id=999,
        impact_data=impact,
        title="Critical Reentrancy - Impact Analysis"
    )
    
    print("\n✅ Evidence generation complete!")
    print(f"   State Diagram: {state_diagram}")
    print(f"   Flow Diagram: {flow_diagram}")
    print(f"   Impact Chart: {impact_chart}")
