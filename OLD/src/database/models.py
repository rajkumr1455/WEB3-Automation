"""
Database models for storing vulnerability detection data
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()

class ScanResult(Base):
    """Stores each contract scan result"""
    __tablename__ = 'scan_results'
    
    id = Column(Integer, primary_key=True)
    contract_name = Column(String(255), nullable=False)
    contract_address = Column(String(42), nullable=True)
    chain = Column(String(50), nullable=False)
    source_code = Column(Text, nullable=False)
    scan_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScanResult(id={self.id}, contract={self.contract_name}, chain={self.chain})>"


class Vulnerability(Base):
    """Stores detected vulnerabilities"""
    __tablename__ = 'vulnerabilities'
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey('scan_results.id'), nullable=False)
    
    # Detection info
    vuln_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    line_number = Column(Integer, nullable=True)
    description = Column(Text, nullable=False)
    
    # ML Scores
    ml_confidence = Column(Float, nullable=True)
    cvss_score = Column(Float, nullable=True)
    
    # Source of detection
    detected_by = Column(String(50), nullable=False)  # slither, mythril, ml_classifier, llm
    
    # POC info
    poc_generated = Column(Boolean, default=False)
    poc_verified = Column(Boolean, default=False)
    poc_file_path = Column(String(500), nullable=True)
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    is_false_positive = Column(Boolean, nullable=True)
    bounty_submitted = Column(Boolean, default=False)
    bounty_accepted = Column(Boolean, nullable=True)
    bounty_reward = Column(Float, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    feedback_at = Column(DateTime, nullable=True)
    
    # Additional metadata
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    scan = relationship("ScanResult", back_populates="vulnerabilities")
    evidence = relationship("Evidence", back_populates="vulnerability", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vulnerability(id={self.id}, type={self.vuln_type}, severity={self.severity})>"


class Evidence(Base):
    """Stores evidence files for vulnerabilities"""
    __tablename__ = 'evidence'
    
    id = Column(Integer, primary_key=True)
    vulnerability_id = Column(Integer, ForeignKey('vulnerabilities.id'), nullable=False)
    
    evidence_type = Column(String(50), nullable=False)  # state_diagram, console_output, screenshot, etc.
    file_path = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vulnerability = relationship("Vulnerability", back_populates="evidence")
    
    def __repr__(self):
        return f"<Evidence(id={self.id}, type={self.evidence_type})>"


class TrainingData(Base):
    """Curated training data for ML model"""
    __tablename__ = 'training_data'
    
    id = Column(Integer, primary_key=True)
    
    # Source
    source = Column(String(100), nullable=False)  # scan, manual, import
    source_id = Column(Integer, nullable=True)  # vulnerability_id if from scan
    
    # Training sample
    code_snippet = Column(Text, nullable=False)
    vulnerability_type = Column(String(100), nullable=False)
    is_vulnerable = Column(Boolean, nullable=False)
    severity = Column(String(20), nullable=True)
    
    # Quality indicators
    verified = Column(Boolean, default=False)
    confidence = Column(Float, default=0.5)
    
    # Usage tracking
    used_in_training = Column(Boolean, default=False)
    training_set = Column(String(50), nullable=True)  # train, val, test
    
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<TrainingData(id={self.id}, type={self.vulnerability_type}, verified={self.verified})>"


class MLModel(Base):
    """Track ML model versions and performance"""
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # classifier, confidence_scorer, etc.
    version = Column(String(50), nullable=False)
    
    # Model artifacts
    model_path = Column(String(500), nullable=False)
    mlflow_run_id = Column(String(100), nullable=True)
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Training info
    training_samples = Column(Integer, nullable=True)
    training_duration = Column(Float, nullable=True)  # seconds
    
    # Deployment
    is_active = Column(Boolean, default=False)
    deployed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    trained_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<MLModel(id={self.id}, name={self.model_name}, version={self.version})>"


# Database setup utility
class Database:
    """Database connection and session management"""
    
    def __init__(self, db_url: str = None):
        if db_url is None:
            # Default to SQLite in data directory
            data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            os.makedirs(data_dir, exist_ok=True)
            db_url = f"sqlite:///{os.path.join(data_dir, 'web3_hunter.db')}"
        
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()


# Global database instance
db = Database()

if __name__ == "__main__":
    # Initialize database
    print("Creating database tables...")
    db.create_tables()
    print("✓ Database initialized successfully!")
    
    # Test connection
    session = db.get_session()
    count = session.query(ScanResult).count()
    print(f"✓ Current scan results: {count}")
    session.close()
