from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import asyncio
import json
import os
from datetime import datetime
from enum import Enum
import numpy as np
from collections import defaultdict

app = FastAPI(
    title="ML-Ops Engine",
    description="Continuous learning and rule generation from validated findings",
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


# In-memory storage for training data and models
training_data: List[Dict] = []
detection_rules: List[Dict] = []
model_metrics: Dict[str, Any] = {
    "total_findings": 0,
    "validated_findings": 0,
    "false_positives": 0,
    "accuracy": 0.0,
    "precision": 0.0,
    "recall": 0.0,
    "rules_generated": 0
}

class FindingType(str, Enum):
    """Types of security findings"""
    REENTRANCY = "reentrancy"
    INTEGER_OVERFLOW = "integer_overflow"
    ACCESS_CONTROL = "access_control"
    UNCHECKED_CALL = "unchecked_call"
    FLASH_LOAN = "flash_loan"
    PRICE_MANIPULATION = "price_manipulation"
    FRONT_RUNNING = "front_running"
    TIMESTAMP_DEPENDENCE = "timestamp_dependence"
    OTHER = "other"

class ValidatedFinding(BaseModel):
    """Validated security finding for training"""
    finding_id: str
    type: FindingType
    severity: str
    is_valid: bool
    confidence: float
    source_code: Optional[str] = None
    execution_trace: Optional[str] = None
    patterns: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DetectionRule(BaseModel):
    """Generated detection rule"""
    rule_id: str
    name: str
    description: str
    finding_type: FindingType
    severity: str
    pattern: str
    confidence_threshold: float
    false_positive_rate: float
    created_at: datetime
    validated_count: int = 0

class TrainingRequest(BaseModel):
    """Request to train models"""
    min_samples: int = Field(default=10, description="Minimum samples per finding type")
    retrain: bool = Field(default=False, description="Retrain all models")

class RuleGenerationRequest(BaseModel):
    """Request to generate new detection rules"""
    finding_types: Optional[List[FindingType]] = None
    min_confidence: float = Field(default=0.8, description="Minimum confidence")
    min_samples: int = Field(default=5, description="Minimum validated samples")

class PatternExtractor:
    """
    Extract patterns from validated findings
    """
    
    @staticmethod
    def extract_code_patterns(source_code: str, finding_type: FindingType) -> List[str]:
        """
        Extract vulnerability patterns from source code
        
        In production, this would use:
        - AST parsing
        - Control flow analysis
        - Data flow analysis
        - Symbolic execution
        """
        patterns = []
        
        if not source_code:
            return patterns
        
        # Simple pattern matching (would be ML-based in production)
        pattern_keywords = {
            FindingType.REENTRANCY: [
                "call.value", "transfer", "send", 
                "external call", "state change after call"
            ],
            FindingType.INTEGER_OVERFLOW: [
                "unchecked", "+=", "-=", "*=", 
                "SafeMath", "overflow", "underflow"
            ],
            FindingType.ACCESS_CONTROL: [
                "onlyOwner", "require(msg.sender", 
                "modifier", "permission", "role"
            ],
            FindingType.UNCHECKED_CALL: [
                ".call", ".delegatecall", ".staticcall",
                "low-level call", "return value"
            ]
        }
        
        keywords = pattern_keywords.get(finding_type, [])
        for keyword in keywords:
            if keyword.lower() in source_code.lower():
                patterns.append(f"contains:{keyword}")
        
        return patterns
    
    @staticmethod
    def extract_trace_patterns(execution_trace: str) -> List[str]:
        """
        Extract patterns from execution traces
        
        In production, would analyze:
        - Call sequences
        - State changes
        - Gas usage patterns
        - Event emissions
        """
        patterns = []
        
        if not execution_trace:
            return patterns
        
        # Simple pattern detection
        if "revert" in execution_trace.lower():
            patterns.append("reverted_transaction")
        
        if "selfdestruct" in execution_trace.lower():
            patterns.append("self_destruct_call")
        
        if "delegatecall" in execution_trace.lower():
            patterns.append("delegate_call_used")
        
        return patterns

class ModelTrainer:
    """
    Train ML models from validated findings
    """
    
    @staticmethod
    def train_classification_model(
        training_samples: List[Dict],
        finding_type: FindingType
    ) -> Dict[str, Any]:
        """
        Train a classification model for a specific finding type
        
        In production, this would use:
        - XGBoost/LightGBM for tabular features
        - Transformer models for code analysis
        - Graph neural networks for control flow
        """
        if len(training_samples) < 5:
            return {
                "status": "insufficient_data",
                "samples": len(training_samples),
                "accuracy": 0.0
            }
        
        # Simplified training simulation
        valid_count = sum(1 for s in training_samples if s["is_valid"])
        total_count = len(training_samples)
        
        # Calculate metrics
        accuracy = valid_count / total_count if total_count > 0 else 0.0
        precision = accuracy  # Simplified
        recall = accuracy  # Simplified
        
        return {
            "status": "trained",
            "finding_type": finding_type.value,
            "samples": total_count,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "model_version": "1.0"
        }
    
    @staticmethod
    def calculate_feature_importance(
        training_samples: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate feature importance for pattern analysis
        
        In production, would use:
        - SHAP values
        - Feature permutation importance
        - Attention weights from transformers
        """
        pattern_counts = defaultdict(int)
        
        for sample in training_samples:
            if sample.get("is_valid"):
                for pattern in sample.get("patterns", []):
                    pattern_counts[pattern] += 1
        
        # Normalize to importance scores
        total = sum(pattern_counts.values())
        if total == 0:
            return {}
        
        return {
            pattern: count / total
            for pattern, count in pattern_counts.items()
        }

class RuleGenerator:
    """
    Generate detection rules from trained models
    """
    
    @staticmethod
    def generate_rule(
        finding_type: FindingType,
        patterns: List[str],
        confidence: float,
        validated_count: int
    ) -> DetectionRule:
        """
        Generate a detection rule from patterns
        
        In production, would:
        - Use template-based generation
        - Optimize rule specificity vs recall
        - Handle rule conflicts
        - Version control for rules
        """
        import uuid
        rule_id = f"rule_{finding_type.value}_{str(uuid.uuid4())[:8]}"
        
        # Create pattern string
        pattern_str = " AND ".join(patterns[:3])  # Top 3 patterns
        
        # Calculate false positive rate (simplified)
        fp_rate = max(0.01, 1.0 - confidence)
        
        severity_map = {
            FindingType.REENTRANCY: "critical",
            FindingType.FLASH_LOAN: "critical",
            FindingType.INTEGER_OVERFLOW: "high",
            FindingType.ACCESS_CONTROL: "high",
            FindingType.UNCHECKED_CALL: "medium",
        }
        
        return DetectionRule(
            rule_id=rule_id,
            name=f"{finding_type.value.replace('_', ' ').title()} Detection",
            description=f"Auto-generated rule for detecting {finding_type.value}",
            finding_type=finding_type,
            severity=severity_map.get(finding_type, "medium"),
            pattern=pattern_str,
            confidence_threshold=confidence,
            false_positive_rate=fp_rate,
            created_at=datetime.utcnow(),
            validated_count=validated_count
        )

@app.post("/ingest")
async def ingest_validated_finding(finding: ValidatedFinding):
    """
    Ingest a validated finding for continuous learning
    
    This endpoint receives findings from the validator-worker
    after they've been confirmed as valid or false positives
    """
    # Extract patterns
    code_patterns = PatternExtractor.extract_code_patterns(
        finding.source_code or "",
        finding.type
    )
    
    trace_patterns = PatternExtractor.extract_trace_patterns(
        finding.execution_trace or ""
    )
    
    all_patterns = code_patterns + trace_patterns
    
    # Store training data
    training_sample = {
        "finding_id": finding.finding_id,
        "type": finding.type.value,
        "severity": finding.severity,
        "is_valid": finding.is_valid,
        "confidence": finding.confidence,
        "patterns": all_patterns,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    training_data.append(training_sample)
    
    # Update metrics
    model_metrics["total_findings"] += 1
    if finding.is_valid:
        model_metrics["validated_findings"] += 1
    else:
        model_metrics["false_positives"] += 1
    
    # Calculate accuracy
    if model_metrics["total_findings"] > 0:
        model_metrics["accuracy"] = (
            model_metrics["validated_findings"] / model_metrics["total_findings"]
        )
    
    return {
        "status": "ingested",
        "finding_id": finding.finding_id,
        "patterns_extracted": len(all_patterns),
        "total_samples": len(training_data)
    }

@app.post("/train")
async def train_models(request: TrainingRequest, background_tasks: BackgroundTasks):
    """
    Train ML models from accumulated validated findings
    """
    if len(training_data) < request.min_samples:
        raise HTTPException(
            400,
            f"Insufficient training data. Have {len(training_data)}, need {request.min_samples}"
        )
    
    # Group by finding type
    samples_by_type = defaultdict(list)
    for sample in training_data:
        samples_by_type[sample["type"]].append(sample)
    
    # Train models
    results = {}
    for finding_type, samples in samples_by_type.items():
        if len(samples) >= request.min_samples:
            result = ModelTrainer.train_classification_model(
                samples,
                FindingType(finding_type)
            )
            results[finding_type] = result
    
    # Update global metrics
    if results:
        total_accuracy = sum(r["accuracy"] for r in results.values() if r.get("accuracy"))
        model_metrics["accuracy"] = total_accuracy / len(results) if results else 0.0
        model_metrics["precision"] = model_metrics["accuracy"]  # Simplified
        model_metrics["recall"] = model_metrics["accuracy"]  # Simplified
    
    return {
        "status": "training_complete",
        "models_trained": len(results),
        "results": results,
        "metrics": model_metrics
    }

@app.post("/generate-rules")
async def generate_rules(request: RuleGenerationRequest):
    """
    Generate detection rules from trained models
    """
    # Get finding types to generate rules for
    types_to_process = request.finding_types or list(FindingType)
    
    # Group validated findings by type
    samples_by_type = defaultdict(list)
    for sample in training_data:
        if sample["is_valid"] and sample["confidence"] >= request.min_confidence:
            samples_by_type[sample["type"]].append(sample)
    
    generated_rules = []
    
    for finding_type in types_to_process:
        samples = samples_by_type.get(finding_type.value, [])
        
        if len(samples) < request.min_samples:
            continue
        
        # Calculate feature importance
        importance = ModelTrainer.calculate_feature_importance(samples)
        
        # Get top patterns
        top_patterns = sorted(
            importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        if not top_patterns:
            continue
        
        # Generate rule
        pattern_list = [p[0] for p in top_patterns]
        avg_confidence = sum(s["confidence"] for s in samples) / len(samples)
        
        rule = RuleGenerator.generate_rule(
            finding_type,
            pattern_list,
            avg_confidence,
            len(samples)
        )
        
        detection_rules.append(rule.dict())
        generated_rules.append(rule)
    
    model_metrics["rules_generated"] += len(generated_rules)
    
    return {
        "status": "rules_generated",
        "count": len(generated_rules),
        "rules": generated_rules
    }

@app.get("/rules")
async def get_detection_rules(
    finding_type: Optional[FindingType] = None,
    min_confidence: Optional[float] = None
):
    """Get all generated detection rules"""
    rules = detection_rules
    
    # Filter by type
    if finding_type:
        rules = [r for r in rules if r["finding_type"] == finding_type.value]
    
    # Filter by confidence
    if min_confidence:
        rules = [r for r in rules if r["confidence_threshold"] >= min_confidence]
    
    return {
        "rules": rules,
        "total": len(rules)
    }

@app.get("/metrics")
async def get_metrics():
    """Get ML-Ops metrics and performance statistics"""
    
    # Calculate additional metrics
    if training_data:
        # Accuracy by finding type
        type_accuracy = {}
        samples_by_type = defaultdict(list)
        
        for sample in training_data:
            samples_by_type[sample["type"]].append(sample)
        
        for ftype, samples in samples_by_type.items():
            valid_count = sum(1 for s in samples if s["is_valid"])
            type_accuracy[ftype] = valid_count / len(samples) if samples else 0.0
    else:
        type_accuracy = {}
    
    return {
        **model_metrics,
        "training_samples": len(training_data),
        "accuracy_by_type": type_accuracy,
        "average_confidence": (
            sum(s["confidence"] for s in training_data) / len(training_data)
            if training_data else 0.0
        )
    }

@app.get("/training-data")
async def get_training_data(
    finding_type: Optional[FindingType] = None,
    limit: int = 100
):
    """Get training data samples"""
    samples = training_data
    
    if finding_type:
        samples = [s for s in samples if s["type"] == finding_type.value]
    
    return {
        "samples": samples[-limit:],  # Most recent
        "total": len(samples)
    }

@app.delete("/training-data")
async def clear_training_data():
    """Clear all training data (use with caution)"""
    training_data.clear()
    detection_rules.clear()
    
    # Reset metrics
    model_metrics.update({
        "total_findings": 0,
        "validated_findings": 0,
        "false_positives": 0,
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "rules_generated": 0
    })
    
    return {
        "status": "cleared",
        "message": "All training data and rules cleared"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mlops-engine",
        "version": "1.0.0",
        "training_samples": len(training_data),
        "detection_rules": len(detection_rules)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
