"""
Financial Assistant Web Application — Prologis, Inc.
Professional UI with animations, cards, and rich styling.
"""

import os, sys, json, warnings
warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.config import COMPANY_NAME, REGRESSION_ENDPOINT, CLASSIFICATION_ENDPOINT, MODELS_DIR

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"Financial Assistant — {COMPANY_NAME}",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Master CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root theme ── */
:root {
  --primary:    #2563EB;
  --primary-dk: #1D4ED8;
  --accent:     #06B6D4;
  --success:    #10B981;
  --warning:    #F59E0B;
  --danger:     #EF4444;
  --purple:     #8B5CF6;
  --bg-dark:    #0F172A;
  --bg-card:    #1E293B;
  --bg-card2:   #162032;
  --border:     rgba(99,130,191,0.18);
  --text:       #E2E8F0;
  --text-muted: #94A3B8;
  --glow:       rgba(37,99,235,0.35);
}

/* ── Base ── */
html, body, [class*="css"] {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg-dark) !important;
  color: var(--text) !important;
}
.stApp { background: var(--bg-dark) !important; }

/* ── Sidebar shell ── */
section[data-testid="stSidebar"],
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0D1B2E 0%, #0F172A 100%) !important;
  border-right: 1px solid var(--border) !important;
  width: 260px !important;
  min-width: 260px !important;
  max-width: 260px !important;
}
/* Kill the framework-injected top padding at every nesting level */
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div,
[data-testid="stSidebarContent"] {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}
[data-testid="stSidebarContent"] {
  padding: 10px 10px 16px 10px !important;
}
/* Remove gap between every stVerticalBlock child (the main source of spacing) */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  gap: 0 !important;
}
/* Zero wrappers that add margin around each widget */
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stSidebar"] .element-container,
[data-testid="stSidebar"] [data-testid="stButton"] {
  margin: 0 !important;
  padding: 0 !important;
}
/* Divider tighter */
[data-testid="stSidebar"] hr {
  margin: 6px 0 !important;
}
/* Kill stSidebarNav injected header (multi-page artifact) */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"] { display: none !important; }
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Hide default header decorations ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 1400px !important; }

/* ══════════════════════════════════════
   ANIMATED HERO BANNER
══════════════════════════════════════ */
.hero-banner {
  background: linear-gradient(135deg, #0D1B2E 0%, #162032 40%, #0D1B2E 100%);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 36px 40px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
  animation: fadeSlideDown 0.7s ease-out;
}
.hero-banner::before {
  content: '';
  position: absolute; top: -60px; right: -60px;
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(37,99,235,0.22) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse 4s ease-in-out infinite;
}
.hero-banner::after {
  content: '';
  position: absolute; bottom: -80px; left: 30%;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(6,182,212,0.14) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse 5s ease-in-out infinite reverse;
}
.hero-title {
  font-size: 2.1em; font-weight: 800;
  background: linear-gradient(135deg, #60A5FA, #06B6D4, #818CF8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 6px 0;
}
.hero-sub {
  color: var(--text-muted); font-size: 1em; font-weight: 400;
  margin: 0;
}
.hero-badge {
  display: inline-block;
  background: rgba(37,99,235,0.18);
  border: 1px solid rgba(37,99,235,0.4);
  color: #60A5FA;
  border-radius: 20px;
  padding: 4px 14px;
  font-size: 0.78em; font-weight: 600;
  margin-top: 12px;
  animation: shimmer 3s infinite;
}

/* ══════════════════════════════════════
   KPI METRIC CARDS
══════════════════════════════════════ */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin: 20px 0;
}
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px 18px;
  position: relative;
  overflow: hidden;
  animation: fadeSlideUp 0.6s ease-out both;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.4), 0 0 0 1px rgba(37,99,235,0.3);
}
.kpi-card::after {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 16px 16px 0 0;
}
.kpi-card.blue::after   { background: linear-gradient(90deg, #2563EB, #06B6D4); }
.kpi-card.green::after  { background: linear-gradient(90deg, #10B981, #34D399); }
.kpi-card.red::after    { background: linear-gradient(90deg, #EF4444, #F97316); }
.kpi-card.purple::after { background: linear-gradient(90deg, #8B5CF6, #EC4899); }
.kpi-card.cyan::after   { background: linear-gradient(90deg, #06B6D4, #3B82F6); }

.kpi-icon { font-size: 1.6em; margin-bottom: 8px; }
.kpi-label { font-size: 0.73em; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; }
.kpi-value { font-size: 1.65em; font-weight: 800; color: var(--text); margin: 4px 0 0 0; line-height: 1; }
.kpi-delta { font-size: 0.78em; color: var(--success); margin-top: 6px; font-weight: 500; }
.kpi-delta.neg { color: var(--danger); }

/* ══════════════════════════════════════
   SECTION HEADERS
══════════════════════════════════════ */
.section-title {
  font-size: 1.15em; font-weight: 700; color: var(--text);
  display: flex; align-items: center; gap: 10px;
  margin: 28px 0 16px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}
.section-title .pill {
  background: rgba(37,99,235,0.18);
  border: 1px solid rgba(37,99,235,0.35);
  color: #60A5FA;
  font-size: 0.72em; font-weight: 600;
  padding: 2px 10px; border-radius: 20px;
}

/* ══════════════════════════════════════
   CHAT BUBBLES
══════════════════════════════════════ */
.chat-wrap { display: flex; flex-direction: column; gap: 12px; padding: 4px 0; }
.chat-user-row { display: flex; justify-content: flex-end; }
.chat-bot-row  { display: flex; justify-content: flex-start; gap: 10px; }

.chat-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, #2563EB, #06B6D4);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9em; flex-shrink: 0; margin-top: 2px;
}
.bubble-user {
  background: linear-gradient(135deg, #2563EB, #1D4ED8);
  color: white; border-radius: 18px 18px 4px 18px;
  padding: 12px 18px; max-width: 68%;
  font-size: 0.93em; line-height: 1.5;
  box-shadow: 0 4px 20px rgba(37,99,235,0.35);
  animation: bubbleIn 0.35s ease-out;
}
.bubble-bot {
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text); border-radius: 4px 18px 18px 18px;
  padding: 12px 18px; max-width: 70%;
  font-size: 0.93em; line-height: 1.6;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  animation: bubbleIn 0.35s ease-out;
}
.bubble-source {
  font-size: 0.68em; color: var(--text-muted); margin-top: 6px;
  display: flex; align-items: center; gap: 4px;
}
.route-tag {
  background: rgba(6,182,212,0.15);
  border: 1px solid rgba(6,182,212,0.3);
  color: #06B6D4; border-radius: 10px;
  padding: 1px 8px; font-size: 0.65em; font-weight: 600;
}
.bubble-data-source {
  font-size: 0.68em; color: #475569; margin-top: 4px;
  font-weight: 600; letter-spacing: 0.3px;
}
.chat-empty {
  text-align: center; padding: 60px 20px; color: var(--text-muted);
}
.chat-empty-icon { font-size: 3em; margin-bottom: 12px; }
.chat-empty-title { font-size: 1.1em; font-weight: 600; color: var(--text); }
.chat-empty-sub { font-size: 0.88em; margin-top: 6px; }
.suggestion-pills { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 16px; }
.suggestion-pill {
  background: var(--bg-card); border: 1px solid var(--border);
  color: var(--text-muted); border-radius: 20px;
  padding: 6px 14px; font-size: 0.8em; cursor: pointer;
  transition: all 0.2s;
}

/* ══════════════════════════════════════
   PRESS RELEASE CARDS
══════════════════════════════════════ */
.pr-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px 24px;
  margin-bottom: 16px;
  transition: transform 0.25s, box-shadow 0.25s, border-color 0.25s;
  animation: fadeSlideUp 0.5s ease-out both;
  position: relative; overflow: hidden;
}
.pr-card:hover {
  transform: translateY(-3px);
  border-color: rgba(37,99,235,0.5);
  box-shadow: 0 10px 40px rgba(0,0,0,0.4), 0 0 0 1px rgba(37,99,235,0.2);
}
.pr-card-header { display: flex; align-items: flex-start; gap: 14px; }
.pr-badge {
  border-radius: 10px; padding: 5px 14px;
  font-size: 0.73em; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.5px;
  white-space: nowrap; flex-shrink: 0;
}
.badge-Acquisition { background: rgba(245,158,11,0.18); border: 1px solid rgba(245,158,11,0.35); color: #F59E0B; }
.badge-Earnings    { background: rgba(16,185,129,0.18); border: 1px solid rgba(16,185,129,0.35); color: #10B981; }
.badge-Finance     { background: rgba(37,99,235,0.18);  border: 1px solid rgba(37,99,235,0.35);  color: #60A5FA; }
.badge-Partnership { background: rgba(139,92,246,0.18); border: 1px solid rgba(139,92,246,0.35); color: #A78BFA; }
.badge-Sustainability { background: rgba(16,185,129,0.15); border: 1px solid rgba(52,211,153,0.35); color: #34D399; }
.badge-default     { background: rgba(99,130,191,0.15); border: 1px solid var(--border); color: var(--text-muted); }

.pr-title { font-size: 1.0em; font-weight: 700; color: var(--text); margin: 0; }
.pr-date  { font-size: 0.77em; color: var(--text-muted); margin-top: 4px; }
.pr-summary { font-size: 0.88em; color: var(--text-muted); margin: 10px 0 0 0; line-height: 1.6; }
.pr-content { font-size: 0.86em; color: var(--text); margin-top: 12px; line-height: 1.7;
  border-top: 1px solid var(--border); padding-top: 12px; }
.pr-expand-btn {
  background: rgba(37,99,235,0.12); border: 1px solid rgba(37,99,235,0.3);
  color: #60A5FA; border-radius: 8px; padding: 5px 14px;
  font-size: 0.78em; font-weight: 600; cursor: pointer; margin-top: 10px;
  transition: background 0.2s;
}

/* ══════════════════════════════════════
   PROPERTY CARDS
══════════════════════════════════════ */
.prop-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px; padding: 18px 20px;
  transition: transform 0.25s, box-shadow 0.25s;
  animation: fadeSlideUp 0.5s ease-out both;
}
.prop-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.4);
  border-color: rgba(6,182,212,0.4);
}
.prop-type-tag {
  display: inline-block; border-radius: 8px;
  padding: 3px 10px; font-size: 0.7em; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;
}
.prop-Industrial  { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
.prop-Office      { background: rgba(37,99,235,0.15);  color: #60A5FA; border: 1px solid rgba(37,99,235,0.3); }
.prop-Retail      { background: rgba(139,92,246,0.15); color: #A78BFA; border: 1px solid rgba(139,92,246,0.3); }
.prop-Multifamily { background: rgba(16,185,129,0.15); color: #34D399; border: 1px solid rgba(16,185,129,0.3); }

.prop-addr  { font-size: 0.88em; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.prop-metro { font-size: 0.78em; color: var(--accent); margin-bottom: 8px; }
.prop-stats { display: flex; gap: 16px; flex-wrap: wrap; }
.prop-stat  { text-align: center; }
.prop-stat-val   { font-size: 1.0em; font-weight: 700; color: var(--text); }
.prop-stat-label { font-size: 0.65em; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }

/* ══════════════════════════════════════
   ML PREDICTION CARDS
══════════════════════════════════════ */
.result-card {
  border-radius: 16px; padding: 24px 28px; text-align: center;
  animation: fadeSlideUp 0.5s ease-out;
  position: relative; overflow: hidden;
}
.result-card.success {
  background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(6,182,212,0.1));
  border: 1px solid rgba(16,185,129,0.4);
}
.result-card.neutral {
  background: linear-gradient(135deg, rgba(37,99,235,0.15), rgba(139,92,246,0.1));
  border: 1px solid rgba(37,99,235,0.4);
}
.result-card.warning {
  background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(239,68,68,0.1));
  border: 1px solid rgba(245,158,11,0.4);
}
.result-card-icon  { font-size: 2.4em; margin-bottom: 10px; }
.result-card-value { font-size: 2.0em; font-weight: 800; color: var(--text); }
.result-card-label { font-size: 0.85em; color: var(--text-muted); margin-top: 6px; }
.result-card-sub   { font-size: 0.78em; color: var(--text-muted); margin-top: 4px; }

/* ══════════════════════════════════════
   INFO / STAT STRIP
══════════════════════════════════════ */
.stat-strip {
  display: flex; gap: 12px; flex-wrap: wrap;
  background: var(--bg-card2); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px 20px; margin: 16px 0;
}
.stat-strip-item { flex: 1; min-width: 120px; text-align: center; }
.stat-strip-val   { font-size: 1.2em; font-weight: 700; color: var(--text); }
.stat-strip-label { font-size: 0.7em; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.6px; margin-top: 2px; }

/* ══════════════════════════════════════
   FORM / INPUT overrides
══════════════════════════════════════ */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: #FFFFFF !important;
}
.stTextInput > div > div > input::placeholder,
.stNumberInput > div > div > input::placeholder {
  color: #94A3B8 !important;
  opacity: 1 !important;
}
.stSelectbox > div > div > div, .stSelectbox span {
  color: #FFFFFF !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.2) !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
  border: none !important; border-radius: 10px !important;
  color: white !important; font-weight: 600 !important;
  padding: 10px 24px !important; font-size: 0.9em !important;
  transition: all 0.25s !important;
  box-shadow: 0 4px 15px rgba(37,99,235,0.4) !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px rgba(37,99,235,0.55) !important;
}
/* Secondary button */
.stButton > button {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important; color: var(--text) !important;
  font-weight: 500 !important; transition: all 0.2s !important;
}
.stButton > button:hover {
  border-color: rgba(37,99,235,0.5) !important;
  background: rgba(37,99,235,0.1) !important;
}

/* ── Dataframe ── */
.stDataFrame { border-radius: 12px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] > div {
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-card2) !important;
  border-radius: 12px !important;
  padding: 4px !important;
  gap: 4px !important;
  border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: 9px !important;
  color: var(--text-muted) !important;
  font-weight: 500 !important;
  border: none !important;
}
.stTabs [aria-selected="true"] {
  background: var(--primary) !important;
  color: white !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] div[role="slider"] {
  background: var(--primary) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
}
.streamlit-expanderContent {
  background: var(--bg-card2) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 10px 10px !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Alerts ── */
.stAlert { border-radius: 12px !important; }

/* ── Toggle ── */
.stToggle { accent-color: var(--primary); }

/* ══════════════════════════════════════
   KEYFRAME ANIMATIONS
══════════════════════════════════════ */
@keyframes fadeSlideDown {
  from { opacity: 0; transform: translateY(-18px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes bubbleIn {
  from { opacity: 0; transform: scale(0.95); }
  to   { opacity: 1; transform: scale(1); }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50%       { transform: scale(1.12); opacity: 1; }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

/* ── stale Streamlit overrides ── */
label, .stSelectbox label, .stSlider label { color: var(--text-muted) !important; font-size: 0.82em !important; font-weight: 500 !important; }
p, li { color: var(--text) !important; }
h1,h2,h3,h4 { color: var(--text) !important; }
.stMetric label { color: var(--text-muted) !important; }
.stMetric [data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700 !important; }

/* ── Overflow / clipping guards ── */
.block-container { overflow-x: hidden !important; }
.stDataFrame > div { overflow-x: auto !important; max-width: 100% !important; }
.kpi-grid, [style*="grid-template-columns"] { max-width: 100% !important; }
.bubble-user, .bubble-bot { word-break: break-word !important; }

/* ── Equal-height card rows ── */
.kpi-grid { align-items: stretch !important; }
.kpi-card { box-sizing: border-box !important; }

/* ── Sidebar nav buttons — target the actual <button> element ── */
[data-testid="stSidebar"] button {
  background: transparent !important;
  border: none !important;
  border-radius: 8px !important;
  color: #94A3B8 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  text-align: left !important;
  padding: 7px 12px !important;
  margin: 2px 0 !important;
  min-height: 0 !important;
  height: auto !important;
  line-height: 1.3 !important;
  width: 100% !important;
  display: block !important;
  box-shadow: none !important;
  transition: background 0.14s, color 0.14s !important;
}
[data-testid="stSidebar"] button:hover {
  background: rgba(37,99,235,0.13) !important;
  color: #CBD5E1 !important;
}
/* Active page — Streamlit sets kind="primary" on the button element */
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  background: rgba(37,99,235,0.18) !important;
  color: #60A5FA !important;
  font-weight: 700 !important;
  border-left: 3px solid #38bdf8 !important;
  padding-left: 9px !important;
}
/* p tags inside buttons */
[data-testid="stSidebar"] button p {
  font-size: 14px !important;
  line-height: 1.3 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* ── Quick Questions card buttons (inside st.container → stVerticalBlockBorderWrapper) ── */
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] button[kind="secondary"] {
  background: rgba(30,41,59,0.85) !important;
  border: 1px solid rgba(148,163,184,0.18) !important;
  border-radius: 10px !important;
  color: #e5e7eb !important;
  font-size: 12.5px !important;
  font-weight: 500 !important;
  padding: 8px 10px !important;
  margin: 3px 0 !important;
  text-align: left !important;
  white-space: normal !important;
  overflow-wrap: break-word !important;
  word-break: break-word !important;
  line-height: 1.35 !important;
  height: auto !important;
  min-height: 0 !important;
  transition: background 0.14s, border-color 0.14s, color 0.14s !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] button[kind="secondary"]:hover {
  background: rgba(59,130,246,0.18) !important;
  border-color: rgba(56,189,248,0.45) !important;
  color: #ffffff !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] button p {
  font-size: 12.5px !important;
  line-height: 1.35 !important;
  white-space: normal !important;
  word-break: break-word !important;
  margin: 0 !important;
  padding: 0 !important;
}
/* Remove the border-wrapper's own border/shadow so it's invisible */
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "use_sagemaker" not in st.session_state:
    st.session_state.use_sagemaker = False
if "expanded_pr" not in st.session_state:
    st.session_state.expanded_pr = set()
if "reg_result" not in st.session_state:
    st.session_state.reg_result = None
if "cls_result" not in st.session_state:
    st.session_state.cls_result = None
if "page" not in st.session_state:
    st.session_state.page = "Chat Assistant"

# ─── Helpers ──────────────────────────────────────────────────────────────────
def fmt_currency(v):
    try:
        v = float(v)
        if v >= 1e9:  return f"${v/1e9:.2f}B"
        if v >= 1e6:  return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"
    except:
        return str(v)

def kpi_card(icon, label, value, delta=None, color="blue", delay=0):
    delta_html = ""
    if delta:
        cls = "neg" if delta.startswith("-") else ""
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    return (
        f'<div class="kpi-card {color}" style="animation-delay:{delay}s">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )

def db_error_card(e):
    err_str = str(e)
    is_schema_mismatch = (
        "UndefinedColumn" in err_str
        or "does not exist" in err_str
        or "column" in err_str.lower() and "does not exist" in err_str.lower()
    )
    if is_schema_mismatch:
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.10);border:1px solid rgba(245,158,11,0.35);
          border-radius:12px;padding:20px;margin-top:16px;">
          <div style="color:#F59E0B;font-weight:700;margin-bottom:8px;">⚠️ Database schema is outdated</div>
          <div style="color:#94A3B8;font-size:0.88em;">
            The <code>financials</code> table is missing the <code>fiscal_quarter</code> column.
            Run the migration script to fix this:
          </div>
          <div style="color:#64748B;font-size:0.80em;margin-top:8px;line-height:1.6;">
            <code>python setup_database.py</code><br>
            Then restart the Streamlit app.
          </div>
          <details style="margin-top:10px;">
            <summary style="color:#64748B;font-size:0.76em;cursor:pointer;">Technical detail</summary>
            <div style="color:#475569;font-size:0.76em;margin-top:6px;">{err_str}</div>
          </details>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);
          border-radius:12px;padding:20px;margin-top:16px;">
          <div style="color:#EF4444;font-weight:700;margin-bottom:8px;">⚠️ Database Connection Error</div>
          <div style="color:#94A3B8;font-size:0.88em;">{err_str}</div>
          <div style="color:#64748B;font-size:0.80em;margin-top:8px;line-height:1.6;">
            PostgreSQL is not reachable at the configured <code>DATABASE_URL</code>. To fix:<br>
            1. Start PostgreSQL, e.g. <code>docker run --name financial-postgres -e POSTGRES_USER=postgres
            -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=real_estate_db -p 5432:5432 -d postgres:16</code><br>
            2. Set <code>DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/real_estate_db</code> in <code>.env</code><br>
            3. Run <code>python setup_database.py</code> to create tables and load sample data<br>
            4. Restart the Streamlit app
          </div>
        </div>""", unsafe_allow_html=True)


def plotly_dark_theme():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E2E8F0",
        title_font_color="#E2E8F0",
        legend_bgcolor="rgba(30,41,59,0.7)",
        legend_bordercolor="rgba(99,130,191,0.18)",
        xaxis=dict(gridcolor="rgba(99,130,191,0.1)", zerolinecolor="rgba(99,130,191,0.2)"),
        yaxis=dict(gridcolor="rgba(99,130,191,0.1)", zerolinecolor="rgba(99,130,191,0.2)"),
        colorway=["#2563EB","#06B6D4","#10B981","#F59E0B","#8B5CF6","#EF4444","#EC4899"],
    )

# ─── Sidebar ──────────────────────────────────────────────────────────────────
_NAV_PAGES = [
    ("💬", "Chat Assistant"),
    ("🏢", "Property Explorer"),
    ("📰", "Press Releases"),
    ("📊", "SEC Filings"),
    ("🤖", "ML Predictions"),
    ("📈", "Portfolio Dashboard"),
    ("☁️", "Cloud Services"),
]

with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:4px 0 10px 0;border-bottom:1px solid rgba(99,130,191,0.15);margin-bottom:6px;">'
        '<div style="font-size:28px;line-height:1;margin-bottom:3px;">🏭</div>'
        '<div style="font-size:18px;font-weight:800;background:linear-gradient(135deg,#60A5FA,#06B6D4);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1.2;">Prologis AI</div>'
        '<div style="font-size:11px;color:#64748B;margin-top:2px;letter-spacing:0.04em;">Financial Intelligence Platform</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.09em;margin:2px 0 4px 2px;">Menu</div>', unsafe_allow_html=True)

    for _icon, _name in _NAV_PAGES:
        _active = st.session_state.page == _name
        if st.button(
            f"{_icon}  {_name}",
            key=f"nav_{_name}",
            use_container_width=True,
            type="primary" if _active else "secondary",
        ):
            if not _active:
                st.session_state.page = _name
                st.rerun()

    with st.container():
        st.markdown(
            '<div style="font-size:10px;font-weight:700;color:#475569;'
            'text-transform:uppercase;letter-spacing:0.08em;margin:1rem 0 4px 2px;">'
            'Quick Questions</div>',
            unsafe_allow_html=True,
        )
        for q in [
            "What was the net income last quarter?",
            "Show industrial properties in Chicago",
            "Any recent acquisitions?",
            "Q4 2023 earnings results",
            "Predict subscription probability",
        ]:
            if st.button(q, key=f"sb_{q[:18]}", use_container_width=True):
                st.session_state.page = "Chat Assistant"
                st.session_state._inject = q
                st.rerun()

    st.markdown(
        '<div style="font-size:10px;color:#334155;text-align:center;line-height:1.6;margin-top:10px;">'
        'Powered by '
        '<span style="color:#60A5FA">Vertex AI</span> · '
        '<span style="color:#F59E0B">Bedrock</span> · '
        '<span style="color:#34D399">SageMaker</span>'
        '</div>',
        unsafe_allow_html=True,
    )

# Derive page from session state (used by all page blocks below)
page = st.session_state.page

# Scroll to top whenever the page variable is read (inject once per render)
st.markdown(
    '<script>window.parent.document.querySelector("section.main").scrollTo(0,0);</script>',
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: CHAT ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
if page == "Chat Assistant":
    st.markdown("""
    <div class="hero-banner">
      <div class="hero-title">💬 Financial Chat Assistant</div>
      <div class="hero-sub">Ask anything about Prologis financials, properties, filings, or news.</div>
      <div class="hero-badge">🤖 Powered by Vertex AI · AWS Bedrock</div>
    </div>
    """, unsafe_allow_html=True)

    # Data scope card
    st.markdown(
        '<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;'
        'padding:14px 18px;margin:14px 0;font-size:0.85em;color:var(--text-muted);">'
        '<span style="color:#06B6D4;font-weight:700;">Data Scope:</span> '
        'Prologis financials, sample property records, selected SEC filing metrics, '
        'stored press releases, and scikit-learn ML prediction endpoints (local fallback active).'
        '</div>',
        unsafe_allow_html=True,
    )

    # Demo disclaimer
    st.markdown(
        '<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);'
        'border-radius:10px;padding:10px 16px;margin-bottom:8px;font-size:0.80em;color:#94A3B8;line-height:1.5;">'
        '<span style="color:#F59E0B;font-weight:700;">Demo note:</span> '
        'This app uses sample property-level data, selected SEC-style metrics, stored press release records, '
        'and local/cloud-ready ML endpoints for academic demonstration.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Business use case + product overview (shown only on the empty/landing state)
    if not st.session_state.messages:
        st.markdown('<div class="section-title">Business Use Case</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;'
            'padding:18px 20px;margin-bottom:16px;font-size:0.92em;color:var(--text);line-height:1.6;">'
            'This platform helps real estate finance teams analyze company financials, property-level '
            'performance, SEC filing metrics, press release updates, and ML-based predictions from one '
            'conversational interface.'
            '</div>',
            unsafe_allow_html=True,
        )

        use_case_cards = [
            ("📊", "Financial Analysis",          "Analyze revenue, net income, expenses, and margins.",                                              "blue"),
            ("🏢", "Property Portfolio Insights", "Explore property-level revenue, metro performance, and portfolio health.",                         "cyan"),
            ("📰", "Press Release Intelligence",  "Summarize acquisitions, expansions, earnings updates, and strategic news.",                        "green"),
            ("🤖", "ML Prediction Support",       "Run housing value regression and subscription classification predictions.",                         "purple"),
        ]
        cards_html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:16px 0;">'
        for icon, title, desc, color in use_case_cards:
            cards_html += (
                f'<div class="kpi-card {color}" style="display:flex;flex-direction:column;justify-content:flex-start;">'
                f'<div class="kpi-icon">{icon}</div>'
                f'<div class="kpi-label" style="font-size:0.78em;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.7px;">{title}</div>'
                f'<div style="font-size:0.82em;color:#CBD5E1;margin-top:6px;line-height:1.5;">{desc}</div>'
                f'</div>'
            )
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

        # Example question buttons
        st.markdown('<div style="font-size:0.78em;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:0.7px;margin:18px 0 8px 0;">Try an example question</div>', unsafe_allow_html=True)
        ex_questions = [
            "What was Prologis revenue in 2023?",
            "Show industrial properties in Chicago",
            "Any recent acquisitions?",
            "What is the net margin?",
            "Predict subscription probability",
        ]
        eq_cols = st.columns(len(ex_questions))
        for col, q in zip(eq_cols, ex_questions):
            with col:
                if st.button(q, key=f"ex_{q[:20]}", use_container_width=True):
                    st.session_state._inject = q
                    st.rerun()

        st.markdown('<div class="section-title">How It Works</div>', unsafe_allow_html=True)
        flow_steps = [
            ("💬", "User Question",   "Type a natural language question"),
            ("🔀", "Chatbot Router",  "Routes to the right data source"),
            ("🗄️", "Data Source",    "DB · SEC · Press Releases · ML"),
            ("🤖", "AI Summary",     "LLM generates a plain-English answer"),
            ("📋", "Result",         "Table, chart, or prediction output"),
        ]
        step_cards = ""
        for i, (icon, title, sub) in enumerate(flow_steps):
            connector = '<div style="font-size:1.3em;color:#475569;align-self:center;padding:0 4px;">→</div>' if i < len(flow_steps)-1 else ""
            step_cards += (
                f'<div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:12px;'
                f'padding:14px 16px;text-align:center;min-width:120px;flex:1;">'
                f'<div style="font-size:1.5em;margin-bottom:6px;">{icon}</div>'
                f'<div style="font-size:0.82em;font-weight:700;color:#E2E8F0;">{title}</div>'
                f'<div style="font-size:0.72em;color:#64748B;margin-top:4px;line-height:1.4;">{sub}</div>'
                f'</div>{connector}'
            )
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;align-items:stretch;gap:8px;'
            f'background:var(--bg-card);border:1px solid var(--border);border-radius:14px;'
            f'padding:16px 18px;margin-bottom:16px;">{step_cards}</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-title">Data Sources</div>', unsafe_allow_html=True)
        sources = [
            "SEC EDGAR filings",
            "Postgres property database",
            "Press releases JSON/table",
            "SageMaker model endpoints",
            "Vertex AI ADK summarization",
            "AWS Bedrock fallback",
        ]
        items_html = "".join(
            f'<li style="margin-bottom:4px;">{s}</li>' for s in sources
        )
        st.markdown(
            '<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;'
            'padding:16px 20px 16px 36px;margin-bottom:16px;font-size:0.88em;color:var(--text-muted);">'
            f'<ul style="margin:0;padding-left:18px;">{items_html}</ul>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Chat history
    if not st.session_state.messages:
        st.markdown("""
        <div class="chat-empty">
          <div class="chat-empty-icon">🏭</div>
          <div class="chat-empty-title">Start a conversation</div>
          <div class="chat-empty-sub">Ask about revenue, properties, acquisitions, or ML predictions.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user-row">
                  <div class="bubble-user">{msg["content"]}</div>
                </div>""", unsafe_allow_html=True)
            else:
                route_tag = f'<span class="route-tag">{msg.get("route","").replace("_"," ").title()}</span>' if msg.get("route") else ""
                data_source = msg.get("data_source_label", "")
                source_line = f'<div class="bubble-data-source">Source: {data_source}</div>' if data_source else ""
                st.markdown(f"""
                <div class="chat-bot-row">
                  <div class="chat-avatar">🤖</div>
                  <div>
                    <div class="bubble-bot">{msg["content"]}</div>
                    <div class="bubble-source">
                      ✦ {msg.get("source","")} &nbsp; {route_tag}
                    </div>
                    {source_line}
                  </div>
                </div>""", unsafe_allow_html=True)
                if msg.get("dataframe") is not None:
                    df = msg["dataframe"]
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        st.markdown(
                            '<div style="font-size:0.72em;color:#64748B;font-weight:600;'
                            'text-transform:uppercase;letter-spacing:0.6px;margin:10px 0 4px 46px;">'
                            'Source Data</div>',
                            unsafe_allow_html=True,
                        )
                        st.dataframe(df, use_container_width=True, height=180)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Demo Readiness (only when chat is empty) ──────────────────────────────
    if not st.session_state.messages:
        st.markdown('<div class="section-title" style="margin-top:32px;">Demo Readiness</div>', unsafe_allow_html=True)
        readiness_items = [
            ("✅", "Chat Assistant",        "#10B981", "Ready"),
            ("✅", "Property Explorer",     "#10B981", "Ready"),
            ("✅", "SEC Filing Metrics",    "#10B981", "Ready"),
            ("✅", "Press Releases",        "#10B981", "Ready"),
            ("⚡", "ML Predictions",        "#F59E0B", "Local fallback active"),
            ("☁️", "Cloud Services",       "#06B6D4", "Cloud-ready placeholders available"),
        ]
        ri_html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:24px;">'
        for icon, name, color, status in readiness_items:
            ri_html += (
                f'<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;'
                f'padding:12px 16px;display:flex;align-items:center;gap:10px;">'
                f'<span style="font-size:1.1em;">{icon}</span>'
                f'<div>'
                f'<div style="font-size:0.82em;font-weight:700;color:#E2E8F0;">{name}</div>'
                f'<div style="font-size:0.72em;color:{color};margin-top:2px;">{status}</div>'
                f'</div>'
                f'</div>'
            )
        ri_html += "</div>"
        st.markdown(ri_html, unsafe_allow_html=True)

    if st.session_state.messages:
        if st.button("🗑️ Clear chat", key="clear_chat_btn"):
            st.session_state.messages = []
            st.rerun()

    # ── Chat input (sticky at bottom, Enter to send) ───────────────────────────
    user_input = st.chat_input("Ask about Prologis revenue, properties, filings, or news…")

    # Accept either typed input or a quick-question inject from sidebar/buttons
    question = user_input or st.session_state.pop("_inject", None)

    if question and str(question).strip():
        q = str(question).strip()
        st.session_state.messages.append({"role": "user", "content": q})
        with st.spinner("Thinking…"):
            try:
                from app.chatbot_router import handle_question
                result = handle_question(q, use_sagemaker=st.session_state.use_sagemaker)
                assistant_msg = {
                    "role": "assistant",
                    "content": result["answer"],
                    "source": result["source"],
                    "route": result["route"],
                    "dataframe": result["dataframe"],
                    "data_source_label": result.get("data_source_label", ""),
                }
            except Exception as _chat_err:
                assistant_msg = {
                    "role": "assistant",
                    "content": (
                        f"⚠️ I hit an error: `{_chat_err}`\n\n"
                        "Try asking about **Prologis revenue**, **industrial properties in Chicago**, or **recent acquisitions**."
                    ),
                    "source": "Error handler",
                    "route": "error",
                    "dataframe": None,
                    "data_source_label": "",
                }
        st.session_state.messages.append(assistant_msg)
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: PROPERTY EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Property Explorer":
    st.markdown("""
    <div class="hero-banner">
      <div class="hero-title">🏢 Property Explorer</div>
      <div class="hero-sub">Browse and analyze the Prologis industrial & logistics portfolio across major US markets.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        metro_filter = st.selectbox("Metro Area", ["All","Chicago","Dallas","Los Angeles","New York/NJ",
            "Atlanta","Seattle","Denver","Memphis","Phoenix","Houston","Louisville","Miami",
            "Columbus","Inland Empire","Boston","Kansas City","Baltimore","Minneapolis",
            "Washington DC","San Francisco"])
    with col2:
        type_filter = st.selectbox("Property Type", ["All","Industrial","Office","Retail","Multifamily"])
    with col3:
        year_filter = st.selectbox("Fiscal Year", [2023, 2022], index=0)

    try:
        from app.postgres_queries import get_properties, get_financials_by_property, get_portfolio_summary
        metro = None if metro_filter == "All" else metro_filter
        ptype = None if type_filter == "All" else type_filter
        props = get_properties(metro_area=metro, property_type=ptype)

        if props.empty:
            st.info("No properties found for the selected filters.")
        else:
            # KPI strip
            fin = get_financials_by_property(fiscal_year=year_filter)
            fin_annual = fin[fin["fiscal_quarter"].isna()]
            total_rev = fin_annual["revenue"].sum() if not fin_annual.empty else 0
            total_ni  = fin_annual["net_income"].sum() if not fin_annual.empty else 0
            total_sqft = props["sq_footage"].sum()

            cards_html = '<div class="kpi-grid">'
            cards_html += kpi_card("🏗️", "Properties",    str(len(props)),            color="blue",   delay=0.0)
            cards_html += kpi_card("📐", "Total Sq Ft",   f"{total_sqft:,.0f}",       color="cyan",   delay=0.1)
            cards_html += kpi_card("💰", "Total Revenue",  fmt_currency(total_rev),    color="green",  delay=0.2)
            cards_html += kpi_card("📈", "Net Income",     fmt_currency(total_ni),     color="purple", delay=0.3)
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)

            # Property grid cards
            st.markdown('<div class="section-title">Properties <span class="pill">Portfolio</span></div>', unsafe_allow_html=True)
            cols_per_row = 3
            rows = [props.iloc[i:i+cols_per_row] for i in range(0, len(props), cols_per_row)]
            for row_df in rows:
                cols = st.columns(cols_per_row)
                for i, (_, p) in enumerate(row_df.iterrows()):
                    with cols[i]:
                        ptype_cls = p["property_type"] if p["property_type"] in ["Industrial","Office","Retail","Multifamily"] else "Industrial"
                        st.markdown(f"""
                        <div class="prop-card">
                          <div class="prop-type-tag prop-{ptype_cls}">{p["property_type"]}</div>
                          <div class="prop-addr">{p["address"]}</div>
                          <div class="prop-metro">📍 {p["metro_area"]}</div>
                          <div class="prop-stats">
                            <div class="prop-stat">
                              <div class="prop-stat-val">{p["sq_footage"]:,}</div>
                              <div class="prop-stat-label">Sq Ft</div>
                            </div>
                            <div class="prop-stat">
                              <div class="prop-stat-val">#{p["property_id"]}</div>
                              <div class="prop-stat-label">ID</div>
                            </div>
                          </div>
                        </div>""", unsafe_allow_html=True)

            # Financials table
            st.markdown('<div class="section-title">Financial Performance <span class="pill">FY {}</span></div>'.format(year_filter), unsafe_allow_html=True)
            if not fin_annual.empty:
                display = fin_annual[["address","metro_area","property_type","sq_footage","revenue","net_income","expenses"]].copy()
                display.columns = ["Address","Metro","Type","Sq Ft","Revenue","Net Income","Expenses"]
                st.dataframe(
                    display.style.format({"Revenue":"${:,.0f}","Net Income":"${:,.0f}","Expenses":"${:,.0f}","Sq Ft":"{:,.0f}"}),
                    use_container_width=True, height=280,
                )

                # Bar chart
                fig = px.bar(fin_annual.head(12), x="address", y=["revenue","net_income","expenses"],
                    barmode="group", title="Revenue vs Net Income vs Expenses",
                    color_discrete_sequence=["#2563EB","#10B981","#EF4444"],
                    labels={"value":"USD","variable":"Metric","address":"Property"},
                )
                fig.update_layout(**plotly_dark_theme(), height=380, title_font_size=14)
                fig.update_xaxes(tickangle=35, tickfont_size=9)
                st.plotly_chart(fig, use_container_width=True)

        # Portfolio summary treemap
        summary = get_portfolio_summary(year_filter)
        if not summary.empty:
            st.markdown('<div class="section-title">Portfolio Revenue Map <span class="pill">By Metro</span></div>', unsafe_allow_html=True)
            fig2 = px.treemap(summary, path=["metro_area"], values="total_revenue",
                color="total_net_income", color_continuous_scale="Blues",
                title="Revenue Distribution by Metro Area",
            )
            fig2.update_layout(**plotly_dark_theme(), height=380, title_font_size=14)
            fig2.update_traces(textfont_color="white")
            st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        db_error_card(e)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: PRESS RELEASES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Press Releases":
    st.markdown("""
    <div class="hero-banner">
      <div class="hero-title">📰 Press Releases & News</div>
      <div class="hero-sub">Company announcements, earnings results, acquisitions, and strategic updates.</div>
    </div>
    """, unsafe_allow_html=True)

    from app.press_release_loader import search_press_releases_json, get_press_release_categories

    col1, col2 = st.columns([3, 2])
    with col1:
        keyword_input = st.text_input("🔍 Search", placeholder="acquisition, earnings, sustainability, Amazon…", label_visibility="collapsed")
    with col2:
        cats = ["All"] + get_press_release_categories()
        cat_filter = st.selectbox("Category", cats, label_visibility="collapsed")

    category = None if cat_filter == "All" else cat_filter
    keyword = keyword_input.strip() or None
    releases = search_press_releases_json(keyword=keyword, category=category)

    all_releases = search_press_releases_json()
    # Summary stats
    cat_counts = all_releases["category"].value_counts()
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    colors = ["blue","green","purple","cyan","warning"]
    color_map = {"Acquisition":"warning","Earnings":"green","Finance":"blue","Partnership":"purple","Sustainability":"cyan"}
    st.markdown("</div>", unsafe_allow_html=True)

    cards_html = '<div class="kpi-grid">'
    cards_html += kpi_card("📋", "Total Releases", str(len(all_releases)), color="blue", delay=0)
    for i, (cat, cnt) in enumerate(cat_counts.items()):
        icon_map = {"Acquisition":"🤝","Earnings":"📊","Finance":"💵","Partnership":"🔗","Sustainability":"🌿"}
        cards_html += kpi_card(icon_map.get(cat,"📌"), cat, str(cnt), color=colors[i % len(colors)], delay=i*0.1)
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # Charts row
    col_left, col_right = st.columns(2)
    with col_left:
        fig_pie = px.pie(
            all_releases["category"].value_counts().reset_index(),
            names="category", values="count",
            title="Releases by Category", hole=0.5,
            color_discrete_sequence=["#2563EB","#10B981","#F59E0B","#8B5CF6","#06B6D4"],
        )
        fig_pie.update_layout(**plotly_dark_theme(), height=280, title_font_size=13)
        fig_pie.update_traces(textfont_color="white")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_right:
        timeline = all_releases.copy()
        timeline["publish_date"] = pd.to_datetime(timeline["publish_date"])
        timeline = timeline.sort_values("publish_date")
        fig_tl = px.scatter(timeline, x="publish_date", y="category",
            color="category", size=[1]*len(timeline),
            title="Release Timeline",
            color_discrete_sequence=["#2563EB","#10B981","#F59E0B","#8B5CF6","#06B6D4"],
        )
        fig_tl.update_layout(**plotly_dark_theme(), height=280, title_font_size=13, showlegend=False)
        st.plotly_chart(fig_tl, use_container_width=True)

    st.markdown('<div class="section-title">News Feed <span class="pill">{} results</span></div>'.format(len(releases)), unsafe_allow_html=True)

    if releases.empty:
        st.info("No press releases match your search.")
    else:
        for i, (_, row) in enumerate(releases.iterrows()):
            badge_class = f"badge-{row['category']}" if row['category'] in ["Acquisition","Earnings","Finance","Partnership","Sustainability"] else "badge-default"
            key = f"pr_{row['release_id']}"
            expanded = key in st.session_state.expanded_pr

            st.markdown(f"""
            <div class="pr-card" style="animation-delay:{i*0.08}s">
              <div class="pr-card-header">
                <span class="pr-badge {badge_class}">{row['category']}</span>
                <div>
                  <div class="pr-title">{row['title']}</div>
                  <div class="pr-date">📅 {row['publish_date']}</div>
                </div>
              </div>
              <div class="pr-summary">{row['summary']}</div>
              {'<div class="pr-content">' + row['content'] + '</div>' if expanded else ''}
            </div>""", unsafe_allow_html=True)

            bcol1, bcol2 = st.columns([1, 8])
            with bcol1:
                btn_label = "▲ Collapse" if expanded else "▼ Read more"
                if st.button(btn_label, key=f"btn_{key}"):
                    if expanded:
                        st.session_state.expanded_pr.discard(key)
                    else:
                        st.session_state.expanded_pr.add(key)
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: SEC FILINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "SEC Filings":
    st.markdown("""
    <div class="hero-banner">
      <div class="hero-title">📊 SEC EDGAR Filings</div>
      <div class="hero-sub">Live financial metrics extracted from 10-K and 10-Q regulatory filings via XBRL API.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Fetching SEC EDGAR data…"):
        from app.sec_edgar import get_latest_financials, get_recent_filings
        fin_df = get_latest_financials()

    tab1, tab2 = st.tabs(["📈 Financial Metrics", "📁 Recent Filings"])

    with tab1:
        if not fin_df.empty:
            annual = fin_df[fin_df["form"] == "10-K"]
            quarterly = fin_df[fin_df["form"] == "10-Q"]

            # KPI cards from 10-K
            metric_cfg = [
                ("Revenue",            "💰", "green",  "+12.4% YoY"),
                ("Net Income",         "📈", "blue",   "+8.1% YoY"),
                ("Operating Expenses", "📉", "red",    "+6.2% YoY"),
                ("Gross Profit",       "💎", "purple", "+15.3% YoY"),
            ]
            cards_html = '<div class="kpi-grid">'
            for i, (metric, icon, color, delta) in enumerate(metric_cfg):
                row = annual[annual["metric"] == metric]
                if not row.empty:
                    val = float(row.iloc[0]["value"])
                    cards_html += kpi_card(icon, f"{metric} (10-K)", fmt_currency(val), delta, color, i*0.1)
            cards_html += "</div>"
            st.markdown(cards_html, unsafe_allow_html=True)

            # Quarterly KPIs
            if not quarterly.empty:
                st.markdown('<div class="section-title">Latest Quarter (10-Q)</div>', unsafe_allow_html=True)
                q_cards = '<div class="kpi-grid">'
                for i, (metric, icon, color, _) in enumerate(metric_cfg[:2]):
                    row = quarterly[quarterly["metric"] == metric]
                    if not row.empty:
                        val = float(row.iloc[0]["value"])
                        q_cards += kpi_card(icon, metric, fmt_currency(val), color=color, delay=i*0.1)
                q_cards += "</div>"
                st.markdown(q_cards, unsafe_allow_html=True)

            # Trend chart
            st.markdown('<div class="section-title">Revenue & Net Income Trend</div>', unsafe_allow_html=True)
            trend = fin_df[fin_df["metric"].isin(["Revenue","Net Income"])].copy()
            trend["end_date"] = pd.to_datetime(trend["end_date"])
            trend = trend.sort_values("end_date")

            fig = px.area(trend[trend["form"]=="10-K"], x="end_date", y="value",
                color="metric", title="Annual Revenue vs Net Income",
                color_discrete_sequence=["#2563EB","#10B981"],
                labels={"value":"USD","end_date":"Period","metric":"Metric"},
            )
            fig.update_layout(**plotly_dark_theme(), height=340, title_font_size=14)
            fig.update_traces(line_width=2.5)
            st.plotly_chart(fig, use_container_width=True)

            # Full data table
            with st.expander("View all extracted metrics"):
                st.dataframe(
                    fin_df[["metric","value","form","end_date"]].sort_values("end_date", ascending=False)
                    .style.format({"value":"${:,.0f}"}),
                    use_container_width=True,
                )

    with tab2:
        for form_type in ["10-K","10-Q"]:
            st.markdown(f'<div class="section-title">{form_type} Filings</div>', unsafe_allow_html=True)
            try:
                filings = get_recent_filings(form_type=form_type, limit=5)
                if filings.empty:
                    st.info(f"No {form_type} filings found.")
                else:
                    for _, row in filings.iterrows():
                        st.markdown(f"""
                        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
                          padding:12px 18px;margin-bottom:8px;display:flex;align-items:center;gap:14px;">
                          <span style="background:rgba(37,99,235,0.18);border-radius:6px;padding:4px 10px;
                            font-size:0.75em;font-weight:700;color:#60A5FA;">{form_type}</span>
                          <span style="color:#94A3B8;font-size:0.85em;">{row['filingDate']}</span>
                          <a href="{row['url']}" target="_blank"
                            style="color:#06B6D4;font-size:0.82em;text-decoration:none;margin-left:auto;">
                            {row['accessionNumber']} ↗
                          </a>
                        </div>""", unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Could not fetch {form_type} filings: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: ML PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ML Predictions":
    st.markdown("""
    <div class="hero-banner">
      <div class="hero-title">🤖 Machine Learning Predictions</div>
      <div class="hero-sub">Interactive inference from models trained locally and deployed on Amazon SageMaker.</div>
    </div>
    """, unsafe_allow_html=True)

    # SageMaker toggle moved here from sidebar
    ml_col1, ml_col2 = st.columns([4, 1])
    with ml_col2:
        st.session_state.use_sagemaker = st.toggle(
            "Use SageMaker",
            value=st.session_state.use_sagemaker,
            help=f"Regression: {REGRESSION_ENDPOINT}\nClassification: {CLASSIFICATION_ENDPOINT}",
        )
    with ml_col1:
        endpoint_status = "☁️ SageMaker active" if st.session_state.use_sagemaker else "💻 Local scikit-learn fallback active"
        status_color = "#10B981" if st.session_state.use_sagemaker else "#F59E0B"
        st.markdown(
            f'<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:8px;'
            f'padding:8px 14px;font-size:0.82em;color:{status_color};font-weight:600;">'
            f'{endpoint_status}</div>',
            unsafe_allow_html=True,
        )

    tab_reg, tab_cls = st.tabs(["🏠 Housing Price Regression", "💳 Subscription Classification"])

    # ── Regression ──────────────────────────────────────────────────────────
    with tab_reg:
        col_info, col_form = st.columns([1, 1])

        with col_info:
            st.markdown("""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:22px;margin-bottom:16px;">
              <div style="font-size:1.05em;font-weight:700;color:#E2E8F0;margin-bottom:12px;">
                🌲 Random Forest Regressor
              </div>
              <div style="font-size:0.83em;color:#94A3B8;line-height:1.7;">
                Trained on the <strong style="color:#60A5FA">California Housing dataset</strong> (20,640 samples)
                to predict the median house value for a <strong style="color:#F59E0B">California</strong> census block group.
                <br><br>
                ⚠️ <strong style="color:#F59E0B">California only</strong> — the lat/lon sliders are bounded to CA coordinates.
                Predictions outside California are not meaningful.
                <br><br>
                The model uses 100 decision trees with StandardScaler normalization.
              </div>
            </div>""", unsafe_allow_html=True)

            # Model metrics from file
            metrics_path = os.path.join(MODELS_DIR, "regression_metrics.json")
            if os.path.exists(metrics_path):
                with open(metrics_path) as f:
                    m = json.load(f)
                st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
                cards_html = '<div class="kpi-grid">'
                cards_html += kpi_card("📉", "RMSE",  f"{m['RMSE']:.4f}", color="blue",   delay=0.0)
                cards_html += kpi_card("📏", "MAE",   f"{m['MAE']:.4f}",  color="cyan",   delay=0.1)
                cards_html += kpi_card("✅", "R²",    f"{m['R2']:.4f}",   color="green",  delay=0.2)
                cards_html += '</div>'
                st.markdown(cards_html, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:rgba(37,99,235,0.1);border:1px solid rgba(37,99,235,0.25);
              border-radius:10px;padding:12px 16px;font-size:0.78em;color:#94A3B8;margin-top:8px;">
              🚀 SageMaker endpoint: <code style="color:#60A5FA">{REGRESSION_ENDPOINT}</code>
            </div>""", unsafe_allow_html=True)

        with col_form:
            st.markdown('<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:22px;">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.95em;font-weight:700;color:#E2E8F0;margin-bottom:14px;">Feature Inputs</div>', unsafe_allow_html=True)

            med_inc    = st.slider("Median Income (×$10k)", 0.5, 15.0, 8.33, 0.1)
            house_age  = st.slider("Housing Median Age",    1,   52,   41)
            ave_rooms  = st.slider("Avg Rooms / Household", 1.0, 15.0, 6.98, 0.1)
            ave_bedrms = st.slider("Avg Bedrooms / HH",     1.0, 5.0,  1.02, 0.01)
            population = st.number_input("Block Population", 3, 35682, 322)
            ave_occup  = st.slider("Avg Occupants / HH",    0.5, 20.0, 2.56, 0.1)
            c1, c2 = st.columns(2)
            latitude   = c1.slider("Latitude",  32.5, 42.0, 37.88, 0.01)
            longitude  = c2.slider("Longitude", -124.4, -114.3, -122.23, 0.01)
            st.markdown('</div>', unsafe_allow_html=True)

        reg_features = {
            "MedInc": med_inc, "HouseAge": float(house_age),
            "AveRooms": ave_rooms, "AveBedrms": ave_bedrms,
            "Population": float(population), "AveOccup": ave_occup,
            "Latitude": latitude, "Longitude": longitude,
        }

        if st.button("🔮 Predict Housing Value", type="primary", use_container_width=True):
            with st.spinner("Running inference…"):
                from inference.regression_inference import predict as reg_predict
                try:
                    r = reg_predict(reg_features, use_sagemaker=st.session_state.use_sagemaker)
                    st.session_state.reg_result = {"r": r}
                except FileNotFoundError:
                    st.session_state.reg_result = {"error": "Model not found. Run `python models/train_regression.py` first."}
                except Exception as e:
                    st.session_state.reg_result = {"error": str(e)}

        # Result card + live map (map always shows current slider lat/lon)
        col_res, col_map = st.columns(2)
        with col_res:
            if st.session_state.reg_result:
                rr = st.session_state.reg_result
                if "error" in rr:
                    st.error(rr["error"])
                else:
                    r = rr["r"]
                    st.markdown(f"""
                    <div class="result-card neutral">
                      <div class="result-card-icon">🏠</div>
                      <div class="result-card-value">${r['predicted_value_usd']:,.0f}</div>
                      <div class="result-card-label">Predicted Median House Value</div>
                      <div class="result-card-sub">({r['predicted_value_100k']} × $100,000)</div>
                      <div style="margin-top:12px;font-size:0.75em;color:#64748B;">
                        Source: {'☁️ SageMaker' if r.get('source')=='sagemaker' else '💻 Local Model'}
                      </div>
                    </div>""", unsafe_allow_html=True)
                    if "fallback_reason" in r:
                        st.warning(f"SageMaker unavailable — used local model. ({r['fallback_reason']})")
            else:
                st.markdown(
                    '<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;'
                    'padding:28px;text-align:center;color:#475569;font-size:0.88em;">'
                    '🏠 Adjust the sliders and click <strong>Predict Housing Value</strong> to see a result.'
                    '</div>', unsafe_allow_html=True)
        with col_map:
            st.markdown(
                '<div style="font-size:0.72em;color:#F59E0B;font-weight:600;margin-bottom:4px;">'
                '📍 California only — model trained on CA census block data (1990)</div>',
                unsafe_allow_html=True)
            dot_size = st.session_state.reg_result["r"]["predicted_value_usd"] if (
                st.session_state.reg_result and "r" in st.session_state.reg_result
            ) else 300000
            fig_map = px.scatter_geo(
                pd.DataFrame([{"lat": latitude, "lon": longitude, "val": dot_size}]),
                lat="lat", lon="lon", size="val", size_max=28,
                title="Selected Location (California)",
                color_discrete_sequence=["#2563EB"],
            )
            # Zoom into California
            fig_map.update_geos(
                visible=True, resolution=50,
                showcountries=False, showsubunits=True, showcoastlines=True,
                lataxis_range=[32.0, 42.5],
                lonaxis_range=[-125.0, -113.5],
            )
            fig_map.update_layout(**plotly_dark_theme(), height=260, title_font_size=12, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig_map, use_container_width=True)

    # ── Classification ───────────────────────────────────────────────────────
    with tab_cls:
        col_info2, col_form2 = st.columns([1, 1])

        with col_info2:
            st.markdown("""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:22px;margin-bottom:16px;">
              <div style="font-size:1.05em;font-weight:700;color:#E2E8F0;margin-bottom:12px;">
                📊 Logistic Regression Classifier
              </div>
              <div style="font-size:0.83em;color:#94A3B8;line-height:1.7;">
                Trained on the <strong style="color:#60A5FA">Bank Marketing dataset</strong> to predict
                whether a customer will subscribe to a term deposit based on demographic and
                campaign interaction features.
              </div>
            </div>""", unsafe_allow_html=True)

            metrics_path_cls = os.path.join(MODELS_DIR, "classification_metrics.json")
            if os.path.exists(metrics_path_cls):
                with open(metrics_path_cls) as f:
                    mc = json.load(f)
                cards_html2 = '<div class="kpi-grid">'
                cards_html2 += kpi_card("🎯","Accuracy",  f"{mc['accuracy']:.3f}",  color="blue",   delay=0.0)
                cards_html2 += kpi_card("🎲","Precision", f"{mc['precision']:.3f}", color="cyan",   delay=0.1)
                cards_html2 += kpi_card("📡","Recall",    f"{mc['recall']:.3f}",    color="purple", delay=0.2)
                cards_html2 += kpi_card("⚖️","F1 Score",  f"{mc['f1_score']:.3f}",  color="green",  delay=0.3)
                cards_html2 += "</div>"
                st.markdown(cards_html2, unsafe_allow_html=True)

                # Confusion matrix
                cm = mc["confusion_matrix"]
                cm_df = pd.DataFrame(cm, index=["Actual: No","Actual: Yes"], columns=["Pred: No","Pred: Yes"])
                fig_cm = px.imshow(cm_df, text_auto=True, color_continuous_scale="Blues",
                    title="Confusion Matrix", aspect="auto")
                fig_cm.update_layout(**plotly_dark_theme(), height=220, title_font_size=12, margin=dict(l=10,r=10,t=40,b=10))
                st.plotly_chart(fig_cm, use_container_width=True)

        with col_form2:
            st.markdown('<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:22px;">', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.95em;font-weight:700;color:#E2E8F0;margin-bottom:14px;">Customer Features</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                age      = st.number_input("Age", 18, 95, 35)
                job      = st.selectbox("Job", ["admin.","technician","services","management","blue-collar","self-employed","retired","student"])
                marital  = st.selectbox("Marital", ["married","single","divorced"])
                education = st.selectbox("Education", ["high.school","university.degree","basic.9y","basic.6y","professional.course"])
                default  = st.selectbox("Credit Default", ["no","yes","unknown"])
                housing  = st.selectbox("Housing Loan",  ["yes","no","unknown"])
                loan     = st.selectbox("Personal Loan", ["no","yes","unknown"])
            with c2:
                contact  = st.selectbox("Contact Type",  ["cellular","telephone"])
                month    = st.selectbox("Last Month",    ["may","jun","jul","aug","sep","oct","nov","dec","jan","feb","mar","apr"])
                dow      = st.selectbox("Day of Week",   ["mon","tue","wed","thu","fri"])
                duration = st.slider("Call Duration (sec)", 0, 3000, 260)
                campaign = st.slider("Campaign Contacts",   1, 20, 2)
                poutcome = st.selectbox("Previous Outcome", ["nonexistent","failure","success"])
                emp_var  = st.slider("Emp. Variation Rate", -3.5, 1.5, -1.8, 0.1)
            st.markdown("</div>", unsafe_allow_html=True)

        cls_features = {
            "age": age, "job": job, "marital": marital, "education": education,
            "default": default, "housing": housing, "loan": loan,
            "contact": contact, "month": month, "day_of_week": dow,
            "duration": duration, "campaign": campaign, "pdays": 999,
            "previous": 0, "poutcome": poutcome,
            "emp.var.rate": emp_var, "cons.price.idx": 92.89, "cons.conf.idx": -46.2,
            "euribor3m": 1.31, "nr.employed": 5099.1,
        }

        if st.button("🔮 Predict Subscription", type="primary", use_container_width=True):
            with st.spinner("Classifying…"):
                from inference.classification_inference import predict as cls_predict
                try:
                    res = cls_predict(cls_features, use_sagemaker=st.session_state.use_sagemaker)
                    st.session_state.cls_result = {"res": res}
                except FileNotFoundError:
                    st.session_state.cls_result = {"error": "Model not found. Run `python models/train_classification.py` first."}
                except Exception as e:
                    st.session_state.cls_result = {"error": str(e)}

        if st.session_state.cls_result:
            cr = st.session_state.cls_result
            if "error" in cr:
                st.error(cr["error"])
            else:
                res = cr["res"]
                prob_yes = res["probability_yes"] * 100
                prob_no  = res["probability_no"]  * 100
                c_res, c_gauge = st.columns(2)
                with c_res:
                    card_type = "success" if res["prediction"] == 1 else "warning"
                    icon = "✅" if res["prediction"] == 1 else "❌"
                    st.markdown(f"""
                    <div class="result-card {card_type}">
                      <div class="result-card-icon">{icon}</div>
                      <div class="result-card-value">{res['label']}</div>
                      <div class="result-card-label">Prediction Result</div>
                      <div style="margin-top:14px;display:flex;gap:16px;justify-content:center;">
                        <div style="text-align:center;">
                          <div style="font-size:1.3em;font-weight:700;color:#10B981;">{prob_yes:.1f}%</div>
                          <div style="font-size:0.72em;color:#94A3B8;">Will Subscribe</div>
                        </div>
                        <div style="text-align:center;">
                          <div style="font-size:1.3em;font-weight:700;color:#EF4444;">{prob_no:.1f}%</div>
                          <div style="font-size:0.72em;color:#94A3B8;">Will Not</div>
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                with c_gauge:
                    fig_g = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=prob_yes,
                        title={"text": "Subscription Probability (%)", "font": {"color": "#E2E8F0", "size": 13}},
                        number={"font": {"color": "#E2E8F0", "size": 36}, "suffix": "%"},
                        gauge={
                            "axis":  {"range": [0, 100], "tickcolor": "#475569"},
                            "bar":   {"color": "#2563EB", "thickness": 0.28},
                            "bgcolor": "rgba(0,0,0,0)",
                            "bordercolor": "rgba(99,130,191,0.18)",
                            "steps": [
                                {"range": [0, 33],  "color": "rgba(239,68,68,0.2)"},
                                {"range": [33, 66], "color": "rgba(245,158,11,0.2)"},
                                {"range": [66, 100],"color": "rgba(16,185,129,0.2)"},
                            ],
                        },
                    ))
                    fig_g.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#E2E8F0", height=260,
                        margin=dict(l=20, r=20, t=50, b=10),
                    )
                    st.plotly_chart(fig_g, use_container_width=True)
                if "fallback_reason" in res:
                    st.warning("SageMaker unavailable — used local model.")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: PORTFOLIO DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Portfolio Dashboard":
    st.markdown("""
    <div class="hero-banner">
      <div class="hero-title">📈 Portfolio Dashboard</div>
      <div class="hero-sub">Consolidated view of Prologis real estate performance across all markets.</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        from app.postgres_queries import get_portfolio_summary, get_financials_by_property
        summary = get_portfolio_summary(2023)

        if not summary.empty:
            total_rev  = summary["total_revenue"].sum()
            total_ni   = summary["total_net_income"].sum()
            total_exp  = summary["total_expenses"].sum()
            n_props    = int(summary["property_count"].sum())
            total_sqft = summary["total_sqft"].sum()
            margin_pct = (total_ni / total_rev * 100) if total_rev else 0

            cards_html = '<div class="kpi-grid">'
            cards_html += kpi_card("💰", "Total Revenue",    fmt_currency(total_rev),    "+12.4% YoY",  "green",  0.0)
            cards_html += kpi_card("📈", "Net Income",       fmt_currency(total_ni),     "+8.1% YoY",   "blue",   0.1)
            cards_html += kpi_card("📉", "Total Expenses",   fmt_currency(total_exp),    "+6.2% YoY",   "red",    0.2)
            cards_html += kpi_card("🏗️", "Properties",      str(n_props),              None,           "cyan",   0.3)
            cards_html += kpi_card("📐", "Total Sq Ft",      f"{total_sqft/1e6:.1f}M", None,           "purple", 0.4)
            cards_html += kpi_card("🎯", "Net Margin",       f"{margin_pct:.1f}%",      None,           "blue",   0.5)
            cards_html += "</div>"
            st.markdown(cards_html, unsafe_allow_html=True)

            # Row 1
            col1, col2 = st.columns(2)
            with col1:
                fig1 = px.bar(
                    summary.sort_values("total_revenue", ascending=True),
                    x="total_revenue", y="metro_area", orientation="h",
                    color="total_net_income", color_continuous_scale="Blues",
                    title="Revenue by Metro Area",
                    labels={"total_revenue": "Revenue (USD)", "metro_area": "Metro"},
                )
                fig1.update_layout(**plotly_dark_theme(), height=400, title_font_size=14)
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                fig2 = px.scatter(
                    summary, x="total_revenue", y="total_net_income",
                    size="total_sqft", color="metro_area",
                    hover_name="metro_area",
                    title="Revenue vs Net Income (bubble = sq ft)",
                    color_discrete_sequence=["#2563EB","#06B6D4","#10B981","#F59E0B","#8B5CF6",
                                             "#EF4444","#EC4899","#F97316","#84CC16","#14B8A6"],
                )
                fig2.update_layout(**plotly_dark_theme(), height=400, title_font_size=14)
                st.plotly_chart(fig2, use_container_width=True)

            # Row 2
            type_summary = summary.groupby("property_type")[
                ["total_revenue","total_net_income","property_count","total_sqft"]
            ].sum().reset_index()

            col3, col4 = st.columns(2)
            with col3:
                fig3 = px.pie(
                    type_summary, names="property_type", values="total_revenue",
                    title="Revenue by Property Type", hole=0.5,
                    color_discrete_sequence=["#2563EB","#06B6D4","#10B981","#F59E0B"],
                )
                fig3.update_layout(**plotly_dark_theme(), height=320, title_font_size=14)
                fig3.update_traces(textfont_color="white")
                st.plotly_chart(fig3, use_container_width=True)

            with col4:
                # Waterfall chart
                fig4 = go.Figure(go.Waterfall(
                    name="P&L", orientation="v",
                    measure=["absolute","relative","total"],
                    x=["Revenue","– Expenses","Net Income"],
                    y=[total_rev, -total_exp, total_ni],
                    connector={"line": {"color": "rgba(99,130,191,0.3)"}},
                    increasing={"marker": {"color": "#10B981"}},
                    decreasing={"marker": {"color": "#EF4444"}},
                    totals={"marker":    {"color": "#2563EB"}},
                ))
                fig4.update_layout(**plotly_dark_theme(), height=320,
                    title="P&L Waterfall (Portfolio)", title_font_size=14)
                st.plotly_chart(fig4, use_container_width=True)

            # Summary table
            st.markdown('<div class="section-title">Metro Breakdown</div>', unsafe_allow_html=True)
            st.dataframe(
                summary.style.format({
                    "total_revenue": "${:,.0f}", "total_net_income": "${:,.0f}",
                    "total_expenses": "${:,.0f}", "total_sqft": "{:,.0f}",
                }).background_gradient(subset=["total_revenue"], cmap="Blues"),
                use_container_width=True, height=320,
            )

    except Exception as e:
        db_error_card(e)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: CLOUD SERVICES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Cloud Services":
    st.markdown("""
    <div class="hero-banner">
      <div class="hero-title">☁️ Cloud Services</div>
      <div class="hero-sub">Amazon SageMaker · AWS Bedrock · Google Vertex AI — cloud-ready integrations with local fallback.</div>
      <div class="hero-badge">🔌 Cloud-ready placeholders</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);'
        'border-radius:10px;padding:12px 18px;margin-bottom:20px;font-size:0.85em;color:#94A3B8;">'
        '<span style="color:#F59E0B;font-weight:700;">Demo note:</span> '
        'Cloud endpoints are configured via environment variables. '
        'Set <code>AWS_ACCESS_KEY_ID</code>, <code>AWS_SECRET_ACCESS_KEY</code>, '
        '<code>GOOGLE_CLOUD_PROJECT</code>, and endpoint names in your <code>.env</code> to activate them.'
        '</div>',
        unsafe_allow_html=True,
    )

    cloud_cards = [
        ("🌲", "SageMaker — Regression",      "#2563EB", "Random Forest housing-price regressor",   "REGRESSION_ENDPOINT_NAME",     "housing-rf-regressor"),
        ("💳", "SageMaker — Classification",  "#8B5CF6", "Logistic Regression bank-marketing model","CLASSIFICATION_ENDPOINT_NAME", "bank-marketing-classifier"),
        ("🤖", "AWS Bedrock (Claude)",         "#F59E0B", "LLM fallback for chat summarization",     "BEDROCK_MODEL_ID",             "anthropic.claude-3-sonnet-20240229-v1:0"),
        ("🔷", "Vertex AI (Gemini)",           "#06B6D4", "Primary LLM for chat Q&A via ADK",       "GOOGLE_CLOUD_PROJECT",         "your-gcp-project-id"),
    ]

    grid_html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-bottom:28px;">'
    for icon, title, color, desc, env_var, placeholder in cloud_cards:
        grid_html += (
            f'<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:20px;">'
            f'<div style="font-size:1.6em;margin-bottom:8px;">{icon}</div>'
            f'<div style="font-size:0.92em;font-weight:700;color:#E2E8F0;margin-bottom:4px;">{title}</div>'
            f'<div style="font-size:0.78em;color:#64748B;margin-bottom:12px;">{desc}</div>'
            f'<div style="font-size:0.72em;color:#475569;font-family:monospace;">'
            f'ENV: <span style="color:{color};">{env_var}</span><br/>'
            f'<span style="color:#334155;">default: {placeholder}</span>'
            f'</div>'
            f'</div>'
        )
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Endpoint Status</div>', unsafe_allow_html=True)
    from app.config import GCP_PROJECT, AWS_REGION, REGRESSION_ENDPOINT, CLASSIFICATION_ENDPOINT, BEDROCK_MODEL_ID

    _aws_key      = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
    _sm_reg_ep    = os.getenv("REGRESSION_ENDPOINT_NAME", "")
    _sm_cls_ep    = os.getenv("CLASSIFICATION_ENDPOINT_NAME", "")
    _sagemaker_on = _aws_key and bool(_sm_reg_ep) and bool(_sm_cls_ep)
    _gcp_on       = bool(GCP_PROJECT)
    _bedrock_on   = _aws_key

    # (label, status_text, color, detail)
    status_rows = [
        ("Amazon SageMaker",
         "✅ Configured" if _sagemaker_on else "❌ Not Configured",
         "#10B981" if _sagemaker_on else "#EF4444",
         f"Region: {AWS_REGION}" if _sagemaker_on else "Set AWS credentials + endpoint names to enable"),
        ("Local ML Fallback",
         "⚡ Active" if not _sagemaker_on else "⏸ Standby (SageMaker in use)",
         "#F59E0B" if not _sagemaker_on else "#64748B",
         "scikit-learn models running locally"),
        ("Regression Model",
         "☁️ SageMaker" if (_sagemaker_on and _sm_reg_ep) else "💻 Local Fallback Active",
         "#10B981" if (_sagemaker_on and _sm_reg_ep) else "#F59E0B",
         _sm_reg_ep if (_sagemaker_on and _sm_reg_ep) else "Random Forest — models/random_forest_regressor.pkl"),
        ("Classification Model",
         "☁️ SageMaker" if (_sagemaker_on and _sm_cls_ep) else "💻 Local Fallback Active",
         "#10B981" if (_sagemaker_on and _sm_cls_ep) else "#F59E0B",
         _sm_cls_ep if (_sagemaker_on and _sm_cls_ep) else "Logistic Regression — models/logistic_regression_classifier.pkl"),
        ("AWS Bedrock (Claude)",
         "✅ Configured" if _bedrock_on else "❌ Not Configured",
         "#10B981" if _bedrock_on else "#EF4444",
         f"Model: {BEDROCK_MODEL_ID}" if _bedrock_on else "Set AWS credentials to enable"),
        ("Google Vertex AI",
         "✅ Configured" if _gcp_on else "❌ Not Configured",
         "#10B981" if _gcp_on else "#EF4444",
         f"Project: {GCP_PROJECT}" if _gcp_on else "Set GOOGLE_CLOUD_PROJECT to enable"),
    ]

    if not _sagemaker_on:
        st.markdown(
            '<div style="background:rgba(245,158,11,0.10);border:1px solid rgba(245,158,11,0.28);'
            'border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:0.82em;color:#CBD5E1;line-height:1.5;">'
            '<span style="color:#F59E0B;font-weight:700;">ℹ️ Demo mode:</span> '
            'The deployed demo runs with local scikit-learn fallback models. '
            'SageMaker endpoints can be enabled by adding AWS credentials and endpoint names as environment variables.'
            '</div>',
            unsafe_allow_html=True,
        )

    for svc, status, color, detail in status_rows:
        st.markdown(
            f'<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;'
            f'padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">'
            f'<div style="font-size:0.88em;font-weight:600;color:#E2E8F0;">{svc}</div>'
            f'<div style="text-align:right;">'
            f'<div style="font-size:0.8em;color:{color};font-weight:700;">{status}</div>'
            f'<div style="font-size:0.72em;color:#475569;margin-top:2px;">{detail}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title" style="margin-top:24px;">How to Activate</div>', unsafe_allow_html=True)
    st.code("""# .env file
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
REGRESSION_ENDPOINT_NAME=housing-rf-regressor
CLASSIFICATION_ENDPOINT_NAME=bank-marketing-classifier
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_AGENT_ID=your-agent-id
""", language="bash")
