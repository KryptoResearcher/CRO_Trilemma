"""
Quantum channel models and interpretability calculations
"""

import numpy as np
from typing import Tuple, Optional, Dict
from scipy.linalg import sqrtm
from dataclasses import dataclass

@dataclass
class QuantumState:
    """Quantum state representation"""
    density_matrix: np.ndarray
    dimension: int
    
    def purity(self) -> float:
        """Calculate purity Tr(ρ²)"""
        return np.real(np.trace(self.density_matrix @ self.density_matrix))
    
    def von_neumann_entropy(self) -> float:
        """Calculate von Neumann entropy"""
        eigenvalues = np.linalg.eigvalsh(self.density_matrix)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        return -np.sum(eigenvalues * np.log2(eigenvalues))

class QuantumChannel:
    """Base class for quantum channels"""
    
    def __init__(self, dimension: int = 2):
        self.dimension = dimension
        
    def apply(self, state: QuantumState) -> QuantumState:
        """Apply channel to quantum state"""
        raise NotImplementedError
    
    def kraus_operators(self) -> list:
        """Get Kraus operators for channel"""
        raise NotImplementedError

class DepolarizingChannel(QuantumChannel):
    """Depolarizing channel implementation"""
    
    def __init__(self, p: float, dimension: int = 2):
        super().__init__(dimension)
        self.p = p  # Depolarizing probability
        
    def apply(self, state: QuantumState) -> QuantumState:
        """Apply depolarizing channel"""
        rho = state.density_matrix
        d = self.dimension
        identity = np.eye(d) / d
        
        # ε(ρ) = (1-p)ρ + p*I/d
        new_rho = (1 - self.p) * rho + self.p * identity
        
        return QuantumState(new_rho, d)
    
    def kraus_operators(self) -> list:
        """Kraus operators for depolarizing channel"""
        d = self.dimension
        ops = []
        
        # Identity operator
        ops.append(np.sqrt(1 - self.p) * np.eye(d))
        
        # Pauli operators (for d=2)
        if d == 2:
            pauli_x = np.array([[0, 1], [1, 0]])
            pauli_y = np.array([[0, -1j], [1j, 0]])
            pauli_z = np.array([[1, 0], [0, -1]])
            
            coefficient = np.sqrt(self.p / 3)
            ops.extend([coefficient * pauli_x,
                       coefficient * pauli_y,
                       coefficient * pauli_z])
        
        return ops

class AmplitudeDampingChannel(QuantumChannel):
    """Amplitude damping channel"""
    
    def __init__(self, gamma: float):
        super().__init__(2)
        self.gamma = gamma
        
    def kraus_operators(self) -> list:
        """Kraus operators for amplitude damping"""
        E0 = np.array([[1, 0], 
                      [0, np.sqrt(1 - self.gamma)]])
        E1 = np.array([[0, np.sqrt(self.gamma)],
                      [0, 0]])
        return [E0, E1]
    
    def apply(self, state: QuantumState) -> QuantumState:
        """Apply amplitude damping"""
        rho = state.density_matrix
        E0, E1 = self.kraus_operators()
        
        new_rho = E0 @ rho @ E0.conj().T + E1 @ rho @ E1.conj().T
        return QuantumState(new_rho, 2)

class PhaseDampingChannel(QuantumChannel):
    """Phase damping (dephasing) channel"""
    
    def __init__(self, lambda_p: float):
        super().__init__(2)
        self.lambda_p = lambda_p
        
    def apply(self, state: QuantumState) -> QuantumState:
        """Apply phase damping"""
        rho = state.density_matrix
        
        # Dephasing only affects off-diagonal elements
        new_rho = rho.copy()
        new_rho[0, 1] *= np.sqrt(1 - self.lambda_p)
        new_rho[1, 0] *= np.sqrt(1 - self.lambda_p)
        
        return QuantumState(new_rho, 2)

def calculate_trace_distance(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """Calculate trace distance between two quantum states"""
    diff = rho1 - rho2
    eigenvalues = np.linalg.eigvalsh(diff)
    return 0.5 * np.sum(np.abs(eigenvalues))

def calculate_fidelity(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """Calculate fidelity between two quantum states"""
    sqrt_rho1 = sqrtm(rho1)
    temp = sqrtm(sqrt_rho1 @ rho2 @ sqrt_rho1)
    return np.real(np.trace(temp)) ** 2

def semantic_distance(state1: QuantumState, state2: QuantumState) -> float:
    """Calculate semantic distance for interpretability"""
    # Use trace distance as proxy for semantic distance
    return calculate_trace_distance(state1.density_matrix, state2.density_matrix)