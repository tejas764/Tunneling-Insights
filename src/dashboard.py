"""Streamlit dashboard for the DNS tunnel detection lab."""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from window_detector import build_baseline, calculate_window_score, get_status, load_windows


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
NORMAL_BEHAVIOR = DATA / "normal_behavioral_features.csv"
TUNNEL_BEHAVIOR = DATA / "tunnel_behavioral_features.csv"
NORMAL_WINDOWS = DATA / "normal_window_features.csv"
TUNNEL_WINDOWS = DATA / "tunnel_window_features.csv"
LIVE_FILE = DATA / "live_windows.csv"
SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_COLORS = {
    "LOW": "#31b98b",
    "MEDIUM": "#e5ae52",
    "HIGH": "#ed8059",
    "CRITICAL": "#e45b70",
}

st.set_page_config(
    page_title="DNS Signal | Detection Lab",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
    :root {
      --ink: #eaf0f5; --muted: #94a4b4; --faint: #66788b;
      --line: rgba(153,180,201,.14); --panel: #111d29; --panel2: #142332;
      --canvas: #0a121b; --mint: #58d6ad; --blue: #72b8f5;
    }
    .stApp { background: radial-gradient(ellipse at 48% -14%, #1a3444 0, #0c1722 36rem, var(--canvas) 75rem); color: var(--ink); }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #0c1721; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
    .block-container { max-width: 1480px; padding-top: 2.35rem; padding-bottom: 3.5rem; }
    h1, h2, h3 { color: var(--ink) !important; letter-spacing: -.035em; }
    h1 { font-size: 2.35rem !important; font-weight: 700 !important; line-height: 1.1 !important; }
    h2 { font-size: 1.45rem !important; font-weight: 650 !important; margin-top: 1.35rem !important; }
    h3 { font-size: 1.06rem !important; font-weight: 650 !important; }
    p, label, [data-testid="stCaptionContainer"] { color: var(--muted); }
    hr { border-color: var(--line); margin: 1.4rem 0; }
    [data-testid="stMetric"] { background: linear-gradient(145deg, rgba(23,41,56,.95), rgba(15,28,40,.95)); border: 1px solid var(--line); border-radius: 15px; padding: 18px 20px; min-height: 116px; }
    [data-testid="stMetricLabel"] { color: #9db0bf; font-size: .82rem; }
    [data-testid="stMetricValue"] { color: #f1f6f9; font-size: 1.8rem; font-weight: 650; letter-spacing: -.04em; }
    [data-testid="stMetricDelta"] { font-size: .77rem; }
    [data-testid="stTabs"] { margin-top: 1.25rem; }
    .stTabs [data-baseweb="tab-list"] { gap: .45rem; border-bottom: 1px solid var(--line); }
    .stTabs [data-baseweb="tab"] { height: 48px; color: #91a2b1; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: var(--mint) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background: var(--mint); }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
    [data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-testid="stMultiSelect"] [data-baseweb="select"] > div { background: #132230; border-color: var(--line); }
    .brand { display:flex; align-items:center; gap:11px; margin: 0 0 2rem; }
    .brand-mark { width:37px; height:37px; display:grid; place-items:center; border-radius:12px; color:#77e4bf; background:#183d3b; border:1px solid #2c645a; font-size:21px; }
    .brand-name { color:#edf5f7; font-weight:700; letter-spacing:-.02em; font-size:1.03rem; }
    .brand-sub { color:#7990a0; font-size:.72rem; margin-top:1px; }
    .eyebrow { color:var(--mint); font-family:'DM Mono',monospace; font-size:.7rem; text-transform:uppercase; letter-spacing:.13em; margin-bottom:.65rem; }
    .lede { color:#9cabb8; font-size:1rem; max-width:760px; line-height:1.6; margin-top:.45rem; }
    .hero-row { display:flex; align-items:center; gap:9px; margin-top:1.05rem; }
    .chip { display:inline-flex; align-items:center; gap:7px; border:1px solid var(--line); border-radius:999px; padding:6px 11px; color:#a9bac5; background:rgba(21,39,52,.7); font-size:.74rem; font-weight:600; }
    .dot { width:7px; height:7px; background:var(--mint); border-radius:50%; box-shadow:0 0 12px #58d6ad80; }
    .section-kicker { color:#8599a8; font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.1em; font-size:.7rem; margin:.6rem 0 .7rem; }
    .surface { background:linear-gradient(145deg,rgba(20,36,50,.94),rgba(15,27,39,.94)); border:1px solid var(--line); border-radius:16px; padding:19px 21px; margin-bottom:12px; }
    .surface-title { color:#e6eef3; font-size:1rem; font-weight:650; margin-bottom:4px; }
    .surface-copy { color:#91a3b1; line-height:1.55; font-size:.85rem; }
    .state { display:flex; align-items:flex-start; gap:14px; padding:20px; border-radius:16px; margin:.5rem 0 1rem; }
    .state-ok { background:linear-gradient(120deg,#102a2a,#10202b); border:1px solid #28524c; }
    .state-alert { background:linear-gradient(120deg,#351d27,#211b25); border:1px solid #72404a; }
    .state-idle { background:linear-gradient(120deg,#142538,#121f2c); border:1px solid #2d4c67; }
    .state-icon { font-size:1.1rem; line-height:1.5; }
    .state-title { color:#edf4f5; font-size:.98rem; font-weight:700; margin-bottom:4px; }
    .state-copy { color:#a0b0bb; font-size:.84rem; line-height:1.5; }
    .mono { font-family:'DM Mono',monospace; }
    .sidebar-note { color:#7f93a2; font-size:.77rem; line-height:1.5; }
    .sidebar-label { color:#e1eaf0; font-size:.79rem; font-weight:700; margin:.6rem 0 .45rem; }
    .stButton > button { border:1px solid #2d5c58; border-radius:10px; background:#173632; color:#b9f3df; font-weight:600; }
    .stButton > button:hover { border-color:#58d6ad; color:white; background:#1d4942; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=2, show_spinner=False)
def read_csv(path: str) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path)


@st.cache_data(show_spinner=False)
def read_windows(path: str) -> list[dict]:
    file_path = Path(path)
    return load_windows(str(file_path)) if file_path.exists() else []


def score_windows(windows: list[dict], baseline: dict) -> list[dict]:
    scored = []
    for window in windows:
        score, signals = calculate_window_score(window, baseline)
        scored.append({"score": score, "status": get_status(score), "signals": signals, "row": window})
    return scored


def count_status(results: list[dict]) -> dict[str, int]:
    return {level: sum(item["status"] == level for item in results) for level in SEVERITY_ORDER}


def mean_of(frame: pd.DataFrame, column: str) -> float:
    if column not in frame:
        return 0.0
    return float(pd.to_numeric(frame[column], errors="coerce").mean())


def severity_chart(frame: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=31)
        .encode(
            x=alt.X("Traffic:N", title=None, axis=alt.Axis(labelColor="#a5b5c1", tickSize=0, domain=False)),
            xOffset=alt.XOffset("Severity:N"),
            y=alt.Y("Windows:Q", title="Detection windows", axis=alt.Axis(labelColor="#8295a4", titleColor="#8295a4", gridColor="#243442", domain=False)),
            color=alt.Color("Severity:N", scale=alt.Scale(domain=SEVERITY_ORDER, range=[SEVERITY_COLORS[k] for k in SEVERITY_ORDER]), legend=alt.Legend(title=None, labelColor="#b3c1ca", orient="top", direction="horizontal", symbolType="circle")),
            tooltip=["Traffic:N", "Severity:N", "Windows:Q"],
        )
        .properties(height=290, background="transparent")
        .configure_view(strokeOpacity=0)
    )


normal_data = read_csv(str(NORMAL_BEHAVIOR))
tunnel_data = read_csv(str(TUNNEL_BEHAVIOR))
normal_windows = read_windows(str(NORMAL_WINDOWS))
tunnel_windows = read_windows(str(TUNNEL_WINDOWS))
if not normal_windows:
    st.error(f"Baseline window data is missing or empty: {NORMAL_WINDOWS}")
    st.stop()

baseline = build_baseline(normal_windows)
normal_results = score_windows(normal_windows, baseline)
tunnel_results = score_windows(tunnel_windows, baseline)
normal_counts = count_status(normal_results)
tunnel_counts = count_status(tunnel_results)
flagged = tunnel_counts["HIGH"] + tunnel_counts["CRITICAL"]
normal_alerts = normal_counts["HIGH"] + normal_counts["CRITICAL"]
high_risk_rate = flagged / len(tunnel_results) if tunnel_results else 0
live = read_csv(str(LIVE_FILE))
latest = live.iloc[-1] if not live.empty else None

st.sidebar.markdown(
    '<div class="brand"><div class="brand-mark">◈</div><div><div class="brand-name">DNS Signal</div><div class="brand-sub">Detection lab · local analysis</div></div></div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown('<div class="sidebar-label">Workspace</div>', unsafe_allow_html=True)
view = st.sidebar.radio("Choose a workspace", ["Overview", "Investigate", "Live monitor"], label_visibility="collapsed")
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-label">Detection model</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    '<div class="sidebar-note">Window scores compare entropy, label length, query rate, unique subdomains, and timing against the normal DNS baseline.</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown('<div class="sidebar-label">Severity guide</div>', unsafe_allow_html=True)
for level, threshold in [("LOW", "0–29"), ("MEDIUM", "30–59"), ("HIGH", "60–79"), ("CRITICAL", "80+")]:
    st.sidebar.markdown(
        f'<div style="display:flex;justify-content:space-between;padding:5px 0;color:{SEVERITY_COLORS[level]};font-size:.79rem;font-weight:600"><span>● &nbsp;{level}</span><span style="color:#8295a4;font-family:DM Mono,monospace">{threshold}</span></div>',
        unsafe_allow_html=True,
    )
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-note">Offline datasets are included with this lab. Live results appear here when the detector writes a window.</div>', unsafe_allow_html=True)

st.markdown('<div class="eyebrow">Network security · behavioral analytics</div>', unsafe_allow_html=True)
st.title("DNS tunnel detection")
st.markdown("<div class='lede'>Understand what normal DNS looks like, inspect suspicious behavior, and follow detection scores as traffic arrives.</div>", unsafe_allow_html=True)
st.markdown('<div class="hero-row"><span class="chip"><span class="dot"></span> LOCAL LAB</span><span class="chip">BASELINE MODEL</span><span class="chip">WINDOW LEVEL</span></div>', unsafe_allow_html=True)

if view == "Overview":
    st.markdown('<div class="section-kicker">01 / At a glance</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Normal DNS queries", f"{len(normal_data):,}")
    c2.metric("Tunnel sample queries", f"{len(tunnel_data):,}")
    c3.metric("Baseline windows", f"{len(normal_windows):,}")
    flagged = tunnel_counts["HIGH"] + tunnel_counts["CRITICAL"]
    c4.metric("High risk windows", f"{flagged:,}", delta=f"{high_risk_rate:.0%} of tunnel sample", delta_color="off")

    left, right = st.columns([1.2, .8], gap="large")
    with left:
        st.markdown("## Detection distribution")
        st.caption("Severity assigned to each traffic window by the baseline model.")
        severity_rows = [
            {"Traffic": traffic, "Severity": level, "Windows": counts[level]}
            for traffic, counts in [("Normal DNS", normal_counts), ("DNS tunnel", tunnel_counts)]
            for level in SEVERITY_ORDER
        ]
        st.altair_chart(severity_chart(pd.DataFrame(severity_rows)), use_container_width=True)
    with right:
        st.markdown("## Latest live state")
        if latest is None:
            st.markdown('<div class="state state-idle"><div class="state-icon">◷</div><div><div class="state-title">Waiting for live traffic</div><div class="state-copy">No detection windows have been recorded yet. Start the live detector to see scores here.</div></div></div>', unsafe_allow_html=True)
        else:
            level = str(latest.get("status", "LOW")).upper()
            is_alert = level in ("HIGH", "CRITICAL")
            icon = "!" if is_alert else "✓"
            headline = "Suspicious DNS activity" if is_alert else "No high severity activity"
            st.markdown(f'<div class="state {"state-alert" if is_alert else "state-ok"}"><div class="state-icon" style="color:{SEVERITY_COLORS.get(level, SEVERITY_COLORS["LOW"])}">{icon}</div><div><div class="state-title">{headline}</div><div class="state-copy">Latest window scored <b>{float(latest.get("score", 0)):.1f}</b> and was classified <b style="color:{SEVERITY_COLORS.get(level, SEVERITY_COLORS["LOW"])}">{level}</b>.</div></div></div>', unsafe_allow_html=True)
            st.metric("Latest window", f"{int(latest.get('query_count', 0)):,} queries", delta=f"{float(latest.get('query_rate', 0)):.2f} queries / sec", delta_color="off")

    st.markdown("## Traffic profile")
    st.caption("Average behavioral features across the sample datasets.")
    profile_features = [
        ("Query rate", "query_rate", "queries / sec"),
        ("Unique subdomains", "unique_subdomain_ratio", "ratio"),
        ("Inter-arrival time", "average_inter_arrival", "seconds"),
        ("Shannon entropy", "shannon_entropy", "bits"),
    ]
    profile = pd.DataFrame([
        {"Signal": label, "Normal DNS": mean_of(normal_data, key), "DNS tunnel": mean_of(tunnel_data, key), "Unit": unit}
        for label, key, unit in profile_features
    ])
    st.dataframe(profile.style.format({"Normal DNS": "{:.3f}", "DNS tunnel": "{:.3f}"}), use_container_width=True, hide_index=True)
    with st.expander("How to read this overview"):
        st.markdown(
            f"The baseline is built from **{len(normal_windows)} normal traffic windows**. "
            f"It produces **{normal_alerts} high or critical flags** on that baseline sample and "
            f"**{flagged} high or critical flags** across the tunnel sample. These figures describe "
            "this lab dataset and are not a production accuracy guarantee."
        )

elif view == "Investigate":
    st.markdown('<div class="section-kicker">02 / Detection workbench</div>', unsafe_allow_html=True)
    st.markdown("## Tunnel window investigation")
    st.caption("Filter scored windows by severity, then replay any window to inspect its signals.")
    if not tunnel_results:
        st.info("No tunnel windows are available in the sample dataset.")
    else:
        table = pd.DataFrame([
            {"Window": item["row"]["window_id"], "Queries": item["row"]["query_count"], "Score": item["score"], "Severity": item["status"]}
            for item in tunnel_results
        ])
        default_levels = [level for level in SEVERITY_ORDER if level in table["Severity"].values]
        filter_col, search_col = st.columns([1, 1])
        with filter_col:
            chosen_levels = st.multiselect("Show severity", SEVERITY_ORDER, default=default_levels, placeholder="Choose severity levels")
        with search_col:
            minimum_score = st.slider("Minimum score", min_value=0, max_value=100, value=0)
        filtered = table[table["Severity"].isin(chosen_levels) & (table["Score"] >= minimum_score)]
        download_records = []
        for item in tunnel_results:
            download_records.append({
                "window_id": item["row"]["window_id"],
                "query_count": item["row"]["query_count"],
                "score": item["score"],
                "severity": item["status"],
                **item["row"],
                **{f"signal_{key}": value for key, value in item["signals"].items()},
            })
        all_records = pd.DataFrame(download_records)
        export = all_records[all_records["severity"].isin(chosen_levels) & (all_records["score"] >= minimum_score)]
        st.download_button(
            "Download filtered results · CSV",
            data=export.to_csv(index=False).encode("utf-8"),
            file_name="dns-tunnel-window-analysis.csv",
            mime="text/csv",
            disabled=export.empty,
        )
        results_col, replay_col = st.columns([1.1, .9], gap="large")
        with results_col:
            st.markdown(f"### Scored windows · {len(filtered)} shown")
            st.dataframe(filtered.sort_values("Score", ascending=False), use_container_width=True, hide_index=True, height=390)
        with replay_col:
            st.markdown("### Window replay")
            window_ids = [item["row"]["window_id"] for item in tunnel_results]
            selected_id = st.selectbox("Select a window", window_ids, format_func=lambda item: f"Window {item:02d}")
            result = next(item for item in tunnel_results if item["row"]["window_id"] == selected_id)
            score_col, status_col = st.columns(2)
            score_col.metric("Detection score", f"{result['score']:.1f} / 100")
            status_col.metric("Classification", result["status"])
            feature_labels = {
                "average_entropy": "Average entropy",
                "average_label_length": "Label length",
                "query_rate": "Query rate",
                "unique_subdomain_ratio": "Unique subdomains",
                "inter_arrival_cv": "Timing variation",
                "burstiness": "Burstiness",
            }
            feature_frame = pd.DataFrame([{"Signal": label, "Value": result["row"].get(key, 0)} for key, label in feature_labels.items()])
            st.dataframe(feature_frame.style.format({"Value": "{:.3f}"}), use_container_width=True, hide_index=True)

        st.markdown("## Signal contributions")
        signal_totals = {}
        for result in tunnel_results:
            for signal, value in result["signals"].items():
                signal_totals[signal.replace("_", " ").title()] = signal_totals.get(signal.replace("_", " ").title(), 0) + value
        signal_data = pd.DataFrame([{"Signal": signal, "Average contribution": value / len(tunnel_results)} for signal, value in signal_totals.items()])
        signal_chart = (
            alt.Chart(signal_data)
            .mark_bar(cornerRadiusEnd=5, color="#56c9a4", size=23)
            .encode(
                x=alt.X("Average contribution:Q", title="Average score contribution", axis=alt.Axis(labelColor="#8295a4", titleColor="#8295a4", gridColor="#243442", domain=False)),
                y=alt.Y("Signal:N", sort="-x", title=None, axis=alt.Axis(labelColor="#a5b5c1", domain=False)),
                tooltip=[alt.Tooltip("Signal:N"), alt.Tooltip("Average contribution:Q", format=".2f")],
            ).properties(height=220, background="transparent").configure_view(strokeOpacity=0)
        )
        st.altair_chart(signal_chart, use_container_width=True)
        st.markdown(f'<div class="surface"><div class="surface-title">Assessment</div><div class="surface-copy">{flagged} of {len(tunnel_results)} tunnel windows ({high_risk_rate:.0%}) scored HIGH or CRITICAL. Scores combine entropy, label length, query rate, subdomain uniqueness, and timing behavior against the normal traffic baseline.</div></div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="section-kicker">03 / Live telemetry</div>', unsafe_allow_html=True)
    st.markdown("## Live DNS monitor")
    refresh_col, interval_col = st.columns([1, 1])
    with refresh_col:
        refresh_now = st.button("↻  Refresh live data")
    with interval_col:
        refresh_interval = st.selectbox("Automatic refresh", ["Off", "5 seconds", "15 seconds", "30 seconds"], index=0)
    if refresh_now:
        read_csv.clear()
        st.rerun()

    def render_live_monitor():
        current_live = read_csv(str(LIVE_FILE))
        if current_live.empty:
            st.markdown('<div class="state state-idle"><div class="state-icon">◷</div><div><div class="state-title">No live windows yet</div><div class="state-copy">Start the capture and live detector. Recorded windows will appear in this workspace.</div></div></div>', unsafe_allow_html=True)
            return

        latest_window = current_live.iloc[-1]
        latest_status = str(latest_window.get("status", "LOW")).upper()
        if latest_status not in SEVERITY_COLORS:
            latest_status = "LOW"
        latest_score = float(latest_window.get("score", 0))
        latest_time = str(latest_window.get("timestamp", "Unknown time"))
        alert_class = "state-alert" if latest_status in ("HIGH", "CRITICAL") else "state-ok"
        st.markdown(f'<div class="state {alert_class}"><div class="state-icon" style="color:{SEVERITY_COLORS[latest_status]}">●</div><div><div class="state-title">Latest window · {latest_status}</div><div class="state-copy">Score <b>{latest_score:.1f}</b> · captured at <span class="mono">{latest_time}</span></div></div></div>', unsafe_allow_html=True)

        live_count = len(current_live)
        live_alerts = int(current_live["status"].astype(str).str.upper().isin(["HIGH", "CRITICAL"]).sum()) if "status" in current_live else 0
        alert_rate = live_alerts / live_count if live_count else 0
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Queries in window", f"{int(latest_window.get('query_count', 0)):,}")
        m2.metric("Query rate", f"{float(latest_window.get('query_rate', 0)):.2f} q/s")
        m3.metric("Detection score", f"{latest_score:.1f} / 100")
        m4.metric("High risk windows", f"{live_alerts:,}", delta=f"{alert_rate:.0%} of {live_count} windows", delta_color="off")
        st.download_button(
            "Download live log · CSV",
            data=current_live.to_csv(index=False).encode("utf-8"),
            file_name="dns-live-detection-log.csv",
            mime="text/csv",
        )
        st.markdown("## Score timeline")
        if "timestamp" in current_live and "score" in current_live:
            timeline_data = current_live[["timestamp", "score"]].copy()
            timeline_data["timestamp"] = pd.to_datetime(timeline_data["timestamp"], errors="coerce")
            timeline_data["score"] = pd.to_numeric(timeline_data["score"], errors="coerce")
            score_line = (
                alt.Chart(timeline_data.dropna())
                .mark_line(point=alt.OverlayMarkDef(filled=True, size=45), strokeWidth=2.5, color="#58d6ad")
                .encode(
                    x=alt.X("timestamp:T", title=None, axis=alt.Axis(labelColor="#8295a4", titleColor="#8295a4", gridColor="#243442", domain=False)),
                    y=alt.Y("score:Q", title="Detection score", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#8295a4", titleColor="#8295a4", gridColor="#243442", domain=False)),
                    tooltip=[alt.Tooltip("timestamp:T", title="Time"), alt.Tooltip("score:Q", format=".1f")],
                )
            )
            threshold_data = pd.DataFrame([
                {"threshold": 30, "label": "MEDIUM threshold"},
                {"threshold": 60, "label": "HIGH threshold"},
                {"threshold": 80, "label": "CRITICAL threshold"},
            ])
            threshold_lines = alt.Chart(threshold_data).mark_rule(strokeDash=[5, 5], opacity=.72).encode(
                y="threshold:Q",
                color=alt.Color("label:N", scale=alt.Scale(
                    domain=["MEDIUM threshold", "HIGH threshold", "CRITICAL threshold"],
                    range=[SEVERITY_COLORS["MEDIUM"], SEVERITY_COLORS["HIGH"], SEVERITY_COLORS["CRITICAL"]],
                ), legend=None),
                tooltip=["label:N", "threshold:Q"],
            )
            timeline = (score_line + threshold_lines).properties(height=300, background="transparent").configure_view(strokeOpacity=0)
            st.altair_chart(timeline, use_container_width=True)

        signal_columns = {
            "entropy_signal": "Entropy",
            "long_label_signal": "Long labels",
            "query_rate_signal": "Query rate",
            "unique_subdomain_signal": "Unique subdomains",
            "timing_signal": "Timing",
        }
        present_signals = [(column, label) for column, label in signal_columns.items() if column in current_live.columns]
        if present_signals:
            st.markdown("## Latest signal contributions")
            contribution_data = pd.DataFrame([{"Signal": label, "Contribution": pd.to_numeric(pd.Series([latest_window[column]]), errors="coerce").iloc[0]} for column, label in present_signals])
            contribution_chart = alt.Chart(contribution_data).mark_bar(cornerRadiusEnd=5, color="#56c9a4", size=22).encode(
                x=alt.X("Contribution:Q", title="Score contribution", axis=alt.Axis(labelColor="#8295a4", titleColor="#8295a4", gridColor="#243442", domain=False)),
                y=alt.Y("Signal:N", sort="-x", title=None, axis=alt.Axis(labelColor="#a5b5c1", domain=False)),
                tooltip=["Signal:N", alt.Tooltip("Contribution:Q", format=".2f")],
            ).properties(height=190, background="transparent").configure_view(strokeOpacity=0)
            st.altair_chart(contribution_chart, use_container_width=True)

        st.markdown("## Recent detection windows")
        recent_cols = ["timestamp", "query_count", "query_rate", "average_entropy", "unique_subdomain_ratio", "score", "status"]
        available = [column for column in recent_cols if column in current_live.columns]
        controls_col, count_col = st.columns([1, 1])
        levels_in_log = [level for level in SEVERITY_ORDER if "status" in current_live and level in current_live["status"].astype(str).str.upper().values]
        with controls_col:
            shown_levels = st.multiselect("Filter severity", SEVERITY_ORDER, default=levels_in_log)
        with count_col:
            row_limit = st.slider("Windows to show", min_value=5, max_value=100, value=10, step=5)
        recent_source = current_live[current_live["status"].astype(str).str.upper().isin(shown_levels)] if "status" in current_live else current_live
        recent = recent_source.tail(row_limit)[available].copy().iloc[::-1]
        st.dataframe(recent, use_container_width=True, hide_index=True)

    if refresh_interval == "Off":
        render_live_monitor()
    else:
        interval_seconds = int(refresh_interval.split()[0])

        @st.fragment(run_every=interval_seconds)
        def live_monitor_fragment():
            render_live_monitor()

        live_monitor_fragment()

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="sidebar-note" style="text-align:center">DNS Signal · Local analysis workspace · Scores are produced by the configured baseline detector</div>', unsafe_allow_html=True)
