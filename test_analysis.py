"""
Unit tests for analysis modules
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analysis.statistical_analysis import StatisticalAnalyzer
from src.analysis.validation import ValidationSuite

class TestStatisticalAnalysis:
    
    def test_confidence_interval_bootstrap(self):
        """Test bootstrap CI calculation"""
        analyzer = StatisticalAnalyzer()
        data = np.random.normal(0.5, 0.1, 100)
        
        lower, upper = analyzer.calculate_confidence_interval(data, method='bootstrap')
        
        assert lower < np.mean(data) < upper
        assert upper - lower < 0.5  # Reasonable CI width
    
    def test_trilemma_violation_test(self):
        """Test trilemma violation hypothesis test"""
        analyzer = StatisticalAnalyzer()
        
        result = analyzer.test_trilemma_violation(
            priv=0.999,
            rel=0.999,
            opp_norm=0.999,
            context_entropy=10.0,
            quantum_loss=0.01
        )
        
        assert result['violation']  # Should violate
        assert result['p_value'] < 0.05  # Significant

class TestValidation:
    
    def test_metric_range_validation(self):
        """Test metric range validation"""
        validator = ValidationSuite()
        
        # Valid metrics
        valid = validator.validate_metric_ranges({
            'confidentiality': 0.5,
            'reliability': 0.9,
            'opposability': 10.0
        })
        assert valid
        
        # Invalid metrics
        invalid = validator.validate_metric_ranges({
            'confidentiality': 1.5,  # Out of range
            'reliability': 0.9,
            'opposability': -10.0  # Negative
        })
        assert not invalid
    
    def test_consistency_check(self):
        """Test consistency validation"""
        validator = ValidationSuite()
        
        # Create test dataframe
        data = {
            'protocol': ['groth16', 'ecdsa'],
            'confidentiality_mean': [0.999, 0.001],
            'reliability_mean': [0.999, 0.995],
            'opposability_mean': [0.5, 120.0]  # Correct pattern
        }
        df = pd.DataFrame(data)
        
        result = validator.validate_consistency(df)
        assert result['consistent']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])