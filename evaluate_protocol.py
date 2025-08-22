#!/usr/bin/env python3
"""
CRO Trilemma Protocol Evaluation Framework
Main evaluation script for measuring CRO metrics across cryptographic protocols
"""

import argparse
import json
import logging
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List
import multiprocessing as mp
from datetime import datetime

# Import protocol implementations
from protocols.groth16 import Groth16Protocol
from protocols.dilithium3 import Dilithium3Protocol
from protocols.stark import STARKProtocol
from protocols.ecdsa import ECDSAProtocol
from protocols.plonk import PlonKProtocol

# Import CRO framework
from cro.metrics import CROMetrics
from cro.entropy import ContextualEntropy
from cro.quantum_loss import QuantumInterpretabilityLoss

# Import verifiers
from verifiers.gdpr_verifier import GDPRVerifier
from verifiers.ccpa_verifier import CCPAVerifier
from verifiers.pipeda_verifier import PIPEDAVerifier

# Import adversaries
from adversaries.classical_adversary import ClassicalAdversary
from adversaries.ml_adversary import MLAdversary
from adversaries.quantum_adversary import QuantumAdversary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Protocol registry
PROTOCOLS = {
    'groth16': Groth16Protocol,
    'dilithium3': Dilithium3Protocol,
    'stark': STARKProtocol,
    'ecdsa': ECDSAProtocol,
    'plonk': PlonKProtocol
}

# Verifier registry
VERIFIERS = {
    'gdpr': GDPRVerifier,
    'ccpa': CCPAVerifier,
    'pipeda': PIPEDAVerifier
}

class CROEvaluator:
    """Main CRO evaluation framework"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize evaluator with configuration"""
        self.config = config
        self.results = {}
        self.metrics = CROMetrics()
        self.entropy_calculator = ContextualEntropy()
        self.quantum_loss = QuantumInterpretabilityLoss()
        
        # Set random seeds for reproducibility
        self._set_random_seeds(config.get('random_seed', 42))
        
        # Initialize adversaries
        self.adversaries = self._initialize_adversaries()
        
        # Initialize verifiers
        self.verifiers = self._initialize_verifiers()
        
    def _set_random_seeds(self, seed: int):
        """Set all random seeds for reproducibility"""
        np.random.seed(seed)
        import random
        random.seed(seed)
        
        # Set PyTorch seeds if available
        try:
            import torch
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        except ImportError:
            pass
            
    def _initialize_adversaries(self) -> Dict[str, Any]:
        """Initialize adversary suite"""
        return {
            'classical': ClassicalAdversary(self.config),
            'ml': MLAdversary(self.config),
            'quantum': QuantumAdversary(self.config)
        }
        
    def _initialize_verifiers(self) -> Dict[str, Any]:
        """Initialize institutional verifiers"""
        return {
            name: verifier_class()
            for name, verifier_class in VERIFIERS.items()
        }
        
    def evaluate_protocol(self, protocol_name: str, num_trials: int = 1000) -> Dict[str, Any]:
        """
        Evaluate a single protocol's CRO metrics
        
        Args:
            protocol_name: Name of the protocol to evaluate
            num_trials: Number of evaluation trials
            
        Returns:
            Dictionary containing CRO metrics and analysis
        """
        logger.info(f"Evaluating protocol: {protocol_name}")
        
        # Initialize protocol
        if protocol_name not in PROTOCOLS:
            raise ValueError(f"Unknown protocol: {protocol_name}")
        protocol = PROTOCOLS[protocol_name](self.config)
        
        # Generate test contexts
        contexts = self._generate_test_contexts(num_trials)
        
        # Measure CRO metrics
        confidentiality_scores = []
        reliability_scores = []
        opposability_scores = []
        
        for i, context in enumerate(contexts):
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{num_trials}")
                
            # Generate test case
            statement, witness = self._generate_test_case(context)
            
            # Generate proof
            proof = protocol.prove(statement, witness, context)
            
            # Measure confidentiality
            conf_score = self._measure_confidentiality(protocol, proof, statement)
            confidentiality_scores.append(conf_score)
            
            # Measure reliability
            rel_score = self._measure_reliability(protocol, proof, statement, witness)
            reliability_scores.append(rel_score)
            
            # Measure opposability
            opp_score = self._measure_opposability(proof, context)
            opposability_scores.append(opp_score)
            
        # Compute statistics
        results = self._compute_statistics(
            confidentiality_scores,
            reliability_scores,
            opposability_scores
        )
        
        # Add metadata
        results['protocol'] = protocol_name
        results['num_trials'] = num_trials
        results['timestamp'] = datetime.utcnow().isoformat()
        
        return results
        
    def _generate_test_contexts(self, num_trials: int) -> List[Dict[str, Any]]:
        """Generate test contexts with legal, temporal, and procedural components"""
        contexts = []
        for _ in range(num_trials):
            context = {
                'L': self._generate_legal_framework(),
                'T': self._generate_temporal_constraints(),
                'R': self._generate_procedural_requirements()
            }
            contexts.append(context)
        return contexts
        
    def _generate_legal_framework(self) -> Dict[str, Any]:
        """Generate random legal framework"""
        frameworks = ['gdpr', 'ccpa', 'pipeda', 'lgpd', 'pipl']
        return {
            'jurisdiction': np.random.choice(frameworks),
            'articles': np.random.randint(1, 100, size=np.random.randint(1, 5)).tolist(),
            'compliance_level': np.random.choice(['strict', 'moderate', 'relaxed'])
        }
        
    def _generate_temporal_constraints(self) -> Dict[str, Any]:
        """Generate temporal constraints"""
        return {
            'processing_period': np.random.randint(1, 365),  # days
            'retention_period': np.random.randint(30, 3650),  # days
            'response_time': np.random.choice([30, 45, 60])  # days
        }
        
    def _generate_procedural_requirements(self) -> Dict[str, Any]:
        """Generate procedural requirements"""
        procedures = ['consent', 'dpia', 'audit', 'notification', 'verification']
        selected = np.random.choice(
            procedures,
            size=np.random.randint(1, len(procedures)),
            replace=False
        )
        return {
            'required_procedures': selected.tolist(),
            'verification_strength': np.random.uniform(0.5, 1.0)
        }
        
    def _generate_test_case(self, context: Dict[str, Any]) -> Tuple[Any, Any]:
        """Generate statement-witness pair for testing"""
        # Simple test case generation
        statement = f"statement_{np.random.randint(10000)}"
        witness = f"witness_{np.random.randint(10000)}"
        return statement, witness
        
    def _measure_confidentiality(self, protocol: Any, proof: Any, statement: Any) -> float:
        """Measure confidentiality using adversarial testing"""
        max_advantage = 0.0
        
        for adv_name, adversary in self.adversaries.items():
            advantage = adversary.attack(protocol, proof, statement)
            max_advantage = max(max_advantage, advantage)
            
        return 1.0 - max_advantage
        
    def _measure_reliability(self, protocol: Any, proof: Any, 
                            statement: Any, witness: Any) -> float:
        """Measure reliability through soundness and completeness testing"""
        # Completeness test
        if not protocol.verify(proof, statement):
            return 0.0  # Completeness failure
            
        # Soundness test (simplified)
        fake_proof = self._generate_fake_proof(protocol)
        if protocol.verify(fake_proof, statement):
            return 0.5  # Soundness failure
            
        return 1.0
        
    def _generate_fake_proof(self, protocol: Any) -> Any:
        """Generate fake proof for soundness testing"""
        # Protocol-specific fake proof generation
        return protocol.generate_random_proof()
        
    def _measure_opposability(self, proof: Any, context: Dict[str, Any]) -> float:
        """Measure legal opposability through institutional verifiers"""
        opposability_scores = []
        
        for verifier_name, verifier in self.verifiers.items():
            interpretation, entropy, status = verifier.interpret(proof, context)
            if status == 'success':
                opposability_scores.append(entropy)
            else:
                opposability_scores.append(0.0)
                
        return np.mean(opposability_scores) if opposability_scores else 0.0
        
    def _compute_statistics(self, conf_scores: List[float],
                           rel_scores: List[float],
                           opp_scores: List[float]) -> Dict[str, Any]:
        """Compute statistical summaries and CRO violation metric"""
        # Basic statistics
        priv_emp = np.mean(conf_scores)
        rel_emp = np.mean(rel_scores)
        opp_emp = np.mean(opp_scores)
        
        # Normalize opposability
        max_log_space = np.log2(2304)  # GDPR max
        opp_normalized = opp_emp / max_log_space
        
        # CRO violation metric
        gamma_cro = 1.0 - min(priv_emp, rel_emp, opp_normalized)
        
        # Bootstrap confidence intervals
        ci_priv = self._bootstrap_ci(conf_scores)
        ci_rel = self._bootstrap_ci(rel_scores)
        ci_opp = self._bootstrap_ci(opp_scores)
        
        return {
            'confidentiality': {
                'mean': priv_emp,
                'std': np.std(conf_scores),
                'ci_95': ci_priv
            },
            'reliability': {
                'mean': rel_emp,
                'std': np.std(rel_scores),
                'ci_95': ci_rel
            },
            'opposability': {
                'mean': opp_emp,
                'std': np.std(opp_scores),
                'ci_95': ci_opp,
                'normalized': opp_normalized
            },
            'cro_violation': gamma_cro,
            'cro_product': priv_emp * rel_emp * opp_normalized
        }
        
    def _bootstrap_ci(self, data: List[float], n_bootstrap: int = 10000,
                     confidence: float = 0.95) -> Tuple[float, float]:
        """Compute bootstrap confidence interval"""
        bootstrap_means = []
        n = len(data)
        
        for _ in range(n_bootstrap):
            sample = np.random.choice(data, size=n, replace=True)
            bootstrap_means.append(np.mean(sample))
            
        alpha = 1 - confidence
        lower = np.percentile(bootstrap_means, 100 * alpha / 2)
        upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
        
        return (lower, upper)
        
    def run_all_protocols(self, num_trials: int = 1000) -> Dict[str, Any]:
        """Evaluate all protocols"""
        all_results = {}
        
        for protocol_name in PROTOCOLS.keys():
            logger.info(f"Starting evaluation of {protocol_name}")
            results = self.evaluate_protocol(protocol_name, num_trials)
            all_results[protocol_name] = results
            
            # Save intermediate results
            self._save_results(results, f"results_{protocol_name}.json")
            
        return all_results
        
    def _save_results(self, results: Dict[str, Any], filename: str):
        """Save results to JSON file"""
        output_dir = Path(self.config.get('output_dir', 'results'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='CRO Trilemma Protocol Evaluation'
    )
    parser.add_argument(
        '--protocol',
        choices=list(PROTOCOLS.keys()) + ['all'],
        default='all',
        help='Protocol to evaluate'
    )
    parser.add_argument(
        '--trials',
        type=int,
        default=1000,
        help='Number of evaluation trials'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/default_config.yaml',
        help='Configuration file path'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results',
        help='Output directory for results'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Enable parallel processing'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    import yaml
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
        
    # Override config with command line arguments
    config['random_seed'] = args.seed
    config['output_dir'] = args.output_dir
    config['parallel'] = args.parallel
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Create evaluator
    evaluator = CROEvaluator(config)
    
    # Run evaluation
    start_time = time.time()
    
    if args.protocol == 'all':
        results = evaluator.run_all_protocols(args.trials)
    else:
        results = evaluator.evaluate_protocol(args.protocol, args.trials)
        
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n" + "="*60)
    print("CRO TRILEMMA EVALUATION COMPLETE")
    print("="*60)
    
    if args.protocol == 'all':
        for protocol_name, protocol_results in results.items():
            print(f"\n{protocol_name.upper()}:")
            print(f"  Confidentiality: {protocol_results['confidentiality']['mean']:.3f}")
            print(f"  Reliability: {protocol_results['reliability']['mean']:.3f}")
            print(f"  Opposability: {protocol_results['opposability']['mean']:.3f}")
            print(f"  CRO Violation: {protocol_results['cro_violation']:.3f}")
    else:
        print(f"\n{args.protocol.upper()}:")
        print(f"  Confidentiality: {results['confidentiality']['mean']:.3f}")
        print(f"  Reliability: {results['reliability']['mean']:.3f}")
        print(f"  Opposability: {results['opposability']['mean']:.3f}")
        print(f"  CRO Violation: {results['cro_violation']:.3f}")
        
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")
    print(f"Results saved to: {config['output_dir']}/")
    

if __name__ == '__main__':
    main()