"""
DataLyzer - Aplicativo de Análise Inteligente de Dados
=======================================================
Aplicativo Streamlit para análise de planilhas, PDFs e documentos Word,
com geração de gráficos, comparativos automáticos e insights inteligentes.
"""

import streamlit as st
import pandas as pd
import os
import sys
import traceback

# Módulos internos
from modules.file_reader import FileReader
from modules.data_analyzer import DataAnalyzer
from modules.chart_generator import ChartGenerator
from modules.insight_engine import InsightEngine
from modules.comparator import DataComparator
from modules.ui_components import (
    render_header, render_file_summary, render_column_overview,
    render_missing_values, render_outliers, render_comparisons,
    render_insights, render_chart_section, render_cross_file_analysis
)

# ─────────────────────────────────────────────
# Configuração da página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DataLyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para visual refinado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
    }
    .stApp {
        background: #0d1117;
        color: #e6edf3;
    }
    .main-header {
        background: linear-gradient(135deg, #1a2332 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
    }
    .insight-card {
        background: #161b22;
        border-left: 3px solid #58a6ff;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .alert-card {
        background: #161b22;
        border-left: 3px solid #f85149;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .success-card {
        background: #161b22;
        border-left: 3px solid #3fb950;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stButton > button {
        background: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
    }
    .stButton > button:hover {
        background: #2ea043;
    }
    section[data-testid="stSidebar"] {
        background: #161b22;
        border-right: 1px solid #30363d;
    }
    .uploadedFile {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
    }
    div[data-testid="stExpander"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Estado da sessão
# ─────────────────────────────────────────────
if "datasets" not in st.session_state:
    st.session_state.datasets = {}   # {nome_arquivo: DataFrame}
if "analyses" not in st.session_state:
    st.session_state.analyses = {}   # {nome_arquivo: dict com análises}
if "active_file" not in st.session_state:
    st.session_state.active_file = None


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 DataLyzer")
    st.markdown("*Análise inteligente de dados*")
    st.divider()

    st.markdown("### 📂 Carregar Arquivos")
    uploaded_files = st.file_uploader(
        "Suporta Excel, CSV, PDF e Word",
        type=["xlsx", "xls", "csv", "pdf", "docx", "doc"],
        accept_multiple_files=True,
        help="Carregue um ou mais arquivos para análise"
    )

    # Processar arquivos enviados
    if uploaded_files:
        reader = FileReader()
        for uploaded_file in uploaded_files:
            fname = uploaded_file.name
            if fname not in st.session_state.datasets:
                with st.spinner(f"Lendo {fname}..."):
                    try:
                        df = reader.read(uploaded_file)
                        if df is not None and not df.empty:
                            st.session_state.datasets[fname] = df
                            # Executar análise automática
                            analyzer = DataAnalyzer(df)
                            st.session_state.analyses[fname] = analyzer.full_analysis()
                            st.success(f"✓ {fname}")
                        else:
                            st.warning(f"⚠ {fname}: nenhum dado encontrado")
                    except Exception as e:
                        st.error(f"✗ {fname}: {str(e)}")

    st.divider()

    # Seletor de arquivo ativo
    if st.session_state.datasets:
        st.markdown("### 🗂 Arquivo Ativo")
        file_names = list(st.session_state.datasets.keys())
        active = st.selectbox(
            "Selecione para analisar:",
            file_names,
            index=0
        )
        st.session_state.active_file = active

        # Botão para limpar todos
        if st.button("🗑 Limpar tudo", use_container_width=True):
            st.session_state.datasets = {}
            st.session_state.analyses = {}
            st.session_state.active_file = None
            st.rerun()

    st.divider()
    st.markdown("### ⚙️ Opções Globais")
    show_raw_data = st.checkbox("Mostrar dados brutos", value=False)
    decimal_places = st.slider("Casas decimais", 0, 4, 2)

    st.divider()
    st.markdown("""
    <div style='font-size:0.75rem; color:#8b949e;'>
    DataLyzer v1.0<br>
    Suporte: xlsx · xls · csv · pdf · docx
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ÁREA PRINCIPAL
# ─────────────────────────────────────────────

# Tela inicial (sem arquivos)
if not st.session_state.datasets:
    st.markdown("""
    <div class='main-header'>
        <h1 style='margin:0; font-size:2.5rem; font-weight:800;'>📊 DataLyzer</h1>
        <p style='color:#8b949e; margin:0.5rem 0 0 0; font-size:1.1rem;'>
            Análise inteligente de dados com insights automáticos
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size:2rem;'>📈</div>
            <div style='font-weight:600; margin-top:0.5rem;'>Gráficos Interativos</div>
            <div style='color:#8b949e; font-size:0.85rem;'>Barras, linhas, pizza, dispersão e histograma</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size:2rem;'>🔍</div>
            <div style='font-weight:600; margin-top:0.5rem;'>Análise Automática</div>
            <div style='color:#8b949e; font-size:0.85rem;'>Detecta padrões, outliers e tendências</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size:2rem;'>💡</div>
            <div style='font-weight:600; margin-top:0.5rem;'>Insights Inteligentes</div>
            <div style='color:#8b949e; font-size:0.85rem;'>Alertas, oportunidades e sugestões</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size:2rem;'>🔗</div>
            <div style='font-weight:600; margin-top:0.5rem;'>Multi-arquivo</div>
            <div style='color:#8b949e; font-size:0.85rem;'>Cruza e compara múltiplos arquivos</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 **Comece carregando um ou mais arquivos** na barra lateral (Excel, CSV, PDF ou Word)")

    # Demonstração de formatos suportados
    st.markdown("### Formatos Suportados")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        | Formato | Extensão | Descrição |
        |---------|----------|-----------|
        | Excel   | .xlsx, .xls | Planilhas com múltiplas abas |
        | CSV     | .csv | Dados separados por vírgula/ponto-e-vírgula |
        """)
    with c2:
        st.markdown("""
        | Formato | Extensão | Descrição |
        |---------|----------|-----------|
        | PDF     | .pdf | Extrai tabelas e texto estruturado |
        | Word    | .docx | Extrai tabelas de documentos Word |
        """)
    st.stop()


# ─────────────────────────────────────────────
# Dashboard principal (com arquivos carregados)
# ─────────────────────────────────────────────
active_file = st.session_state.active_file
df = st.session_state.datasets[active_file]
analysis = st.session_state.analyses[active_file]

st.markdown(f"""
<div class='main-header'>
    <h1 style='margin:0; font-size:2rem; font-weight:800;'>📊 {active_file}</h1>
    <p style='color:#8b949e; margin:0.5rem 0 0 0;'>
        {df.shape[0]:,} linhas · {df.shape[1]} colunas · {len(st.session_state.datasets)} arquivo(s) carregado(s)
    </p>
</div>
""", unsafe_allow_html=True)

# Métricas rápidas no topo
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("📋 Linhas", f"{df.shape[0]:,}")
with m2:
    st.metric("📊 Colunas", df.shape[1])
with m3:
    num_cols = len(analysis.get("numeric_columns", []))
    st.metric("🔢 Numéricas", num_cols)
with m4:
    missing_pct = analysis.get("missing_pct_total", 0)
    st.metric("❓ Dados Faltantes", f"{missing_pct:.1f}%")
with m5:
    outlier_count = sum(len(v) for v in analysis.get("outliers", {}).values())
    st.metric("⚠ Outliers", outlier_count)

st.divider()

# Dados brutos (opcional)
if show_raw_data:
    with st.expander("📄 Dados Brutos", expanded=False):
        st.dataframe(df.head(100), use_container_width=True)
        st.caption(f"Mostrando primeiras 100 de {len(df):,} linhas")

# ─────────────────────────────────────────────
# ABAS PRINCIPAIS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Visão Geral",
    "📈 Gráficos",
    "💡 Insights",
    "🔀 Comparativos",
    "🔗 Multi-arquivo"
])

# ── ABA 1: VISÃO GERAL ──────────────────────
with tab1:
    render_column_overview(df, analysis, decimal_places)
    st.divider()
    render_missing_values(df, analysis)
    st.divider()
    render_outliers(df, analysis)

# ── ABA 2: GRÁFICOS ─────────────────────────
with tab2:
    render_chart_section(df, analysis)

# ── ABA 3: INSIGHTS ─────────────────────────
with tab3:
    engine = InsightEngine(df, analysis)
    insights = engine.generate_insights()
    render_insights(insights)

# ── ABA 4: COMPARATIVOS ─────────────────────
with tab4:
    render_comparisons(df, analysis)

# ── ABA 5: MULTI-ARQUIVO ────────────────────
with tab5:
    render_cross_file_analysis(
        st.session_state.datasets,
        st.session_state.analyses
    )
