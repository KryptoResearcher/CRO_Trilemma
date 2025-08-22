"""
Statistical analysis tools for CRO measurements
Implements methods from Appendix D.4
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from typing import Dict, List, Tuple, Optional
import warnings

class StatisticalAnalyzer:
    """Complete statistical analysis toolkit"""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
    def calculate_confidence_interval(self,
                                     data: np.ndarray,
                                     method: str = 'bootstrap') -> Tuple[float, float]:
        """
        Calculate confidence interval
        
        Methods:
        - 'bootstrap': Bootstrap CI
        - 'normal': Normal approximation
        - 't': Student's t-distribution
        """
        if method == 'bootstrap':
            return self._bootstrap_ci(data)
        elif method == 'normal':
            return self._normal_ci(data)
        elif method == 't':
            return self._t_ci(data)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _bootstrap_ci(self, 
                     data: np.ndarray,
                     n_bootstrap: int = 10000) -> Tuple[float, float]:
        """Bootstrap confidence interval"""
        bootstrap_means = []
        n = len(data)
        
        for _ in range(n_bootstrap):
            sample = np.random.choice(data, size=n, replace=True)
            bootstrap_means.append(np.mean(sample))
        
        lower = np.percentile(bootstrap_means, (1 - self.confidence_level) * 50)
        upper = np.percentile(bootstrap_means, (1 + self.confidence_level) * 50)
        
        return lower, upper
    
    def _normal_ci(self, data: np.ndarray) -> Tuple[float, float]:
        """Normal approximation CI"""
        mean = np.mean(data)
        std_error = stats.sem(data)
        margin = self.z_score * std_error
        
        return mean - margin, mean + margin
    
    def _t_ci(self, data: np.ndarray) -> Tuple[float, float]:
        """Student's t CI"""
        mean = np.mean(data)
        std_error = stats.sem(data)
        df = len(data) - 1
        t_score = stats.t.ppf((1 + self.confidence_level) / 2, df)
        margin = t_score * std_error
        
        return mean - margin, mean + margin
    
    def test_trilemma_violation(self,
                               priv: float,
                               rel: float,
                               opp_normalized: float,
                               context_entropy: float,
                               quantum_loss: float) -> Dict:
        """
        Test if measurements violate trilemma bound
        H0: Protocol satisfies trilemma
        H1: Protocol violates trilemma
        """
        # Calculate bound
        negligible = 2**(-128)
        theoretical_bound = 1/(2**context_entropy) + quantum_loss + negligible
        
        # Calculate actual
        actual = priv * rel * opp_normalized
        
        # Test statistic
        test_statistic = (actual - theoretical_bound) / negligible
        
        # P-value (one-sided test)
        p_value = 1 - stats.norm.cdf(test_statistic)
        
        return {
            'theoretical_bound': theoretical_bound,
            'actual': actual,
            'test_statistic': test_statistic,
            'p_value': p_value,
            'reject_h0': p_value < 0.05,
            'violation': actual > theoretical_bound
        }
    
    def regression_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Regression analysis of Γ_CRO vs protocol characteristics
        Reproduces regression from Appendix D.4
        """
        # Create feature matrix
        features = []
        for _, row in df.iterrows():
            is_post_quantum = 1 if row['protocol'] in ['dilithium3', 'sphincs_plus'] else 0
            is_zk = 1 if row['protocol'] == 'groth16' else 0
            has_structure = 1 if row['protocol'] in ['dilithium3', 'sphincs_plus'] else 0
            
            features.append([is_post_quantum, is_zk, has_structure])
        
        X = np.array(features)
        y = df['gamma_cro'].values
        
        # Fit model
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate R²
        r2 = model.score(X, y)
        
        # Predictions
        predictions = model.predict(X)
        residuals = y - predictions
        
        # Standard errors
        n = len(y)
        p = X.shape[1]
        residual_std = np.sqrt(np.sum(residuals**2) / (n - p - 1))
        
        # Coefficient standard errors
        XtX_inv = np.linalg.inv(X.T @ X)
        coef_std_errors = residual_std * np.sqrt(np.diag(XtX_inv))
        
        return {
            'intercept': model.intercept_,
            'coefficients': model.coef_,
            'coef_std_errors': coef_std_errors,
            'r_squared': r2,
            'residual_std': residual_std,
            'predictions': predictions,
            'residuals': residuals
        }
    
    def normality_test(self, data: np.ndarray) -> Dict:
        """Test for normality of data"""
        # Shapiro-Wilk test
        stat_sw, p_sw = stats.shapiro(data)
        
        # Anderson-Darling test  
        result_ad = stats.anderson(data)
        
        # Kolmogorov-Smirnov test
        stat_ks, p_ks = stats.kstest(data, 'norm', 
                                     args=(np.mean(data), np.std(data)))
        
        return {
            'shapiro_wilk': {'statistic': stat_sw, 'p_value': p_sw},
            'anderson_darling': {'statistic': result_ad.statistic, 
                               'critical_values': result_ad.critical_values},
            'kolmogorov_smirnov': {'statistic': stat_ks, 'p_value': p_ks}
        }
    
    def correlation_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Correlation analysis between CRO dimensions
        """
        metrics = ['confidentiality_mean', 'reliability_mean', 
                  'opposability_normalized', 'gamma_cro']
        
        corr_matrix = df[metrics].corr(method='pearson')
        
        # Calculate p-values for correlations
        n = len(df)
        p_values = pd.DataFrame(np.zeros_like(corr_matrix), 
                               columns=corr_matrix.columns,
                               index=corr_matrix.index)
        
        for i in range(len(metrics)):
            for j in range(len(metrics)):
                if i != j:
                    r = corr_matrix.iloc[i, j]
                    t_stat = r * np.sqrt(n - 2) / np.sqrt(1 - r**2)
                    p_values.iloc[i, j] = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
        
        return corr_matrix, p_values