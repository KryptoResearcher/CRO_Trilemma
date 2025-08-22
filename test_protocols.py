"""
Unit tests for protocol implementations
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.protocols import (
    ProtocolParams,
    Groth16Protocol,
    DilithiumProtocol,
    SPHINCSPlusProtocol,
    ECDSAProtocol,
    ProtocolRegistry
)

class TestProtocols:
    
    def test_groth16_signature_size(self):
        """Test Groth16 proof size"""
        params = ProtocolParams("groth16", "zksnark", 128, {})
        protocol = Groth16Protocol(params)
        
        assert protocol.get_signature_size() == 192  # 3 group elements
    
    def test_dilithium_parameters(self):
        """Test Dilithium parameters"""
        params = ProtocolParams(
            "dilithium",
            "lattice",
            128,
            {"n": 1024, "q": 8380417, "tau": 49}
        )
        protocol = DilithiumProtocol(params)
        
        assert protocol.n == 1024
        assert protocol.q == 8380417
        
    def test_protocol_registry(self):
        """Test protocol registry"""
        available = ProtocolRegistry.list_protocols()
        
        assert "groth16" in available
        assert "dilithium" in available
        assert "ecdsa" in available
    
    def test_signature_generation(self):
        """Test signature generation for all protocols"""
        protocols = ["groth16", "dilithium", "sphincs", "ecdsa"]
        
        for name in protocols:
            params = ProtocolParams(name, "test", 128, {})
            protocol = ProtocolRegistry.create(name, params)
            
            # Generate keys
            sk, pk = protocol.generate_keys()
            
            # Sign message
            message = b"test message"
            signature = protocol.sign(message, sk)
            
            # Check signature size
            assert len(signature) > 0
            assert len(signature) == protocol.get_signature_size()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])