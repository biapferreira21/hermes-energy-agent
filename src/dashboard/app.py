import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st
import yaml

from src.db import SessionLocal, init_db
from src.models import ResearchItem

BASE_DIR = Path(__file__).parent.parent.parent

# -----------------------------------------------------------------
# Page config
# -----------------------------------------------------------------
st.set_page_config(
    page_title="Repsol Energy Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------
# Load Repsol SVG logo (base64)
# -----------------------------------------------------------------
_logo_path = BASE_DIR / "src/dashboard/assets/repsol_logo.svg"
if _logo_path.exists():
    _svg = _logo_path.read_text(encoding="utf-8").replace('fill="#001E37"', 'fill="#FFFFFF"')
    _logo_b64 = base64.b64encode(_svg.encode()).decode()
else:
    _logo_b64 = ""

# -----------------------------------------------------------------
# Premium dark CSS
# -----------------------------------------------------------------
st.markdown(f"""
<style>
/* ── Global background ── */
.stApp {{
    background: #070F1E;
    background-image:
        radial-gradient(ellipse 80% 50% at 10% 0%, rgba(255,98,0,0.08) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 100%, rgba(0,31,91,0.5) 0%, transparent 60%);
}}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer {{visibility: hidden;}}

/* ── Header ── */
.hermes-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 32px 18px 32px;
    background: linear-gradient(135deg, rgba(255,98,0,0.12) 0%, rgba(10,20,45,0.95) 60%);
    border: 1px solid rgba(255,98,0,0.25);
    border-radius: 14px;
    margin-bottom: 28px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 40px rgba(255,98,0,0.08), inset 0 1px 0 rgba(255,255,255,0.05);
}}
.hermes-header .logo-block {{
    display: flex;
    align-items: center;
    gap: 20px;
}}
.hermes-header .logo-block img {{
    height: 40px;
}}
.hermes-header .divider {{
    width: 1px;
    height: 36px;
    background: rgba(255,98,0,0.5);
}}
.hermes-header .title-block h1 {{
    color: #F0F4FF !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    letter-spacing: -0.2px;
    line-height: 1.2;
}}
.hermes-header .title-block .sub {{
    color: rgba(200,215,255,0.55);
    font-size: 0.78rem;
    margin-top: 3px;
    letter-spacing: 0.3px;
}}
.hermes-badge {{
    background: linear-gradient(135deg, #FF6200, #FF8C42);
    color: white;
    font-size: 0.65rem;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 1px;
    text-transform: uppercase;
    display: inline-block;
    margin-left: 10px;
    vertical-align: middle;
    box-shadow: 0 2px 12px rgba(255,98,0,0.4);
}}
.hermes-header .right-info {{
    text-align: right;
    color: rgba(200,215,255,0.4);
    font-size: 0.72rem;
    line-height: 1.6;
}}
.hermes-header .right-info span {{
    color: rgba(255,98,0,0.8);
    font-weight: 600;
}}

/* ── Section titles ── */
.section-title {{
    color: #E0E8FF;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    border-left: 3px solid #FF6200;
    padding-left: 12px;
    margin: 24px 0 10px 0;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,98,0,0.2);
    border-top: 2px solid #FF6200;
    border-radius: 10px;
    padding: 14px 16px !important;
    backdrop-filter: blur(8px);
    transition: border-color 0.2s;
}}
[data-testid="metric-container"]:hover {{
    border-color: rgba(255,98,0,0.45);
    border-top-color: #FF8C42;
}}
[data-testid="metric-container"] label {{
    color: rgba(200,215,255,0.55) !important;
    font-weight: 600 !important;
    font-size: 0.68rem !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: #FF6200 !important;
    font-weight: 800 !important;
    font-size: 1.7rem !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid rgba(255,98,0,0.15) !important;
    border-radius: 10px !important;
    overflow: hidden;
    background: rgba(7,15,30,0.8);
}}

/* ── Filter bar ── */
.filter-bar {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,98,0,0.12);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 16px;
}}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select {{
    background: rgba(7,15,30,0.9) !important;
    border-color: rgba(255,98,0,0.25) !important;
    color: #E0E8FF !important;
}}

/* ── Horizontal divider ── */
hr {{
    border-color: rgba(255,98,0,0.15) !important;
    margin: 20px 0;
}}

/* ── Caption / small text ── */
[data-testid="stCaptionContainer"] p {{
    color: rgba(200,215,255,0.45) !important;
}}

/* ── Article detail card ── */
.detail-card {{
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,98,0,0.2);
    border-radius: 12px;
    padding: 24px 28px;
    margin-top: 12px;
}}
.detail-card h3 {{
    color: #F0F4FF;
    font-size: 1.05rem;
    margin-bottom: 12px;
}}

/* ── Footer ── */
.hermes-footer {{
    text-align: center;
    color: rgba(200,215,255,0.25);
    font-size: 0.7rem;
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid rgba(255,98,0,0.1);
    letter-spacing: 0.3px;
}}
.hermes-footer span {{
    color: rgba(255,98,0,0.5);
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------
# Header
# -----------------------------------------------------------------
st.markdown(f"""
<div class="hermes-header">
    <div class="logo-block">
        <img src="data:image/svg+xml;base64,{_logo_b64}" alt="Repsol" />
        <div class="divider"></div>
        <div class="title-block">
            <h1>Repsol Energy Research Agent <span class="hermes-badge">INTELLIGENCE</span></h1>
            <div class="sub">Financial Investments · Energy &amp; Commodity Markets · Blockchain &amp; RWA</div>
        </div>
    </div>
    <div class="right-info">
        <span>INTERNAL USE ONLY</span><br>
        Not investment advice
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------
# Load data
# -----------------------------------------------------------------
init_db()
from src.db import engine as _engine
st.caption(f"🔧 DEBUG — DB: `{_engine.url}` | exists: `{Path(str(_engine.url).replace('sqlite:///','/')).exists()}`")
session = SessionLocal()
rows = (
    session.query(ResearchItem)
    .order_by(ResearchItem.id.desc())
    .limit(1000)
    .all()
)
session.close()

data = []
for r in rows:
    data.append({
        "id": r.id,
        "titulo": r.title,
        "fonte": r.source or "",
        "score": float(r.signal_score or 0),
        "asset_classes": r.asset_classes or "[]",
        "empresas": r.companies or "[]",
        "instituicoes": r.institutions or "[]",
        "blockchain": r.blockchain_relation or "",
        "tokenizacao": bool(r.tokenization),
        "stablecoin": bool(r.stablecoin_relation),
        "relevancia_fin": r.financial_relevance or "",
        "sentimento": getattr(r, "market_sentiment", "") or "",
        "driver": getattr(r, "price_driver", "") or "",
        "horizonte": getattr(r, "time_horizon", "") or "",
        "url": r.url or "",
        "resumo": r.summary or "",
        "data_pub": r.published_at or "",
    })

df = pd.DataFrame(data)

# -----------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------
@st.cache_data
def load_keywords_entities():
    keywords, entities = [], []
    try:
        kw = yaml.safe_load((BASE_DIR / "config/keywords.yaml").read_text(encoding="utf-8"))
        for g in kw.values():
            keywords.extend(str(k) for k in g)
    except Exception:
        pass
    try:
        ent = yaml.safe_load((BASE_DIR / "config/entities.yaml").read_text(encoding="utf-8"))
        for g in ent.values():
            entities.extend(str(e) for e in g)
    except Exception:
        pass
    return keywords, entities


def kw_score(row, keywords, entities):
    text = (row["titulo"] + " " + row["resumo"]).lower()
    s = sum(1 for k in keywords if k.lower() in text)
    s += sum(2 for e in entities if e.lower() in text)
    try:
        s += len(json.loads(row["empresas"] or "[]"))
        s += len(json.loads(row["instituicoes"] or "[]"))
    except Exception:
        pass
    return s


_SENTIMENT = {
    "bullish": "🟢 Bullish", "bearish": "🔴 Bearish",
    "neutral": "⚪ Neutral", "mixed": "🟡 Mixed", "unclear": "—",
}
_DRIVER = {
    "supply": "Oferta", "demand": "Procura", "geopolitical": "Geopolítica",
    "regulatory": "Regulação", "financial": "Financeiro",
    "corporate": "Corporate", "none": "—",
}

# -----------------------------------------------------------------
# Metrics
# -----------------------------------------------------------------
if not df.empty:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total artigos", len(df))
    c2.metric("Score médio", f"{df['score'].mean():.0f}")
    high_fin = int((df["relevancia_fin"] == "high").sum())
    c3.metric("Alta relevância fin.", high_fin)
    c4.metric("Com blockchain", int(
        (df["blockchain"].notna() & (df["blockchain"] != "") & (df["blockchain"] != "none")).sum()
    ))
    c5.metric("Tokenização", int(df["tokenizacao"].sum()))

st.markdown("---")

# -----------------------------------------------------------------
# TOP 25
# -----------------------------------------------------------------
st.markdown('<div class="section-title">Top 25 — Intelligence de Investimento</div>', unsafe_allow_html=True)
st.caption("Ranking por score financeiro + relevância para keywords e entidades configuradas")

if not df.empty:
    keywords, entities = load_keywords_entities()
    df["kw_score"] = df.apply(lambda r: kw_score(r, keywords, entities), axis=1)
    df["score_total"] = df["score"] + df["kw_score"].clip(upper=20)

    top25 = df.nlargest(25, "score_total").copy().reset_index(drop=True)
    top25.index = top25.index + 1

    table_data = []
    for rank, row in top25.iterrows():
        table_data.append({
            "#": int(rank),
            "Score": int(row["score_total"]),
            "Sentimento": _SENTIMENT.get(row["sentimento"], "—"),
            "Driver": _DRIVER.get(row["driver"], row["driver"] or "—"),
            "Horizonte": row["horizonte"].replace("_", " ") if row["horizonte"] else "—",
            "Fonte": row["fonte"],
            "Notícia": row["titulo"],
            "URL": row["url"],
        })

    tdf = pd.DataFrame(table_data)

    st.dataframe(
        tdf,
        column_config={
            "#":          st.column_config.NumberColumn("#", width=40),
            "Score":      st.column_config.ProgressColumn("Score", min_value=0, max_value=100, width=90),
            "Sentimento": st.column_config.TextColumn("Sentimento", width=110),
            "Driver":     st.column_config.TextColumn("Driver", width=100),
            "Horizonte":  st.column_config.TextColumn("Horizonte", width=110),
            "Fonte":      st.column_config.TextColumn("Fonte", width=130),
            "Notícia":    st.column_config.TextColumn("Notícia", width=420),
            "URL":        st.column_config.LinkColumn("Link", display_text="Abrir →", width=80),
        },
        hide_index=True,
        use_container_width=True,
        height=700,
    )
else:
    st.info("Sem artigos. Corre o pipeline primeiro com INICIAR_HERMES.bat")

st.markdown("---")

# -----------------------------------------------------------------
# Filters + full list
# -----------------------------------------------------------------
st.markdown('<div class="section-title">Todos os Artigos</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
with col1:
    search_term = st.text_input("Pesquisar título / resumo", "")
with col2:
    blockchain_filter = st.selectbox("Blockchain", [
        "todas", "none", "tokenization", "stablecoin_settlement",
        "tokenized_deposits", "carbon_credit_tokenization",
        "rwa_infrastructure", "smart_contracts", "post_trade_reconciliation",
        "blockchain_data_layer", "digital_documents", "unclear",
    ])
with col3:
    sentiment_filter = st.selectbox("Sentimento", ["todos", "bullish", "bearish", "neutral", "mixed"])
with col4:
    min_score = st.slider("Score mínimo", 0, 100, 0)

filtered = df.copy()
if not filtered.empty:
    if search_term:
        mask = (
            filtered["titulo"].str.contains(search_term, case=False, na=False)
            | filtered["resumo"].str.contains(search_term, case=False, na=False)
        )
        filtered = filtered[mask]
    if blockchain_filter != "todas":
        filtered = filtered[filtered["blockchain"] == blockchain_filter]
    if sentiment_filter != "todos":
        filtered = filtered[filtered["sentimento"] == sentiment_filter]
    filtered = filtered[filtered["score"] >= min_score]

st.caption(f"**{len(filtered)} artigos** encontrados")

if not filtered.empty:
    display_cols = filtered[["id", "score", "fonte", "titulo", "sentimento", "driver", "blockchain", "relevancia_fin", "url"]].copy()
    display_cols.columns = ["ID", "Score", "Fonte", "Título", "Sentimento", "Driver", "Blockchain", "Relevância", "URL"]

    st.dataframe(
        display_cols,
        column_config={
            "ID":         st.column_config.NumberColumn("ID", width=50),
            "Score":      st.column_config.ProgressColumn("Score", min_value=0, max_value=100, width=80),
            "Fonte":      st.column_config.TextColumn("Fonte", width=130),
            "Título":     st.column_config.TextColumn("Título", width=380),
            "Sentimento": st.column_config.TextColumn("Sentimento", width=100),
            "Driver":     st.column_config.TextColumn("Driver", width=100),
            "Blockchain": st.column_config.TextColumn("Blockchain", width=130),
            "Relevância": st.column_config.TextColumn("Rel. Fin.", width=80),
            "URL":        st.column_config.LinkColumn("Link", display_text="Abrir →", width=80),
        },
        hide_index=True,
        use_container_width=True,
        height=500,
    )

# -----------------------------------------------------------------
# Article detail
# -----------------------------------------------------------------
st.markdown("---")
st.markdown('<div class="section-title">Detalhe do Artigo</div>', unsafe_allow_html=True)

selected_id = st.number_input("ID do artigo", min_value=0, value=0, step=1)
if selected_id > 0:
    match = df[df["id"] == selected_id]
    if not match.empty:
        row = match.iloc[0]
        st.markdown(f"### {row['titulo']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Score", int(row["score"]))
        m2.metric("Sentimento", _SENTIMENT.get(row["sentimento"], "—"))
        m3.metric("Driver", _DRIVER.get(row["driver"], row["driver"] or "—"))
        m4.metric("Horizonte", row["horizonte"].replace("_", " ") if row["horizonte"] else "—")
        st.write(f"**Fonte:** {row['fonte']} · **Data:** {row['data_pub']}")
        st.write(f"**Blockchain:** {row['blockchain']} · **Tokenização:** {row['tokenizacao']} · **Stablecoin:** {row['stablecoin']}")
        st.markdown(f"[Abrir artigo original]({row['url']})")
        st.markdown("---")
        st.markdown("#### Memo de Intelligence")
        st.markdown(row["resumo"] or "_Sem memo disponível_")
    else:
        st.warning("ID não encontrado.")

# -----------------------------------------------------------------
# Footer
# -----------------------------------------------------------------
st.markdown(
    '<div class="hermes-footer"><span>REPSOL</span> Energy Intelligence · Hermes Agent · Uso interno · Dados para análise, não conselho de investimento</div>',
    unsafe_allow_html=True,
)
