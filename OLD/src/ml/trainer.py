"""
ML Training Pipeline for Smart Contract Vulnerability Detection
Supports both GPU and CPU training with automatic fallback
"""
import os
import json
import torch
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import mlflow
from tqdm import tqdm
from src.database.models import db, TrainingData, MLModel

class VulnerabilityClassifier:
    """
    Fine-tuned CodeBERT/CodeT5 for vulnerability classification
    Supports GPU (CUDA) and CPU with automatic detection
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/codebert-base",
        num_labels: int = 10,  # Number of vulnerability types
        device: str = "auto"
    ):
        self.model_name = model_name
        self.num_labels = num_labels
        
        # Auto-detect device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"🔧 Initializing ML Trainer on device: {self.device.upper()}")
        if self.device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = None
        self.vulnerability_types = [
            "Reentrancy",
            "Integer Overflow/Underflow",
            "Access Control",
            "Unchecked Return Values",
            "Denial of Service",
            "Front-Running",
            "Timestamp Dependence",
            "Tx.Origin Authentication",
            "Delegate Call",
            "Uninitialized Storage"
        ]
        
    def load_training_data_from_db(self) -> List[Dict]:
        """Load training data from database"""
        print("📊 Loading training data from database...")
        session = db.get_session()
        
        try:
            data_records = session.query(TrainingData).filter_by(verified=True).all()
            
            training_samples = []
            for record in data_records:
                training_samples.append({
                    'code': record.code_snippet,
                    'vulnerability_type': record.vulnerability_type,
                    'is_vulnerable': record.is_vulnerable,
                    'severity': record.severity or 'Medium'
                })
            
            print(f"✓ Loaded {len(training_samples)} verified training samples")
            return training_samples
            
        finally:
            session.close()
    
    def prepare_dataset(self, samples: List[Dict]) -> Tuple[List, List]:
        """Prepare dataset for training"""
        print("🔄 Preparing dataset...")
        
        texts = []
        labels = []
        
        for sample in samples:
            texts.append(sample['code'])
            
            # Map vulnerability type to label index
            vuln_type = sample['vulnerability_type']
            if vuln_type in self.vulnerability_types:
                label = self.vulnerability_types.index(vuln_type)
            else:
                label = 0  # Default to first type
            
            if not sample['is_vulnerable']:
                label = self.num_labels - 1  # Last label for "No Vulnerability"
            
            labels.append(label)
        
        print(f"✓ Prepared {len(texts)} samples")
        return texts, labels
    
    def tokenize_data(self, texts: List[str], max_length: int = 512):
        """Tokenize code snippets"""
        return self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        )
    
    def train(
        self,
        samples: List[Dict] = None,
        epochs: int = 10,
        batch_size: int = 8,
        learning_rate: float = 2e-5,
        output_dir: str = "models/vulnerability_classifier",
        experiment_name: str = "vulnerability_detection"
    ) -> Dict:
        """
        Train the vulnerability classifier
        """
        # Load data from DB if not provided
        if samples is None:
            samples = self.load_training_data_from_db()
        
        if len(samples) < 10:
            print("⚠️  Warning: Very few training samples. Need at least 100 for good performance.")
            print("   Run data collection first: python rag_pipeline/live_updater.py")
        
        # Prepare dataset
        texts, labels = self.prepare_dataset(samples)
        
        # Split data
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        print(f"📊 Dataset split: {len(train_texts)} train, {len(val_texts)} validation")
        
        # Tokenize
        train_encodings = self.tokenize_data(train_texts)
        val_encodings = self.tokenize_data(val_texts)
        
        # Create PyTorch datasets
        class VulnDataset(torch.utils.data.Dataset):
            def __init__(self, encodings, labels):
                self.encodings = encodings
                self.labels = labels
            
            def __getitem__(self, idx):
                item = {key: val[idx] for key, val in self.encodings.items()}
                item['labels'] = torch.tensor(self.labels[idx])
                return item
            
            def __len__(self):
                return len(self.labels)
        
        train_dataset = VulnDataset(train_encodings, train_labels)
        val_dataset = VulnDataset(val_encodings, val_labels)
        
        # Initialize model
        print(f"🚀 Loading model: {self.model_name}")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=self.num_labels
        )
        self.model.to(self.device)
        
        # Training arguments
        os.makedirs(output_dir, exist_ok=True)
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=10,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="accuracy",
            greater_is_better=True,
            warmup_steps=100,
            fp16=self.device == "cuda",  # Use mixed precision on GPU
            dataloader_num_workers=0,  # Avoid multiprocessing issues on Windows
        )
        
        # Metrics
        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            predictions = np.argmax(predictions, axis=1)
            
            accuracy = accuracy_score(labels, predictions)
            precision, recall, f1, _ = precision_recall_fscore_support(
                labels, predictions, average='weighted'
            )
            
            return {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
        
            # Trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                compute_metrics=compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # Train
            print("\n🏋️  Training started...")
            train_start = datetime.now()
            
            train_result = trainer.train()
            
            train_duration = (datetime.now() - train_start).total_seconds()
            print(f"✓ Training completed in {train_duration:.1f}s")
            
            # Evaluate
            print("\n📈 Evaluating model...")
            eval_results = trainer.evaluate()
            
            # Log metrics
            mlflow.log_metrics(eval_results)
            mlflow.log_metric("training_duration", train_duration)
            
            # Save model
            print(f"💾 Saving model to {output_dir}")
            trainer.save_model(output_dir)
            self.tokenizer.save_pretrained(output_dir)
            
            # Save to database
            session = db.get_session()
            try:
                model_record = MLModel(
                    model_name="vulnerability_classifier",
                    model_type="transformer",
                    version=datetime.now().strftime("%Y%m%d_%H%M%S"),
                    model_path=output_dir,
                    mlflow_run_id=run.info.run_id,
                    accuracy=eval_results.get('eval_accuracy'),
                    precision=eval_results.get('eval_precision'),
                    recall=eval_results.get('eval_recall'),
                    f1_score=eval_results.get('eval_f1'),
                    training_samples=len(samples),
                    training_duration=train_duration,
                    is_active=True,
                    metadata={
                        'device': self.device,
                        'model_name': self.model_name,
                        'num_labels': self.num_labels
                    }
                )
                
                # Deactivate previous models
                session.query(MLModel).filter_by(
                    model_name="vulnerability_classifier",
                    is_active=True
                ).update({'is_active': False})
                
                session.add(model_record)
                session.commit()
                print(f"✓ Model record saved to database (ID: {model_record.id})")
                
            finally:
                session.close()
            
            print("\n" + "="*50)
            print("🎉 Training Complete!")
            print("="*50)
            print(f"Accuracy:  {eval_results['eval_accuracy']:.4f}")
            print(f"Precision: {eval_results['eval_precision']:.4f}")
            print(f"Recall:    {eval_results['eval_recall']:.4f}")
            print(f"F1 Score:  {eval_results['eval_f1']:.4f}")
            print(f"Model: {output_dir}")
            print(f"MLflow Run: {run.info.run_id}")
            
            return {
                'metrics': eval_results,
                'model_path': output_dir,
                'run_id': run.info.run_id,
                'training_duration': train_duration
            }
    
    def predict(self, code: str) -> Dict:
        """Predict vulnerability for a code snippet"""
        if self.model is None:
            raise ValueError("Model not loaded. Train or load a model first.")
        
        inputs = self.tokenizer(
            code,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class = torch.argmax(predictions, dim=-1).item()
            confidence = predictions[0][predicted_class].item()
        
        result = {
            'vulnerability_type': self.vulnerability_types[predicted_class],
            'confidence': confidence,
            'all_scores': {
                self.vulnerability_types[i]: predictions[0][i].item()
                for i in range(self.num_labels)
            }
        }
        
        return result


if __name__ == "__main__":
    # Example usage
    print("ML Training Pipeline - Smart Contract Vulnerability Detection")
    print("=" * 70)
    
    classifier = VulnerabilityClassifier()
    
    # Check if we have training data
    session = db.get_session()
    sample_count = session.query(TrainingData).filter_by(verified=True).count()
    session.close()
    
    if sample_count < 10:
        print("\n⚠️  No training data found!")
        print("\nTo get started:")
        print("1. Run: python database/__init__.py  (initialize database)")
        print("2. Run: python rag_pipeline/live_updater.py  (collect training data)")
        print("3. Run: python ml_trainer.py  (train model)\n")
    else:
        print(f"\n✓ Found {sample_count} training samples")
        print("\nStarting training...")
        
        results = classifier.train(
            epochs=5,
            batch_size=8,
            experiment_name="vulnerability_classifier_v1"
        )
        
        print(f"\n✓ Model saved to: {results['model_path']}")
