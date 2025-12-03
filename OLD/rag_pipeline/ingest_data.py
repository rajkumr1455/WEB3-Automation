import os
import lancedb
from sentence_transformers import SentenceTransformer
import subprocess
from ast_splitter import ASTSplitter
import shutil

# Configuration
DATASET_URL = "https://github.com/smartbugs/smartbugs-curated.git"
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
DATASET_DIR = os.path.join(DATA_DIR, "smartbugs-curated")
DB_PATH = os.path.join(DATA_DIR, "lancedb")

def clone_dataset():
    if os.path.exists(DATASET_DIR):
        print("Dataset already exists. Skipping clone.")
        return
    
    print(f"Cloning dataset from {DATASET_URL}...")
    os.makedirs(DATA_DIR, exist_ok=True)
    subprocess.run(["git", "clone", DATASET_URL, DATASET_DIR], check=True)

def ingest():
    # Initialize DB
    db = lancedb.connect(DB_PATH)
    
    # Initialize Model
    print("Loading embedding model...")
    model = SentenceTransformer('BAAI/bge-m3')
    
    # Initialize Splitter
    splitter = ASTSplitter()
    
    data = []
    
    print("Processing files...")
    for root, _, files in os.walk(DATASET_DIR):
        for file in files:
            if file.endswith(".sol"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    # Split into functions
                    functions = splitter.extract_functions(content)
                    
                    for func in functions:
                        if len(func.strip()) < 20: # Skip tiny snippets
                            continue
                            
                        data.append({
                            "text": func,
                            "filename": file,
                            "path": file_path,
                            "vector": model.encode(func).tolist()
                        })
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    if not data:
        print("No data found to ingest.")
        return

    print(f"Ingesting {len(data)} chunks into LanceDB...")
    try:
        tbl = db.create_table("smart_contracts", data, mode="overwrite")
        print("Ingestion complete.")
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    clone_dataset()
    ingest()
