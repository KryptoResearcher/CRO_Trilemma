"""
Validation suite for CRO measurements
"""

import numpy as np
from typing import Dict, List, Tuple
import pandas as pd

class ValidationSuite:
    """Validate CRO measurements against theoretical bounds"""
    
    def __init__(self):
        self.violations = []
        self.warnings = []
        
    def validate_trilemma_bound(self,
                               priv: float,
                               rel: float,
                               opp_norm: float,
                               h_c: float,
                               eta_q: float) -> bool:
        """Check if measurement violates trilemma bound"""
        actual = priv * rel * opp_norm
        bound = 1/(2**h_c) + eta_q + 2**(-128)
        
        if actual > bound + 0.01:  # Allow small numerical error
            self.violations.append({
                "type": "trilemma_bound",
                "actual": actual,
                "bound": bound,
                "excess": actual - bound
            })
            return False
        return True
    
    def validate_metric_ranges(self, metrics: Dict) -> bool:
        """Validate that all metrics are in valid ranges"""
        valid = True
        
        # Check confidentiality [0, 1]
        if not 0 <= metrics.get('confidentiality', 0) <= 1:
            self.warnings.append(f"Confidentiality out of range: {metrics['confidentiality']}")
            valid = False
            
        # Check reliability [0, 1]
        if not 0 <= metrics.get('reliability', 0) <= 1:
            self.warnings.append(f"Reliability out of range: {metrics['reliability']}")
            valid = False
            
        # Check opposability >= 0
        if metrics.get('opposability', 0) < 0:
            self.warnings.append(f"Negative opposability: {metrics['opposability']}")
            valid = False
            
        return valid
    
    def validate_consistency(self, df: pd.DataFrame) -> Dict:
        """Check consistency across measurements"""
        results = {
            "consistent": True,
            "issues": []
        }
        
        # Check that ZK proofs have low opposability
        zk_protocols = ['groth16']
        for protocol in zk_protocols:
            protocol_data = df[df['protocol'] == protocol]
            if not protocol_data.empty:
                mean_opp = protocol_data['opposability_mean'].mean()
                if mean_opp > 5:  # Should be < 5 bits for ZK
                    results["consistent"] = False
                    results["issues"].append(
                        f"{protocol} has unexpectedly high opposability: {mean_opp}"
                    )
        
        # Check that classical signatures have low confidentiality
        classical = ['ecdsa', 'bls']
        for protocol in classical:
            protocol_data = df[df['protocol'] == protocol]
            if not protocol_data.empty:
                mean_priv = protocol_data['confidentiality_mean'].mean()
                if mean_priv > 0.1:  # Should be < 0.1 for classical
                    results["consistent"] = False
                    results["issues"].append(
                        f"{protocol} has unexpectedly high confidentiality: {mean_priv}"
                    )
        
        return results
    
    def generate_validation_report(self) -> str:
        """Generate validation report"""
        report = "="*50 + "\n"
        report += "CRO VALIDATION REPORT\n"
        report += "="*50 + "\n\n"
        
        if not self.violations:
            report += "✓ No trilemma violations detected\n"
        else:
            report += f"✗ {len(self.violations)} trilemma violations found:\n"
            for v in self.violations:
                report += f"  - Excess: {v['excess']:.6f} (actual={v['actual']:.6f}, bound={v['bound']:.6f})\n"
        
        if not self.warnings:
            report += "✓ All metrics in valid ranges\n"
        else:
            report += f"⚠ {len(self.warnings)} warnings:\n"
            for w in self.warnings:
                report += f"  - {w}\n"
        
        return report