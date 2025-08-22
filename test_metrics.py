"""
Unit tests for CRO metrics
"""

import pytest
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.metrics import (
    CROMetrics, 
    ProtocolMetrics,
    ContextualEntropy,
    QuantumInterpretability,
    calculate_trilemma_bound
)

class TestCROMetrics:
    
    def test_gamma_cro_calculation(self):
        """Test Gamma_CRO calculation"""
        metrics = CROMetrics(
            confidentiality=0.9,
            reliability=0.9,
            opposability=10.0,  # 10 bits
            context_entropy=10.0,
            quantum_loss=0.01
        )
        
        gamma = metrics.gamma_cro
        expected = 1 - min(0.9, 0.9, 10.0/128)
        assert abs(gamma - expected) < 0.001
    
    def test_trilemma_bound(self):
        """Test trilemma bound calculation"""
        metrics = CROMetrics(
            confidentiality=0.999,
            reliability=0.999,
            opposability=0.1,
            context_entropy=10.0,
            quantum_loss=0.01
        )
        
        bound, actual, satisfied = calculate_trilemma_bound(metrics)
        
        # Should violate bound
        assert actual > bound
        assert not satisfied
    
    def test_protocol_metrics_groth16(self):
        """Test Groth16 metrics calculation"""
        pm = ProtocolMetrics()
        priv, std = pm.calculate_confidentiality("groth16", {})
        
        assert priv > 0.99  # Should be near perfect
        assert std < 0.01
    
    def test_contextual_entropy(self):
        """Test context entropy calculation"""
        ce = ContextualEntropy()
        
        h_c = ce.calculate(
            legal_constraints=1024,
            temporal_constraints=512,
            procedural_constraints=256
        )
        
        assert h_c > 0
        assert h_c == np.log2(1024) + np.log2(512)*0.8 + np.log2(256)*0.6

class TestQuantumLoss:
    
    def test_depolarizing_channel(self):
        """Test depolarizing channel loss"""
        qi = QuantumInterpretability()
        loss = qi.calculate_loss("dilithium", "depolarizing", 0.01)
        
        assert loss > 0
        assert loss < 1
    
    def test_channel_comparison(self):
        """Test different channels give different losses"""
        qi = QuantumInterpretability()
        
        loss_dep = qi.calculate_loss("dilithium", "depolarizing", 0.01)
        loss_amp = qi.calculate_loss("dilithium", "amplitude_damping", 0.01)
        loss_phase = qi.calculate_loss("dilithium", "phase_damping", 0.01)
        
        # Should all be different
        assert loss_dep != loss_amp
        assert loss_amp != loss_phase

if __name__ == "__main__":
    pytest.main([__file__, "-v"])