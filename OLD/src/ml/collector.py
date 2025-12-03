"""
Automated Training Data Collection
Collects vulnerability examples from multiple sources:
- Public CVE databases
- Bug bounty disclosures  
- GitHub security advisories
- Audit reports
"""
import os
import json
import asyncio
import aiohttp
from typing import List, Dict
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tqdm import tqdm
from src.database.models import db, TrainingData

class TrainingDataCollector:
    """Collect and curate training data from public sources"""
    
    def __init__(self):
        self.session = None
        self.sources = {
            'github': self.collect_from_github_advisories,
            'immunefi': self.collect_from_immunefi,
            'smartbugs': self.collect_from_smartbugs,
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def collect_from_github_advisories(self) -> List[Dict]:
        """
        Collect from GitHub Security Advisories
        Uses GitHub API to find Solidity-related vulnerabilities
        """
        print("\n📡 Collecting from GitHub Security Advisories...")
        
        samples = []
        
        # GitHub GraphQL API for security advisories
        # For now, we'll use a simplified approach
        # In production, you'd use GitHub's API with authentication
        
        url = "https://api.github.com/advisories"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        try:
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    advisories = await response.json()
                    
                    for advisory in advisories[:10]:  # Limit for demo
                        if 'solidity' in str(advisory).lower():
                            samples.append({
                                'source': 'github_advisory',
                                'code': advisory.get('description', ''),
                                'vulnerability_type': advisory.get('severity', 'Unknown'),
                                'is_vulnerable': True,
                                'metadata': advisory
                            })
        except Exception as e:
            print(f"⚠️  GitHub API error: {e}")
        
        print(f"   ✓ Collected {len(samples)} samples from GitHub")
        return samples
    
    async def collect_from_immunefi(self) -> List[Dict]:
        """
        Collect from Immunefi bug bounty disclosures
        Note: This is a simplified version. Real implementation would need proper scraping
        """
        print("\n📡 Collecting from Immunefi disclosures...")
        
        samples = []
        
        # In a real implementation, you would:
        # 1. Scrape Immunefi's disclosed vulnerabilities
        # 2. Extract contract code and vulnerability details
        # 3. Parse and structure the data
        
        # For now, we'll return empty and rely on other sources
        print("   ℹ️  Immunefi scraping requires authentication (skipped)")
        
        return samples
    
    async def collect_from_smartbugs(self) -> List[Dict]:
        """
        Collect from SmartBugs Curated dataset (already downloaded)
        """
        print("\n📁 Processing SmartBugs Curated dataset...")
        
        samples = []
        dataset_dir = os.path.join(os.path.dirname(__file__), "..", "data", "smartbugs-curated")
        
        if not os.path.exists(dataset_dir):
            print("   ⚠️  SmartBugs dataset not found")
            return samples
        
        # SmartBugs has categorized vulnerabilities
        vulnerability_dirs = {
            'reentrancy': 'Reentrancy',
            'access_control': 'Access Control',
            'arithmetic': 'Integer Overflow/Underflow',
            'unchecked_low_level_calls': 'Unchecked Return Values',
            'denial_of_service': 'Denial of Service',
            'bad_randomness': 'Timestamp Dependence',
            'front_running': 'Front-Running',
            'time_manipulation': 'Timestamp Dependence',
            'short_addresses': 'Short Address Attack'
        }
        
        for vuln_dir, vuln_type in vulnerability_dirs.items():
            dir_path = os.path.join(dataset_dir, vuln_dir)
            
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith('.sol'):
                        file_path = os.path.join(dir_path, filename)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                code = f.read()
                            
                            # Extract functions (simplified - take whole contract for now)
                            if len(code) > 100 and len(code) < 10000:  # Reasonable size
                                samples.append({
                                    'source': 'smartbugs',
                                    'code': code,
                                    'vulnerability_type': vuln_type,
                                    'is_vulnerable': True,
                                    'severity': 'High',
                                    'extra_data': {
                                        'filename': filename,
                                        'category': vuln_dir
                                    }
                                })
                        except Exception as e:
                            print(f"   Error reading {filename}: {e}")
        
        print(f"   ✓ Collected {len(samples)} samples from SmartBugs")
        return samples
    
    async def collect_all(self) -> List[Dict]:
        """Collect from all sources"""
        print("🔍 Starting training data collection...")
        print("=" * 50)
        
        all_samples = []
        
        for source_name, collector_func in self.sources.items():
            try:
                samples = await collector_func()
                all_samples.extend(samples)
            except Exception as e:
                print(f"❌ Error collecting from {source_name}: {e}")
        
        print(f"\n✓ Total samples collected: {len(all_samples)}")
        return all_samples
    
    def save_to_database(self, samples: List[Dict], verify: bool = True):
        """Save collected samples to database"""
        print(f"\n💾 Saving {len(samples)} samples to database...")
        
        session = db.get_session()
        
        try:
            saved_count = 0
            skipped_count = 0
            
            for sample in tqdm(samples, desc="Saving"):
                # Check for duplicates (basic check by code hash)
                code_hash = hash(sample['code'])
                
                existing = session.query(TrainingData).filter_by(
                    code_snippet=sample['code']
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                training_record = TrainingData(
                    source=sample.get('source', 'unknown'),
                    code_snippet=sample['code'],
                    vulnerability_type=sample['vulnerability_type'],
                    is_vulnerable=sample['is_vulnerable'],
                    severity=sample.get('severity', 'Medium'),
                    verified=verify,  # Auto-verify samples from trusted sources
                    confidence=0.8 if verify else 0.5,
                    metadata=sample.get('metadata', {})
                )
                
                session.add(training_record)
                saved_count += 1
            
            session.commit()
            
            print(f"✓ Saved: {saved_count} | Skipped (duplicates): {skipped_count}")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error saving to database: {e}")
            raise
        
        finally:
            session.close()


async def bootstrap_training_data():
    """Bootstrap initial training dataset"""
    print("\n🚀 Bootstrapping Training Data")
    print("=" * 50)
    
    async with TrainingDataCollector() as collector:
        # Collect from all sources
        samples = await collector.collect_all()
        
        if not samples:
            print("\n⚠️  No samples collected!")
            print("\nMake sure you have:")
            print("1. SmartBugs dataset: python rag_pipeline/ingest_data.py")
            print("2. Internet connection for GitHub API")
            return
        
        # Save to database
        collector.save_to_database(samples, verify=True)
    
    print("\n" + "=" * 50)
    print("✅ Training data collection complete!")
    print("\nNext steps:")
    print("1. Review data: SELECT * FROM training_data LIMIT 10")
    print("2. Train model: python ml_trainer.py")


if __name__ == "__main__":
    # Run bootstrap
    asyncio.run(bootstrap_training_data())
