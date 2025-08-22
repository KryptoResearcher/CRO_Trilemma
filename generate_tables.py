#!/usr/bin/env python3
"""
Generate LaTeX tables from measurement results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import argparse

def generate_main_table(df: pd.DataFrame, output_dir: str):
    """Generate Table 3: Main CRO Metrics"""
    
    # Filter for GDPR context
    gdpr_data = df[df['context'] == 'gdpr'].copy()
    
    # Select and rename columns
    table_data = gdpr_data[['protocol', 'confidentiality_mean', 'confidentiality_std',
                           'reliability_mean', 'reliability_std',
                           'opposability_mean', 'opposability_std',
                           'gamma_cro']]
    
    # Format for LaTeX
    latex_str = r"""\begin{table}[H]
\centering
\caption{Empirical CRO Measurements for Contemporary Protocols}
\label{tab:cro_metrics}
\begin{tabular}{lcccc}
\toprule
\textbf{Protocol} & \textbf{Priv} & \textbf{Rel} & \textbf{$H_{\text{Opp}}$ (bits)} & \textbf{$\Gamma_{\text{CRO}}$} \\
\midrule
"""
    
    for _, row in table_data.iterrows():
        protocol = row['protocol'].replace('_', r'\_')
        priv = f"{row['confidentiality_mean']:.4f} ± {row['confidentiality_std']:.4f}"
        rel = f"{row['reliability_mean']:.4f} ± {row['reliability_std']:.4f}"
        opp = f"{row['opposability_mean']:.2f} ± {row['opposability_std']:.2f}"
        gamma = f"{row['gamma_cro']:.4f}"
        
        latex_str += f"{protocol} & ${priv}$ & ${rel}$ & ${opp}$ & ${gamma}$ \\\\\n"
    
    latex_str += r"""\bottomrule
\end{tabular}
\end{table}"""
    
    # Save
    output_path = Path(output_dir) / "table_main_metrics.tex"
    with open(output_path, 'w') as f:
        f.write(latex_str)
    
    print(f"Generated: {output_path}")

def generate_context_table(df: pd.DataFrame, output_dir: str):
    """Generate Table 4: Context Sensitivity"""
    
    # Pivot table
    pivot = df.pivot_table(
        values='opposability_mean',
        index='protocol',
        columns='context',
        aggfunc='mean'
    )
    
    latex_str = r"""\begin{table}[H]
\centering
\caption{Opposability Under Different Contexts (bits)}
\label{tab:context_sensitivity}
\begin{tabular}{lcccc}
\toprule
\textbf{Protocol} & \textbf{GDPR} & \textbf{HIPAA} & \textbf{Financial} & \textbf{Criminal} \\
\midrule
"""
    
    for protocol in pivot.index:
        protocol_str = protocol.replace('_', r'\_')
        values = [f"{pivot.loc[protocol, ctx]:.2f}" for ctx in pivot.columns]
        latex_str += f"{protocol_str} & {' & '.join(values)} \\\\\n"
    
    latex_str += r"""\bottomrule
\end{tabular}
\end{table}"""
    
    # Save
    output_path = Path(output_dir) / "table_context_sensitivity.tex"
    with open(output_path, 'w') as f:
        f.write(latex_str)
    
    print(f"Generated: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate LaTeX tables')
    parser.add_argument('--input', default='data/results/complete_measurements.csv',
                       help='Input CSV file')
    parser.add_argument('--output', default='data/results',
                       help='Output directory')
    args = parser.parse_args()
    
    # Load data
    df = pd.read_csv(args.input)
    
    # Generate tables
    generate_main_table(df, args.output)
    generate_context_table(df, args.output)
    
    print("\nAll tables generated successfully!")

if __name__ == "__main__":
    main()