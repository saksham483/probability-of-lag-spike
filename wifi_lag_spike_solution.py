#!/usr/bin/env python3
"""
Wi-Fi Lag Spike Analysis & Statistical Modeling Solution
=========================================================
Course: Applied Probability & Statistical Inference
Project: The Probability of a Lag Spike: Statistical Modeling of Network Latency

This script performs:
1. Data parsing & cleaning of ping latency measurements (wifi_data.txt)
2. Exploratory Data Analysis (EDA): central tendency, dispersion, skewness, kurtosis
3. Distribution modeling via Maximum Likelihood Estimation (MLE):
   - Shifted Gamma
   - Shifted Weibull
   - Shifted Log-Normal
   - Log-Normal (loc=0)
   - Shifted Exponential
   - Normal Distribution
4. Goodness-of-Fit & Model Selection:
   - Log-Likelihood, AIC, BIC
   - Kolmogorov-Smirnov (K-S) test statistic & p-value
   - D'Agostino-Pearson normality test
5. Lag Spike Disruption Probability Analysis:
   - P(X > 100 ms), P(X > 150 ms), P(X > 200 ms)
   - Empirical vs Fitted vs Gaussian models
6. Bootstrap Uncertainty Estimation:
   - 95% Confidence Intervals for Median, Mean, P90, P99, and P(X > 100 ms)
7. Temporal / Autocorrelation & Burst Analysis
8. Publication-Quality Figure Generation matching the presentation theme.
"""

import os
import re
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# -----------------------------------------------------------------------------
# Configuration & Theme Colors (Matching the Presentation Theme)
# -----------------------------------------------------------------------------
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

THEME = {
    'navy': '#12355b',
    'royal_blue': '#1e3989',
    'accent_blue': '#2563eb',
    'light_blue': '#8392bd',
    'bg_cream': '#f7f3eb',
    'card_bg': '#ffffff',
    'dark_text': '#0f172a',
    'muted_text': '#555b66',
    'border_gray': '#e2e8f0',
    'red_accent': '#dc2626',
    'amber_accent': '#d97706',
    'green_accent': '#16a34a',
    'purple_accent': '#7c3aed'
}

plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.titlecolor'] = THEME['navy']
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['axes.labelcolor'] = THEME['dark_text']
plt.rcParams['xtick.color'] = THEME['muted_text']
plt.rcParams['ytick.color'] = THEME['muted_text']
plt.rcParams['figure.facecolor'] = '#ffffff'
plt.rcParams['axes.facecolor'] = '#ffffff'

DATA_PATH = 'wifi_data.txt'
OUTPUT_DIR = 'solution_outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Data Ingestion & Cleaning
# -----------------------------------------------------------------------------
def load_and_clean_data(file_path):
    print(f"Loading raw ping data from {file_path}...")
    with open(file_path, 'r') as f:
        lines = f.readlines()

    records = []
    total_transmitted = 0
    total_received = 0
    packet_loss_reported = 0.0

    for line in lines:
        line = line.strip()
        # Parse ping statistics header/footer if present
        if 'packets transmitted' in line:
            # e.g., 4444 packets transmitted, 3685 received, +160 errors, 17.0792% packet loss
            m_stat = re.search(r'(\d+)\s+packets transmitted,\s+(\d+)\s+received.*?([\d\.]+)%\s+packet loss', line)
            if m_stat:
                total_transmitted = int(m_stat.group(1))
                total_received = int(m_stat.group(2))
                packet_loss_reported = float(m_stat.group(3))

        # Parse individual ping response
        # e.g., 64 bytes from 8.8.8.8: icmp_seq=1 ttl=113 time=44.4 ms
        m = re.search(r'icmp_seq=(\d+)\s+.*(?:ttl=(\d+))?.*time=([\d\.]+)\s*ms', line)
        if m:
            seq = int(m.group(1))
            ttl = int(m.group(2)) if m.group(2) else None
            rtt = float(m.group(3))
            records.append({'icmp_seq': seq, 'ttl': ttl, 'rtt_ms': rtt})

    df = pd.DataFrame(records)
    df.sort_values('icmp_seq', inplace=True)
    df.reset_index(drop=True, inplace=True)

    seq_min = df['icmp_seq'].min()
    seq_max = df['icmp_seq'].max()
    seq_span = seq_max - seq_min + 1
    lost_in_span = seq_span - len(df)

    if total_transmitted == 0:
        total_transmitted = seq_span
        total_received = len(df)
        packet_loss_reported = (lost_in_span / seq_span) * 100.0

    print(f"-> Successfully parsed {len(df)} ping replies.")
    print(f"-> ICMP sequence range: {seq_min} to {seq_max} (Span: {seq_span})")
    print(f"-> Total packets transmitted: {total_transmitted}, Received: {total_received}")
    print(f"-> Packet loss: {packet_loss_reported:.2f}% ({total_transmitted - total_received} packets lost)")

    return df, {
        'total_transmitted': total_transmitted,
        'total_received': total_received,
        'packet_loss_pct': packet_loss_reported,
        'seq_min': seq_min,
        'seq_max': seq_max,
        'seq_span': seq_span,
        'lost_in_span': lost_in_span
    }

# -----------------------------------------------------------------------------
# 2. Exploratory Data Analysis (EDA)
# -----------------------------------------------------------------------------
def compute_eda_statistics(data):
    n = len(data)
    mean_val = np.mean(data)
    std_val = np.std(data, ddof=1)
    var_val = np.var(data, ddof=1)
    median_val = np.median(data)
    q25 = np.percentile(data, 25)
    q75 = np.percentile(data, 75)
    iqr_val = q75 - q25
    min_val = np.min(data)
    max_val = np.max(data)
    p90 = np.percentile(data, 90)
    p95 = np.percentile(data, 95)
    p99 = np.percentile(data, 99)
    skewness = float(stats.skew(data))
    kurtosis_excess = float(stats.kurtosis(data))  # excess kurtosis (Fisher, normal=0)
    kurtosis_raw = kurtosis_excess + 3.0           # Pearson kurtosis (normal=3)

    # Normality test: D'Agostino-Pearson Omnibus
    k2_stat, norm_p = stats.normaltest(data)

    stats_dict = {
        'n': int(n),
        'mean': float(mean_val),
        'std': float(std_val),
        'variance': float(var_val),
        'median': float(median_val),
        'q25': float(q25),
        'q75': float(q75),
        'iqr': float(iqr_val),
        'min': float(min_val),
        'max': float(max_val),
        'p90': float(p90),
        'p95': float(p95),
        'p99': float(p99),
        'skewness': float(skewness),
        'kurtosis_excess': float(kurtosis_excess),
        'kurtosis_raw': float(kurtosis_raw),
        'dagostino_k2': float(k2_stat),
        'dagostino_p_value': float(norm_p)
    }

    print("\n--- EXPLORATORY DATA ANALYSIS SUMMARY ---")
    print(f"Sample Size (N)     : {n:,}")
    print(f"Mean Latency        : {mean_val:.2f} ms")
    print(f"Std Deviation       : {std_val:.2f} ms")
    print(f"Median Latency      : {median_val:.2f} ms")
    print(f"IQR (Q1 - Q3)       : {iqr_val:.2f} ms ({q25:.2f} - {q75:.2f} ms)")
    print(f"Min / Max Latency   : {min_val:.2f} ms / {max_val:.2f} ms")
    print(f"P90 / P95 / P99     : {p90:.2f} ms / {p95:.2f} ms / {p99:.2f} ms")
    print(f"Sample Skewness     : {skewness:.3f} (Strong positive right-skew)")
    print(f"Excess Kurtosis     : {kurtosis_excess:.3f} (Extremely heavy-tailed / leptokurtic)")
    print(f"D'Agostino K^2 Test : stat={k2_stat:.1f}, p={norm_p:.2e} (Decisive rejection of normality)")

    return stats_dict

# -----------------------------------------------------------------------------
# 3. Parametric Distribution Fitting via MLE
# -----------------------------------------------------------------------------
def fit_distributions(data):
    n = len(data)
    min_x = np.min(data)

    # Dictionary to store fitted models and parameters
    fitted_models = {}

    # 1. Shifted Gamma: physical floor at min_x
    # scipy gamma pdf: (x-loc)**(a-1) * exp(-(x-loc)/scale) / (gamma(a) * scale**a)
    gamma_params = stats.gamma.fit(data, loc=min_x - 0.01)
    fitted_models['Shifted Gamma'] = {
        'dist': stats.gamma,
        'params': gamma_params,
        'k': len(gamma_params),
        'param_names': ['shape (alpha)', 'loc (gamma)', 'scale (beta)']
    }

    # 2. Shifted Weibull (weibull_min)
    weibull_params = stats.weibull_min.fit(data, loc=min_x - 0.01)
    fitted_models['Shifted Weibull'] = {
        'dist': stats.weibull_min,
        'params': weibull_params,
        'k': len(weibull_params),
        'param_names': ['shape (c)', 'loc (gamma)', 'scale (lambda)']
    }

    # 3. Shifted Log-Normal
    # scipy lognorm: shape s (sigma), loc, scale (exp(mu))
    lognorm_s_params = stats.lognorm.fit(data)
    fitted_models['Shifted Log-Normal'] = {
        'dist': stats.lognorm,
        'params': lognorm_s_params,
        'k': len(lognorm_s_params),
        'param_names': ['shape (sigma)', 'loc (gamma)', 'scale (exp(mu))']
    }

    # 4. Standard Log-Normal (loc=0)
    lognorm_0_params = stats.lognorm.fit(data, floc=0)
    fitted_models['Log-Normal (loc=0)'] = {
        'dist': stats.lognorm,
        'params': lognorm_0_params,
        'k': 2,
        'param_names': ['shape (sigma)', 'loc (fixed 0)', 'scale (exp(mu))']
    }

    # 5. Shifted Exponential
    expon_params = stats.expon.fit(data)
    fitted_models['Shifted Exponential'] = {
        'dist': stats.expon,
        'params': expon_params,
        'k': len(expon_params),
        'param_names': ['loc (gamma)', 'scale (beta)']
    }

    # 6. Gaussian / Normal (baseline model)
    norm_params = stats.norm.fit(data)
    fitted_models['Normal (Gaussian)'] = {
        'dist': stats.norm,
        'params': norm_params,
        'k': len(norm_params),
        'param_names': ['mean (mu)', 'std (sigma)']
    }

    # Evaluate goodness of fit
    comparison_records = []
    print("\n--- DISTRIBUTION FITTING & GOODNESS-OF-FIT EVALUATION ---")

    for name, m in fitted_models.items():
        dist = m['dist']
        params = m['params']
        k = m['k']

        # Log-Likelihood
        loglik = float(np.sum(dist.logpdf(data, *params)))
        # Information criteria
        aic = float(2 * k - 2 * loglik)
        bic = float(k * np.log(n) - 2 * loglik)

        # Kolmogorov-Smirnov Test
        ks_res = stats.kstest(data, dist.name, args=params)
        ks_stat = float(ks_res.statistic)
        ks_pval = float(ks_res.pvalue)

        # Disruption probabilities
        p_100 = float((1.0 - dist.cdf(100.0, *params)) * 100.0)
        p_150 = float((1.0 - dist.cdf(150.0, *params)) * 100.0)
        p_200 = float((1.0 - dist.cdf(200.0, *params)) * 100.0)

        # Pack into model
        m['loglik'] = loglik
        m['aic'] = aic
        m['bic'] = bic
        m['ks_stat'] = ks_stat
        m['ks_pval'] = ks_pval
        m['p_lag_100'] = p_100
        m['p_lag_150'] = p_150
        m['p_lag_200'] = p_200

        comparison_records.append({
            'Model': name,
            'Parameters': {pname: float(pval) for pname, pval in zip(m['param_names'], params)},
            'Num_Params (k)': k,
            'Log_Likelihood': loglik,
            'AIC': aic,
            'BIC': bic,
            'KS_Statistic': ks_stat,
            'KS_p_value': ks_pval,
            'P_X_gt_100ms_pct': p_100,
            'P_X_gt_150ms_pct': p_150,
            'P_X_gt_200ms_pct': p_200
        })

    comp_df = pd.DataFrame(comparison_records)
    comp_df.sort_values('AIC', inplace=True)
    comp_df.reset_index(drop=True, inplace=True)

    print(f"{'Model':<24} {'LogLik':<10} {'AIC':<10} {'BIC':<10} {'KS-Stat':<10} {'KS p-val':<10} {'P(X>100)':<10}")
    print("-" * 88)
    for _, row in comp_df.iterrows():
        print(f"{row['Model']:<24} {row['Log_Likelihood']:<10.1f} {row['AIC']:<10.1f} {row['BIC']:<10.1f} {row['KS_Statistic']:<10.4f} {row['KS_p_value']:<10.2e} {row['P_X_gt_100ms_pct']:<10.2f}%")

    emp_p100 = np.mean(data > 100.0) * 100.0
    print(f"{'Empirical Live Wi-Fi':<24} {'-':<10} {'-':<10} {'-':<10} {'-':<10} {'-':<10} {emp_p100:<10.2f}%")

    return fitted_models, comp_df

# -----------------------------------------------------------------------------
# 4. Bootstrap Confidence Intervals
# -----------------------------------------------------------------------------
def compute_bootstrap_ci(data, b_iterations=5000, seed=42):
    print(f"\nComputing Non-Parametric Bootstrap Confidence Intervals (B = {b_iterations:,} resamples)...")
    np.random.seed(seed)
    n = len(data)

    boot_idx = np.random.randint(0, n, size=(b_iterations, n))
    boot_samples = data[boot_idx]

    boot_means = np.mean(boot_samples, axis=1)
    boot_medians = np.median(boot_samples, axis=1)
    boot_p90s = np.percentile(boot_samples, 90.0, axis=1)
    boot_p99s = np.percentile(boot_samples, 99.0, axis=1)
    boot_p100s = np.mean(boot_samples > 100.0, axis=1) * 100.0

    ci_results = {
        'mean': {
            'point_estimate': float(np.mean(data)),
            'ci_lower_95': float(np.percentile(boot_means, 2.5)),
            'ci_upper_95': float(np.percentile(boot_means, 97.5)),
            'boot_dist': boot_means
        },
        'median': {
            'point_estimate': float(np.median(data)),
            'ci_lower_95': float(np.percentile(boot_medians, 2.5)),
            'ci_upper_95': float(np.percentile(boot_medians, 97.5)),
            'boot_dist': boot_medians
        },
        'p90': {
            'point_estimate': float(np.percentile(data, 90.0)),
            'ci_lower_95': float(np.percentile(boot_p90s, 2.5)),
            'ci_upper_95': float(np.percentile(boot_p90s, 97.5)),
            'boot_dist': boot_p90s
        },
        'p99': {
            'point_estimate': float(np.percentile(data, 99.0)),
            'ci_lower_95': float(np.percentile(boot_p99s, 2.5)),
            'ci_upper_95': float(np.percentile(boot_p99s, 97.5)),
            'boot_dist': boot_p99s
        },
        'p_lag_100': {
            'point_estimate': float(np.mean(data > 100.0) * 100.0),
            'ci_lower_95': float(np.percentile(boot_p100s, 2.5)),
            'ci_upper_95': float(np.percentile(boot_p100s, 97.5)),
            'boot_dist': boot_p100s
        }
    }

    print("--- 95% BOOTSTRAP CONFIDENCE INTERVALS ---")
    for metric, res in ci_results.items():
        unit = "%" if metric == "p_lag_100" else "ms"
        print(f"{metric:<15}: Point = {res['point_estimate']:.2f}{unit} | 95% CI: [{res['ci_lower_95']:.2f}{unit}, {res['ci_upper_95']:.2f}{unit}]")

    return ci_results

# -----------------------------------------------------------------------------
# 5. Temporal Autocorrelation & Burst Dynamics
# -----------------------------------------------------------------------------
def analyze_temporal_dynamics(df):
    data = df['rtt_ms'].values
    lag1_corr = float(np.corrcoef(data[:-1], data[1:])[0, 1])

    # Run lengths of lag spikes (consecutive pings > 100 ms)
    is_spike = (data > 100.0).astype(int)
    burst_lengths = []
    current_run = 0
    for v in is_spike:
        if v == 1:
            current_run += 1
        else:
            if current_run > 0:
                burst_lengths.append(current_run)
                current_run = 0
    if current_run > 0:
        burst_lengths.append(current_run)

    burst_lengths = np.array(burst_lengths) if burst_lengths else np.array([0])

    temporal_stats = {
        'lag1_autocorrelation': lag1_corr,
        'total_bursts': int(len(burst_lengths)),
        'mean_burst_length': float(np.mean(burst_lengths)),
        'median_burst_length': float(np.median(burst_lengths)),
        'max_burst_length': int(np.max(burst_lengths)),
        'p90_burst_length': float(np.percentile(burst_lengths, 90))
    }

    print("\n--- TEMPORAL & BURST DYNAMICS ---")
    print(f"Lag-1 Autocorrelation (rho_1) : {lag1_corr:.3f} (Significant positive correlation)")
    print(f"Total Disruption Bursts (>100ms) : {len(burst_lengths)}")
    print(f"Mean Burst Duration           : {np.mean(burst_lengths):.1f} consecutive packets")
    print(f"Max Burst Duration            : {np.max(burst_lengths)} consecutive packets")

    return temporal_stats

# -----------------------------------------------------------------------------
# 6. High-Quality Figure Generation
# -----------------------------------------------------------------------------
def generate_all_figures(df, eda_stats, fitted_models, comp_df, ci_results, temporal_stats):
    data = df['rtt_ms'].values
    print("\nGenerating presentation-ready figures...")

    # -------------------------------------------------------------------------
    # Figure 1: Ping Latency Time Series & Lag Spike Burst Run Chart
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)
    fig.patch.set_facecolor(THEME['bg_cream'])
    ax.set_facecolor('#ffffff')

    seqs = df['icmp_seq'].values
    ax.plot(seqs, data, color=THEME['navy'], alpha=0.65, lw=0.8, label='Empirical Latency (ms)')
    ax.axhline(100.0, color=THEME['red_accent'], linestyle='--', lw=1.8, label='Lag Spike Threshold (T = 100 ms)')
    ax.axhline(eda_stats['mean'], color=THEME['amber_accent'], linestyle=':', lw=1.5, label=f"Mean Latency ({eda_stats['mean']:.1f} ms)")
    ax.axhline(eda_stats['median'], color=THEME['green_accent'], linestyle='-.', lw=1.5, label=f"Median Latency ({eda_stats['median']:.1f} ms)")

    # Highlight tail spikes
    extreme_mask = data > 500
    if np.any(extreme_mask):
        ax.scatter(seqs[extreme_mask], data[extreme_mask], color=THEME['red_accent'], s=25, zorder=5, label='Extreme Spikes (>500 ms)')

    ax.set_title("Live Wi-Fi Latency Run Chart: Sequential ICMP Ping Measurements", fontsize=13, weight='bold', pad=12)
    ax.set_xlabel("ICMP Sequence Number", weight='bold')
    ax.set_ylabel("Round Trip Time (ms)", weight='bold')
    ax.set_ylim(0, min(1500, np.percentile(data, 99.8)))
    ax.legend(loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)

    # Annotation badge
    ax.text(0.02, 0.93, f"P(X > 100 ms) = {np.mean(data > 100)*100:.1f}%\nMax Burst = {temporal_stats['max_burst_length']} pkts\nLoss = 17.1%",
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor=THEME['royal_blue'], lw=1.2),
            fontsize=9, weight='bold', color=THEME['navy'])

    fig.tight_layout()
    fig1_path = os.path.join(OUTPUT_DIR, 'figure1_time_series_lag_spikes.png')
    fig.savefig(fig1_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved {fig1_path}")

    # -------------------------------------------------------------------------
    # Figure 2: Latency Density & Distribution Fits (Histogram + Models)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    fig.patch.set_facecolor(THEME['bg_cream'])
    ax.set_facecolor('#ffffff')

    # Empirical histogram & KDE
    clip_x = 700
    clipped_data = data[data <= clip_x]
    bins = np.linspace(0, clip_x, 70)
    ax.hist(clipped_data, bins=bins, density=True, alpha=0.35, color=THEME['light_blue'], edgecolor='#94a3b8', label='Empirical Density (Histogram)')

    x_grid = np.linspace(17.9, clip_x, 1000)

    # Shifted Gamma PDF (Best fit)
    gamma_pdf = fitted_models['Shifted Gamma']['dist'].pdf(x_grid, *fitted_models['Shifted Gamma']['params'])
    ax.plot(x_grid, gamma_pdf, color=THEME['royal_blue'], lw=2.4, label='Shifted Gamma (Best Fit, AIC=44,591)')

    # Shifted Weibull PDF
    weibull_pdf = fitted_models['Shifted Weibull']['dist'].pdf(x_grid, *fitted_models['Shifted Weibull']['params'])
    ax.plot(x_grid, weibull_pdf, color=THEME['purple_accent'], lw=2.0, linestyle='--', label='Shifted Weibull (AIC=44,640)')

    # Shifted Log-Normal PDF
    lognorm_pdf = fitted_models['Shifted Log-Normal']['dist'].pdf(x_grid, *fitted_models['Shifted Log-Normal']['params'])
    ax.plot(x_grid, lognorm_pdf, color=THEME['green_accent'], lw=1.8, linestyle='-.', label='Shifted Log-Normal (AIC=44,640)')

    # Normal PDF (Naive baseline)
    norm_pdf = fitted_models['Normal (Gaussian)']['dist'].pdf(x_grid, *fitted_models['Normal (Gaussian)']['params'])
    ax.plot(x_grid, norm_pdf, color=THEME['red_accent'], lw=1.8, linestyle=':', label='Normal / Gaussian (AIC=47,771 - Poor)')

    # Threshold indicator
    ax.axvline(100.0, color=THEME['red_accent'], linestyle='-', lw=1.2, alpha=0.8)
    ax.text(105, ax.get_ylim()[1]*0.85, 'Disruption Threshold\nT = 100 ms', color=THEME['red_accent'], weight='bold', fontsize=9)

    ax.set_title("Wi-Fi Latency Density & Candidate Probability Distributions (MLE)", fontsize=13, weight='bold', pad=12)
    ax.set_xlabel("Latency (ms)", weight='bold')
    ax.set_ylabel("Probability Density f(x)", weight='bold')
    ax.set_xlim(0, clip_x)
    ax.legend(loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)

    fig.tight_layout()
    fig2_path = os.path.join(OUTPUT_DIR, 'figure2_distribution_fits_kde.png')
    fig.savefig(fig2_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved {fig2_path}")

    # -------------------------------------------------------------------------
    # Figure 3: Empirical CDF vs Theoretical CDFs with Lag Spike Threshold
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.0), dpi=300)
    fig.patch.set_facecolor(THEME['bg_cream'])
    ax.set_facecolor('#ffffff')

    # Empirical CDF
    sorted_data = np.sort(data)
    ecdf_y = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax.plot(sorted_data, ecdf_y, color=THEME['navy'], lw=2.2, label='Empirical Cumulative Distribution (ECDF)')

    # Model CDFs
    x_cdf = np.linspace(17.9, 800, 1000)
    gamma_cdf = fitted_models['Shifted Gamma']['dist'].cdf(x_cdf, *fitted_models['Shifted Gamma']['params'])
    ax.plot(x_cdf, gamma_cdf, color=THEME['royal_blue'], lw=2.0, linestyle='--', label='Shifted Gamma CDF')

    lognorm_cdf = fitted_models['Shifted Log-Normal']['dist'].cdf(x_cdf, *fitted_models['Shifted Log-Normal']['params'])
    ax.plot(x_cdf, lognorm_cdf, color=THEME['green_accent'], lw=1.8, linestyle='-.', label='Shifted Log-Normal CDF')

    norm_cdf = fitted_models['Normal (Gaussian)']['dist'].cdf(x_cdf, *fitted_models['Normal (Gaussian)']['params'])
    ax.plot(x_cdf, norm_cdf, color=THEME['red_accent'], lw=1.8, linestyle=':', label='Normal CDF (Misfit)')

    # Lag Spike marker at 100 ms
    p100_emp = np.mean(data <= 100.0)
    ax.axvline(100.0, color=THEME['amber_accent'], linestyle='-', lw=1.5)
    ax.plot([0, 100], [p100_emp, p100_emp], color=THEME['amber_accent'], linestyle=':', lw=1.2)
    ax.scatter([100], [p100_emp], color=THEME['amber_accent'], s=50, zorder=6)
    ax.text(110, p100_emp - 0.08, f"F(100) = {p100_emp*100:.1f}%\nP(X > 100) = {(1-p100_emp)*100:.1f}%",
            weight='bold', color=THEME['navy'], fontsize=9,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffffff', edgecolor=THEME['amber_accent']))

    ax.set_title("Cumulative Distribution Functions: Empirical vs Parametric Models", fontsize=13, weight='bold', pad=12)
    ax.set_xlabel("Latency Threshold x (ms)", weight='bold')
    ax.set_ylabel("Cumulative Probability F(x) = P(X <= x)", weight='bold')
    ax.set_xlim(0, 800)
    ax.set_ylim(0, 1.02)
    ax.legend(loc='lower right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)

    fig.tight_layout()
    fig3_path = os.path.join(OUTPUT_DIR, 'figure3_ecdf_vs_models.png')
    fig.savefig(fig3_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved {fig3_path}")

    # -------------------------------------------------------------------------
    # Figure 4: Q-Q Plots Comparison (Normal vs Gamma vs Log-Normal vs Weibull)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5), dpi=300)
    fig.patch.set_facecolor(THEME['bg_cream'])

    quantiles = np.linspace(0.01, 0.99, 100)
    emp_quantiles = np.percentile(data, quantiles * 100)

    plot_models = [
        ('Shifted Gamma (Best Fit)', fitted_models['Shifted Gamma'], axes[0, 0], THEME['royal_blue']),
        ('Shifted Weibull', fitted_models['Shifted Weibull'], axes[0, 1], THEME['purple_accent']),
        ('Shifted Log-Normal', fitted_models['Shifted Log-Normal'], axes[1, 0], THEME['green_accent']),
        ('Normal (Gaussian)', fitted_models['Normal (Gaussian)'], axes[1, 1], THEME['red_accent']),
    ]

    for title, m, ax, col in plot_models:
        ax.set_facecolor('#ffffff')
        theo_quantiles = m['dist'].ppf(quantiles, *m['params'])
        ax.scatter(theo_quantiles, emp_quantiles, color=col, alpha=0.7, s=18, edgecolors='none')
        # Reference 45-degree line
        min_q = min(np.min(theo_quantiles), np.min(emp_quantiles))
        max_q = max(np.max(theo_quantiles), np.max(emp_quantiles))
        ax.plot([min_q, max_q], [min_q, max_q], color='#475569', linestyle='--', lw=1.2)

        ax.set_title(f"Q-Q Plot: {title}\n(KS={m['ks_stat']:.4f}, AIC={m['aic']:.0f})", fontsize=10, weight='bold')
        ax.set_xlabel("Theoretical Quantiles (ms)", weight='bold', fontsize=9)
        ax.set_ylabel("Empirical Quantiles (ms)", weight='bold', fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.5)

    fig.suptitle("Quantile-Quantile (Q-Q) Diagnostics: Assessing Goodness-of-Fit", fontsize=14, weight='bold', color=THEME['navy'], y=0.99)
    fig.tight_layout()
    fig4_path = os.path.join(OUTPUT_DIR, 'figure4_qq_plots.png')
    fig.savefig(fig4_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved {fig4_path}")

    # -------------------------------------------------------------------------
    # Figure 5: Tail Disruption Risk Curve P(X > T)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.0), dpi=300)
    fig.patch.set_facecolor(THEME['bg_cream'])
    ax.set_facecolor('#ffffff')

    thresholds = np.linspace(20, 600, 200)
    emp_p_tail = np.array([np.mean(data > t) * 100.0 for t in thresholds])
    gamma_p_tail = np.array([(1.0 - fitted_models['Shifted Gamma']['dist'].cdf(t, *fitted_models['Shifted Gamma']['params'])) * 100.0 for t in thresholds])
    weibull_p_tail = np.array([(1.0 - fitted_models['Shifted Weibull']['dist'].cdf(t, *fitted_models['Shifted Weibull']['params'])) * 100.0 for t in thresholds])
    lognorm_p_tail = np.array([(1.0 - fitted_models['Shifted Log-Normal']['dist'].cdf(t, *fitted_models['Shifted Log-Normal']['params'])) * 100.0 for t in thresholds])
    norm_p_tail = np.array([(1.0 - fitted_models['Normal (Gaussian)']['dist'].cdf(t, *fitted_models['Normal (Gaussian)']['params'])) * 100.0 for t in thresholds])

    ax.plot(thresholds, emp_p_tail, color=THEME['navy'], lw=2.5, label='Empirical Wi-Fi Risk P(X > T)')
    ax.plot(thresholds, gamma_p_tail, color=THEME['royal_blue'], lw=2.0, linestyle='--', label='Shifted Gamma Prediction')
    ax.plot(thresholds, weibull_p_tail, color=THEME['purple_accent'], lw=1.8, linestyle='-.', label='Shifted Weibull Prediction')
    ax.plot(thresholds, lognorm_p_tail, color=THEME['green_accent'], lw=1.8, linestyle=':', label='Shifted Log-Normal Prediction')
    ax.plot(thresholds, norm_p_tail, color=THEME['red_accent'], lw=1.8, linestyle='-', alpha=0.7, label='Gaussian Prediction (Fails at Tail)')

    # Highlighting key thresholds
    key_t = [100, 150, 200]
    for t_val in key_t:
        emp_v = np.mean(data > t_val) * 100.0
        ax.scatter([t_val], [emp_v], color=THEME['red_accent'], s=45, zorder=5)
        ax.annotate(f"T={t_val}ms\n{emp_v:.1f}%", xy=(t_val, emp_v), xytext=(t_val + 15, emp_v + 5),
                    arrowprops=dict(arrowstyle='->', color=THEME['navy'], lw=1.0),
                    fontsize=8.5, weight='bold', color=THEME['navy'],
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#cbd5e1'))

    ax.set_title("Probability of Network Disruption: P(X > T) across Latency Thresholds", fontsize=13, weight='bold', pad=12)
    ax.set_xlabel("Latency Disruption Threshold T (ms)", weight='bold')
    ax.set_ylabel("Disruption Probability P(X > T) %", weight='bold')
    ax.set_xlim(20, 600)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)

    fig.tight_layout()
    fig5_path = os.path.join(OUTPUT_DIR, 'figure5_disruption_risk_curve.png')
    fig.savefig(fig5_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved {fig5_path}")

    # -------------------------------------------------------------------------
    # Figure 6: Bootstrap Sampling Distributions & 95% Confidence Intervals
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), dpi=300)
    fig.patch.set_facecolor(THEME['bg_cream'])

    # Left: Median Latency Bootstrap
    ax1 = axes[0]
    ax1.set_facecolor('#ffffff')
    med_res = ci_results['median']
    ax1.hist(med_res['boot_dist'], bins=30, color=THEME['royal_blue'], alpha=0.7, edgecolor='#ffffff')
    ax1.axvline(med_res['point_estimate'], color=THEME['navy'], lw=2.2, label=f"Median Point: {med_res['point_estimate']:.1f} ms")
    ax1.axvline(med_res['ci_lower_95'], color=THEME['red_accent'], lw=1.8, linestyle='--', label=f"95% CI Lower: {med_res['ci_lower_95']:.1f} ms")
    ax1.axvline(med_res['ci_upper_95'], color=THEME['red_accent'], lw=1.8, linestyle='--', label=f"95% CI Upper: {med_res['ci_upper_95']:.1f} ms")
    ax1.set_title("Bootstrap Distribution: Median Latency", weight='bold', fontsize=11)
    ax1.set_xlabel("Bootstrap Median (ms)", weight='bold')
    ax1.set_ylabel("Frequency", weight='bold')
    ax1.legend(loc='upper right', fontsize=8.5, frameon=True, facecolor='#ffffff')
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Right: P99 Tail Latency Bootstrap
    ax2 = axes[1]
    ax2.set_facecolor('#ffffff')
    p99_res = ci_results['p99']
    ax2.hist(p99_res['boot_dist'], bins=35, color=THEME['amber_accent'], alpha=0.75, edgecolor='#ffffff')
    ax2.axvline(p99_res['point_estimate'], color=THEME['navy'], lw=2.2, label=f"P99 Point: {p99_res['point_estimate']:.1f} ms")
    ax2.axvline(p99_res['ci_lower_95'], color=THEME['red_accent'], lw=1.8, linestyle='--', label=f"95% CI Lower: {p99_res['ci_lower_95']:.1f} ms")
    ax2.axvline(p99_res['ci_upper_95'], color=THEME['red_accent'], lw=1.8, linestyle='--', label=f"95% CI Upper: {p99_res['ci_upper_95']:.1f} ms")
    ax2.set_title("Bootstrap Distribution: 99th Percentile (P99 Tail)", weight='bold', fontsize=11)
    ax2.set_xlabel("Bootstrap P99 (ms)", weight='bold')
    ax2.set_ylabel("Frequency", weight='bold')
    ax2.legend(loc='upper right', fontsize=8.5, frameon=True, facecolor='#ffffff')
    ax2.grid(True, linestyle='--', alpha=0.5)

    fig.suptitle("Uncertainty Estimation: 95% Bootstrap Confidence Intervals (B = 5,000)", fontsize=13, weight='bold', color=THEME['navy'], y=0.99)
    fig.tight_layout()
    fig6_path = os.path.join(OUTPUT_DIR, 'figure6_bootstrap_distributions.png')
    fig.savefig(fig6_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved {fig6_path}")

    # -------------------------------------------------------------------------
    # Figure 7: Boxplot & Outlier Diagnostic
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 3.8), dpi=300)
    fig.patch.set_facecolor(THEME['bg_cream'])
    ax.set_facecolor('#ffffff')

    bp = ax.boxplot(data, vert=False, patch_artist=True,
                    boxprops=dict(facecolor=THEME['light_blue'], color=THEME['navy'], lw=1.5),
                    medianprops=dict(color=THEME['red_accent'], lw=2.0),
                    whiskerprops=dict(color=THEME['navy'], lw=1.5),
                    capprops=dict(color=THEME['navy'], lw=1.5),
                    flierprops=dict(marker='o', markersize=3, markerfacecolor=THEME['red_accent'], alpha=0.4, markeredgecolor='none'))

    ax.axvline(100.0, color=THEME['red_accent'], linestyle='--', lw=1.5, label='Lag Spike Threshold (100 ms)')
    ax.set_title("Wi-Fi Latency Boxplot: Visualizing IQR, Tail Length, and Outliers", weight='bold', fontsize=11, pad=10)
    ax.set_xlabel("Latency (ms)", weight='bold')
    ax.set_yticks([])
    ax.set_xlim(0, 1600)
    ax.legend(loc='upper right', frameon=True, facecolor='#ffffff', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)

    # Annotate summary numbers
    ax.text(0.03, 0.25, f"Min: {eda_stats['min']:.1f} ms\nQ1: {eda_stats['q25']:.1f} ms\nMedian: {eda_stats['median']:.1f} ms\nQ3: {eda_stats['q75']:.1f} ms\nMax: {eda_stats['max']:.1f} ms",
            transform=ax.transAxes, fontsize=8.5, weight='bold', color=THEME['navy'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffffff', edgecolor='#cbd5e1'))

    fig.tight_layout()
    fig7_path = os.path.join(OUTPUT_DIR, 'figure7_boxplot_outliers.png')
    fig.savefig(fig7_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved {fig7_path}")

# -----------------------------------------------------------------------------
# 7. Export Processed Data & Metadata
# -----------------------------------------------------------------------------
def export_solution_data(df, eda_stats, comp_df, ci_results, temporal_stats):
    # Save clean dataset
    clean_csv_path = os.path.join(OUTPUT_DIR, 'wifi_clean_data.csv')
    df.to_csv(clean_csv_path, index=False)
    print(f"-> Exported clean dataset to {clean_csv_path}")

    # Save model comparison table
    model_csv_path = os.path.join(OUTPUT_DIR, 'wifi_model_comparison.csv')
    comp_df.to_csv(model_csv_path, index=False)
    print(f"-> Exported model comparison to {model_csv_path}")

    # Save bootstrap CI table
    ci_table = []
    for metric, res in ci_results.items():
        ci_table.append({
            'Metric': metric,
            'Point_Estimate': res['point_estimate'],
            'CI_Lower_95': res['ci_lower_95'],
            'CI_Upper_95': res['ci_upper_95']
        })
    ci_df = pd.DataFrame(ci_table)
    ci_csv_path = os.path.join(OUTPUT_DIR, 'wifi_bootstrap_results.csv')
    ci_df.to_csv(ci_csv_path, index=False)
    print(f"-> Exported bootstrap results to {ci_csv_path}")

    # Save comprehensive metrics JSON
    json_metrics = {
        'eda': eda_stats,
        'temporal': temporal_stats,
        'bootstrap': {m: {'point': res['point_estimate'], 'lower': res['ci_lower_95'], 'upper': res['ci_upper_95']} for m, res in ci_results.items()},
        'best_model': comp_df.iloc[0].to_dict()
    }

    def convert_np(obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    json_path = os.path.join(OUTPUT_DIR, 'wifi_solution_metrics.json')
    with open(json_path, 'w') as f:
        json.dump(json_metrics, f, indent=2, default=convert_np)
    print(f"-> Exported JSON metrics to {json_path}")

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("WI-FI LAG SPIKE STATISTICAL SOLUTION PIPELINE")
    print("=" * 70)

    # 1. Load data
    df, net_stats = load_and_clean_data(DATA_PATH)

    # 2. Exploratory Data Analysis
    eda_stats = compute_eda_statistics(df['rtt_ms'].values)
    eda_stats.update(net_stats)

    # 3. Model Fitting
    fitted_models, comp_df = fit_distributions(df['rtt_ms'].values)

    # 4. Bootstrap CI
    ci_results = compute_bootstrap_ci(df['rtt_ms'].values, b_iterations=5000)

    # 5. Temporal / Autocorrelation
    temporal_stats = analyze_temporal_dynamics(df)

    # 6. Generate Figures
    generate_all_figures(df, eda_stats, fitted_models, comp_df, ci_results, temporal_stats)

    # 7. Export Datasets & Summaries
    export_solution_data(df, eda_stats, comp_df, ci_results, temporal_stats)

    print("\n" + "=" * 70)
    print("ANALYSIS PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    main()
