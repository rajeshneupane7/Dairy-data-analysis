import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────
API_UPLOAD_URL    = "http://backend:8000/upload"
API_INSIGHTS_URL  = "http://backend:8000/generate_insights"
API_CHAT_URL      = "http://backend:8000/chat"          # NEW: chatbox endpoint

st.set_page_config(
    page_title="Dairy Assistant AI | TAMU Dairy Lab",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Design Tokens & CSS ──────────────────────────────────────────────────────
# Root issue: white / light-gray text on a very-light gradient → invisible.
# Fix: enforce high-contrast text (#1a1a2e on white cards) and keep the
# gradient only as a subtle tint rather than the full page background.
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* ── CSS Variables ── */
:root {
    --navy:        #1a2b4a;
    --navy-mid:    #1e3d59;
    --coral:       #e8563a;
    --coral-light: #ff7f5c;
    --cream:       #fdf8f3;
    --white:       #ffffff;
    --gray-100:    #f4f6f9;
    --gray-200:    #e8ecf1;
    --gray-600:    #4a5568;
    --gray-800:    #1a202c;
    --green:       #2d7a5f;
    --amber:       #c8811a;
    --radius:      12px;
}

/* ── Global Resets ── */
html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--cream) !important;
    color: var(--gray-800) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--navy) !important;
    color: var(--white) !important;
}
[data-testid="stSidebar"] * {
    color: var(--white) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--coral);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    width: 100%;
    padding: 0.6rem;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--coral-light);
}
[data-testid="stSidebar"] .stFileUploader label,
[data-testid="stSidebar"] .stFileUploader * {
    color: var(--white) !important;
}

/* ── Hero Section ── */
.hero-wrap {
    background: linear-gradient(135deg, var(--navy) 0%, #2a4a72 60%, #3a6b9e 100%);
    border-radius: 18px;
    padding: 3rem 2.5rem;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(26,43,74,0.25);
}
.hero-wrap::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(circle at 70% 30%, rgba(232,86,58,0.15) 0%, transparent 60%);
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(2rem, 5vw, 3.4rem);
    color: var(--white) !important;
    margin: 0 0 0.4rem;
    line-height: 1.1;
    position: relative;
}
.hero-sub {
    font-size: 1.25rem;
    color: var(--coral-light) !important;
    font-weight: 500;
    margin-bottom: 1.2rem;
    position: relative;
}
.hero-body {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.82) !important;
    max-width: 720px;
    margin: 0 auto;
    line-height: 1.7;
    position: relative;
}

/* ── Feature Cards ── */
.feat-card {
    background: var(--white);
    border-radius: var(--radius);
    padding: 1.6rem;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    border-top: 4px solid var(--coral);
    height: 100%;
    transition: transform 0.2s, box-shadow 0.2s;
}
.feat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.12);
}
.feat-card h3 {
    color: var(--navy) !important;
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    margin: 0 0 0.6rem;
}
.feat-card p {
    color: var(--gray-600) !important;
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 0;
}

/* ── KPI Metric Cards ── */
[data-testid="stMetric"] {
    background: var(--white);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-left: 4px solid var(--coral);
}
[data-testid="stMetricLabel"] { color: var(--gray-600) !important; font-size: 0.85rem; }
[data-testid="stMetricValue"] { color: var(--navy) !important; font-weight: 700; font-size: 1.7rem; }

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--gray-100);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--gray-600) !important;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--white) !important;
    color: var(--navy) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.10);
}

/* ── Alert Boxes ── */
.alert-card {
    background: #fff5f5;
    border-left: 5px solid #e53e3e;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    color: #742a2a !important;
    font-size: 0.95rem;
    font-weight: 500;
}
.alert-card.warn {
    background: #fffbeb;
    border-color: var(--amber);
    color: #7b4f12 !important;
}
.alert-card .alert-title {
    font-weight: 700;
    color: inherit !important;
    margin-bottom: 0.25rem;
}

/* ── Chatbox ── */
.chat-wrap {
    background: var(--white);
    border-radius: var(--radius);
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    overflow: hidden;
    border: 1px solid var(--gray-200);
    margin-top: 1.5rem;
}
.chat-header {
    background: var(--navy);
    color: var(--white) !important;
    padding: 0.9rem 1.4rem;
    font-weight: 700;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.chat-messages {
    padding: 1.2rem;
    min-height: 260px;
    max-height: 420px;
    overflow-y: auto;
    background: var(--gray-100);
}
.msg-user {
    background: var(--navy);
    color: var(--white) !important;
    border-radius: 16px 16px 4px 16px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.6rem;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.92rem;
    width: fit-content;
    text-align: right;
}
.msg-ai {
    background: var(--white);
    color: var(--gray-800) !important;
    border-radius: 16px 16px 16px 4px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.6rem;
    max-width: 80%;
    font-size: 0.92rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    width: fit-content;
}
.msg-label {
    font-size: 0.72rem;
    margin-bottom: 2px;
    color: var(--gray-600) !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Section Headers ── */
.section-h {
    font-family: 'DM Serif Display', serif;
    color: var(--navy) !important;
    font-size: 1.5rem;
    margin: 0.5rem 0 1.2rem;
    border-bottom: 2px solid var(--coral);
    padding-bottom: 0.4rem;
}

/* ── Insight Expanders ── */
[data-testid="stExpander"] {
    background: var(--white) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--gray-200) !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
[data-testid="stExpander"] summary {
    color: var(--navy) !important;
    font-weight: 600;
}
[data-testid="stExpander"] p {
    color: var(--gray-600) !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

/* ── Download / Success ── */
.stDownloadButton > button {
    background: var(--navy);
    color: white !important;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    padding: 0.55rem 1.4rem;
}
.stDownloadButton > button:hover { background: var(--coral); }

/* ── Footer ── */
.tamu-footer {
    background: var(--navy);
    color: rgba(255,255,255,0.7) !important;
    text-align: center;
    padding: 0.8rem;
    font-size: 0.8rem;
    margin-top: 3rem;
    border-radius: var(--radius);
}

/* ── Spinner & Info ── */
.stSpinner > div { color: var(--coral) !important; }
.stInfo { background: #e8f4fd !important; color: var(--navy) !important; }
.stSuccess { color: var(--green) !important; }

/* ── Inputs ── */
.stTextInput input {
    border-radius: 8px !important;
    border: 1.5px solid var(--gray-200) !important;
    color: var(--gray-800) !important;
    background: var(--white) !important;
    font-size: 0.95rem !important;
}
.stTextInput input:focus {
    border-color: var(--coral) !important;
    box-shadow: 0 0 0 3px rgba(232,86,58,0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "ai", "content": "👋 Hello! I'm your Dairy AI Assistant. Ask me anything about your herd data, milk production, SCC trends, or nutritional recommendations."}
    ]

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center; padding:0.5rem 0 1rem;'>"
        "<span style='font-size:3.5rem;'>🐄</span>"
        "<div style='font-family:DM Serif Display,serif; font-size:1.2rem; color:white; margin-top:4px;'>Dairy Assistant AI</div>"
        "<div style='font-size:0.75rem; color:rgba(255,255,255,0.6);'>TAMU Dairy System Lab</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("**📂 Herd Management**")
    uploaded_file = st.file_uploader(
        "Upload Farm Records",
        type=["csv", "xlsx"],
        help="Upload yield, SCC, health, or feed data in CSV/Excel format.",
    )

    st.markdown("---")
    st.markdown("**🛠 AI Capabilities**")
    for cap in [
        "✅ Smart Column Mapping",
        "✅ Health Outlier Detection",
        "✅ Generative Visualizations",
        "✅ Natural Language Chat",
        "✅ SCC & Fat % Alerts",
    ]:
        st.markdown(f"<span style='color:rgba(255,255,255,0.85); font-size:0.88rem;'>{cap}</span>", unsafe_allow_html=True)

    if uploaded_file:
        st.markdown("---")
        if st.button("🔄 Reset Session"):
            st.session_state.chat_history = [
                {"role": "ai", "content": "Session reset. Upload a new file to get started."}
            ]
            st.rerun()

# ─── Helper: render chat history ──────────────────────────────────────────────
def render_chat():
    msgs_html = ""
    for m in st.session_state.chat_history:
        if m["role"] == "user":
            msgs_html += (
                f"<div class='msg-label' style='text-align:right; margin-left:auto;'>You</div>"
                f"<div class='msg-user'>{m['content']}</div>"
            )
        else:
            msgs_html += (
                f"<div class='msg-label'>🐄 Dairy AI</div>"
                f"<div class='msg-ai'>{m['content']}</div>"
            )
    return msgs_html


def chatbox_widget(context: str = ""):
    """Renders the central chatbox. `context` is a JSON string of the current dataset summary."""
    st.markdown(
        """
        <div class='chat-wrap'>
          <div class='chat-header'>💬 Ask Your Dairy AI Assistant</div>
          <div class='chat-messages' id='chat-scroll'>
        """
        + render_chat()
        + "</div></div>",
        unsafe_allow_html=True,
    )

    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        user_input = st.text_input(
            "message",
            label_visibility="collapsed",
            placeholder="e.g.  'Which cows have the lowest fat %?' or 'Explain SCC thresholds'",
            key="chat_input_field",
        )
    with col_btn:
        send = st.button("Send →", use_container_width=True)

    if send and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
        # ── Call backend chat endpoint (graceful fallback if unavailable) ──
        ai_reply = _get_ai_reply(user_input.strip(), context)
        st.session_state.chat_history.append({"role": "ai", "content": ai_reply})
        st.rerun()


def _get_ai_reply(question: str, context: str) -> str:
    """Posts to backend chat endpoint; falls back to a helpful static message."""
    try:
        resp = requests.post(
            API_CHAT_URL,
            json={"question": question, "context": context},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("answer", "No response from model.")
    except Exception:
        pass
    # ── Graceful fallback so UI never breaks ──
    return (
        "⚠️ The AI backend is currently unreachable. "
        "Once the backend is running at <code>http://backend:8000/chat</code>, "
        "I'll answer your questions about SCC, milk yield trends, nutritional flags, and more."
    )


# ─── Landing Page (no file uploaded) ─────────────────────────────────────────
if uploaded_file is None:

    st.markdown("""
    <div class='hero-wrap'>
        <div class='hero-title'>🐄 Dairy Assistant AI</div>
        <div class='hero-sub'>Empowering Producers with Precision Herd Analytics</div>
        <div class='hero-body'>
            Transform raw farm records into actionable intelligence — automatically
            standardize data, detect critical health trends, and unlock AI-generated
            insights for every cow in your operation.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    cards = [
        ("🔍 Smart Analysis",
         "Upload any CSV or Excel file. Our LLM engine maps your columns automatically — "
         "no template required."),
        ("🚨 Proactive Alerts",
         "Instantly flag cows with >20 % production drops, elevated SCC, or nutritional "
         "imbalances before they escalate."),
        ("📊 AI-Generated Visuals",
         "The model suggests and renders custom charts tailored to the unique patterns "
         "found in your specific dataset."),
    ]
    for col, (title, body) in zip([c1, c2, c3], cards):
        with col:
            st.markdown(
                f"<div class='feat-card'><h3>{title}</h3><p>{body}</p></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Central Chatbox (no data loaded yet) ──────────────────────────────
    st.markdown("<div class='section-h'>💬 Ask the AI — No Data Needed</div>", unsafe_allow_html=True)
    st.caption("Ask general dairy science questions while you prepare your file.")
    chatbox_widget()

# ─── Main Dashboard (file uploaded) ──────────────────────────────────────────
else:
    with st.spinner("AI Assistant is processing your herd data…"):
        try:
            files   = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            resp    = requests.post(API_UPLOAD_URL, files=files)

            if resp.status_code == 200:
                result = resp.json()
                df     = pd.DataFrame(result["data"])
                alerts = result.get("alerts", [])

                # Dataset context string for chatbox
                data_ctx = (
                    f"Columns: {list(df.columns)}. "
                    f"Rows: {len(df)}. "
                    f"Sample (first 3 rows): {df.head(3).to_dict(orient='records')}"
                )

                st.success(
                    f"✅ Processing complete — **{result['rows']}** records analysed from **{uploaded_file.name}**"
                )

                # ── Tabs ──────────────────────────────────────────────────
                tab_ai, tab_chat, tab_analytics, tab_raw = st.tabs([
                    "🤖 Smart Assistant",
                    "💬 AI Chatbox",
                    "📈 Operational Analytics",
                    "📋 Data Registry",
                ])

                # ────────── Tab 1 · Smart Assistant ──────────────────────
                with tab_ai:
                    st.markdown("<div class='section-h'>Critical Alerts & AI Insights</div>",
                                unsafe_allow_html=True)

                    if alerts:
                        for alert in alerts:
                            css_class = "alert-card" if alert["severity"] == "High" else "alert-card warn"
                            st.markdown(
                                f"<div class='{css_class}'>"
                                f"<div class='alert-title'>{alert['type']}</div>"
                                f"{alert['message']}"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.balloons()
                        st.success("All systems normal — no critical health or production anomalies detected.")

                    st.markdown("---")
                    st.markdown("#### ✨ AI-Suggested Visualizations")

                    with st.spinner("Consulting model for deeper patterns…"):
                        try:
                            ins_resp = requests.post(
                                API_INSIGHTS_URL,
                                json={"columns": list(df.columns)},
                            )
                            if ins_resp.status_code == 200:
                                ai_insights = ins_resp.json()
                                insights_list = (
                                    ai_insights["result"]
                                    if isinstance(ai_insights, dict) and "result" in ai_insights
                                    else ai_insights if isinstance(ai_insights, list)
                                    else []
                                )
                                if insights_list:
                                    cols = st.columns(2)
                                    for i, ins in enumerate(insights_list):
                                        with cols[i % 2]:
                                            with st.expander(f"📊 {ins.get('title','Insight')}", expanded=True):
                                                st.write(ins.get("justification", ""))
                                                ctype = ins.get("chart_type", "").lower()
                                                x_col = ins.get("x")
                                                y_col = ins.get("y")
                                                if x_col in df.columns:
                                                    fig = None
                                                    if ctype == "bar" and y_col in df.columns:
                                                        fig = px.bar(df, x=x_col, y=y_col,
                                                                     color_discrete_sequence=["#1a2b4a"])
                                                    elif ctype == "line" and y_col in df.columns:
                                                        pdf = df.sort_values(by=x_col) if x_col == "date" else df
                                                        fig = px.line(pdf, x=x_col, y=y_col, markers=True)
                                                    elif ctype == "scatter" and y_col in df.columns:
                                                        fig = px.scatter(df, x=x_col, y=y_col, trendline="ols")
                                                    elif ctype == "histogram":
                                                        fig = px.histogram(df, x=x_col, nbins=30)
                                                    if fig:
                                                        fig.update_layout(
                                                            margin=dict(l=20, r=20, t=30, b=20),
                                                            plot_bgcolor="white",
                                                            paper_bgcolor="white",
                                                            font_color="#1a202c",
                                                        )
                                                        st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not load AI insights: {e}")

                # ────────── Tab 2 · Chatbox ───────────────────────────────
                with tab_chat:
                    st.markdown("<div class='section-h'>Ask Your Dairy AI Assistant</div>",
                                unsafe_allow_html=True)
                    st.caption(
                        "Your dataset is loaded as context. Ask about specific cows, trends, "
                        "SCC thresholds, feeding adjustments, or anything herd-related."
                    )
                    chatbox_widget(context=data_ctx)

                # ────────── Tab 3 · Operational Analytics ─────────────────
                with tab_analytics:
                    st.markdown("<div class='section-h'>Herd Performance Overview</div>",
                                unsafe_allow_html=True)
                    k1, k2, k3, k4 = st.columns(4)

                    if "milk_yield" in df.columns:
                        k1.metric("Total Yield (L)",   f"{df['milk_yield'].sum():,.1f}")
                        k2.metric("Avg Yield / Cow",   f"{df['milk_yield'].mean():.2f} L")
                    if "cow_id" in df.columns:
                        k3.metric("Monitored Cows",    f"{df['cow_id'].nunique()}")
                    if "fat_percentage" in df.columns:
                        k4.metric("Avg Fat %",         f"{df['fat_percentage'].mean():.2f}%")

                    st.markdown("---")
                    col_l, col_r = st.columns(2)

                    if "date" in df.columns and "milk_yield" in df.columns:
                        daily   = df.groupby("date")["milk_yield"].sum().reset_index()
                        fig_trn = px.area(
                            daily, x="date", y="milk_yield",
                            title="Herd Production Trend",
                            color_discrete_sequence=["#e8563a"],
                        )
                        fig_trn.update_layout(
                            plot_bgcolor="white", paper_bgcolor="white",
                            font_color="#1a202c",
                        )
                        col_l.plotly_chart(fig_trn, use_container_width=True)

                    if "milk_yield" in df.columns:
                        fig_box = px.box(
                            df, y="milk_yield",
                            title="Yield Distribution (Variance Analysis)",
                            color_discrete_sequence=["#1a2b4a"],
                        )
                        fig_box.update_layout(
                            plot_bgcolor="white", paper_bgcolor="white",
                            font_color="#1a202c",
                        )
                        col_r.plotly_chart(fig_box, use_container_width=True)

                # ────────── Tab 4 · Data Registry ─────────────────────────
                with tab_raw:
                    st.markdown("<div class='section-h'>Standardized Data Registry</div>",
                                unsafe_allow_html=True)
                    st.caption("Data automatically cleaned and standardized by the AI engine.")
                    st.dataframe(df, use_container_width=True)
                    st.download_button(
                        "⬇️ Export Standardized CSV",
                        df.to_csv(index=False),
                        "standardized_herd_data.csv",
                        "text/csv",
                    )

        except requests.RequestException as e:
            st.error(
                f"**Backend Unreachable.** "
                f"Ensure the FastAPI server is running at `http://backend:8000`. Error: `{e}`"
            )

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='tamu-footer'>"
    "© 2024 TAMU Dairy System Lab · Texas A&M University · "
    "Empowering Sustainable Dairy Production through Precision AI"
    "</div>",
    unsafe_allow_html=True,
)