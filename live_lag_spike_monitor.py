#!/usr/bin/env python3
"""
Live Wi-Fi Lag Spike Monitor & Real-Time Statistical Inference Dashboard
========================================================================
Course: Applied Probability & Statistical Inference
Project: The Probability of a Lag Spike: Statistical Modeling of Network Latency

This script demonstrates the solution working LIVE:
1. Streams packet latency observations either:
   - REPLAY MODE (default): Replays the 3,685 packets from wifi_data.txt
   - LIVE MODE (--live): Runs actual live ICMP ping to 8.8.8.8 or custom host
2. Dynamically updates statistical metrics in real-time:
   - Sample Size N, Min, Median, Mean, Max, P90, P99
   - Skewness and Excess Kurtosis (showing the emergence of right-skewness)
   - Real-time MLE fitting of 3-Parameter Shifted Gamma distribution
   - Real-time Disruption Probability P(X > 100 ms): Empirical vs Gamma vs Normal
   - Burst detection and temporal clustering tracking
3. Provides:
   - Interactive Terminal UI (ANSI truecolor, sparkline, live histogram, gauges)
   - Optional Live Web Dashboard (--web) on http://localhost:8050
"""

import os
import sys
import time
import math
import select
import termios
import tty
import json
import argparse
import threading
import subprocess
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import numpy as np
import scipy.stats as stats

# -----------------------------------------------------------------------------
# Color Codes & Theme (Matching PPT Theme: Navy #12355b, Royal #1e3989)
# -----------------------------------------------------------------------------
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"

# Truecolor ANSI helpers
def rgb_fg(r, g, b): return f"\033[38;2;{r};{g};{b}m"
def rgb_bg(r, g, b): return f"\033[48;2;{r};{g};{b}m"

CLR_NAVY = rgb_fg(18, 53, 91)
CLR_ROYAL = rgb_fg(30, 57, 137)
CLR_BG_NAVY = rgb_bg(18, 53, 91)
CLR_BG_ROYAL = rgb_bg(30, 57, 137)
CLR_CREAM = rgb_fg(247, 243, 235)
CLR_WHITE = rgb_fg(255, 255, 255)
CLR_MUTED = rgb_fg(148, 163, 184)
CLR_GREEN = rgb_fg(34, 197, 94)
CLR_AMBER = rgb_fg(245, 158, 11)
CLR_RED = rgb_fg(239, 68, 68)
CLR_CRITICAL = rgb_fg(244, 63, 94)
CLR_CYAN = rgb_fg(6, 182, 212)
CLR_PURPLE = rgb_fg(168, 85, 247)

SPARK_CHARS = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

# -----------------------------------------------------------------------------
# Global Shared State
# -----------------------------------------------------------------------------
class MonitorState:
    def __init__(self):
        self.lock = threading.Lock()
        self.latencies = []
        self.seqs = []
        self.packet_loss_count = 0
        self.total_transmitted = 0
        self.current_rtt = 0.0
        self.current_seq = 0
        self.is_paused = False
        self.speed_multiplier = 5.0  # default 5x replay speed
        self.mode = "replay"
        self.target_host = "8.8.8.8"
        self.done = False

        # Live Stats
        self.n = 0
        self.mean = 0.0
        self.std = 0.0
        self.median = 0.0
        self.min_val = 0.0
        self.max_val = 0.0
        self.p90 = 0.0
        self.p99 = 0.0
        self.skewness = 0.0
        self.kurtosis = 0.0

        # Disruption & Fit
        self.p_lag_100_emp = 0.0
        self.p_lag_150_emp = 0.0
        self.p_lag_200_emp = 0.0
        self.gamma_params = (1.29, 17.87, 122.95)
        self.p_lag_100_gamma = 0.0
        self.p_lag_100_norm = 0.0

        # Bursts
        self.active_burst = 0
        self.max_burst = 0
        self.total_bursts = 0

    def update_metrics(self):
        with self.lock:
            n = len(self.latencies)
            if n == 0:
                return
            self.n = n
            arr = np.array(self.latencies)
            self.min_val = float(np.min(arr))
            self.max_val = float(np.max(arr))
            self.mean = float(np.mean(arr))
            self.std = float(np.std(arr, ddof=1)) if n > 1 else 0.0
            self.median = float(np.median(arr))
            self.p90 = float(np.percentile(arr, 90.0))
            self.p99 = float(np.percentile(arr, 99.0))
            self.p_lag_100_emp = float(np.mean(arr > 100.0) * 100.0)
            self.p_lag_150_emp = float(np.mean(arr > 150.0) * 100.0)
            self.p_lag_200_emp = float(np.mean(arr > 200.0) * 100.0)

            if n > 8:
                self.skewness = float(stats.skew(arr))
                self.kurtosis = float(stats.kurtosis(arr))
            else:
                self.skewness = 0.0
                self.kurtosis = 0.0

            # Estimate MLE parameters periodically
            if n >= 20:
                try:
                    g_params = stats.gamma.fit(arr, loc=self.min_val - 0.01)
                    self.gamma_params = g_params
                    self.p_lag_100_gamma = float((1.0 - stats.gamma.cdf(100.0, *g_params)) * 100.0)
                except Exception:
                    pass

                # Normal fit comparison
                if self.std > 0:
                    self.p_lag_100_norm = float((1.0 - stats.norm.cdf(100.0, loc=self.mean, scale=self.std)) * 100.0)

STATE = MonitorState()

# -----------------------------------------------------------------------------
# Data Ingestion Providers
# -----------------------------------------------------------------------------
def replay_file_worker(filepath, state):
    print(f"Reading dataset {filepath} for replay...")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        state.done = True
        return

    records = []
    with open(filepath, 'r') as f:
        for line in f:
            m = re.search(r'icmp_seq=(\d+)\s+.*time=([\d\.]+)\s*ms', line)
            if m:
                records.append((int(m.group(1)), float(m.group(2))))

    if not records:
        print("No valid ping lines found in dataset.")
        state.done = True
        return

    expected_seq = records[0][0]

    for seq, rtt in records:
        if state.done:
            break

        # Check for packet loss in sequence
        if seq > expected_seq:
            lost = seq - expected_seq
            with state.lock:
                state.packet_loss_count += lost
                state.total_transmitted += lost
        expected_seq = seq + 1

        while state.is_paused and not state.done:
            time.sleep(0.1)

        # Update State
        with state.lock:
            state.total_transmitted += 1
            state.latencies.append(rtt)
            state.seqs.append(seq)
            state.current_rtt = rtt
            state.current_seq = seq

            # Burst tracking
            if rtt > 100.0:
                state.active_burst += 1
                if state.active_burst > state.max_burst:
                    state.max_burst = state.active_burst
            else:
                if state.active_burst > 0:
                    state.total_bursts += 1
                    state.active_burst = 0

        # Sleep according to speed multiplier
        sleep_time = max(0.005, 1.0 / max(0.1, state.speed_multiplier))
        time.sleep(sleep_time)

    with state.lock:
        if state.active_burst > 0:
            state.total_bursts += 1
            state.active_burst = 0
    state.done = True

def live_ping_worker(target, state):
    print(f"Starting live ping subprocess to {target}...")
    cmd = ["ping", "-i", "0.5", target]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    except Exception as e:
        print(f"Error launching ping: {e}")
        state.done = True
        return

    expected_seq = None
    for line in iter(proc.stdout.readline, ''):
        if state.done:
            break
        m = re.search(r'icmp_seq=(\d+)\s+.*time=([\d\.]+)\s*ms', line)
        if m:
            seq = int(m.group(1))
            rtt = float(m.group(2))

            if expected_seq is not None and seq > expected_seq:
                lost = seq - expected_seq
                with state.lock:
                    state.packet_loss_count += lost
                    state.total_transmitted += lost
            expected_seq = seq + 1

            with state.lock:
                state.total_transmitted += 1
                state.latencies.append(rtt)
                state.seqs.append(seq)
                state.current_rtt = rtt
                state.current_seq = seq

                if rtt > 100.0:
                    state.active_burst += 1
                    if state.active_burst > state.max_burst:
                        state.max_burst = state.active_burst
                else:
                    if state.active_burst > 0:
                        state.total_bursts += 1
                        state.active_burst = 0
        elif "Destination Host Unreachable" in line or "Request timeout" in line:
            with state.lock:
                state.total_transmitted += 1
                state.packet_loss_count += 1

    proc.terminate()
    state.done = True

# -----------------------------------------------------------------------------
# Terminal UI Dashboard Renderer
# -----------------------------------------------------------------------------
def render_terminal_ui(state):
    state.update_metrics()

    w = 78  # Standard terminal width
    out = []

    # Helper: Center Text
    def c_txt(txt, width=w):
        clean = re.sub(r'\033\[[0-9;]*m', '', txt)
        pad = max(0, width - len(clean))
        lpad = pad // 2
        rpad = pad - lpad
        return " " * lpad + txt + " " * rpad

    # Top Header Banner
    out.append(f"{CLR_BG_NAVY}{CLR_WHITE}{ANSI_BOLD}{'━' * w}{ANSI_RESET}")
    title = f"WI-FI LAG SPIKE STATISTICAL MONITOR  |  APPLIED PROBABILITY INFERENCE"
    out.append(f"{CLR_BG_NAVY}{CLR_WHITE}{ANSI_BOLD}{c_txt(title)}{ANSI_RESET}")
    mode_str = f"MODE: {state.mode.upper()} ({state.target_host}) | SPEED: {state.speed_multiplier:.1f}x | STATUS: {'PAUSED' if state.is_paused else 'STREAMING'}"
    out.append(f"{CLR_BG_NAVY}{CLR_CYAN}{c_txt(mode_str)}{ANSI_RESET}")
    out.append(f"{CLR_BG_NAVY}{CLR_WHITE}{ANSI_BOLD}{'━' * w}{ANSI_RESET}")

    # Section 1: Live Probe Readout & Key Metrics
    rtt = state.current_rtt
    if rtt < 50.0:
        rtt_clr = CLR_GREEN
        tag = "  [OPTIMAL <50ms]  "
    elif rtt <= 100.0:
        rtt_clr = CLR_AMBER
        tag = "  [ACCEPTABLE]     "
    elif rtt <= 300.0:
        rtt_clr = CLR_RED
        tag = "  ⚡ LAG SPIKE! >100ms"
    else:
        rtt_clr = CLR_CRITICAL
        tag = "  💥 SEVERE SPIKE! >300ms"

    loss_pct = (state.packet_loss_count / max(1, state.total_transmitted)) * 100.0

    out.append(f"\n{ANSI_BOLD}1. REAL-TIME PROBE OBSERVATION & DISPERSION{ANSI_RESET}")
    out.append(f"┌{'─' * 42}┬{'─' * 33}┐")
    out.append(f"│ Current Ping: {rtt_clr}{ANSI_BOLD}{rtt:6.1f} ms{ANSI_RESET} {tag} │ Packets Sampled: {CLR_CYAN}{state.n:6,d}{ANSI_RESET}   │")
    out.append(f"│ Sequence:     {state.current_seq:<8d} {'':18} │ Packet Loss:     {CLR_AMBER if loss_pct>5 else CLR_GREEN}{loss_pct:5.1f}%{ANSI_RESET} ({state.packet_loss_count} lost)│")
    out.append(f"├{'─' * 42}┼{'─' * 33}┤")
    out.append(f"│ Median (P50): {CLR_CYAN}{state.median:6.1f} ms{ANSI_RESET}  IQR: {state.p90-state.min_val:6.1f} ms │ Floor (Min):     {CLR_GREEN}{state.min_val:6.1f} ms{ANSI_RESET}   │")
    out.append(f"│ Mean (μ):     {CLR_AMBER}{state.mean:6.1f} ms{ANSI_RESET}  Std: {state.std:6.1f} ms │ Peak Spike (Max):{CLR_RED}{state.max_val:6.1f} ms{ANSI_RESET}   │")
    out.append(f"│ Tail P90:     {CLR_AMBER}{state.p90:6.1f} ms{ANSI_RESET}  P99: {CLR_RED}{state.p99:6.1f} ms{ANSI_RESET} │ Skewness (γ1):   {CLR_PURPLE}{state.skewness:+6.2f}{ANSI_RESET}   │")
    out.append(f"└{'─' * 42}┴{'─' * 33}┘")

    # Section 2: Disruption Probability & Theoretical Fitting
    out.append(f"\n{ANSI_BOLD}2. LAG SPIKE DISRUPTION PROBABILITY: P(X > 100 ms){ANSI_RESET}")
    out.append(f"┌{'─' * 76}┐")

    # Visual Comparison Bars
    p_emp = state.p_lag_100_emp
    p_gamma = state.p_lag_100_gamma
    p_norm = state.p_lag_100_norm
    bar_width = 38

    def make_bar(pct, fill_clr):
        fill = int((pct / 100.0) * bar_width)
        fill = min(bar_width, max(0, fill))
        return f"{fill_clr}{'█' * fill}{ANSI_RESET}{CLR_MUTED}{'░' * (bar_width - fill)}{ANSI_RESET}"

    out.append(f"│ Initial Proposal Placeholder (Wi-Fi): {make_bar(4.5, CLR_MUTED)}  4.5%   │")
    out.append(f"│ Live Empirical Ground Truth (Wi-Fi):  {make_bar(p_emp, CLR_ROYAL)} {ANSI_BOLD}{p_emp:5.1f}%{ANSI_RESET}  │")
    out.append(f"│ MLE Shifted Gamma Model Fit:          {make_bar(p_gamma, CLR_NAVY)} {ANSI_BOLD}{p_gamma:5.1f}%{ANSI_RESET}  │")
    out.append(f"│ Gaussian Normal Baseline (Fails):     {make_bar(p_norm, CLR_AMBER)} {p_norm:5.1f}%  │")
    out.append(f"├{'─' * 76}┤")
    g_a, g_loc, g_b = state.gamma_params
    out.append(f"│ Shifted Gamma MLE Params:  Shape (α)={g_a:5.2f} | Loc (γ)={g_loc:5.1f}ms | Scale (β)={g_b:5.1f}ms │")
    out.append(f"└{'─' * 76}┘")

    # Section 3: Live Sparkline & Disruption Bursts
    out.append(f"\n{ANSI_BOLD}3. RECENT LATENCY RUN & TEMPORAL CLUSTERING{ANSI_RESET}")
    recent = state.latencies[-50:] if len(state.latencies) >= 50 else state.latencies
    spark_str = ""
    for v in recent:
        idx = int((min(v, 600.0) / 600.0) * (len(SPARK_CHARS) - 1))
        c = SPARK_CHARS[idx]
        if v < 50:
            spark_str += f"{CLR_GREEN}{c}"
        elif v <= 100:
            spark_str += f"{CLR_AMBER}{c}"
        else:
            spark_str += f"{CLR_RED}{c}"
    spark_str += ANSI_RESET

    burst_status = f"{CLR_RED}{ANSI_BOLD}ACTIVE ({state.active_burst} pkts){ANSI_RESET}" if state.active_burst > 0 else f"{CLR_GREEN}Clear{ANSI_RESET}"
    out.append(f"Recent Trace (Last 50): {spark_str}")
    out.append(f"Burst Clustering Status: {burst_status} | Max Burst Observed: {CLR_AMBER}{state.max_burst} pkts{ANSI_RESET} | Total Bursts: {state.total_bursts}")

    # Bottom Control Bar
    out.append(f"\n{CLR_BG_ROYAL}{CLR_WHITE}{ANSI_BOLD} [Space] Pause/Resume  [+] Speed Up  [-] Slow Down  [w] Open Web UI  [q] Quit {ANSI_RESET}")

    return "\n".join(out)

# -----------------------------------------------------------------------------
# Embedded Web Dashboard Server (Optional on http://localhost:8050)
# -----------------------------------------------------------------------------
HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Live Wi-Fi Lag Spike Statistical Monitor</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --navy: #12355b;
      --royal: #1e3989;
      --cream: #f7f3eb;
      --card-bg: #ffffff;
      --dark-text: #0f172a;
      --muted-text: #555b66;
      --red: #dc2626;
      --green: #16a34a;
      --amber: #d97706;
    }
    body {
      margin: 0;
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
      background-color: var(--cream);
      color: var(--dark-text);
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-bottom: 40px;
    }
    header {
      width: 100%;
      background-color: var(--navy);
      color: white;
      padding: 24px 40px;
      box-sizing: border-box;
      border-bottom: 4px solid var(--royal);
    }
    header h1 {
      margin: 0 0 6px 0;
      font-size: 24px;
      letter-spacing: -0.5px;
    }
    header p {
      margin: 0;
      color: #cbd5e1;
      font-size: 14px;
    }
    .container {
      width: 92%;
      max-width: 1200px;
      margin-top: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .grid-4 {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }
    .card {
      background: var(--card-bg);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.05);
      border-top: 4px solid var(--royal);
      box-sizing: border-box;
    }
    .card h3 {
      margin: 0 0 10px 0;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--muted-text);
    }
    .card .val {
      font-size: 32px;
      font-weight: bold;
      color: var(--navy);
      margin: 0;
    }
    .card .sub {
      font-size: 12px;
      color: var(--muted-text);
      margin-top: 4px;
    }
    .chart-box {
      background: var(--card-bg);
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.05);
      border-top: 4px solid var(--royal);
    }
    .chart-box h2 {
      margin: 0 0 16px 0;
      font-size: 18px;
      color: var(--navy);
    }
    .takeaway-bar {
      background: var(--card-bg);
      border-left: 6px solid var(--royal);
      padding: 16px 24px;
      border-radius: 4px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.05);
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .takeaway-bar .tag {
      font-weight: bold;
      color: var(--royal);
      font-size: 12px;
      letter-spacing: 0.5px;
    }
    .takeaway-bar .text {
      font-weight: bold;
      color: var(--navy);
      font-size: 15px;
    }
  </style>
</head>
<body>
  <header>
    <h1>The Probability of a Lag Spike: Live Statistical Inference</h1>
    <p>Real-Time Maximum Likelihood Estimation of Shifted Gamma Models on Wi-Fi Latency</p>
  </header>

  <div class="container">
    <div class="grid-4">
      <div class="card">
        <h3>Current Ping Latency</h3>
        <p class="val" id="cur-rtt">-- ms</p>
        <p class="sub" id="cur-status">Streaming probe reply...</p>
      </div>
      <div class="card">
        <h3>Disruption Risk P(X > 100)</h3>
        <p class="val" id="p-disrupt" style="color: var(--red);">--%</p>
        <p class="sub" id="gamma-pred">Gamma Model: --%</p>
      </div>
      <div class="card">
        <h3>Median vs Mean Latency</h3>
        <p class="val" id="med-mean">-- / --</p>
        <p class="sub">Median (P50) is 35ms below Mean</p>
      </div>
      <div class="card">
        <h3>Tail Percentile (P99)</h3>
        <p class="val" id="p99-val" style="color: var(--amber);">-- ms</p>
        <p class="sub" id="loss-stat">Packet Loss: --%</p>
      </div>
    </div>

    <div class="chart-box">
      <h2>Sequential Ping Round-Trip Time (Live Run Chart)</h2>
      <canvas id="rttChart" height="90"></canvas>
    </div>

    <div class="takeaway-bar">
      <span class="tag">TAKEAWAY</span>
      <span class="text" id="takeaway-msg">Mean latency hides disruptive tail spikes; live Shifted Gamma model accurately captures tail risk.</span>
    </div>
  </div>

  <script>
    const ctx = document.getElementById('rttChart').getContext('2d');
    const rttChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Ping RTT (ms)',
          data: [],
          borderColor: '#1e3989',
          backgroundColor: 'rgba(30, 57, 137, 0.08)',
          borderWidth: 1.8,
          pointRadius: 2.5,
          tension: 0.1,
          fill: true
        }, {
          label: 'Lag Spike Threshold (T = 100 ms)',
          data: [],
          borderColor: '#dc2626',
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        }]
      },
      options: {
        responsive: true,
        animation: false,
        scales: {
          x: { title: { display: true, text: 'Sample Index' }, grid: { display: false } },
          y: { title: { display: true, text: 'Latency (ms)' }, min: 0 }
        }
      }
    });

    async function fetchData() {
      try {
        const res = await fetch('/api/stats');
        const d = await res.json();
        
        document.getElementById('cur-rtt').innerText = d.current_rtt.toFixed(1) + ' ms';
        const st = document.getElementById('cur-status');
        if (d.current_rtt > 100) {
          st.innerText = '⚡ Lag Spike Active!';
          st.style.color = 'var(--red)';
        } else {
          st.innerText = 'Normal latency';
          st.style.color = 'var(--green)';
        }

        document.getElementById('p-disrupt').innerText = d.p_lag_100_emp.toFixed(1) + '%';
        document.getElementById('gamma-pred').innerText = 'Shifted Gamma Model: ' + d.p_lag_100_gamma.toFixed(1) + '%';
        document.getElementById('med-mean').innerText = d.median.toFixed(0) + ' / ' + d.mean.toFixed(0) + ' ms';
        document.getElementById('p99-val').innerText = d.p99.toFixed(1) + ' ms';
        document.getElementById('loss-stat').innerText = 'Loss: ' + d.loss_pct.toFixed(1) + '% | Bursts: ' + d.total_bursts;

        // Update chart data
        if (d.recent_rtt && d.recent_rtt.length > 0) {
          rttChart.data.labels = d.recent_seq;
          rttChart.data.datasets[0].data = d.recent_rtt;
          rttChart.data.datasets[1].data = new Array(d.recent_rtt.length).fill(100);
          rttChart.update();
        }
      } catch (err) {
        console.error(err);
      }
    }
    setInterval(fetchData, 400);
  </script>
</body>
</html>
"""

class WebServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress console log spam

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode('utf-8'))
        elif self.path == '/api/stats':
            with STATE.lock:
                recent_rtt = STATE.latencies[-60:]
                recent_seq = STATE.seqs[-60:] if STATE.seqs else list(range(len(recent_rtt)))
                loss_pct = (STATE.packet_loss_count / max(1, STATE.total_transmitted)) * 100.0
                data = {
                    'current_rtt': STATE.current_rtt,
                    'current_seq': STATE.current_seq,
                    'n': STATE.n,
                    'mean': STATE.mean,
                    'median': STATE.median,
                    'min': STATE.min_val,
                    'max': STATE.max_val,
                    'p90': STATE.p90,
                    'p99': STATE.p99,
                    'skewness': STATE.skewness,
                    'kurtosis': STATE.kurtosis,
                    'p_lag_100_emp': STATE.p_lag_100_emp,
                    'p_lag_100_gamma': STATE.p_lag_100_gamma,
                    'loss_pct': loss_pct,
                    'active_burst': STATE.active_burst,
                    'max_burst': STATE.max_burst,
                    'total_bursts': STATE.total_bursts,
                    'recent_rtt': recent_rtt,
                    'recent_seq': recent_seq
                }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def start_web_server(port=8050):
    server = HTTPServer(('127.0.0.1', port), WebServerHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server

# -----------------------------------------------------------------------------
# Main Application Loop
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Live Wi-Fi Lag Spike Monitor & Inference Dashboard")
    parser.add_argument("--live", action="store_true", help="Capture live ping probes to 8.8.8.8 instead of replaying wifi_data.txt")
    parser.add_argument("--target", type=str, default="8.8.8.8", help="Target host for live ping (default: 8.8.8.8)")
    parser.add_argument("--speed", type=float, default=10.0, help="Replay speed multiplier (e.g. 5.0 = 5x faster than real-time)")
    parser.add_argument("--web", action="store_true", help="Launch live web dashboard on http://localhost:8050")
    parser.add_argument("--port", type=int, default=8050, help="Web dashboard port (default: 8050)")
    parser.add_argument("--duration", type=int, default=0, help="Exit automatically after N seconds (useful for scripts/testing)")
    parser.add_argument("--summary", action="store_true", help="Run in non-interactive batch mode and print summary")
    args = parser.parse_args()

    STATE.speed_multiplier = args.speed
    STATE.target_host = args.target

    if args.web:
        start_web_server(port=args.port)
        print(f"Web Dashboard launched at http://localhost:{args.port}")

    # Launch ingestion thread
    if args.live:
        STATE.mode = "live"
        producer = threading.Thread(target=live_ping_worker, args=(args.target, STATE), daemon=True)
    else:
        STATE.mode = "replay"
        data_file = "wifi_data.txt"
        producer = threading.Thread(target=replay_file_worker, args=(data_file, STATE), daemon=True)

    producer.start()

    # Non-interactive / headless summary mode
    if args.summary:
        print(f"Running monitor in headless summary mode (duration: {args.duration or 5}s)...")
        t_end = time.time() + (args.duration or 5)
        while time.time() < t_end and not STATE.done:
            time.sleep(0.5)
            STATE.update_metrics()
        print(render_terminal_ui(STATE))
        STATE.done = True
        return

    # Check if stdin is an interactive TTY
    is_tty = sys.stdin.isatty() and sys.stdout.isatty()
    old_term_settings = None

    if is_tty:
        # Save terminal settings and switch to raw mode for single keypress detection
        try:
            old_term_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            # Enter alternate screen buffer & hide cursor
            sys.stdout.write("\033[?1049h\033[?25l")
            sys.stdout.flush()
        except Exception:
            is_tty = False

    start_time = time.time()

    try:
        while not STATE.done:
            # Handle keyboard input
            if is_tty and select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                if ch in ('q', 'Q', '\x03'):  # q or Ctrl+C
                    STATE.done = True
                    break
                elif ch == ' ':
                    STATE.is_paused = not STATE.is_paused
                elif ch in ('+', '='):
                    STATE.speed_multiplier = min(100.0, STATE.speed_multiplier * 1.5)
                elif ch in ('-', '_'):
                    STATE.speed_multiplier = max(0.5, STATE.speed_multiplier / 1.5)
                elif ch in ('w', 'W'):
                    if not args.web:
                        start_web_server(port=args.port)
                        args.web = True
                    try:
                        import webbrowser
                        webbrowser.open(f"http://localhost:{args.port}")
                    except Exception:
                        pass

            # Render Dashboard
            ui_text = render_terminal_ui(STATE)
            if is_tty:
                # Move to top-left and render without flicker
                sys.stdout.write("\033[H" + ui_text)
                sys.stdout.flush()
            else:
                print("\033[H\033[J" + ui_text)

            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                break

            time.sleep(0.12)

    except KeyboardInterrupt:
        pass
    finally:
        STATE.done = True
        if is_tty and old_term_settings:
            # Restore cursor and alternate screen
            sys.stdout.write("\033[?25h\033[?1049l")
            sys.stdout.flush()
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_term_settings)

    print("\nLive monitor finished. Final state recorded.")

if __name__ == '__main__':
    main()
