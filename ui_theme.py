"""Design tokens and the single consolidated stylesheet for the app."""
from __future__ import annotations

import re
import base64
import hashlib
from functools import lru_cache
from pathlib import Path
from collections.abc import Sequence

import streamlit as st
import streamlit.components.v1 as components

PALETTES = {
    "dark": {
        "bg": "#0b0f19",
        "bg_deep": "#070a13",
        "surface": "#111827",
        "surface_2": "#1f2937",
        "border": "#253147",
        "border_strong": "#334155",
        "text": "#F4F7FA",
        "muted": "#BCC9D5",
        "muted_2": "#A6B5C3",
        "blue": "#14b8a6",
        "on_primary": "#032019",
        "button_hover": "#2dd4bf",
        "cyan": "#14b8a6",
        "violet": "#B9A3F5",
        "green": "#34D399",
        "red": "#FB7185",
        "amber": "#FBBF24",
        "rating_low": "#FB7185",
        "rating_mid": "#FBBF24",
        "rating_high": "#34D399",
        "positive_bg": "rgba(52,211,153,0.12)",
        "neutral_bg": "rgba(251,191,36,0.12)",
        "negative_bg": "rgba(251,113,133,0.12)",
        "shadow": "0 8px 24px rgba(2,6,23,0.24)",
        "shadow_glow": "0 5px 16px rgba(20,184,166,0.22)",
        "plot_grid": "rgba(188,201,213,0.14)",
        "topbar_bg": "rgba(11,15,25,0.86)",
    },
    "light": {
        "bg": "#F4F7F8",
        "bg_deep": "#EAF1F3",
        "surface": "#FFFFFF",
        "surface_2": "#EDF3F4",
        "border": "#CCD8DE",
        "border_strong": "#AFBEC8",
        "text": "#172B35",
        "muted": "#425662",
        "muted_2": "#526772",
        "blue": "#00766C",
        "on_primary": "#FFFFFF",
        "button_hover": "#005F56",
        "cyan": "#006B62",
        "violet": "#6D28D9",
        "green": "#047857",
        "red": "#B42318",
        "amber": "#A15C00",
        "rating_low": "#B42318",
        "rating_mid": "#A15C00",
        "rating_high": "#047857",
        "positive_bg": "rgba(4,120,87,0.08)",
        "neutral_bg": "rgba(161,92,0,0.08)",
        "negative_bg": "rgba(180,35,24,0.08)",
        "shadow": "0 8px 24px rgba(23,43,53,0.06)",
        "shadow_glow": "0 5px 16px rgba(0,118,108,0.14)",
        "plot_grid": "rgba(66,86,98,0.16)",
        "topbar_bg": "rgba(244,247,248,0.88)",
    },
}

SENTIMENT_COLORS = {
    "dark": {"Positive": "#34D399", "Neutral": "#FBBF24", "Negative": "#FB7185"},
    "light": {"Positive": "#047857", "Neutral": "#A15C00", "Negative": "#B42318"},
}

APP_COLORS = {
    "dark": ["#58E0C4", "#34D399", "#2DD4BF", "#10B981"],
    "light": ["#006B62", "#047857", "#0F766E", "#0E7490"],
}

STAR_COLORS = {
    "dark": ("#2F91FF", "#F02D90", "#FF6517"),
    "light": ("#0964D9", "#C81973", "#D64B00"),
}

@lru_cache(maxsize=1)
def wallpaper_url() -> str:
    image = Path(__file__).parent / "assets" / "market-wallpaper.jpeg"
    return "data:image/jpeg;base64," + base64.b64encode(image.read_bytes()).decode("ascii")

_CORE = """
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: var(--font-sans);
}
.stApp, [data-testid="stAppViewContainer"] {
  background-color: var(--bg) !important;
  background-image: linear-gradient(var(--wallpaper-overlay), var(--wallpaper-overlay)), var(--wallpaper) !important;
  background-size: cover !important;
  background-position: center top !important;
  background-attachment: fixed !important;
  color: var(--text);
}
.stApp label { color: var(--muted); }
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] strong,
.stApp [data-testid="stMarkdownContainer"] li { color: var(--text); }
.stApp label [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stCaptionContainer"] p { color: var(--muted); }
h1, h2, h3, h4 { color: var(--text) !important; font-weight: 700; letter-spacing: -0.01em; }

/* ---------- Native chrome ---------- */
[data-testid="stHeader"] {
  background: transparent;
  box-shadow: none;
  pointer-events: none;
}
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stMainMenuButton"],
[data-testid="stToolbarActions"],
#MainMenu, footer { display: none !important; }
[data-testid="stExpandSidebarButton"],
[data-testid="stExpandSidebarButton"] button {
  pointer-events: auto;
}
[data-testid="stExpandSidebarButton"] button {
  border-radius: 10px;
  color: var(--muted);
  background: var(--surface);
  border: 1px solid var(--border);
}
[data-testid="stExpandSidebarButton"] button:hover {
  color: var(--text);
  border-color: var(--border-strong);
}
[data-testid="stStatusWidget"] { display: none; }

/* ---------- Layout ---------- */
[data-testid="stMain"] .block-container {
  max-width: 100% !important;
  padding: 0 var(--content-pad) 4rem !important;
}

/* ---------- Top bar ---------- */
.st-key-topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  width: calc(100% + 2 * var(--content-pad));
  max-width: none;
  margin: 0 calc(-1 * var(--content-pad)) 1.6rem;
  padding: 0.55rem var(--content-pad);
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(14px) saturate(140%);
}
.workspace-intro { padding: 1.5rem 0 1.2rem; max-width: 850px; }
.workspace-kicker { color: var(--cyan); font-size: .72rem; letter-spacing: .12em; font-weight: 700; }
.workspace-intro h2 { font-size: clamp(1.65rem, 3vw, 2.7rem); margin: .6rem 0; line-height: 1.5; }
.workspace-intro p { color: var(--muted) !important; line-height: 1.9; }
.discovery-empty { margin-block: 2rem; padding: 2.5rem 1.5rem; text-align: center;
  border: 1px solid var(--border); background: var(--surface); border-radius: 18px; }
.discovery-symbol { display: inline-grid; place-items: center; width: 52px; height: 52px;
  border: 1px solid var(--border-strong); background: var(--surface-2); color: var(--cyan);
  border-radius: 16px; font-size: 2rem; margin-bottom: .6rem; }
.discovery-empty p { color: var(--muted) !important; }
.discovery-next { display: flex; flex-wrap: wrap; justify-content: center; gap: 2rem;
  margin-block-start: 1.8rem; color: var(--muted); font-size: .8rem; }
.stApp input, .stApp button, .stApp label { line-height: 1.7; }
[data-testid="stSidebar"] { transition: margin 220ms ease, transform 220ms ease; }
[data-testid="stSidebarCollapsedControl"] { inset-inline-start: .5rem; inset-inline-end: auto; }
[data-testid="stExpandSidebarButton"] svg { transform: scaleX(var(--sidebar-icon-flip)); }
.stApp button { transition: background-color 180ms ease, border-color 180ms ease; }
.st-key-topbar [data-testid="stHorizontalBlock"] {
  align-items: center;
  gap: 0.75rem;
}
body:has([data-testid="stSidebar"][aria-expanded="false"]) .st-key-topbar [data-testid="stHorizontalBlock"] {
  padding-inline-start: var(--toggle-pad);
}
.st-key-topbar h1 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.3;
}
.st-key-topbar h1 a { display: none; }
.st-key-topbar .topbar-eyebrow {
  display: block;
  color: var(--muted-2);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.st-key-topbar [data-testid="stButton"] { display: flex; justify-content: flex-end; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: var(--bg-deep);
  border-inline-end: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border);
}
[data-testid="stSidebarCollapseButton"] button {
  border-radius: 10px;
  color: var(--muted);
}
[data-testid="stSidebarCollapseButton"] button:hover {
  color: var(--text);
  background: var(--surface-2);
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.4rem 0 0.9rem;
}
.sidebar-brand .mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  flex: none;
  border-radius: 12px;
  background: var(--grad);
  color: var(--on-primary);
}
.sidebar-brand .mark svg { width: 20px; height: 20px; }
.sidebar-brand .tag {
  display: block;
  color: var(--muted-2);
  font-size: 0.68rem;
  line-height: 1.3;
}
.sidebar-group {
  margin: 1.1rem 0 0.35rem;
  color: var(--muted-2);
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
[data-testid="stSidebar"] hr {
  margin: 1.1rem 0;
  border-color: var(--border);
}

/* ---------- Stepper ---------- */
.stepper {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0 0 1.6rem;
  padding: 0;
  list-style: none;
}
.stepper li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--muted-2);
  font-size: 0.8rem;
  font-weight: 600;
}
.stepper li:not(:last-child)::after {
  content: "";
  width: clamp(18px, 5vw, 54px);
  height: 1px;
  margin-inline: 0.4rem;
  background: var(--border);
}
.stepper .dot {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  flex: none;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: var(--surface);
  font-size: 0.72rem;
  font-weight: 700;
}
.stepper li[data-state="active"] { color: var(--text); }
.stepper li[data-state="active"] .dot {
  background: var(--grad);
  border-color: transparent;
  color: var(--on-primary);
}
.stepper li[data-state="done"] { color: var(--cyan); }
.stepper li[data-state="done"] .dot {
  border-color: var(--cyan);
  color: var(--cyan);
}

/* ---------- Step headings ---------- */
.step-head {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin: 1.7rem 0 0.9rem;
  padding-bottom: 0.7rem;
  border-bottom: 1px solid var(--border);
}
.step-head .badge {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex: none;
  border: 1px solid var(--border);
  border-radius: 11px;
  background: var(--surface-2);
  color: var(--cyan);
  font-size: 0.9rem;
  font-weight: 800;
}
.step-head .copy { display: flex; flex-direction: column; gap: 0.12rem; min-width: 0; }
.step-head .title { color: var(--text); font-size: 1.02rem; font-weight: 700; }
.step-head .hint { color: var(--muted-2); font-size: 0.78rem; }
.step-head .flag {
  margin-inline-start: auto;
  flex: none;
  padding: 0.22rem 0.62rem;
  border: 1px solid var(--border);
  border-radius: 99px;
  color: var(--muted);
  font-size: 0.7rem;
  font-weight: 700;
}
.step-head .flag[data-tone="done"] {
  border-color: transparent;
  background: var(--positive-bg);
  color: var(--green);
}
.step-head .flag[data-tone="active"] {
  border-color: transparent;
  background: var(--neutral-bg);
  color: var(--amber);
}

/* ---------- App picker cards ---------- */
[class*="st-key-appcard_"] {
  display: flex;
  flex-direction: column;
  min-height: 194px;
  padding: 0.95rem 1rem 0.85rem;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--surface);
  box-shadow: var(--shadow);
  transition: border-color 150ms ease, transform 150ms ease, box-shadow 150ms ease;
}
[class*="st-key-appcard_"] > [data-testid="stVerticalBlock"] {
  display: flex;
  flex: 1;
  flex-direction: column;
  justify-content: space-between;
  gap: 0.75rem;
}
[class*="st-key-appcard_"]:hover {
  border-color: var(--border-strong);
  transform: translateY(-2px);
}
.app-card-body { display: flex; flex-direction: column; gap: 0.7rem; min-width: 0; }
.app-card-top { display: flex; align-items: center; gap: 0.7rem; min-width: 0; }
.app-card-icon {
  width: 46px;
  height: 46px;
  flex: none;
  border: 1px solid var(--border);
  border-radius: 13px;
  object-fit: cover;
  background: var(--surface-2);
}
.app-card-titles { display: flex; flex-direction: column; min-width: 0; gap: 0.1rem; }
.app-card-title {
  overflow: hidden;
  color: var(--text);
  font-size: 0.9rem;
  font-weight: 700;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.app-card-dev {
  overflow: hidden;
  color: var(--muted-2);
  font-size: 0.75rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.app-card-score {
  display: flex;
  align-items: center;
  gap: 0.28rem;
  margin-inline-start: auto;
  flex: none;
  padding: 0.2rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 99px;
  color: var(--amber);
  font-size: 0.74rem;
  font-weight: 800;
}
.app-card-id {
  overflow: hidden;
  color: var(--muted-2);
  font-family: var(--font-mono);
  font-size: 0.68rem;
  text-overflow: ellipsis;
  white-space: nowrap;
  direction: ltr;
  unicode-bidi: isolate;
}
.app-card-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
  align-self: flex-start;
  padding: 0.24rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: 99px;
  background: var(--surface-2);
  color: var(--muted);
  font-size: 0.7rem;
  font-weight: 700;
}
.app-card-chip[data-selected="true"] {
  border-color: transparent;
  background: var(--positive-bg);
  color: var(--green);
}

/* ---------- Section titles ---------- */
.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 30px 0 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
  font-size: 1.02rem;
  font-weight: 700;
}
.panel-title::before {
  content: "";
  width: 4px;
  height: 20px;
  border-radius: 2px;
  background: var(--grad-energetic);
}

/* ---------- KPI cards ---------- */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 18px 0;
}
.kpi {
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--surface);
  box-shadow: var(--shadow);
}
.kpi::before {
  content: "";
  position: absolute;
  top: 0;
  inset-inline: 0;
  height: 3px;
  background: var(--grad-energetic);
}
.kpi-label {
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}
.kpi-value { font-size: 2rem; font-weight: 700; line-height: 1.1; }
.num {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  direction: ltr;
  unicode-bidi: embed;
}

/* ---------- App header card ---------- */
.app-head {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 12px 0;
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--surface);
  box-shadow: var(--shadow);
}
.app-head img {
  width: 60px;
  height: 60px;
  border: 1px solid var(--border);
  border-radius: 14px;
}
.app-name { font-size: 1.3rem; font-weight: 700; }
.app-dev { color: var(--muted); font-size: 0.9rem; }

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {
  border-radius: 11px;
  font-family: var(--font-sans);
  font-weight: 700;
  transition: background-color 150ms ease, border-color 150ms ease, transform 150ms ease, box-shadow 150ms ease;
}
[data-testid="stBaseButton-primary"] {
  background: var(--grad);
  border: 1px solid transparent;
  color: var(--on-primary);
  box-shadow: var(--shadow-glow);
}
[data-testid="stBaseButton-primary"]:hover {
  background: var(--button-hover);
  border-color: transparent;
  color: var(--on-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-1px);
}
[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p { color: var(--on-primary) !important; }
[data-testid="stBaseButton-secondary"] {
  background: var(--surface);
  border: 1px solid var(--border-strong);
  color: var(--text);
}
[data-testid="stBaseButton-secondary"]:hover {
  background: var(--surface-2);
  border-color: var(--cyan);
  color: var(--text);
}
[data-testid="stBaseButton-tertiary"] {
  background: transparent;
  border: 1px solid transparent;
  color: var(--muted);
}
[data-testid="stBaseButton-tertiary"]:hover {
  background: var(--surface-2);
  color: var(--text);
}
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(0); }
.stButton > button:disabled, .stDownloadButton > button:disabled {
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--muted-2);
  box-shadow: none;
  transform: none;
}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible,
.stTextInput input:focus-visible, [data-baseweb="select"] > div:focus-within,
[data-testid="stSlider"] [role="slider"]:focus-visible, [data-testid="stSlider"] [role="slider"]:focus {
  outline: 3px solid var(--cyan) !important;
  outline-offset: 2px;
}

/* ---------- Inputs ---------- */
.stTextInput input, [data-testid="stTextInput"] input,
[data-baseweb="select"] > div {
  background: var(--surface) !important;
  border-color: var(--border-strong) !important;
  border-radius: 11px !important;
  color: var(--text) !important;
}
.stTextInput input::placeholder { color: var(--muted-2); }
[data-testid="stSelectbox"] [role="combobox"] { background: transparent !important; color: var(--text) !important; }
[data-testid="stSelectbox"] svg { color: var(--muted) !important; }
[data-baseweb="popover"], [data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] li {
  background: var(--surface) !important; color: var(--text) !important;
}
[data-baseweb="popover"] li[aria-selected="true"] {
  background: var(--surface-2) !important;
}

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--border); }
[data-baseweb="tab"] {
  color: var(--muted);
  font-family: var(--font-sans);
  font-weight: 700;
}
[data-baseweb="tab"][aria-selected="true"] { color: var(--text); }
[data-baseweb="tab-highlight"] { background: var(--cyan) !important; }

/* ---------- Dataframes ---------- */
.stDataFrame, [data-testid="stDataFrame"] {
  overflow: hidden;
  border: 1px solid var(--border) !important;
  border-radius: 12px;
}

/* ---------- Sliders stay LTR ---------- */
[data-testid="stSlider"] { direction: ltr !important; }
[data-testid="stSlider"] label,
[data-testid="stSlider"] label p { text-align: var(--slider-align) !important; }
[data-testid="stSliderThumbValue"],
[data-testid="stSliderTickBarMin"],
[data-testid="stSliderTickBarMax"] { direction: ltr !important; }

/* ---------- Charts / code stay LTR ---------- */
.js-plotly-plot, .stCodeBlock, pre, code { direction: ltr; }
.js-plotly-plot { color: var(--text); }
[data-testid="stPlotlyChart"] { animation: popIn .6s cubic-bezier(.22,1,.36,1); }

/* ---------- Sentiment donut ---------- */
.donut-wrap { position: relative; display: grid; place-items: center; }
.donut { display: block; animation: popIn .7s cubic-bezier(.22,1,.36,1); }
.donut .ring-track { fill: none; stroke: var(--border-strong); }
.donut .ring-seg { fill: none; animation: segIn .95s cubic-bezier(.22,1,.36,1); }
.donut-center { position: absolute; text-align: center; pointer-events: none; line-height: 1.15; }
.donut-center b { font-size: 1.35rem; font-weight: 800; }
.donut-center span { display: block; color: var(--muted); font-size: .7rem; }
.donut-app { margin-top: 6px; color: var(--muted); font-size: .78rem; line-height: 1.3; text-align: center; }
.donut-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px;
  margin: 12px 0 0;
  color: var(--muted);
  font-size: .82rem;
}
.donut-legend i {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-inline-end: 6px;
  border-radius: 3px;
  vertical-align: middle;
}

/* ---------- Comparison bars ---------- */
.bars { display: flex; gap: 18px; align-items: flex-start; padding: 6px 4px 0; }
.barcol { display: flex; flex: 1; flex-direction: column; align-items: center; gap: 8px; min-width: 0; }
.plot {
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  width: 100%;
  height: 210px;
}
.barval {
  position: absolute;
  top: 0;
  inset-inline: 0;
  color: var(--blue);
  font-size: .85rem;
  font-weight: 700;
  text-align: center;
}
.bar {
  width: 60%;
  max-width: 92px;
  height: var(--h);
  border-radius: 14px 14px 8px 8px;
  background: linear-gradient(180deg, rgba(255,255,255,0.30), rgba(255,255,255,0) 58%), var(--c);
  box-shadow: 0 0 24px -10px var(--c);
  animation: barGrow 1s cubic-bezier(.22,1,.36,1);
}
.barcol em {
  overflow: hidden;
  max-width: 100%;
  color: var(--muted);
  font-size: .8rem;
  font-style: normal;
  line-height: 1.3;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@property --h { syntax: '<percentage>'; initial-value: 0%; inherits: true; }
@keyframes barGrow { from { --h: 0%; } }
@keyframes segIn { from { stroke-dasharray: 0 1000; } }
@keyframes popIn { from { opacity: 0; transform: scale(.94); } }

/* ---------- Review cards ---------- */
.review-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-auto-rows: 156px;
  gap: 12px;
  max-height: 324px;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 4px 6px 4px 2px;
  margin: 8px 0 12px;
  scrollbar-width: thin;
  scrollbar-color: var(--border-strong) transparent;
}
.review-grid::-webkit-scrollbar { width: 8px; }
.review-grid::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 8px; }
.review-card {
  display: flex;
  min-width: 0;
  box-sizing: border-box;
  height: 156px;
  flex-direction: column;
  gap: 7px;
  overflow: hidden;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-inline-start: 3px solid var(--cyan);
  border-radius: 12px;
  background: var(--surface);
  box-shadow: var(--shadow);
}
.review-card[data-sentiment="positive"] { border-inline-start-color: var(--green); }
.review-card[data-sentiment="neutral"] { border-inline-start-color: var(--amber); }
.review-card[data-sentiment="negative"] { border-inline-start-color: var(--red); }
.review-card-header, .review-card-footer, .review-person {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 8px;
}
.review-card-header { justify-content: space-between; }
.review-person { overflow: hidden; }
.review-avatar {
  display: grid;
  width: 34px;
  height: 34px;
  flex: none;
  place-items: center;
  border-radius: 50%;
  background: var(--surface-2);
  color: var(--cyan);
  font-weight: 800;
}
.review-name {
  overflow: hidden;
  color: var(--text);
  font-size: 0.9rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.review-date { flex: none; color: var(--muted); font-size: 0.72rem; direction: ltr; unicode-bidi: isolate; }
.review-copy {
  display: -webkit-box;
  min-height: 0;
  margin: 0;
  overflow: hidden;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.5;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.review-card-footer { flex-wrap: wrap; margin-top: auto; }
.review-rating { display: flex; flex: 1 1 120px; align-items: center; gap: 8px; min-width: 0; }
.review-rating-value { color: var(--text); font-size: 0.78rem; font-weight: 800; }
.review-rating-track {
  position: relative;
  display: block;
  flex: 1;
  height: 7px;
  overflow: visible;
  border-radius: 99px;
  background: linear-gradient(90deg, var(--rating-low), var(--rating-mid) 52%, var(--rating-high));
  direction: ltr;
}
.review-rating-track > span {
  position: absolute;
  top: 50%;
  left: clamp(6px, var(--rating-position), calc(100% - 6px));
  width: 12px;
  height: 12px;
  border: 2px solid var(--surface);
  border-radius: 50%;
  background: var(--text);
  box-shadow: 0 0 0 1px var(--border-strong);
  transform: translate(-50%, -50%);
}
.review-sentiment, .review-app {
  max-width: 100%;
  overflow: hidden;
  padding: 2px 7px;
  border: 1px solid var(--border);
  border-radius: 99px;
  font-size: 0.68rem;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.review-sentiment.positive { background: var(--positive-bg); color: var(--green); }
.review-sentiment.neutral { background: var(--neutral-bg); color: var(--amber); }
.review-sentiment.negative { background: var(--negative-bg); color: var(--red); }
.review-app { background: var(--surface-2); color: var(--cyan); }
.review-likes { flex: none; color: var(--muted); font-size: 0.68rem; direction: ltr; unicode-bidi: isolate; }
.rating-range-track {
  position: relative;
  height: 8px;
  margin: 4px 0 0;
  overflow: hidden;
  border-radius: 99px;
  background: linear-gradient(90deg, var(--rating-low), var(--rating-mid) 52%, var(--rating-high));
  direction: ltr;
}
.rating-range-track > span {
  position: absolute;
  top: 0;
  bottom: 0;
  left: var(--range-start);
  width: var(--range-width);
  border-inline: 2px solid var(--text);
  background: rgba(255,255,255,0.16);
}

/* ---------- Responsive ---------- */
@media (max-width: 900px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .review-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); max-height: 330px; }
}
@media (max-width: 600px) {
  .review-grid { grid-template-columns: 1fr; max-height: 484px; }
  .step-head { flex-wrap: wrap; }
  .step-head .flag { margin-inline-start: 0; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
  [class*="st-key-appcard_"]:hover { transform: none; }
}
"""

_DIRECTION = {
    "rtl": """
[data-testid="stAppViewContainer"] { direction: rtl; }
[data-testid="stMain"], [data-testid="stSidebar"] { direction: rtl; }
.st-key-theme_light [data-baseweb="checkbox"] {
  flex-direction: row-reverse !important;
  direction: rtl;
  gap: .55rem;
}
.st-key-theme_light [data-baseweb="checkbox"] > div:first-child,
.st-key-theme_light [data-baseweb="checkbox"] > div:first-child > div {
  transition: all 180ms ease;
}
.st-key-theme_light [data-baseweb="checkbox"]:has(input[aria-checked="true"])
  > div:first-child > div {
  transform: translateX(-16px) !important;
}
[data-testid="stSidebar"] { right: 0; left: auto; }
[data-testid="stSidebarCollapsedControl"] { right: .5rem; left: auto; }
:root { --sidebar-icon-flip: -1; }
[data-testid="stSidebar"][aria-expanded="false"] {
  visibility: hidden;
  overflow: hidden;
}
[data-testid="stSidebar"][aria-expanded="false"] { transform: none !important; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown p { text-align: right; }
[data-testid="stMain"] [data-testid="stTextInput"] input,
[data-testid="stSidebar"] [data-testid="stTextInput"] input,
[data-testid="stMain"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] {
  text-align: right;
}
.review-card[dir="rtl"] { text-align: right; }
""",
    "ltr": """
[data-testid="stAppViewContainer"] { direction: ltr; }
[data-testid="stMain"], [data-testid="stSidebar"] { direction: ltr; }
[data-testid="stSidebar"] { left: 0; right: auto; }
[data-testid="stSidebarCollapsedControl"] { left: .5rem; right: auto; }
:root { --sidebar-icon-flip: 1; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown p { text-align: left; }
[data-testid="stMain"] [data-testid="stTextInput"] input,
[data-testid="stSidebar"] [data-testid="stTextInput"] input,
[data-testid="stMain"] [data-testid="stSelectbox"] [role="combobox"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] {
  text-align: left;
}
.review-card[dir="ltr"] { text-align: left; }
""",
}


def card_token(app_id: str) -> str:
    label = re.sub(r"[^0-9a-zA-Z]+", "_", str(app_id)).strip("_") or "app"
    return label + "_" + hashlib.sha256(str(app_id).encode()).hexdigest()[:8]


def _selected_cards(selected_app_ids: Sequence[str]) -> str:
    return "\n".join(
        f".st-key-appcard_{card_token(app_id)} {{\n"
        "  border-color: var(--blue);\n"
        "  box-shadow: 0 0 0 1px var(--blue), var(--shadow-glow);\n"
        "}"
        for app_id in selected_app_ids
    )


def build_stylesheet(theme: str, rtl: bool = False, selected_app_ids: Sequence[str] = ()) -> str:
    palette = PALETTES[theme]
    overlay = "rgba(11,15,25,.50)" if theme == "dark" else "rgba(244,247,248,.92)"
    variables = "\n".join(
        f"  --{name.replace('_', '-')}: {value};" for name, value in palette.items()
    )
    slider_align = "right" if rtl else "left"
    root = (
        ":root {\n"
        f"{variables}\n"
        f"  --wallpaper: url('{wallpaper_url()}');\n"
        f"  --wallpaper-overlay: {overlay};\n"
        "  --grad: linear-gradient(135deg, var(--blue), var(--button-hover));\n"
        "  --grad-energetic: linear-gradient(135deg, var(--cyan), var(--green));\n"
        "  --content-pad: 1.15rem;\n"
        "  --toggle-pad: 3.1rem;\n"
        "  --font-sans: 'Segoe UI', Tahoma, Arial, sans-serif;\n"
        "  --font-mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;\n"
        f"  --slider-align: {slider_align};\n"
        f"  color-scheme: {theme};\n"
        "}\n"
    )
    return (
        "<style>\n"
        + root
        + _CORE
        + _DIRECTION["rtl" if rtl else "ltr"]
        + _selected_cards(selected_app_ids)
        + "\n</style>"
    )


def apply_theme(theme: str, rtl: bool = False, selected_app_ids: Sequence[str] = ()) -> None:
    direction, language = ("rtl", "ar") if rtl else ("ltr", "en")
    components.html(
        f"""<script>
        const root = window.parent.document.documentElement;
        root.dir = '{direction}'; root.lang = '{language}';
        root.style.colorScheme = '{theme}';
        </script>""", height=0,
    )
    st.markdown(
        build_stylesheet(theme, rtl=rtl, selected_app_ids=selected_app_ids),
        unsafe_allow_html=True,
    )
