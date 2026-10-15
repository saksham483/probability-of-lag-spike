# The Probability of a Lag Spike: Statistical Modeling & Solution for Wi-Fi Latency

**Course:** Applied Probability & Statistical Inference  
**Presenter / Author:** Saksham [Applied Probability & Statistical Inference Group]  
**Dataset:** Empirical Live Wi-Fi Ping Capture (`wifi_data.txt`, Target: `8.8.8.8`)  
**Deliverables:**
- Analysis Engine: [`wifi_lag_spike_solution.py`](file:///home/saksham/probability%20proj/wifi_lag_spike_solution.py)
- Presentation Slides (PowerPoint): [`wifi_lag_spike_solution.pptx`](file:///home/saksham/probability%20proj/wifi_lag_spike_solution.pptx)
- Presentation Slides (PDF): [`wifi_lag_spike_solution.pdf`](file:///home/saksham/probability%20proj/wifi_lag_spike_solution.pdf)
- Cleaned Dataset: [`solution_outputs/wifi_clean_data.csv`](file:///home/saksham/probability%20proj/solution_outputs/wifi_clean_data.csv)
- Model Comparison Table: [`solution_outputs/wifi_model_comparison.csv`](file:///home/saksham/probability%20proj/solution_outputs/wifi_model_comparison.csv)
- Bootstrap Uncertainty Table: [`solution_outputs/wifi_bootstrap_results.csv`](file:///home/saksham/probability%20proj/solution_outputs/wifi_bootstrap_results.csv)

---

## Executive Summary

Standard network diagnostics rely almost universally on "average ping" (mean round-trip time). However, in real-time digital communications—such as video conferencing, esports gaming, and financial execution—mean latency is a deceptive metric. In practice, network latency distributions are bounded on the left by physical propagation hardware limits and exhibit long, volatile right tails. 

This project executes the full 4-step statistical inference workflow proposed in the course syllabus on live Wi-Fi latency measurements ($N = 3,685$ successful probe replies):

1. **Exploratory Data Analysis (EDA):** Demonstrates that the mean latency ($176.81\text{ ms}$) is heavily skewed by extreme outliers, standing $34.8\text{ ms}$ above the median ($142.00\text{ ms}$). The dataset displays severe positive skewness ($\gamma_1 = +3.560$) and extreme excess kurtosis ($\kappa = +25.996$), with maximum spikes reaching $2,479.0\text{ ms}$ alongside a $17.08\%$ packet loss rate.
2. **Parametric Distribution Fitting via MLE:** Implements Maximum Likelihood Estimation across candidate families (Shifted Gamma, Shifted Weibull, Shifted Log-Normal, Standard Log-Normal, Shifted Exponential, and Gaussian Normal).
3. **Goodness-of-Fit Testing & Model Selection:** Formally rejects the Gaussian assumption ($D = 0.1603, p = 3.53 \times 10^{-83}$). Identifies the **3-Parameter Shifted Gamma Distribution** as the superior model ($\text{AIC} = 44,590.9, \text{BIC} = 44,609.5, D_{\text{KS}} = 0.0404$), closely followed by Shifted Weibull and Shifted Log-Normal.
4. **Disruption Risk Estimation ($P(X > 100\text{ ms})$):** Replaces the project proposal's initial illustrative Wi-Fi placeholder ($4.5\%$) with the real empirical finding: **$64.04\%$ of packets experience disruption**. The fitted Shifted Gamma model predicts **$64.34\%$** (relative error $< 0.5\%$), confirming high predictive accuracy.
5. **Uncertainty Quantification:** Generates $95\%$ non-parametric bootstrap confidence intervals ($B = 5,000$ iterations), proving that while the median is tightly bounded ($\pm 4\text{ ms}$), the 99th percentile spans a volatile range of $[680.0\text{ ms}, 928.0\text{ ms}]$.
6. **Temporal Clustering:** Identifies significant lag-1 autocorrelation ($\rho_1 = +0.270, p < 10^{-15}$), showing that Wi-Fi lag spikes cluster into persistent multi-second bursts (maximum continuous disruption duration $= 21$ consecutive packets).

---

## 1. Data Ingestion & Preprocessing Architecture

The raw network trace [`wifi_data.txt`](file:///home/saksham/probability%20proj/wifi_data.txt) was captured via continuous ICMP echo probes (`ping 8.8.8.8`). Each entry records ICMP sequence numbers, time-to-live (`ttl`), and round-trip time (`rtt_ms`).

```
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=113 time=44.4 ms
...
--- 8.8.8.8 ping statistics ---
4444 packets transmitted, 3685 received, +160 errors, 17.0792% packet loss, time 4467746ms
rtt min/avg/max/mdev = 17.893/176.822/2479.149/157.980 ms
```

### Ingestion Summary:
- **Total Probes Transmitted:** $4,444$
- **Total Probes Received ($N$):** $3,685$
- **Packets Dropped:** $759$ ($17.08\%$ packet loss)
- **Sequence Index Span:** $1$ to $4,110$
- **Measurement Time Horizon:** $\approx 4,468\text{ seconds}$ ($\approx 1.24\text{ hours}$ at $1\text{ probe/sec}$)

---

## 2. Exploratory Data Analysis (EDA)

### Summary Statistics Table

| Metric | Empirical Value | Statistical Interpretation |
| :--- | :--- | :--- |
| **Sample Size ($N$)** | $3,685$ | High statistical power for MLE and bootstrap inference |
| **Mean ($\mu$)** | $176.81\text{ ms}$ | Standard metric reported by ISPs; inflated by right-tail spikes |
| **Standard Deviation ($\sigma$)** | $157.99\text{ ms}$ | High dispersion; coefficient of variation $CV = 0.894$ |
| **Variance ($\sigma^2$)** | $24,960.5\text{ ms}^2$ | Extreme latency instability |
| **Median ($P_{50}$)** | $142.00\text{ ms}$ | True central tendency; $34.81\text{ ms}$ below the mean |
| **Interquartile Range (IQR)** | $159.10\text{ ms}$ | $Q_1 = 70.90\text{ ms}, Q_3 = 230.00\text{ ms}$ |
| **Minimum ($X_{\min}$)** | $17.89\text{ ms}$ | Hardware/propagation delay floor; strict lower bound |
| **Maximum ($X_{\max}$)** | $2,479.00\text{ ms}$ | Catastrophic outlier; $14.0\times$ higher than the mean |
| **90th Percentile ($P_{90}$)** | $340.00\text{ ms}$ | $10\%$ of all packets experience severe gaming/audio lag |
| **95th Percentile ($P_{95}$)** | $444.60\text{ ms}$ | Near half-second delay; causes dropped frames in video calls |
| **99th Percentile ($P_{99}$)** | $826.76\text{ ms}$ | Extreme lag spike; causes connection timeouts |
| **Sample Skewness ($\gamma_1$)** | $+3.560$ | Highly positive; asymmetric right-skewed tail |
| **Excess Kurtosis ($\kappa$)** | $+25.996$ | Leptokurtic; extreme probability mass concentrated in the tail |

### Key EDA Takeaway
A standard bell curve assumption implies that $68\%$ of data falls within $\mu \pm 1\sigma$ ($[18.82\text{ ms}, 334.80\text{ ms}]$) symmetrically. In reality, the physical floor stops at $17.89\text{ ms}$, while the right tail extends to $2,479.00\text{ ms}$. The discrepancy between median ($142\text{ ms}$) and mean ($177\text{ ms}$) is a direct signature of heavy-tailed skewness.

---

## 3. Parametric Distribution Modeling via MLE

Because network latency cannot be negative and contains a physical hardware propagation delay floor $\gamma \approx 17.89\text{ ms}$, we fit both unshifted and 3-parameter shifted distributions:

$$X = \gamma + Y, \quad Y \ge 0$$

### Mathematical Formulations of Candidate Families

1. **Shifted Gamma Distribution:**
   $$f(x; \alpha, \beta, \gamma) = \frac{(x - \gamma)^{\alpha - 1} e^{-(x - \gamma)/\beta}}{\beta^\alpha \Gamma(\alpha)}, \quad x > \gamma$$
2. **Shifted Weibull Distribution:**
   $$f(x; c, \lambda, \gamma) = \frac{c}{\lambda} \left(\frac{x - \gamma}{\lambda}\right)^{c - 1} \exp\left(-\left(\frac{x - \gamma}{\lambda}\right)^c\right), \quad x > \gamma$$
3. **Shifted Log-Normal Distribution:**
   $$f(x; \sigma, \mu, \gamma) = \frac{1}{(x - \gamma)\sigma\sqrt{2\pi}} \exp\left(-\frac{(\ln(x - \gamma) - \mu)^2}{2\sigma^2}\right), \quad x > \gamma$$
4. **Gaussian Normal Distribution (Baseline):**
   $$f(x; \mu, \sigma) = \frac{1}{\sigma\sqrt{2\pi}} \exp\left(-\frac{(x - \mu)^2}{2\sigma^2}\right), \quad x \in \mathbb{R}$$

### Fitted Parameter Estimates

| Model | Parameters (MLE) | Log-Likelihood | Number of Parameters ($k$) |
| :--- | :--- | :--- | :--- |
| **Shifted Gamma** | $\alpha = 1.2927, \gamma = 17.87\text{ ms}, \beta = 122.95\text{ ms}$ | **-22,292.4** | $3$ |
| **Shifted Weibull** | $c = 1.1275, \gamma = 17.89\text{ ms}, \lambda = 166.48\text{ ms}$ | -22,317.1 | $3$ |
| **Shifted Log-Normal**| $\sigma = 0.8508, \gamma = 6.33\text{ ms}, \text{scale} = 121.37\text{ ms}$ | -22,317.2 | $3$ |
| **Log-Normal ($loc=0$)**| $\sigma = 0.7939, \gamma = 0.00, \text{scale} = 130.24\text{ ms}$ | -22,322.1 | $2$ |
| **Shifted Exponential**| $\gamma = 17.89\text{ ms}, \beta = 158.93\text{ ms}$ | -22,361.8 | $2$ |
| **Normal (Gaussian)** | $\mu = 176.81\text{ ms}, \sigma = 157.99\text{ ms}$ | -23,883.7 | $2$ |

---

## 4. Goodness-of-Fit & Model Selection

Model selection was conducted using the **Akaike Information Criterion (AIC)**, **Bayesian Information Criterion (BIC)**, and the **Kolmogorov-Smirnov (K-S) distance statistic**:

$$\text{AIC} = 2k - 2\ln(\hat{L}), \quad \text{BIC} = k\ln(N) - 2\ln(\hat{L}), \quad D_{\text{KS}} = \sup_{x} |F_n(x) - F_0(x)|$$

### Comparative Evaluation Table

| Rank | Candidate Model | Log-Likelihood | AIC | BIC | K-S Stat ($D$) | K-S $p$-value | $P(X > 100\text{ ms})$ |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **Shifted Gamma (Best)** | **-22,292.4** | **44,590.9** | **44,609.5** | **0.0404** | $1.19 \times 10^{-5}$ | **64.34%** |
| 2 | Shifted Weibull | -22,317.1 | 44,640.3 | 44,658.9 | 0.0463 | $2.72 \times 10^{-7}$ | 63.72% |
| 3 | Shifted Log-Normal | -22,317.2 | 44,640.3 | 44,659.0 | 0.0597 | $7.62 \times 10^{-12}$ | 61.96% |
| 4 | Log-Normal ($loc=0$) | -22,322.1 | 44,648.2 | 44,660.6 | 0.0500 | $1.87 \times 10^{-8}$ | 63.04% |
| 5 | Shifted Exponential | -22,361.8 | 44,727.5 | 44,739.9 | 0.0588 | $1.56 \times 10^{-11}$ | 59.65% |
| 6 | Normal (Gaussian) | -23,883.7 | 47,771.4 | 47,783.8 | 0.1603 | $3.53 \times 10^{-83}$ | 68.66% |
| — | **Empirical Ground Truth** | — | — | — | — | — | **64.04%** |

### Statistical Tests of Normality
- **D'Agostino-Pearson Omnibus Normality Test:** $K^2 = 2,967.5, \quad p = 0.000$ (Decisive rejection).
- **Kolmogorov-Smirnov Test vs Normal:** $D = 0.1603, \quad p = 3.53 \times 10^{-83}$ (Decisive rejection).
- **Why Normal Fails:** 
  1. Predicts $P(X < 0) = \Phi\left(\frac{0 - 176.81}{157.99}\right) = \Phi(-1.119) = 13.16\%$ (physical impossibility).
  2. Severely under-predicts catastrophic tail spikes: $P_{\text{Normal}}(X > 800\text{ ms}) \approx 0.003\%$, whereas empirical $P(X > 800\text{ ms}) = 1.00\%$ ($330\times$ underestimation).

---

## 5. Beyond the Mean: Probability of Disruption ($P(X > T)$)

Slide 6 of the course proposal defined a lag spike at $T = 100\text{ ms}$ and stated:
$$\text{Evaluate } P(X > 100) = 1 - F_X(100)$$
The proposal provided an illustrative placeholder of **$\approx 4.5\%$** for Wi-Fi.

### Empirical Replacement Results

| Threshold ($T$) | Severity Level | Proposal Placeholder | Empirical Wi-Fi | Shifted Gamma Model | Shifted Weibull | Shifted Log-Normal |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **$T = 100\text{ ms}$** | **Standard Lag Spike** | **4.5%** | **64.04%** | **64.34%** | 63.72% | 61.96% |
| **$T = 150\text{ ms}$** | **Jitter Disruption** | — | **46.89%** | **46.15%** | 46.28% | 42.14% |
| **$T = 200\text{ ms}$** | **Severe Degradation**| — | **32.59%** | **32.57%** | 33.07% | 29.14% |
| **$T = 300\text{ ms}$** | **Connection Hang** | — | **13.08%** | **15.69%** | 16.33% | 15.11% |
| **$T = 500\text{ ms}$** | **Critical Timeout** | — | **3.01%** | **3.06%** | 3.59% | 4.88% |

### Core Finding
The actual empirical disruption probability on this Wi-Fi network is **$64.04\%$**, which is **$14.2\times$ higher** than the proposal's initial illustrative placeholder ($4.5\%$). The Shifted Gamma model predicts **$64.34\%$**, exhibiting an absolute modeling error of only **$0.30\%$**!

---

## 6. Uncertainty Quantification: Non-Parametric Bootstrapping

To avoid relying on parametric asymptotic normality assumptions for confidence intervals, we executed $B = 5,000$ non-parametric bootstrap resamples on the $3,685$ observations.

### 95% Bootstrap Confidence Intervals ($B = 5,000$)

| Metric | Point Estimate | 95% Bootstrap CI Lower | 95% Bootstrap CI Upper | Margin of Error |
| :--- | :---: | :---: | :---: | :---: |
| **Median Latency ($P_{50}$)** | **$142.00\text{ ms}$** | **$138.00\text{ ms}$** | **$146.00\text{ ms}$** | $\pm 4.00\text{ ms}$ ($\pm 2.8\%$) |
| **Mean Latency ($\mu$)** | **$176.81\text{ ms}$** | **$171.87\text{ ms}$** | **$182.00\text{ ms}$** | $\pm 5.07\text{ ms}$ ($\pm 2.9\%$) |
| **90th Percentile ($P_{90}$)** | **$340.00\text{ ms}$** | **$325.00\text{ ms}$** | **$357.00\text{ ms}$** | $\pm 16.00\text{ ms}$ ($\pm 4.7\%$) |
| **99th Percentile ($P_{99}$)** | **$826.76\text{ ms}$** | **$680.00\text{ ms}$** | **$928.00\text{ ms}$** | $\pm 124.0\text{ ms}$ ($\pm 15.0\%$) |
| **Disruption Risk $P(X > 100\text{ ms})$** | **$64.04\%$** | **$62.58\%$** | **$65.59\%$** | $\pm 1.51\%$ ($\pm 2.4\%$) |

### Interpretation
- **Median Robustness:** The median latency exhibits tight stability ($[138\text{ ms}, 146\text{ ms}]$).
- **Extreme Tail Volatility:** The 99th percentile spans a wide uncertainty window of nearly $250\text{ ms}$ ($[680\text{ ms}, 928\text{ ms}]$). This highlights why network SLAs based purely on point estimates fail to guarantee user experience under load.

---

## 7. Temporal Dynamics, Autocorrelation & Burstiness

Network packets do not arrive as independent identically distributed (i.i.d.) random variables; physical Wi-Fi channels suffer from medium contention, channel fading, and bufferbloat.

### Empirical Temporal Findings
1. **Lag-1 Autocorrelation:**
   $$\rho_1 = \text{Corr}(X_t, X_{t+1}) = \mathbf{+0.270} \quad (p < 10^{-15})$$
   A packet experiencing high latency significantly increases the probability that the immediate subsequent packet will also experience high latency.
2. **Disruption Run-Length Analysis ($X_t > 100\text{ ms}$):**
   - **Total Distinct Spikes / Bursts:** $642$
   - **Mean Burst Duration:** $3.7$ consecutive packets ($\approx 3.7\text{ seconds}$)
   - **Maximum Burst Duration:** **$21$ consecutive packets** ($> 21\text{ seconds}$ of sustained degradation)
3. **Composite Network Health:**
   - Packet Loss: $17.08\%$
   - Latency Disruption ($>100\text{ ms}$): $64.04\%$ of received packets ($53.10\%$ of all transmitted probes)
   - **Healthy On-Time Packets:** Only **$29.82\%$** of transmitted probes were received under $100\text{ ms}$!

---

## 8. Network Engineering Implications & SLA Reforms

1. **Retire Mean Ping from Service Level Agreements (SLAs):**
   ISPs commonly advertise average ping times. However, an ISP can report an average latency of $177\text{ ms}$ while $64\%$ of packets exceed $100\text{ ms}$ and $1\%$ exceed $827\text{ ms}$. Regulators and enterprise audits must mandate **P95, P99, and Tail Exceedance Probabilities ($P(X > 100\text{ ms})$)**.
2. **Deploy Active Queue Management (AQM):**
   The long right-tail spikes ($>1,000\text{ ms}$) observed in this trace are classic symptoms of **bufferbloat**—excessive buffering within Wi-Fi router queues. Enabling modern AQM algorithms (such as **FQ-CoDel** or **Cake**) automatically prioritizes interactive ICMP/VoIP traffic and caps queue delays.
3. **Adaptive Playout Buffering for Real-Time Applications:**
   VoIP/video applications (Zoom, Microsoft Teams, WebRTC) configure dynamic jitter buffers. The bootstrap confidence bounds ($P_{99} \in [680\text{ ms}, 928\text{ ms}]$) provide a rigorous mathematical basis for sizing de-jitter buffers during Wi-Fi transmission.

---

## 9. Deliverables Inventory

| File | Type | Description |
| :--- | :--- | :--- |
| [`wifi_lag_spike_solution.py`](file:///home/saksham/probability%20proj/wifi_lag_spike_solution.py) | Python Script | Complete end-to-end analytical pipeline (EDA, MLE, tests, plots, exports) |
| [`build_presentation.py`](file:///home/saksham/probability%20proj/build_presentation.py) | Python Script | Programmatic builder for the 8-slide PowerPoint presentation |
| [`wifi_lag_spike_solution.pptx`](file:///home/saksham/probability%20proj/wifi_lag_spike_solution.pptx) | PPTX | Native editable PowerPoint presentation matching the proposal theme |
| [`wifi_lag_spike_solution.pdf`](file:///home/saksham/probability%20proj/wifi_lag_spike_solution.pdf) | PDF | Compiled presentation slides ready for display |
| [`solution_outputs/figure1_time_series_lag_spikes.png`](file:///home/saksham/probability%20proj/solution_outputs/figure1_time_series_lag_spikes.png) | PNG | Time series run chart with 100 ms threshold and burst callout |
| [`solution_outputs/figure2_distribution_fits_kde.png`](file:///home/saksham/probability%20proj/solution_outputs/figure2_distribution_fits_kde.png) | PNG | Histogram + KDE with fitted Shifted Gamma, Weibull, Log-Normal, and Normal |
| [`solution_outputs/figure3_ecdf_vs_models.png`](file:///home/saksham/probability%20proj/solution_outputs/figure3_ecdf_vs_models.png) | PNG | Empirical CDF vs theoretical CDFs with disruption threshold marker |
| [`solution_outputs/figure4_qq_plots.png`](file:///home/saksham/probability%20proj/solution_outputs/figure4_qq_plots.png) | PNG | 4-panel Q-Q diagnostic plot comparing Normal, Gamma, Weibull, and Log-Normal |
| [`solution_outputs/figure5_disruption_risk_curve.png`](file:///home/saksham/probability%20proj/solution_outputs/figure5_disruption_risk_curve.png) | PNG | Disruption probability curve $P(X > T)$ for $T \in [20, 600]\text{ ms}$ |
| [`solution_outputs/figure6_bootstrap_distributions.png`](file:///home/saksham/probability%20proj/solution_outputs/figure6_bootstrap_distributions.png) | PNG | Bootstrap sampling histograms for Median and P99 with 95% CIs |
| [`solution_outputs/figure7_boxplot_outliers.png`](file:///home/saksham/probability%20proj/solution_outputs/figure7_boxplot_outliers.png) | PNG | Horizontal boxplot illustrating IQR and extreme tail outliers |
| [`solution_outputs/wifi_clean_data.csv`](file:///home/saksham/probability%20proj/solution_outputs/wifi_clean_data.csv) | CSV | Cleaned sequence numbers, TTL, and latency readings |
| [`solution_outputs/wifi_model_comparison.csv`](file:///home/saksham/probability%20proj/solution_outputs/wifi_model_comparison.csv) | CSV | Comparative table of Log-Likelihood, AIC, BIC, KS-Stat, and $P(X > 100)$ |
| [`solution_outputs/wifi_bootstrap_results.csv`](file:///home/saksham/probability%20proj/solution_outputs/wifi_bootstrap_results.csv) | CSV | Point estimates and 95% bootstrap confidence bounds |
| [`solution_outputs/wifi_solution_metrics.json`](file:///home/saksham/probability%20proj/solution_outputs/wifi_solution_metrics.json) | JSON | Machine-readable comprehensive metrics export |
