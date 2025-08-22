"""
Generate all figures for the manuscript
Implements visualizations from Section 7 and Appendix D
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set publication-quality defaults
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Computer Modern Roman']
plt.rcParams['text.usetex'] = False  # Set True if LaTeX available

def create_all_figures(df: pd.DataFrame, output_dir: str):
    """Create all figures for manuscript"""
    
    # Figure 1: CRO Space Visualization (3D)
    fig1 = create_cro_space_plot(df)
    fig1.savefig(f"{output_dir}/figure_cro_space.pdf", bbox_inches='tight')
    
    # Figure 2: Trilemma Violation Heatmap
    fig2 = create_violation_heatmap(df)
    fig2.savefig(f"{output_dir}/figure_violation_heatmap.pdf", bbox_inches='tight')
    
    # Figure 3: Context Sensitivity
    fig3 = create_context_sensitivity_plot(df)
    fig3.savefig(f"{output_dir}/figure_context_sensitivity.pdf", bbox_inches='tight')
    
    # Figure 4: Trade-off Curves
    fig4 = create_tradeoff_curves(df)
    fig4.savefig(f"{output_dir}/figure_tradeoffs.pdf", bbox_inches='tight')
    
    plt.close('all')

def create_cro_space_plot(df: pd.DataFrame) -> plt.Figure:
    """
    Create 3D visualization of CRO space
    Reproduces Figure 7.1 from manuscript
    """
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Get unique protocols (use GDPR context as default)
    gdpr_data = df[df['context'] == 'gdpr']
    
    # Define colors for each protocol type
    colors = {
        'groth16': 'red',
        'dilithium3': 'blue',
        'sphincs_plus': 'green',
        'ecdsa': 'orange',
        'bls': 'purple'
    }
    
    # Plot each protocol
    for _, row in gdpr_data.iterrows():
        ax.scatter(row['confidentiality_mean'],
                  row['reliability_mean'],
                  row['opposability_normalized'],
                  c=colors[row['protocol']],
                  s=100,
                  alpha=0.8,
                  edgecolors='black',
                  linewidth=0.5,
                  label=row['protocol'])
    
    # Draw theoretical bound surface
    priv_range = np.linspace(0, 1, 50)
    rel_range = np.linspace(0, 1, 50)
    Priv, Rel = np.meshgrid(priv_range, rel_range)
    
    # Simplified bound surface (for visualization)
    context_entropy = 10  # Simplified for visualization
    Opp_bound = (1 / (2**context_entropy)) / (Priv * Rel + 0.001)
    Opp_bound = np.minimum(Opp_bound, 1)  # Cap at 1
    
    ax.plot_surface(Priv, Rel, Opp_bound, alpha=0.2, color='gray')
    
    # Labels and formatting
    ax.set_xlabel('Confidentiality (Priv)', labelpad=10)
    ax.set_ylabel('Reliability (Rel)', labelpad=10)
    ax.set_zlabel('Opposability (H_Opp/log|V_J|)', labelpad=10)
    ax.set_title('CRO Space: Empirical Measurements vs Theoretical Bound', pad=20)
    
    # Remove duplicate labels
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper left')
    
    # Set viewing angle
    ax.view_init(elev=20, azim=45)
    
    return fig

def create_violation_heatmap(df: pd.DataFrame) -> plt.Figure:
    """
    Create heatmap showing trilemma violations
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Prepare data for heatmap
    pivot_data = df.pivot_table(
        values='gamma_cro',
        index='protocol',
        columns='context',
        aggfunc='mean'
    )
    
    # Create heatmap
    sns.heatmap(pivot_data, 
                annot=True, 
                fmt='.3f',
                cmap='RdYlGn_r',
                vmin=0, 
                vmax=1,
                cbar_kws={'label': 'Γ_CRO (Trilemma Deviation)'},
                ax=ax)
    
    ax.set_title('CRO Trilemma Deviation Across Protocols and Contexts')
    ax.set_xlabel('Context')
    ax.set_ylabel('Protocol')
    
    # Add threshold line annotation
    for i in range(len(pivot_data.index)):
        for j in range(len(pivot_data.columns)):
            value = pivot_data.iloc[i, j]
            if value > 0.5:  # Threshold for "violation"
                ax.add_patch(plt.Rectangle((j, i), 1, 1, 
                                          fill=False, 
                                          edgecolor='red', 
                                          lw=2))
    
    plt.tight_layout()
    return fig

def create_context_sensitivity_plot(df: pd.DataFrame) -> plt.Figure:
    """
    Create context sensitivity analysis plot
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left: Opposability variation
    ax1 = axes[0]
    for protocol in df['protocol'].unique():
        protocol_data = df[df['protocol'] == protocol]
        contexts = protocol_data['context'].values
        opposability = protocol_data['opposability_mean'].values
        error = protocol_data['opposability_std'].values
        
        x_pos = np.arange(len(contexts))
        ax1.errorbar(x_pos, opposability, yerr=error, 
                    label=protocol, marker='o', capsize=5)
    
    ax1.set_xticks(range(len(CONTEXTS)))
    ax1.set_xticklabels(CONTEXTS)
    ax1.set_xlabel('Context')
    ax1.set_ylabel('Opposability (bits)')
    ax1.set_title('Context Impact on Opposability')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Right: Gamma_CRO variation
    ax2 = axes[1]
    pivot_gamma = df.pivot_table(
        values='gamma_cro',
        index='context',
        columns='protocol',
        aggfunc='mean'
    )
    
    pivot_gamma.plot(kind='bar', ax=ax2)
    ax2.set_xlabel('Context')
    ax2.set_ylabel('Γ_CRO')
    ax2.set_title('Trilemma Deviation by Context')
    ax2.legend(title='Protocol', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
    
    plt.tight_layout()
    return fig

def create_tradeoff_curves(df: pd.DataFrame) -> plt.Figure:
    """
    Create trade-off curves between CRO dimensions
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    gdpr_data = df[df['context'] == 'gdpr']
    
    # Priv vs Opp
    ax1 = axes[0, 0]
    ax1.scatter(gdpr_data['confidentiality_mean'], 
               gdpr_data['opposability_mean'])
    for _, row in gdpr_data.iterrows():
        ax1.annotate(row['protocol'][:4], 
                    (row['confidentiality_mean'], row['opposability_mean']),
                    fontsize=8)
    ax1.set_xlabel('Confidentiality')
    ax1.set_ylabel('Opposability (bits)')
    ax1.set_title('Privacy-Opposability Trade-off')
    ax1.grid(True, alpha=0.3)
    
    # Rel vs Opp
    ax2 = axes[0, 1]
    ax2.scatter(gdpr_data['reliability_mean'], 
               gdpr_data['opposability_mean'])
    for _, row in gdpr_data.iterrows():
        ax2.annotate(row['protocol'][:4],
                    (row['reliability_mean'], row['opposability_mean']),
                    fontsize=8)
    ax2.set_xlabel('Reliability')
    ax2.set_ylabel('Opposability (bits)')
    ax2.set_title('Reliability-Opposability Trade-off')
    ax2.grid(True, alpha=0.3)
    
    # Priv vs Rel
    ax3 = axes[1, 0]
    ax3.scatter(gdpr_data['confidentiality_mean'],
               gdpr_data['reliability_mean'])
    for _, row in gdpr_data.iterrows():
        ax3.annotate(row['protocol'][:4],
                    (row['confidentiality_mean'], row['reliability_mean']),
                    fontsize=8)
    ax3.set_xlabel('Confidentiality')
    ax3.set_ylabel('Reliability')
    ax3.set_title('Privacy-Reliability Trade-off')
    ax3.grid(True, alpha=0.3)
    
    # Gamma vs Context Entropy
    ax4 = axes[1, 1]
    ax4.scatter(df['context_entropy'], df['gamma_cro'])
    ax4.set_xlabel('Context Entropy H(C)')
    ax4.set_ylabel('Γ_CRO')
    ax4.set_title('Trilemma Deviation vs Context Complexity')
    ax4.grid(True, alpha=0.3)
    
    # Add theoretical bound line
    h_range = np.linspace(df['context_entropy'].min(), 
                         df['context_entropy'].max(), 100)
    theoretical_bound = 1 / (2**h_range)
    ax4.plot(h_range, theoretical_bound, 'r--', 
            label='Theoretical Bound', alpha=0.7)
    ax4.legend()
    
    plt.tight_layout()
    return fig