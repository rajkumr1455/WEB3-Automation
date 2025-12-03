"""
Feedback Collection System
Collects user feedback, bounty results, and verification outcomes
"""
from sqlalchemy import func
from datetime import datetime
from typing import Dict, Optional
from src.database.models import db, Vulnerability, TrainingData, ScanResult

class FeedbackCollector:
    """Collect and manage feedback for continuous learning"""
    
    def __init__(self):
        self.session = db.get_session()
    
    def rate_vulnerability(
        self,
        vulnerability_id: int,
        rating: int,
        is_false_positive: bool = False,
        notes: str = ""
    ) -> bool:
        """
        Rate a vulnerability detection
        
        Args:
            vulnerability_id: ID of the vulnerability
            rating: 1-5 stars (1=poor, 5=excellent)
            is_false_positive: Whether this was a false positive
            notes: Additional feedback notes
        """
        try:
            vuln = self.session.query(Vulnerability).filter_by(id=vulnerability_id).first()
            
            if not vuln:
                print(f"Vulnerability {vulnerability_id} not found")
                return False
            
            vuln.user_rating = rating
            vuln.is_false_positive = is_false_positive
            vuln.feedback_at = datetime.utcnow()
            
            # Update metadata
            if not vuln.extra_data:
                vuln.extra_data = {}
            vuln.extra_data['feedback_notes'] = notes
            
            self.session.commit()
            
            # Add to training data if rated
            self._add_to_training_data(vuln, rating, is_false_positive)
            
            print(f"✓ Feedback recorded for vulnerability #{vulnerability_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to record feedback: {e}")
            self.session.rollback()
            return False
    
    def record_bounty_result(
        self,
        vulnerability_id: int,
        submitted: bool = True,
        accepted: bool = False,
        reward: float = 0.0,
        platform: str = "",
        notes: str = ""
    ) -> bool:
        """
        Record bug bounty submission result
        
        Args:
            vulnerability_id: ID of the vulnerability
            submitted: Whether it was submitted to a platform
            accepted: Whether it was accepted
            reward: Bounty reward amount in USD
            platform: Platform name (HackerOne, Immunefi, etc.)
            notes: Additional notes
        """
        try:
            vuln = self.session.query(Vulnerability).filter_by(id=vulnerability_id).first()
            
            if not vuln:
                print(f"Vulnerability {vulnerability_id} not found")
                return False
            
            vuln.bounty_submitted = submitted
            vuln.bounty_accepted = accepted
            vuln.bounty_reward = reward
            
            # Update metadata
            if not vuln.extra_data:
                vuln.extra_data = {}
            
            vuln.extra_data['bounty_platform'] = platform
            vuln.extra_data['bounty_notes'] = notes
            vuln.extra_data['bounty_timestamp'] = datetime.utcnow().isoformat()
            
            self.session.commit()
            
            # Add to training data with high confidence if accepted
            if accepted:
                self._add_to_training_data(vuln, rating=5, is_false_positive=False)
            elif submitted and not accepted:
                # Mark as potential false positive or low quality
                self._add_to_training_data(vuln, rating=2, is_false_positive=True)
            
            print(f"✓ Bounty result recorded for vulnerability #{vulnerability_id}")
            print(f"  Platform: {platform}, Accepted: {accepted}, Reward: ${reward}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to record bounty result: {e}")
            self.session.rollback()
            return False
    
    def _add_to_training_data(
        self,
        vuln: Vulnerability,
        rating: int,
        is_false_positive: bool
    ):
        """Add vulnerability to training dataset"""
        try:
            # Get the scan to retrieve source code
            scan = self.session.query(ScanResult).filter_by(id=vuln.scan_id).first()
            
            if not scan:
                return
            
            # Check if already exists
            existing = self.session.query(TrainingData).filter_by(
                source='feedback',
                source_id=vuln.id
            ).first()
            
            if existing:
                # Update existing
                existing.verified = not is_false_positive
                existing.confidence = rating / 5.0
                existing.is_vulnerable = not is_false_positive
            else:
                # Create new training sample
                training_sample = TrainingData(
                    source='feedback',
                    source_id=vuln.id,
                    code_snippet=scan.source_code[:5000],  # Limit size
                    vulnerability_type=vuln.vuln_type,
                    is_vulnerable=not is_false_positive,
                    severity=vuln.severity,
                    verified=True,
                    confidence=rating / 5.0,
                    extra_data={
                        'user_rating': rating,
                        'ml_confidence': vuln.ml_confidence,
                        'detected_by': vuln.detected_by
                    }
                )
                self.session.add(training_sample)
            
            self.session.commit()
            print(f"  ✓ Added to training data")
            
        except Exception as e:
            print(f"  ⚠️  Failed to add to training data: {e}")
            self.session.rollback()
    
    def get_feedback_stats(self) -> Dict:
        """Get feedback statistics"""
        try:
            total_vulns = self.session.query(Vulnerability).count()
            rated = self.session.query(Vulnerability).filter(
                Vulnerability.user_rating.isnot(None)
            ).count()
            false_positives = self.session.query(Vulnerability).filter_by(
                is_false_positive=True
            ).count()
            bounties_submitted = self.session.query(Vulnerability).filter_by(
                bounty_submitted=True
            ).count()
            bounties_accepted = self.session.query(Vulnerability).filter_by(
                bounty_accepted=True
            ).count()
            
            total_rewards = self.session.query(func.sum(Vulnerability.bounty_reward)).filter(
                Vulnerability.bounty_accepted == True
            ).scalar() or 0.0
            
            stats = {
                'total_vulnerabilities': total_vulns,
                'rated': rated,
                'rating_percentage': (rated / total_vulns * 100) if total_vulns > 0 else 0,
                'false_positives': false_positives,
                'false_positive_rate': (false_positives / total_vulns * 100) if total_vulns > 0 else 0,
                'bounties_submitted': bounties_submitted,
                'bounties_accepted': bounties_accepted,
                'acceptance_rate': (bounties_accepted / bounties_submitted * 100) if bounties_submitted > 0 else 0,
                'total_rewards': total_rewards
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Close database session"""
        self.session.close()


if __name__ == "__main__":
    # Test feedback collector
    collector = FeedbackCollector()
    
    print("\n📊 Feedback Statistics")
    print("=" * 50)
    stats = collector.get_feedback_stats()
    
    for key, value in stats.items():
        if 'rate' in key or 'percentage' in key:
            print(f"{key}: {value:.1f}%")
        elif 'rewards' in key:
            print(f"{key}: ${value:,.2f}")
        else:
            print(f"{key}: {value}")
    
    collector.close()
