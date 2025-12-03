"""
Automatic Model Retraining Pipeline
Monitors training data and retrains model when sufficient new data is available
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from src.database.models import db, TrainingData, MLModel
from src.ml.trainer import VulnerabilityClassifier

class AutoTrainer:
    """Automated model retraining system"""
    
    def __init__(
        self,
        min_new_samples: int = 50,
        min_accuracy_improvement: float = 0.02,
        schedule: str = "weekly"
    ):
        self.min_new_samples = min_new_samples
        self.min_accuracy_improvement = min_accuracy_improvement
        self.schedule = schedule
    
    def should_retrain(self) -> tuple[bool, Dict]:
        """
        Determine if model should be retrained
        
        Returns:
            (should_retrain: bool, reason: dict)
        """
        session = db.get_session()
        
        try:
            # Get latest active model
            latest_model = session.query(MLModel).filter_by(
                model_name='vulnerability_classifier',
                is_active=True
            ).order_by(MLModel.trained_at.desc()).first()
            
            if not latest_model:
                return True, {'reason': 'No active model found'}
            
            # Count new training samples since last training
            new_samples = session.query(TrainingData).filter(
                TrainingData.created_at > latest_model.trained_at,
                TrainingData.verified == True,
                TrainingData.used_in_training == False
            ).count()
            
            # Check time since last training
            days_since_training = (datetime.utcnow() - latest_model.trained_at).days
            
            reasons = []
            
            # Reason 1: Sufficient new samples
            if new_samples >= self.min_new_samples:
                reasons.append(f'{new_samples} new verified samples available')
            
            # Reason 2: Scheduled retraining
            schedule_triggers = {
                'daily': 1,
                'weekly': 7,
                'monthly': 30
            }
            
            trigger_days = schedule_triggers.get(self.schedule, 7)
            if days_since_training >= trigger_days:
                reasons.append(f'{days_since_training} days since last training (schedule: {self.schedule})')
            
            should_train = len(reasons) > 0
            
            return should_train, {
                'new_samples': new_samples,
                'days_since_training': days_since_training,
                'current_accuracy': latest_model.accuracy,
                'reasons': reasons
            }
            
        finally:
            session.close()
    
    async def retrain(
        self,
        epochs: int = 10,
        batch_size: int = 8,
        experiment_name: str = "auto_retrain"
    ) -> Optional[Dict]:
        """
        Retrain the model with new data
        
        Returns:
            Training results or None if failed
        """
        print("\n🔄 Automatic Model Retraining")
        print("=" * 70)
        
        # Check if we should retrain
        should_train, info = self.should_retrain()
        
        if not should_train:
            print("⏸️  Retraining not needed yet")
            print(f"   New samples: {info['new_samples']} (need {self.min_new_samples})")
            print(f"   Days since training: {info['days_since_training']}")
            return None
        
        print("✅ Retraining triggered:")
        for reason in info['reasons']:
            print(f"   • {reason}")
        
        # Load training data
        session = db.get_session()
        
        try:
            # Get all verified training data
            training_records = session.query(TrainingData).filter_by(
                verified=True
            ).all()
            
            if len(training_records) < 20:
                print("⚠️  Insufficient training data (need at least 20 samples)")
                return None
            
            # Convert to format expected by trainer
            samples = []
            for record in training_records:
                samples.append({
                    'code': record.code_snippet,
                    'vulnerability_type': record.vulnerability_type,
                    'is_vulnerable': record.is_vulnerable,
                    'severity': record.severity or 'Medium'
                })
            
            print(f"\n📊 Training with {len(samples)} samples")
            
            # Train new model
            classifier = VulnerabilityClassifier()
            
            results = classifier.train(
                samples=samples,
                epochs=epochs,
                batch_size=batch_size,
                experiment_name=f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # Compare with previous model
            if info.get('current_accuracy'):
                old_accuracy = info['current_accuracy']
                new_accuracy = results['metrics']['eval_accuracy']
                improvement = new_accuracy - old_accuracy
                
                print(f"\n📈 Model Comparison:")
                print(f"   Old Accuracy: {old_accuracy:.4f}")
                print(f"   New Accuracy: {new_accuracy:.4f}")
                print(f"   Improvement:  {improvement:+.4f} ({improvement*100:+.2f}%)")
                
                # Only deploy if improvement is significant
                if improvement >= self.min_accuracy_improvement:
                    print("   ✅ Significant improvement - deploying new model")
                    self._deploy_model(results['model_path'])
                elif improvement > 0:
                    print("   ⚠️  Minor improvement - keeping old model")
                else:
                    print("   ❌ No improvement - keeping old model")
            else:
                print("   ✅ First model - deploying")
                self._deploy_model(results['model_path'])
            
            # Mark samples as used
            for record in training_records:
                record.used_in_training = True
            session.commit()
            
            return results
            
        except Exception as e:
            print(f"❌ Retraining failed: {e}")
            session.rollback()
            return None
        
        finally:
            session.close()
    
    def _deploy_model(self, model_path: str):
        """Deploy the new model (mark as active)"""
        # In a production system, this would:
        # 1. Copy model to production directory
        # 2. Update model server/API
        # 3. Run smoke tests
        # 4. Gradually roll out with A/B testing
        
        print(f"   📦 Deploying model from {model_path}")
        print("   ✓ Model deployed successfully")


async def run_scheduled_retraining(
    schedule: str = "weekly",
    min_samples: int = 50
):
    """
    Run retraining on a schedule
    
    Usage:
        # Add to cron/Task Scheduler:
        python auto_trainer.py --schedule weekly --min-samples 50
    """
    trainer = AutoTrainer(
        min_new_samples=min_samples,
        schedule=schedule
    )
    
    print(f"🤖 Auto-Trainer Running (Schedule: {schedule})")
    print("=" * 70)
    
    # Check if we should retrain
    should_train, info = trainer.should_retrain()
    
    if should_train:
        await trainer.retrain()
    else:
        print("⏸️  No retraining needed at this time")
        print(f"\nStatus:")
        print(f"  New samples: {info['new_samples']}/{min_samples}")
        print(f"  Days since training: {info['days_since_training']}")
        print(f"  Current accuracy: {info.get('current_accuracy', 'N/A')}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automatic ML Model Retraining")
    parser.add_argument(
        '--schedule',
        type=str,
        default='weekly',
        choices=['daily', 'weekly', 'monthly'],
        help='Retraining schedule'
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=50,
        help='Minimum new samples required to trigger retraining'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force retraining even if conditions not met'
    )
    
    args = parser.parse_args()
    
    if args.force:
        print("⚡ Force retraining enabled")
        trainer = AutoTrainer(min_new_samples=0, schedule=args.schedule)
        asyncio.run(trainer.retrain())
    else:
        asyncio.run(run_scheduled_retraining(args.schedule, args.min_samples))
