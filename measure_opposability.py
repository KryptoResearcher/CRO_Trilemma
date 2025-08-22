"""
Opposability measurement implementation
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import hashlib
from dataclasses import dataclass

@dataclass
class SemanticExtractor:
    """Extract semantic content from cryptographic proofs"""
    
    def extract_from_proof(self, 
                          proof: bytes,
                          protocol: str) -> Dict[str, any]:
        """Extract interpretable information from proof"""
        extracted = {
            "timestamp": None,
            "identity": None,
            "message_commitment": None,
            "legal_binding": None,
            "audit_trail": None
        }
        
        if protocol == "ecdsa":
            # ECDSA is transparent
            extracted["identity"] = proof[:32]  # Public key hash
            extracted["message_commitment"] = proof[32:64]  # Message hash
            extracted["timestamp"] = True  # Can add timestamp
            extracted["legal_binding"] = True  # Clear signature
            extracted["audit_trail"] = True  # Full trail
            
        elif protocol == "dilithium":
            # Partial extraction from structure
            extracted["message_commitment"] = proof[:32]  # Challenge
            extracted["identity"] = proof[32:40]  # Partial key info
            extracted["legal_binding"] = True  # Signature binding
            
        elif protocol == "groth16":
            # Almost nothing extractable
            extracted["message_commitment"] = hashlib.sha256(proof).digest()[:8]
            
        return extracted
    
    def calculate_entropy(self, extracted: Dict) -> float:
        """Calculate entropy of extracted information"""
        bits = 0
        
        for key, value in extracted.items():
            if value is not None:
                if isinstance(value, bytes):
                    bits += len(value) * 8
                elif isinstance(value, bool) and value:
                    bits += 1
                    
        return bits

class OpposabilityMeasurement:
    """Measure legal opposability of protocols"""
    
    def __init__(self):
        self.extractor = SemanticExtractor()
        self.legal_requirements = {
            "gdpr": ["identity", "timestamp", "audit_trail"],
            "hipaa": ["identity", "timestamp", "message_commitment", "audit_trail"],
            "financial": ["identity", "timestamp", "message_commitment", "legal_binding"],
            "criminal": ["identity", "timestamp", "legal_binding", "audit_trail"]
        }
    
    def measure_opposability(self,
                           protocol: str,
                           context: str,
                           num_samples: int = 100) -> Tuple[float, float]:
        """
        Measure opposability entropy
        Returns: (mean_bits, std_dev)
        """
        entropies = []
        
        for _ in range(num_samples):
            # Generate sample proof
            proof_size = self._get_proof_size(protocol)
            proof = np.random.bytes(proof_size)
            
            # Extract semantic content
            extracted = self.extractor.extract_from_proof(proof, protocol)
            
            # Calculate entropy
            entropy = self.extractor.calculate_entropy(extracted)
            
            # Adjust for context requirements
            requirements = self.legal_requirements.get(context, [])
            satisfied = sum(1 for req in requirements if extracted.get(req) is not None)
            context_factor = satisfied / len(requirements) if requirements else 1.0
            
            adjusted_entropy = entropy * context_factor
            entropies.append(adjusted_entropy)
        
        return np.mean(entropies), np.std(entropies)
    
    def _get_proof_size(self, protocol: str) -> int:
        """Get typical proof size for protocol"""
        sizes = {
            "groth16": 192,
            "dilithium": 2420,
            "sphincs": 17088,
            "ecdsa": 64,
            "bls": 96
        }
        return sizes.get(protocol, 256)
    
    def measure_interpretability_score(self,
                                      protocol: str,
                                      jurisdiction: str) -> float:
        """
        Calculate interpretability score for legal jurisdiction
        Score from 0 (uninterpretable) to 1 (fully interpretable)
        """
        # Generate test proof
        proof = np.random.bytes(self._get_proof_size(protocol))
        extracted = self.extractor.extract_from_proof(proof, protocol)
        
        # Check requirements
        requirements = self.legal_requirements.get(jurisdiction, [])
        if not requirements:
            return 0.5  # Default score
        
        satisfied = sum(1 for req in requirements if extracted.get(req) is not None)
        return satisfied / len(requirements)