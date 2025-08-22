"""
Helper utilities for CRO experiments
"""

import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Any, Dict, List, Optional
import hashlib
import time

def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level),
        format=log_format,
        handlers=handlers
    )
    
    return logging.getLogger("cro-trilemma")

def load_data(filepath: str) -> Any:
    """Load data from file (CSV, JSON, or pickle)"""
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if path.suffix == ".csv":
        return pd.read_csv(filepath)
    elif path.suffix == ".json":
        with open(filepath, 'r') as f:
            return json.load(f)
    elif path.suffix in [".pkl", ".pickle"]:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def save_results(data: Any, filepath: str, format: str = "auto"):
    """Save results to file"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "auto":
        format = path.suffix[1:] if path.suffix else "json"
    
    if format == "csv":
        if isinstance(data, pd.DataFrame):
            data.to_csv(filepath, index=False)
        else:
            pd.DataFrame(data).to_csv(filepath, index=False)
    elif format == "json":
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    elif format in ["pkl", "pickle"]:
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    else:
        raise ValueError(f"Unsupported format: {format}")

def calculate_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Calculate hash of data"""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()

def generate_random_message(size: int = 32) -> bytes:
    """Generate random message for testing"""
    return np.random.bytes(size)

def measure_execution_time(func):
    """Decorator to measure function execution time"""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        
        logger = logging.getLogger("cro-trilemma")
        logger.debug(f"{func.__name__} took {end - start:.4f} seconds")
        
        return result
    return wrapper

def batch_process(items: List, process_func, batch_size: int = 100, **kwargs):
    """Process items in batches"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = [process_func(item, **kwargs) for item in batch]
        results.extend(batch_results)
        
    return results

def validate_protocol_params(protocol: str, params: Dict) -> bool:
    """Validate protocol parameters"""
    required_params = {
        "dilithium": ["n", "q", "tau"],
        "sphincs": ["n", "h", "d"],
        "groth16": [],
        "ecdsa": [],
        "bls": []
    }
    
    if protocol not in required_params:
        return False
        
    for param in required_params[protocol]:
        if param not in params:
            return False
            
    return True

def format_results_table(results: pd.DataFrame) -> str:
    """Format results as ASCII table"""
    return results.to_string(index=False, float_format=lambda x: f"{x:.4f}")

def calculate_statistics(data: List[float]) -> Dict[str, float]:
    """Calculate comprehensive statistics"""
    return {
        "mean": np.mean(data),
        "std": np.std(data),
        "median": np.median(data),
        "min": np.min(data),
        "max": np.max(data),
        "q25": np.percentile(data, 25),
        "q75": np.percentile(data, 75),
        "iqr": np.percentile(data, 75) - np.percentile(data, 25)
    }