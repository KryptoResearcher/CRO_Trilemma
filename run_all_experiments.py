#!/usr/bin/env python3
"""
Master script to run all CRO experiments
Reproduces all results from the manuscript
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import json
import time
from pathlib import Path
from typing import Dict, List
import argparse

from src.core.metrics import (
    ProtocolMetrics, 
    ContextualEntropy, 
    QuantumInterpretability,
    CROMetrics,
    calculate_trilemma_bound
)
from src.measurements.measure_confidentiality import run_confidentiality_measurements
from src.analysis.statistical_analysis import StatisticalAnalyzer
from src.analysis.visualization import create_all_figures

# Protocol configurations matching manuscript
PROTOCOLS = {
    "groth16": {
        "type": "zksnark",
        "security_level": 128,
        "params": {}
    },
    "dilithium3": {
        "type": "lattice",
        "security_level": 128,
        "params": {
            "n": 1024,
            "q": 8380417,
            "tau": 49,
            "gamma1": 2**19,
            "gamma2": 2**17,
            "omega": 80
        }
    },
    "sphincs_plus": {
        "type": "hash",
        "security_level": 128,
        "params": {
            "n": 128,
            "h": 64,
            "d": 8,
            "variant": "128f"
        }
    },
    "ecdsa": {
        "type": "classical",
        "security_level": 128,
        "params": {
            "curve": "P-256"
        }
    },
    "bls": {
        "type": "pairing",
        "security_level": 128,
        "params": {
            "curve": "BLS12-381"
        }
    }
}

CONTEXTS = ["gdpr", "hipaa", "financial", "criminal"]

class CROExperiment:
    """Main experiment runner"""
    
    def __init__(self, output_dir: str = "data/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = ProtocolMetrics()
        self.context_entropy = ContextualEntropy()
        self.quantum = QuantumInterpretability()
        self.analyzer = StatisticalAnalyzer()
        
    def run_all_measurements(self, num_trials: int = 1000) -> pd.DataFrame:
        """
        Run complete measurement suite
        Reproduces Table 3 and Table 4 from manuscript
        """
        results = []
        
        for protocol_name, config in PROTOCOLS.items():
            print(f"\n{'='*50}")
            print(f"Measuring Protocol: {protocol_name}")
            print(f"{'='*50}")
            
            for context in CONTEXTS:
                print(f"\nContext: {context}")
                
                # Run measurements
                result = self.measure_protocol(
                    protocol_name, 
                    config, 
                    context,
                    num_trials
                )
                results.append(result)
                
                # Print summary
                self.print_result_summary(result)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Save results
        df.to_csv(self.output_dir / "complete_measurements.csv", index=False)
        df.to_json(self.output_dir / "complete_measurements.json", 
                   orient='records', indent=2)
        
        return df
    
    def measure_protocol(self, 
                        name: str, 
                        config: Dict,
                        context: str,
                        num_trials: int) -> Dict:
        """Measure single protocol in context"""
        
        result = {
            'protocol': name,
            'context': context,
            'timestamp': time.time()
        }
        
        # 1. Confidentiality
        priv_mean, priv_std = self.metrics.calculate_confidentiality(
            name.replace('3', '').replace('_plus', ''), 
            config['params']
        )
        result['confidentiality_mean'] = priv_mean
        result['confidentiality_std'] = priv_std
        
        # 2. Reliability
        rel_mean, rel_std = self.metrics.calculate_reliability(
            name.replace('3', '').replace('_plus', ''),
            config['params'],
            num_trials
        )
        result['reliability_mean'] = rel_mean
        result['reliability_std'] = rel_std
        
        # 3. Opposability
        opp_mean, opp_std = self.metrics.calculate_opposability(
            name.replace('3', '').replace('_plus', ''),
            config['params'],
            context
        )
        result['opposability_mean'] = opp_mean
        result['opposability_std'] = opp_std
        result['opposability_normalized'] = opp_mean / 128  # |V_J| = 2^128
        
        # 4. Context Entropy
        h_c = self.context_entropy.calculate_from_jurisdiction(context)
        result['context_entropy'] = h_c
        
        # 5. Quantum Loss
        eta_q = self.quantum.calculate_loss(
            name.replace('3', '').replace('_plus', ''),
            'depolarizing',
            0.01
        )
        result['quantum_loss'] = eta_q
        
        # 6. CRO Metrics
        metrics = CROMetrics(
            confidentiality=priv_mean,
            reliability=rel_mean,
            opposability=opp_mean,
            context_entropy=h_c,
            quantum_loss=eta_q
        )
        result['gamma_cro'] = metrics.gamma_cro
        
        # 7. Trilemma Bound Check
        bound, actual, satisfied = calculate_trilemma_bound(metrics)
        result['trilemma_bound'] = bound
        result['trilemma_actual'] = actual
        result['trilemma_satisfied'] = satisfied
        
        return result
    
    def print_result_summary(self, result: Dict):
        """Print formatted result summary"""
        print(f"\nProtocol: {result['protocol']} in {result['context']}")
        print(f"  Confidentiality: {result['confidentiality_mean']:.4f} ± {result['confidentiality_std']:.4f}")
        print(f"  Reliability: {result['reliability_mean']:.4f} ± {result['reliability_std']:.4f}")
        print(f"  Opposability: {result['opposability_mean']:.2f} ± {result['opposability_std']:.2f} bits")
        print(f"  Γ_CRO: {result['gamma_cro']:.4f}")
        print(f"  Trilemma: {'✓ Satisfied' if result['trilemma_satisfied'] else '✗ Violated'}")
    
    def generate_latex_tables(self, df: pd.DataFrame):
        """Generate LaTeX tables for manuscript"""
        
        # Table 3: Main CRO Metrics
        main_table = df[df['context'] == 'gdpr'][
            ['protocol', 'confidentiality_mean', 'reliability_mean', 
             'opposability_normalized', 'gamma_cro']
        ].copy()
        
        latex = main_table.to_latex(
            index=False,
            float_format="%.4f",
            caption="Empirical CRO Metrics for Contemporary Protocols",
            label="tab:cro_metrics"
        )
        
        with open(self.output_dir / "table_cro_metrics.tex", 'w') as f:
            f.write(latex)
        
        # Table 4: Context Sensitivity
        context_table = df.pivot_table(
            values='opposability_mean',
            index='protocol',
            columns='context'
        )
        
        latex = context_table.to_latex(
            float_format="%.