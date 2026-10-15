#!/usr/bin/env bash
# Quick Launcher for the Live Wi-Fi Lag Spike Statistical Monitor

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "======================================================================"
echo "    WI-FI LAG SPIKE STATISTICAL MONITOR - LIVE INFERENCE DEMO"
echo "    Course: Applied Probability & Statistical Inference"
echo "======================================================================"
echo ""
echo "Modes:"
echo "  1) Replay Mode (default): Replays the 3,685 packets from wifi_data.txt"
echo "  2) Live Mode (--live):    Probes live internet network right now"
echo "  3) Web UI (--web):        Starts local browser dashboard at http://localhost:8050"
echo ""

python3 live_lag_spike_monitor.py "$@"
