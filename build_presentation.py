#!/usr/bin/env python3
"""
Build Wi-Fi Lag Spike Solution Presentation (.pptx and .pdf)
=============================================================
Course: Applied Probability & Statistical Inference
Theme: Matches 'probability of lag spike.pdf' exactly:
  - Header: Dark Navy #12355b with Royal Blue #1e3989 accent
  - Background: Warm Cream #f7f3eb
  - Cards: White #ffffff with Royal Blue #1e3989 top accent band
  - Text: White on navy, Slate #0f172a for titles/takeaway, Slate Gray #555b66 for body
  - Takeaway Bar: White card with #1e3989 left vertical bar
"""

import os
import json
import subprocess
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# -----------------------------------------------------------------------------
# Color Palette Constants
# -----------------------------------------------------------------------------
COLOR_NAVY = RGBColor(18, 53, 91)       # #12355b
COLOR_ROYAL = RGBColor(30, 57, 137)     # #1e3989
COLOR_ACCENT = RGBColor(37, 99, 235)    # #2563eb
COLOR_LIGHT_BLUE = RGBColor(131, 146, 189) # #8392bd
COLOR_CREAM = RGBColor(247, 243, 235)   # #f7f3eb
COLOR_WHITE = RGBColor(255, 255, 255)   # #ffffff
COLOR_SLATE_DARK = RGBColor(15, 23, 42) # #0f172a
COLOR_MUTED = RGBColor(85, 91, 102)     # #555b66
COLOR_LIGHT_GRAY = RGBColor(203, 211, 219) # #cbd3db
COLOR_BORDER = RGBColor(226, 232, 240)  # #e2e8f0
COLOR_RED = RGBColor(220, 38, 38)       # #dc2626
COLOR_GREEN = RGBColor(22, 163, 74)     # #16a34a
COLOR_AMBER = RGBColor(217, 119, 6)     # #d97706

METRICS_PATH = 'solution_outputs/wifi_solution_metrics.json'
with open(METRICS_PATH, 'r') as f:
    METRICS = json.load(f)

EDA = METRICS['eda']
TEMPORAL = METRICS['temporal']
BOOT = METRICS['bootstrap']

# Initialize Presentation (16:9 Widescreen)
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Helper: Set slide background to warm cream
def set_slide_background(slide):
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = COLOR_CREAM
    bg_shape.line.fill.background()
    return bg_shape

# Helper: Add Standard Header Bar
def add_header(slide, title_text, subtitle_text):
    # Dark Navy Header Box
    header_box = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.42)
    )
    header_box.fill.solid()
    header_box.fill.fore_color.rgb = COLOR_NAVY
    header_box.line.fill.background()

    # Royal Blue Accent Stripe below Header
    stripe = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, Inches(1.42), prs.slide_width, Inches(0.06)
    )
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = COLOR_ROYAL
    stripe.line.fill.background()

    # Title Text Box
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.14), Inches(11.8), Inches(0.68))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = "Arial"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    # Subtitle Text Box
    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.84), Inches(11.8), Inches(0.48))
    stf = sub_box.text_frame
    stf.word_wrap = True
    stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
    sp = stf.paragraphs[0]
    sp.text = subtitle_text
    sp.font.name = "Arial"
    sp.font.size = Pt(12.5)
    sp.font.color.rgb = COLOR_LIGHT_GRAY

# Helper: Add Bottom Takeaway Banner
def add_takeaway(slide, takeaway_text):
    card_y = Inches(6.45)
    card_h = Inches(0.62)
    card_w = Inches(11.733)
    card_x = Inches(0.8)

    # White Background Card
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, card_x, card_y, card_w, card_h)
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_WHITE
    card.line.color.rgb = COLOR_BORDER
    card.line.width = Pt(1)

    # Left Vertical Stripe (Royal Blue)
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, card_x, card_y, Inches(0.08), card_h)
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = COLOR_ROYAL
    stripe.line.fill.background()

    # Text Box
    tb = slide.shapes.add_textbox(card_x + Inches(0.18), card_y + Inches(0.12), card_w - Inches(0.3), Inches(0.38))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]

    run1 = p.add_run()
    run1.text = "TAKEAWAY   "
    run1.font.name = "Arial"
    run1.font.size = Pt(10.5)
    run1.font.bold = True
    run1.font.color.rgb = COLOR_ROYAL

    run2 = p.add_run()
    run2.text = takeaway_text
    run2.font.name = "Arial"
    run2.font.size = Pt(10.8)
    run2.font.bold = True
    run2.font.color.rgb = COLOR_SLATE_DARK

    # Tiny footer
    foot_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(5.0), Inches(0.3))
    ftf = foot_box.text_frame
    ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
    fp = ftf.paragraphs[0]
    fp.text = "Probability of a Lag Spike • Wi-Fi Empirical Solution"
    fp.font.name = "Arial"
    fp.font.size = Pt(8.5)
    fp.font.color.rgb = RGBColor(156, 163, 175)

# Helper: Create a styled card with top blue accent stripe
def create_card(slide, x, y, w, h, top_stripe=True):
    # Main White Card
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_WHITE
    card.line.color.rgb = COLOR_BORDER
    card.line.width = Pt(1)

    if top_stripe:
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.06))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = COLOR_ROYAL
        stripe.line.fill.background()

    return card

# -----------------------------------------------------------------------------
# SLIDE 1: Title Slide (Two-Column Split Theme)
# -----------------------------------------------------------------------------
def build_slide_1():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)

    # Left Dark Navy Half
    left_w = Inches(6.8)
    left_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, left_w, prs.slide_height)
    left_bg.fill.solid()
    left_bg.fill.fore_color.rgb = COLOR_NAVY
    left_bg.line.fill.background()

    # Left Vertical Stripe Accent
    left_stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.12), prs.slide_height)
    left_stripe.fill.solid()
    left_stripe.fill.fore_color.rgb = COLOR_ROYAL
    left_stripe.line.fill.background()

    # Title & Subtitle on Navy Left
    t_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.5), Inches(3.2))
    tf = t_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p = tf.paragraphs[0]
    p.text = "The Probability of a Lag Spike: Statistical Solution for Wi-Fi Latency"
    p.font.name = "Arial"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.space_after = Pt(20)

    p2 = tf.add_paragraph()
    p2.text = "Moving Beyond \"Average Ping\" Using Right-Skewed Probability Distributions, Goodness-of-Fit Testing, and Tail Risk Inference"
    p2.font.name = "Arial"
    p2.font.size = Pt(14)
    p2.font.color.rgb = COLOR_LIGHT_GRAY

    # Right Cream Half: Cards
    # Presenter Card
    p_label = slide.shapes.add_textbox(Inches(7.5), Inches(1.8), Inches(5.0), Inches(0.35))
    ptf = p_label.text_frame
    pp = ptf.paragraphs[0]
    pp.text = "Presenter"
    pp.font.name = "Arial"
    pp.font.size = Pt(14)
    pp.font.bold = True
    pp.font.color.rgb = COLOR_SLATE_DARK

    p_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.5), Inches(2.25), Inches(5.0), Inches(1.1))
    p_card.fill.solid()
    p_card.fill.fore_color.rgb = RGBColor(232, 235, 243)
    p_card.line.fill.background()

    p_stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.5), Inches(2.25), Inches(0.08), Inches(1.1))
    p_stripe.fill.solid()
    p_stripe.fill.fore_color.rgb = COLOR_ROYAL
    p_stripe.line.fill.background()

    p_tx = slide.shapes.add_textbox(Inches(7.75), Inches(2.55), Inches(4.6), Inches(0.5))
    ptf2 = p_tx.text_frame
    pp2 = ptf2.paragraphs[0]
    pp2.text = "Saksham  [Applied Probability & Inference]"
    pp2.font.name = "Arial"
    pp2.font.size = Pt(14)
    pp2.font.bold = True
    pp2.font.color.rgb = COLOR_SLATE_DARK

    # Course Card
    c_label = slide.shapes.add_textbox(Inches(7.5), Inches(3.7), Inches(5.0), Inches(0.35))
    ctf = c_label.text_frame
    cp = ctf.paragraphs[0]
    cp.text = "Course & Implementation Scope"
    cp.font.name = "Arial"
    cp.font.size = Pt(14)
    cp.font.bold = True
    cp.font.color.rgb = COLOR_SLATE_DARK

    c_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.5), Inches(4.15), Inches(5.0), Inches(1.6))
    c_card.fill.solid()
    c_card.fill.fore_color.rgb = RGBColor(232, 235, 243)
    c_card.line.fill.background()

    c_stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.5), Inches(4.15), Inches(0.08), Inches(1.6))
    c_stripe.fill.solid()
    c_stripe.fill.fore_color.rgb = COLOR_ROYAL
    c_stripe.line.fill.background()

    c_tx = slide.shapes.add_textbox(Inches(7.75), Inches(4.35), Inches(4.6), Inches(1.2))
    ctf2 = c_tx.text_frame
    ctf2.word_wrap = True
    cp2 = ctf2.paragraphs[0]
    cp2.text = "Applied Probability & Statistical Inference"
    cp2.font.name = "Arial"
    cp2.font.size = Pt(13)
    cp2.font.bold = True
    cp2.font.color.rgb = COLOR_SLATE_DARK

    cp3 = ctf2.add_paragraph()
    cp3.text = f"Empirical Wi-Fi Dataset: N = {EDA['n']:,} ICMP Echo Probes\nEvaluation of Right-Skewed Models & Lag Spike Tail Risk"
    cp3.font.name = "Arial"
    cp3.font.size = Pt(11)
    cp3.font.color.rgb = COLOR_MUTED

# -----------------------------------------------------------------------------
# SLIDE 2: Problem & Empirical Reality
# -----------------------------------------------------------------------------
def build_slide_2():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_header(
        slide,
        "The Problem: Why \"Average Latency\" Lies to You on Wi-Fi",
        "The mean latency appears moderate, but tail volatility and severe skewness create disruptive lag spikes."
    )

    card_y = Inches(1.7)
    card_h = Inches(4.45)
    card_w = Inches(5.65)

    # Left Card: What People Assume
    create_card(slide, Inches(0.8), card_y, card_w, card_h)

    badge1 = slide.shapes.add_textbox(Inches(1.1), card_y + Inches(0.2), Inches(4.5), Inches(0.3))
    btf1 = badge1.text_frame
    bp1 = btf1.paragraphs[0]
    bp1.text = "WHAT PEOPLE ASSUME"
    bp1.font.name = "Arial"
    bp1.font.size = Pt(11)
    bp1.font.bold = True
    bp1.font.color.rgb = COLOR_MUTED

    title1 = slide.shapes.add_textbox(Inches(1.1), card_y + Inches(0.55), Inches(5.0), Inches(0.45))
    ttf1 = title1.text_frame
    tp1 = ttf1.paragraphs[0]
    tp1.text = "Symmetric Normal Distribution"
    tp1.font.name = "Arial"
    tp1.font.size = Pt(18)
    tp1.font.bold = True
    tp1.font.color.rgb = COLOR_SLATE_DARK

    bullets1 = slide.shapes.add_textbox(Inches(1.1), card_y + Inches(1.2), Inches(5.0), Inches(2.9))
    bl_tf1 = bullets1.text_frame
    bl_tf1.word_wrap = True

    items1 = [
        ("Bell-Curve Assumption:", "Belief that latency symmetrically clusters around the 176.8 ms average."),
        ("Predicts Negative Latency:", "Normal model predicts a 13.1% probability of RTT < 0 ms (physically absurd!)."),
        ("Severe Tail Blindness:", "Estimates probability of catastrophic lag (>800 ms) as 0.003% (virtually zero)."),
        ("Misleading SLA Audits:", "ISPs report mean ping, masking user disconnections and frame freezes.")
    ]
    for i, (head, body) in enumerate(items1):
        p = bl_tf1.paragraphs[0] if i == 0 else bl_tf1.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = f"• {head} "
        r1.font.bold = True
        r1.font.size = Pt(12)
        r1.font.color.rgb = COLOR_ROYAL
        r2 = p.add_run()
        r2.text = body
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = COLOR_MUTED

    # Right Card: Wi-Fi Reality
    create_card(slide, Inches(6.88), card_y, card_w, card_h)

    badge2 = slide.shapes.add_textbox(Inches(7.18), card_y + Inches(0.2), Inches(4.5), Inches(0.3))
    btf2 = badge2.text_frame
    bp2 = btf2.paragraphs[0]
    bp2.text = "EMPIRICAL WI-FI REALITY"
    bp2.font.name = "Arial"
    bp2.font.size = Pt(11)
    bp2.font.bold = True
    bp2.font.color.rgb = COLOR_ROYAL

    title2 = slide.shapes.add_textbox(Inches(7.18), card_y + Inches(0.55), Inches(5.0), Inches(0.45))
    ttf2 = title2.text_frame
    tp2 = ttf2.paragraphs[0]
    tp2.text = "Right-Skewed & Heavy-Tailed"
    tp2.font.name = "Arial"
    tp2.font.size = Pt(18)
    tp2.font.bold = True
    tp2.font.color.rgb = COLOR_SLATE_DARK

    bullets2 = slide.shapes.add_textbox(Inches(7.18), card_y + Inches(1.2), Inches(5.0), Inches(2.9))
    bl_tf2 = bullets2.text_frame
    bl_tf2.word_wrap = True

    items2 = [
        ("Strict Propagation Floor:", f"Physical minimum latency bound at {EDA['min']:.1f} ms (no values below this)."),
        ("Extreme Right-Skewness:", f"Skewness = +{EDA['skewness']:.3f} (heavily asymmetrical long right tail)."),
        ("Leptokurtic Kurtosis:", f"Excess Kurtosis = +{EDA['kurtosis_excess']:.2f} (extreme outlier probability)."),
        ("Catastrophic Latency Spikes:", f"Max observed ping = {EDA['max']:.1f} ms (14× higher than the 176.8 ms mean!)."),
        ("High Disruption Rate:", f"P(X > 100 ms) = {BOOT['p_lag_100']['point']:.1f}% (64% of packets experience lag!).")
    ]
    for i, (head, body) in enumerate(items2):
        p = bl_tf2.paragraphs[0] if i == 0 else bl_tf2.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = f"• {head} "
        r1.font.bold = True
        r1.font.size = Pt(12)
        r1.font.color.rgb = COLOR_NAVY
        r2 = p.add_run()
        r2.text = body
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = COLOR_MUTED

    add_takeaway(
        slide,
        f"Mean latency ({EDA['mean']:.1f} ms) masks an extreme {EDA['max']:.0f} ms tail spike; right-skewed models are mathematically mandatory."
    )

# -----------------------------------------------------------------------------
# SLIDE 3: Exploratory Data Analysis & Statistics
# -----------------------------------------------------------------------------
def build_slide_3():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_header(
        slide,
        "Exploratory Data Analysis: Wi-Fi Empirical Characteristics",
        f"Rigorous distributional summary of N = {EDA['n']:,} consecutive ICMP ping packets collected over Wi-Fi."
    )

    card_y = Inches(1.65)
    card_h = Inches(4.55)

    # Left Column: 3 Metric Cards (Width: 4.8 in)
    col1_w = Inches(4.6)

    # Sub-card 1: Central Tendency
    sc1 = create_card(slide, Inches(0.8), card_y, col1_w, Inches(1.35))
    tx1 = slide.shapes.add_textbox(Inches(1.0), card_y + Inches(0.12), col1_w - Inches(0.4), Inches(1.1))
    tf1 = tx1.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "Central Tendency vs Spread"
    p1.font.bold = True
    p1.font.size = Pt(13)
    p1.font.color.rgb = COLOR_ROYAL
    p1_sub = tf1.add_paragraph()
    p1_sub.text = f"• Mean: {EDA['mean']:.2f} ms  |  Median: {EDA['median']:.2f} ms\n• Std Dev: {EDA['std']:.2f} ms  |  IQR: {EDA['iqr']:.2f} ms\n• Minimum: {EDA['min']:.2f} ms  |  Maximum: {EDA['max']:.2f} ms"
    p1_sub.font.size = Pt(11)
    p1_sub.font.color.rgb = COLOR_MUTED

    # Sub-card 2: Percentile Spectrum
    sc2 = create_card(slide, Inches(0.8), card_y + Inches(1.5), col1_w, Inches(1.35))
    tx2 = slide.shapes.add_textbox(Inches(1.0), card_y + Inches(1.62), col1_w - Inches(0.4), Inches(1.1))
    tf2 = tx2.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = "Percentile Spectrum"
    p2.font.bold = True
    p2.font.size = Pt(13)
    p2.font.color.rgb = COLOR_ROYAL
    p2_sub = tf2.add_paragraph()
    p2_sub.text = f"• 50th Percentile (P50): {EDA['median']:.2f} ms\n• 90th Percentile (P90): {EDA['p90']:.2f} ms\n• 95th Percentile (P95): {EDA['p95']:.2f} ms\n• 99th Percentile (P99): {EDA['p99']:.2f} ms (Severe Tail)"
    p2_sub.font.size = Pt(11)
    p2_sub.font.color.rgb = COLOR_MUTED

    # Sub-card 3: Higher Moments & Loss
    sc3 = create_card(slide, Inches(0.8), card_y + Inches(3.0), col1_w, Inches(1.4))
    tx3 = slide.shapes.add_textbox(Inches(1.0), card_y + Inches(3.12), col1_w - Inches(0.4), Inches(1.15))
    tf3 = tx3.text_frame
    p3 = tf3.paragraphs[0]
    p3.text = "Higher Moments & Network Reliability"
    p3.font.bold = True
    p3.font.size = Pt(13)
    p3.font.color.rgb = COLOR_ROYAL
    p3_sub = tf3.add_paragraph()
    p3_sub.text = f"• Skewness: +{EDA['skewness']:.3f} (Severe Right Asymmetry)\n• Excess Kurtosis: +{EDA['kurtosis_excess']:.2f} (Fat Tails)\n• Packet Loss: {EDA['packet_loss_pct']:.2f}% ({EDA['total_transmitted'] - EDA['total_received']} / {EDA['total_transmitted']:,} packets dropped)"
    p3_sub.font.size = Pt(11)
    p3_sub.font.color.rgb = COLOR_MUTED

    # Right Column: Visual Boxplot & Outliers Image
    img_card = create_card(slide, Inches(5.65), card_y, Inches(6.88), card_h)
    img_path = 'solution_outputs/figure1_time_series_lag_spikes.png'
    if os.path.exists(img_path):
        slide.shapes.add_picture(img_path, Inches(5.75), card_y + Inches(0.2), Inches(6.68), Inches(4.15))

    add_takeaway(
        slide,
        f"Median latency ({EDA['median']:.1f} ms) is 35 ms below the mean; 1% of packets (P99) exceed {EDA['p99']:.0f} ms with {EDA['packet_loss_pct']:.1f}% packet loss."
    )

# -----------------------------------------------------------------------------
# SLIDE 4: Hypothesis Testing & Normality Rejection
# -----------------------------------------------------------------------------
def build_slide_4():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_header(
        slide,
        "Hypothesis Testing: Statistical Rejection of Gaussian Normality",
        "Multiple formal statistical tests decisively reject the null hypothesis of normal latency (p < 1e-82)."
    )

    card_y = Inches(1.65)
    card_h = Inches(4.55)
    card_w = Inches(5.65)

    # Left Card: Goodness-of-Fit Tests
    create_card(slide, Inches(0.8), card_y, card_w, card_h)

    t1 = slide.shapes.add_textbox(Inches(1.1), card_y + Inches(0.25), Inches(5.0), Inches(0.45))
    ttf1 = t1.text_frame
    tp1 = ttf1.paragraphs[0]
    tp1.text = "Formal Goodness-of-Fit Tests"
    tp1.font.name = "Arial"
    tp1.font.size = Pt(18)
    tp1.font.bold = True
    tp1.font.color.rgb = COLOR_SLATE_DARK

    tx1 = slide.shapes.add_textbox(Inches(1.1), card_y + Inches(0.85), Inches(5.0), Inches(3.4))
    tf1 = tx1.text_frame
    tf1.word_wrap = True

    tests = [
        ("Kolmogorov-Smirnov (K-S) Test:", f"D = 0.1603, p = 3.53e-83\nDecisive rejection of Gaussian CDF at alpha = 0.001."),
        ("D'Agostino-Pearson Omnibus Test:", f"K^2 = {EDA['dagostino_k2']:.1f}, p = 0.000\nSimultaneously tests skewness and kurtosis components."),
        ("Excess Kurtosis Test:", f"Excess kurtosis = +{EDA['kurtosis_excess']:.2f} (Normal = 0)\nExtreme leptokurtic peakedness and heavy right tail."),
        ("Conclusion:", "The empirical data is fundamentally non-Gaussian; parametric modeling requires strictly positive, skewed distributions.")
    ]
    for i, (hd, bd) in enumerate(tests):
        p = tf1.paragraphs[0] if i == 0 else tf1.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = f"• {hd}\n  "
        r1.font.bold = True
        r1.font.size = Pt(12)
        r1.font.color.rgb = COLOR_ROYAL
        r2 = p.add_run()
        r2.text = bd
        r2.font.size = Pt(11)
        r2.font.color.rgb = COLOR_MUTED

    # Right Column: Visual Q-Q Plots
    create_card(slide, Inches(6.88), card_y, card_w, card_h)
    img_path = 'solution_outputs/figure4_qq_plots.png'
    if os.path.exists(img_path):
        slide.shapes.add_picture(img_path, Inches(6.98), card_y + Inches(0.15), Inches(5.45), Inches(4.25))

    add_takeaway(
        slide,
        "Normality is rejected with p < 1e-82; Q-Q diagnostics demonstrate that Gaussian models deviate catastrophically in the upper tail."
    )

# -----------------------------------------------------------------------------
# SLIDE 5: Distribution Modeling via MLE
# -----------------------------------------------------------------------------
def build_slide_5():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_header(
        slide,
        "Distribution Modeling: Maximum Likelihood Estimation (MLE)",
        "Evaluating right-skewed parametric families incorporating the physical propagation floor (gamma = 17.9 ms)."
    )

    card_y = Inches(1.65)
    card_h = Inches(4.55)

    # Left: Model Comparison Table (Width: 6.2 in)
    tbl_card = create_card(slide, Inches(0.8), card_y, Inches(6.2), card_h)

    # Table inside
    rows = 7
    cols = 5
    table_shape = slide.shapes.add_table(rows, cols, Inches(0.95), card_y + Inches(0.3), Inches(5.9), Inches(3.2))
    table = table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(0.9)
    table.columns[2].width = Inches(0.95)
    table.columns[3].width = Inches(0.95)
    table.columns[4].width = Inches(0.9)

    headers = ["Distribution Model", "Log-Lik", "AIC", "BIC", "K-S Stat"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_NAVY
        for p in cell.text_frame.paragraphs:
            p.font.name = "Arial"
            p.font.size = Pt(10.5)
            p.font.bold = True
            p.font.color.rgb = COLOR_WHITE
            p.alignment = PP_ALIGN.CENTER

    model_data = [
        ("Shifted Gamma (Best)", "-22,292.4", "44,590.9", "44,609.5", "0.0404"),
        ("Shifted Weibull", "-22,317.1", "44,640.3", "44,658.9", "0.0463"),
        ("Shifted Log-Normal", "-22,317.2", "44,640.3", "44,659.0", "0.0597"),
        ("Log-Normal (loc=0)", "-22,322.1", "44,648.2", "44,660.6", "0.0500"),
        ("Shifted Exponential", "-22,361.8", "44,727.5", "44,739.9", "0.0588"),
        ("Normal (Gaussian)", "-23,883.7", "47,771.4", "47,783.8", "0.1603")
    ]

    for i, row_vals in enumerate(model_data):
        for j, val in enumerate(row_vals):
            cell = table.cell(i + 1, j)
            cell.text = val
            cell.fill.solid()
            if i == 0:  # Highlight best model
                cell.fill.fore_color.rgb = RGBColor(238, 242, 255)
            else:
                cell.fill.fore_color.rgb = COLOR_WHITE
            for p in cell.text_frame.paragraphs:
                p.font.name = "Arial"
                p.font.size = Pt(9.5)
                p.font.color.rgb = COLOR_ROYAL if i == 0 else COLOR_SLATE_DARK
                if i == 0:
                    p.font.bold = True
                p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER

    # Parameters Annotation below table
    p_box = slide.shapes.add_textbox(Inches(0.95), card_y + Inches(3.6), Inches(5.9), Inches(0.8))
    ptf = p_box.text_frame
    ptf.word_wrap = True
    pp = ptf.paragraphs[0]
    pp.text = "Best Model Parameters: 3-Parameter Shifted Gamma\n• Shape (alpha) = 1.2927  |  Scale (beta) = 122.95 ms  |  Loc (gamma) = 17.87 ms\n• Physical interpretation: gamma represents the hardware propagation floor."
    pp.font.name = "Arial"
    pp.font.size = Pt(10)
    pp.font.color.rgb = COLOR_MUTED

    # Right: Fitted Densities Visual
    img_card = create_card(slide, Inches(7.2), card_y, Inches(5.333), card_h)
    img_path = 'solution_outputs/figure2_distribution_fits_kde.png'
    if os.path.exists(img_path):
        slide.shapes.add_picture(img_path, Inches(7.3), card_y + Inches(0.2), Inches(5.133), Inches(4.15))

    add_takeaway(
        slide,
        "Shifted Gamma achieves the lowest AIC (44,591) and K-S statistic (0.0404), outperforming Weibull, Log-Normal, and Normal."
    )

# -----------------------------------------------------------------------------
# SLIDE 6: Probability of Disruption P(X > 100 ms)
# -----------------------------------------------------------------------------
def build_slide_6():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_header(
        slide,
        "Beyond the Mean: Calculating the Probability of Disruption",
        "Evaluating lag spike disruption risk: P(X > 100 ms) = 1 - F_X(100), comparing empirical reality to proposal estimates."
    )

    card_y = Inches(1.65)
    card_h = Inches(4.55)

    # Left: Disruption Comparison & Highlights (Width: 5.6 in)
    c1 = create_card(slide, Inches(0.8), card_y, Inches(5.6), card_h)

    t1 = slide.shapes.add_textbox(Inches(1.05), card_y + Inches(0.25), Inches(5.1), Inches(0.45))
    ttf1 = t1.text_frame
    tp1 = ttf1.paragraphs[0]
    tp1.text = "Threshold Disruption Analysis"
    tp1.font.name = "Arial"
    tp1.font.size = Pt(18)
    tp1.font.bold = True
    tp1.font.color.rgb = COLOR_SLATE_DARK

    tx1 = slide.shapes.add_textbox(Inches(1.05), card_y + Inches(0.8), Inches(5.1), Inches(3.5))
    tf1 = tx1.text_frame
    tf1.word_wrap = True

    sections = [
        ("T = 100 ms Disruption Evaluation:",
         f"• Proposal Illustrative Placeholder: ~4.5% (Initial Wi-Fi assumption)\n"
         f"• Empirical Live Wi-Fi Reality: {BOOT['p_lag_100']['point']:.2f}% (2,360 / 3,685 pkts)\n"
         f"• Shifted Gamma Fitted Model: 64.34% (Relative error < 0.5%)\n"
         f"• Shifted Weibull Model: 63.72%  |  Log-Normal: 61.96%"),
        ("T = 150 ms & 200 ms Thresholds:",
         "• P(X > 150 ms): Empirical = 46.89%  |  Shifted Gamma = 46.15%\n"
         "• P(X > 200 ms): Empirical = 32.59%  |  Shifted Gamma = 32.57%")
    ]

    for i, (hd, bd) in enumerate(sections):
        p = tf1.paragraphs[0] if i == 0 else tf1.add_paragraph()
        p.space_after = Pt(4)
        r1 = p.add_run()
        r1.text = f"{hd}\n"
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = COLOR_ROYAL
        r2 = p.add_run()
        r2.text = bd
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_MUTED

    # Visual Comparison Bars (Matching original proposal Slide 6 theme)
    bar_y_start = card_y + Inches(2.55)
    bar_data = [
        ("Proposal Placeholder (Wi-Fi)", 0.045, "4.5%", COLOR_LIGHT_BLUE),
        ("Empirical Live Capture (Wi-Fi)", 0.6404, "64.0%", COLOR_ROYAL),
        ("Shifted Gamma MLE (Wi-Fi)", 0.6434, "64.3%", COLOR_NAVY)
    ]
    track_w = Inches(3.4)
    track_h = Inches(0.18)

    for b_idx, (b_label, b_val, b_pct, b_col) in enumerate(bar_data):
        curr_y = bar_y_start + Inches(b_idx * 0.58)

        # Label & Percentage
        lb_box = slide.shapes.add_textbox(Inches(1.05), curr_y, Inches(4.5), Inches(0.24))
        ltf = lb_box.text_frame
        ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0
        lp = ltf.paragraphs[0]
        lr1 = lp.add_run()
        lr1.text = b_label
        lr1.font.size = Pt(9.5)
        lr1.font.bold = True
        lr1.font.color.rgb = COLOR_SLATE_DARK

        lr2 = lp.add_run()
        lr2.text = f"  ({b_pct})"
        lr2.font.size = Pt(9.5)
        lr2.font.bold = True
        lr2.font.color.rgb = b_col

        # Gray Track
        trk = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.05), curr_y + Inches(0.24), track_w, track_h)
        trk.fill.solid()
        trk.fill.fore_color.rgb = RGBColor(221, 221, 223) # #dddddf
        trk.line.fill.background()

        # Colored Progress Fill
        fill_w = max(Inches(0.12), track_w * b_val)
        pfl = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.05), curr_y + Inches(0.24), fill_w, track_h)
        pfl.fill.solid()
        pfl.fill.fore_color.rgb = b_col
        pfl.line.fill.background()

    # Right: Disruption Risk Curve Visual
    img_card = create_card(slide, Inches(6.6), card_y, Inches(5.933), card_h)
    img_path = 'solution_outputs/figure5_disruption_risk_curve.png'
    if os.path.exists(img_path):
        slide.shapes.add_picture(img_path, Inches(6.7), card_y + Inches(0.2), Inches(5.733), Inches(4.15))

    add_takeaway(
        slide,
        f"Empirical Wi-Fi disruption at 100 ms is {BOOT['p_lag_100']['point']:.1f}% (vs 4.5% proposal estimate); Shifted Gamma predicts 64.34% with remarkable precision."
    )

# -----------------------------------------------------------------------------
# SLIDE 7: Bootstrap Uncertainty Estimation
# -----------------------------------------------------------------------------
def build_slide_7():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_header(
        slide,
        "Uncertainty Estimation: 95% Bootstrap Confidence Intervals",
        "Quantifying parameter stability via B = 5,000 non-parametric bootstrap resamples on live Wi-Fi latency observations."
    )

    card_y = Inches(1.65)
    card_h = Inches(4.55)

    # Left: 4 Metric Cards (Width: 5.4 in)
    col1_w = Inches(5.2)

    cards_info = [
        ("Median Latency [P50]", f"{BOOT['median']['point']:.2f} ms", f"[{BOOT['median']['lower']:.2f} ms, {BOOT['median']['upper']:.2f} ms]", "Extremely tight bound (+-4 ms); represents typical packet latency."),
        ("Mean Latency", f"{BOOT['mean']['point']:.2f} ms", f"[{BOOT['mean']['lower']:.2f} ms, {BOOT['mean']['upper']:.2f} ms]", "Influenced by right-tail outliers; spans +-5.1 ms."),
        ("90th Percentile [P90]", f"{BOOT['p90']['point']:.2f} ms", f"[{BOOT['p90']['lower']:.2f} ms, {BOOT['p90']['upper']:.2f} ms]", "Substantial tail delay (+-16 ms); critical for interactive cloud gaming."),
        ("99th Percentile [P99 Tail]", f"{BOOT['p99']['point']:.2f} ms", f"[{BOOT['p99']['lower']:.2f} ms, {BOOT['p99']['upper']:.2f} ms]", "High tail volatility spanning [680 ms, 928 ms]; causes frame freezes.")
    ]

    sub_h = Inches(1.02)
    for idx, (title, pt, ci, note) in enumerate(cards_info):
        sy = card_y + Inches(idx * 1.12)
        create_card(slide, Inches(0.8), sy, col1_w, sub_h)
        tb = slide.shapes.add_textbox(Inches(1.0), sy + Inches(0.08), col1_w - Inches(0.4), sub_h - Inches(0.16))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = f"{title}: "
        r1.font.bold = True
        r1.font.size = Pt(12)
        r1.font.color.rgb = COLOR_ROYAL

        r2 = p.add_run()
        r2.text = f"{pt}   "
        r2.font.bold = True
        r2.font.size = Pt(13)
        r2.font.color.rgb = COLOR_SLATE_DARK

        r3 = p.add_run()
        r3.text = f"95% CI: {ci}\n"
        r3.font.bold = True
        r3.font.size = Pt(11)
        r3.font.color.rgb = COLOR_AMBER

        r4 = p.add_run()
        r4.text = note
        r4.font.size = Pt(9.5)
        r4.font.color.rgb = COLOR_MUTED

    # Right: Bootstrap Distribution Plots Image
    create_card(slide, Inches(6.2), card_y, Inches(6.333), card_h)
    img_path = 'solution_outputs/figure6_bootstrap_distributions.png'
    if os.path.exists(img_path):
        slide.shapes.add_picture(img_path, Inches(6.3), card_y + Inches(0.2), Inches(6.133), Inches(4.15))

    add_takeaway(
        slide,
        f"Non-parametric bootstrap confirms median stability [{BOOT['median']['lower']:.0f}-{BOOT['median']['upper']:.0f} ms] alongside extreme tail volatility [{BOOT['p99']['lower']:.0f}-{BOOT['p99']['upper']:.0f} ms]."
    )

# -----------------------------------------------------------------------------
# SLIDE 8: Temporal Dynamics & Network Engineering Takeaways
# -----------------------------------------------------------------------------
def build_slide_8():
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)
    add_header(
        slide,
        "Temporal Dynamics, Burstiness & Network Engineering Conclusions",
        "Wi-Fi lag spikes are not independent; temporal clustering exacerbates user disruption and demands modernized SLAs."
    )

    card_y = Inches(1.65)
    card_h = Inches(4.55)
    card_w = Inches(3.75)

    # 3 Strategy Cards across the slide
    # Card 1: Temporal Autocorrelation & Burstiness
    create_card(slide, Inches(0.8), card_y, card_w, card_h)
    t1 = slide.shapes.add_textbox(Inches(1.0), card_y + Inches(0.2), card_w - Inches(0.4), Inches(0.4))
    tp1 = t1.text_frame.paragraphs[0]
    tp1.text = "1 · Temporal Dynamics"
    tp1.font.bold = True
    tp1.font.size = Pt(15)
    tp1.font.color.rgb = COLOR_ROYAL

    tx1 = slide.shapes.add_textbox(Inches(1.0), card_y + Inches(0.7), card_w - Inches(0.4), Inches(3.6))
    tf1 = tx1.text_frame
    tf1.word_wrap = True

    items1 = [
        ("Lag-1 Autocorrelation:", f"rho_1 = +{TEMPORAL['lag1_autocorrelation']:.3f} (p < 1e-15).\nConsecutive packets share network queuing states."),
        ("Disruption Clustering:", f"{TEMPORAL['total_bursts']} distinct spike bursts (>100 ms).\nMean burst length = {TEMPORAL['mean_burst_length']:.1f} packets."),
        ("Extreme Burst Duration:", f"Maximum burst = {TEMPORAL['max_burst_length']} consecutive packets.\nTranslates to ~21 seconds of continuous degradation!"),
        ("Engineering Reality:", "Spikes occur in clustered waves rather than memoryless Poisson arrivals.")
    ]
    for i, (hd, bd) in enumerate(items1):
        p = tf1.paragraphs[0] if i == 0 else tf1.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = f"• {hd}\n  "
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = COLOR_NAVY
        r2 = p.add_run()
        r2.text = bd
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_MUTED

    # Card 2: Real-World Disruption Impact
    create_card(slide, Inches(4.8), card_y, card_w, card_h)
    t2 = slide.shapes.add_textbox(Inches(5.0), card_y + Inches(0.2), card_w - Inches(0.4), Inches(0.4))
    tp2 = t2.text_frame.paragraphs[0]
    tp2.text = "2 · Disruption Impact"
    tp2.font.bold = True
    tp2.font.size = Pt(15)
    tp2.font.color.rgb = COLOR_ROYAL

    tx2 = slide.shapes.add_textbox(Inches(5.0), card_y + Inches(0.7), card_w - Inches(0.4), Inches(3.6))
    tf2 = tx2.text_frame
    tf2.word_wrap = True

    items2 = [
        ("Video Conferencing (Zoom/Teams):", "100 ms+ jitter bursts exceed playout buffers, causing frozen frames and clipped audio."),
        ("Esports & Cloud Gaming:", f"P90 ({EDA['p90']:.0f} ms) and P99 ({EDA['p99']:.0f} ms) trigger server desync, input drops, and missed tick-rates."),
        ("Financial Transactions:", "Deterministic latency bounds are violated; time-sensitive executions risk slippage."),
        ("Composite Quality Score:", f"17.1% packet loss + 64.0% lag spikes = only 29.8% of packets are on-time and healthy.")
    ]
    for i, (hd, bd) in enumerate(items2):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = f"• {hd}\n  "
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = COLOR_NAVY
        r2 = p.add_run()
        r2.text = bd
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_MUTED

    # Card 3: Actionable Solutions & SLA Reforms
    create_card(slide, Inches(8.8), card_y, card_w, card_h)
    t3 = slide.shapes.add_textbox(Inches(9.0), card_y + Inches(0.2), card_w - Inches(0.4), Inches(0.4))
    tp3 = t3.text_frame.paragraphs[0]
    tp3.text = "3 · Engineering Solutions"
    tp3.font.bold = True
    tp3.font.size = Pt(15)
    tp3.font.color.rgb = COLOR_ROYAL

    tx3 = slide.shapes.add_textbox(Inches(9.0), card_y + Inches(0.7), card_w - Inches(0.4), Inches(3.6))
    tf3 = tx3.text_frame
    tf3.word_wrap = True

    items3 = [
        ("Redefine ISP SLAs:", "Replace deceptive 'average ping' guarantees with Shifted Gamma tail percentiles (P95, P99) and P(X > 100 ms)."),
        ("Active Queue Management (AQM):", "Implement FQ-CoDel or Cake AQM on Wi-Fi access points to eliminate bufferbloat queuing spikes."),
        ("Adaptive Jitter Buffers:", "Real-time communication software must dynamically size jitter buffers up to ~850 ms during Wi-Fi bursts."),
        ("Project Methodology Success:", "Empirical analysis validates the 4-step framework proposed in Applied Probability course.")
    ]
    for i, (hd, bd) in enumerate(items3):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = f"• {hd}\n  "
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = COLOR_NAVY
        r2 = p.add_run()
        r2.text = bd
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_MUTED

    add_takeaway(
        slide,
        "Wi-Fi latency spikes exhibit temporal autocorrelation (rho_1 = 0.27); network engineering must replace average ping with Shifted Gamma tail metrics."
    )

# -----------------------------------------------------------------------------
# Main Generation
# -----------------------------------------------------------------------------
def main():
    print("Building solution presentation slides matching original theme...")
    build_slide_1()
    build_slide_2()
    build_slide_3()
    build_slide_4()
    build_slide_5()
    build_slide_6()
    build_slide_7()
    build_slide_8()

    output_pptx = "wifi_lag_spike_solution.pptx"
    prs.save(output_pptx)
    print(f"-> Successfully saved PowerPoint presentation: {output_pptx}")

    # Convert to PDF using LibreOffice
    print("Converting presentation to PDF via LibreOffice...")
    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", output_pptx]
    subprocess.run(cmd, check=True)
    print("-> Successfully converted to wifi_lag_spike_solution.pdf")

    # Render slides as PNGs to inspect
    print("Rendering slide pages to PNG for quality inspection...")
    subprocess.run(["pdftoppm", "-png", "-r", "150", "wifi_lag_spike_solution.pdf", "solution_slide"], check=True)
    print("-> Successfully rendered solution_slide-*.png")

if __name__ == '__main__':
    main()
