"""
modules/ui_components.py
========================
Componentes de interface Streamlit reutilizáveis.
Contém todas as funções de renderização das abas do DataLyzer.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
from typing import Dict, Any, Optional

from modules.chart_generator import ChartGenerator
from modules.comparator import DataComparator


# ─────────────────────────────────────────────
# Cards HTML
# ─────────────────────────────────────────────
def _insight_card(icon, titulo, descricao, sugestao, tipo="info"):
    """Renderiza um card de insight com borda colorida."""
    border_colors = {
        "alerta":    "#f85149",
        "queda":     "#f85149",
        "crescimento": "#3fb950",
        "info":      "#58a6ff",
        "oportunidade": "#ffa657",
        "qualidade": "#d2a8ff",
    }
    color = border_colors.get(tipo, "#58a6ff")
    st.markdown(f"""
    <div style='background:#161b22; border-left:3px solid {color};
                border-radius:0 8px 8px 0; padding:1rem 1.2rem;
                margin:0.4rem 0;'>
        <div style='font-weight:600; font-size:0.95rem;'>{icon} {titulo}</div>
        <div style='color:#8b949e; font-size:0.85rem; margin-top:0.3rem;'>{descricao}</div>
        <div style='color:#e6edf3; font-size:0.85rem; margin-top:0.4rem;
                    background:#0d1117; padding:0.4rem 0.6rem; border-radius:4px;'>
            💬 <em>{sugestao}</em>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Cabeçalho
# ─────────────────────────────────────────────
def render_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class='main-header'>
        <h1 style='margin:0; font-size:2rem; font-weight:800;'>📊 {title}</h1>
        <p style='color:#8b949e; margin:0.5rem 0 0 0;'>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_file_summary(df: pd.DataFrame, analysis: Dict):
    pass  # Integrado direto no app.py


# ─────────────────────────────────────────────
# Aba 1: Visão Geral de Colunas
# ─────────────────────────────────────────────
def render_column_overview(df: pd.DataFrame, analysis: Dict, decimal_places: int = 2):
    st.markdown("### 📋 Visão Geral das Colunas")

    # Tabela de tipos e resumo
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        n_unique = df[col].nunique()
        n_missing = df[col].isnull().sum()

        if col in analysis.get("numeric_columns", []):
            category = "🔢 Numérica"
        elif col in analysis.get("date_columns", []):
            category = "📅 Data"
        elif col in analysis.get("categorical_columns", []):
            category = "🏷 Categórica"
        else:
            category = "📝 Texto"

        col_info.append({
            "Coluna": col,
            "Tipo": category,
            "Valores Únicos": n_unique,
            "Ausentes": n_missing,
            "Ausentes %": f"{n_missing/max(len(df),1)*100:.1f}%",
            "Dtype": dtype
        })

    st.dataframe(
        pd.DataFrame(col_info),
        use_container_width=True,
        hide_index=True
    )

    # Estatísticas numéricas
    stats = analysis.get("descriptive_stats", {})
    if "numeric" in stats and not stats["numeric"].empty:
        st.markdown("### 📊 Estatísticas Descritivas (Numéricas)")
        st.dataframe(
            stats["numeric"].round(decimal_places),
            use_container_width=True
        )

    # Distribuição categórica
    cat_counts = analysis.get("category_counts", {})
    if cat_counts:
        st.markdown("### 🏷 Distribuição de Categorias")
        cols = st.columns(min(len(cat_counts), 3))
        for i, (col, counts) in enumerate(cat_counts.items()):
            with cols[i % 3]:
                st.markdown(f"**{col}**")
                df_counts = counts.head(10).reset_index()
                df_counts.columns = ["Valor", "Contagem"]
                st.dataframe(df_counts, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# Dados ausentes
# ─────────────────────────────────────────────
def render_missing_values(df: pd.DataFrame, analysis: Dict):
    missing_df = analysis.get("missing", pd.DataFrame())

    if missing_df.empty:
        st.success("✅ Nenhum valor ausente encontrado nos dados!")
        return

    st.markdown("### ❓ Valores Ausentes")
    st.dataframe(missing_df, use_container_width=True, hide_index=True)

    # Gráfico de barras dos ausentes
    if len(missing_df) > 0:
        cg = ChartGenerator(missing_df)
        fig = go.Figure(go.Bar(
            x=missing_df["Coluna"],
            y=missing_df["Percentual (%)"],
            marker_color="#f85149",
            text=missing_df["Percentual (%)"].apply(lambda x: f"{x:.1f}%"),
            textposition="auto",
        ))
        fig.update_layout(
            paper_bgcolor="#161b22",
            plot_bgcolor="#0d1117",
            font=dict(color="#e6edf3"),
            xaxis=dict(gridcolor="#30363d"),
            yaxis=dict(gridcolor="#30363d", title="% Ausentes"),
            title="Percentual de Valores Ausentes por Coluna",
            margin=dict(l=50, r=30, t=50, b=80),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# Outliers
# ─────────────────────────────────────────────
def render_outliers(df: pd.DataFrame, analysis: Dict):
    outliers = analysis.get("outliers", {})

    if not outliers:
        st.success("✅ Nenhum outlier significativo detectado.")
        return

    st.markdown("### ⚠️ Outliers Detectados (Método IQR)")

    for col, out_df in outliers.items():
        n = len(out_df)
        pct = n / max(len(df), 1) * 100
        with st.expander(f"🔍 {col} — {n} outliers ({pct:.1f}%)", expanded=False):
            # Boxplot
            cg = ChartGenerator(df)
            fig = cg.boxplot(col, title=f"Distribuição: {col}")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                out_df.drop(columns=["_limite_inferior", "_limite_superior"])
                      .rename(columns={"_tipo": "Classificação"})
                      .head(50),
                use_container_width=True
            )
            st.caption(
                f"Limites: [{out_df['_limite_inferior'].iloc[0]:.4f} — "
                f"{out_df['_limite_superior'].iloc[0]:.4f}]"
            )


# ─────────────────────────────────────────────
# Aba 2: Gráficos
# ─────────────────────────────────────────────
def render_chart_section(df: pd.DataFrame, analysis: Dict):
    cg = ChartGenerator(df)
    numeric_cols = analysis.get("numeric_columns", [])
    cat_cols = analysis.get("categorical_columns", [])
    date_cols = analysis.get("date_columns", [])
    all_cols = list(df.columns)

    # Correlação automática
    corr = analysis.get("correlations")
    if corr is not None and len(corr) > 1:
        with st.expander("🔗 Mapa de Correlação", expanded=False):
            fig = cg.correlation_heatmap(corr)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🎨 Criar Gráfico Personalizado")

    chart_types = {
        "📊 Barras": "bar",
        "📈 Linhas": "line",
        "🥧 Pizza/Donut": "pie",
        "🔵 Dispersão": "scatter",
        "📉 Histograma": "histogram",
        "📦 Boxplot": "boxplot",
        "⏱ Série Temporal": "timeseries",
        "📅 Comparativo de Períodos": "period",
    }

    c1, c2 = st.columns([1, 2])
    with c1:
        chart_type_label = st.selectbox("Tipo de gráfico:", list(chart_types.keys()))
        chart_type = chart_types[chart_type_label]
        chart_title = st.text_input("Título do gráfico:", value=chart_type_label.split(" ", 1)[1])

    fig = None

    with c2:
        # ── Barras ──────────────────────────────
        if chart_type == "bar":
            x_col = st.selectbox("Eixo X (categorias):", all_cols, key="bar_x")
            y_col = st.selectbox("Eixo Y (valores):", numeric_cols if numeric_cols else all_cols, key="bar_y")
            color_col = st.selectbox("Cor (opcional):", ["Nenhum"] + cat_cols, key="bar_c")
            orientation = st.radio("Orientação:", ["Vertical", "Horizontal"], horizontal=True)
            agg_func = st.selectbox("Agregação:", ["sum", "mean", "count", "max", "min"], key="bar_agg")

            if st.button("Gerar Gráfico", key="gen_bar"):
                fig = cg.bar_chart(
                    x_col, y_col,
                    color_col if color_col != "Nenhum" else None,
                    "h" if orientation == "Horizontal" else "v",
                    chart_title, agg_func
                )

        # ── Linhas ──────────────────────────────
        elif chart_type == "line":
            x_col = st.selectbox("Eixo X:", all_cols, key="line_x")
            y_cols = st.multiselect("Eixo Y (uma ou mais colunas):", numeric_cols, key="line_y")
            show_m = st.checkbox("Mostrar marcadores", value=True)

            if st.button("Gerar Gráfico", key="gen_line") and y_cols:
                fig = cg.line_chart(x_col, y_cols, chart_title, show_m)

        # ── Pizza ───────────────────────────────
        elif chart_type == "pie":
            label_col = st.selectbox("Categoria (rótulo):", cat_cols if cat_cols else all_cols, key="pie_l")
            value_col = st.selectbox("Valor:", numeric_cols if numeric_cols else all_cols, key="pie_v")
            donut = st.checkbox("Estilo Donut", value=True)
            top_n = st.slider("Top N categorias:", 3, 30, 10)

            if st.button("Gerar Gráfico", key="gen_pie"):
                fig = cg.pie_chart(label_col, value_col, chart_title, donut, top_n)

        # ── Dispersão ───────────────────────────
        elif chart_type == "scatter":
            x_col = st.selectbox("Eixo X:", numeric_cols if numeric_cols else all_cols, key="sc_x")
            y_col = st.selectbox("Eixo Y:", numeric_cols if numeric_cols else all_cols, key="sc_y")
            color_col = st.selectbox("Cor (opcional):", ["Nenhum"] + cat_cols, key="sc_c")
            size_col = st.selectbox("Tamanho (opcional):", ["Nenhum"] + numeric_cols, key="sc_s")
            trend = st.checkbox("Linha de tendência", value=True)

            if st.button("Gerar Gráfico", key="gen_sc"):
                fig = cg.scatter_chart(
                    x_col, y_col,
                    color_col if color_col != "Nenhum" else None,
                    size_col if size_col != "Nenhum" else None,
                    chart_title, trend
                )

        # ── Histograma ──────────────────────────
        elif chart_type == "histogram":
            col = st.selectbox("Coluna:", numeric_cols if numeric_cols else all_cols, key="hist_c")
            bins = st.slider("Número de bins:", 5, 100, 30)
            kde = st.checkbox("Mostrar boxplot marginal", value=True)

            if st.button("Gerar Gráfico", key="gen_hist"):
                fig = cg.histogram(col, bins, None, chart_title, kde)

        # ── Boxplot ─────────────────────────────
        elif chart_type == "boxplot":
            y_col = st.selectbox("Coluna numérica:", numeric_cols if numeric_cols else all_cols, key="bp_y")
            x_col = st.selectbox("Agrupar por:", ["Nenhum"] + cat_cols, key="bp_x")

            if st.button("Gerar Gráfico", key="gen_bp"):
                fig = cg.boxplot(y_col, x_col if x_col != "Nenhum" else None, chart_title)

        # ── Série Temporal ──────────────────────
        elif chart_type == "timeseries":
            if not date_cols:
                st.warning("⚠ Nenhuma coluna de data detectada.")
            else:
                date_col = st.selectbox("Coluna de data:", date_cols, key="ts_d")
                value_cols = st.multiselect("Valores:", numeric_cols, key="ts_v")
                freq = st.selectbox("Frequência:", ["D", "W", "M", "Q", "Y"],
                                    format_func=lambda x: {"D":"Diário","W":"Semanal","M":"Mensal","Q":"Trimestral","Y":"Anual"}[x])
                agg_func = st.selectbox("Agregação:", ["sum", "mean", "count"], key="ts_agg")

                if st.button("Gerar Gráfico", key="gen_ts") and value_cols:
                    fig = cg.time_series(date_col, value_cols, freq, agg_func, chart_title)

        # ── Comparativo de Períodos ─────────────
        elif chart_type == "period":
            if not date_cols:
                st.warning("⚠ Nenhuma coluna de data detectada.")
            else:
                date_col = st.selectbox("Coluna de data:", date_cols, key="per_d")
                value_col = st.selectbox("Valor:", numeric_cols, key="per_v")
                period = st.radio("Período:", ["month", "year"],
                                  format_func=lambda x: "Mês a Mês" if x == "month" else "Ano a Ano",
                                  horizontal=True)

                if st.button("Gerar Gráfico", key="gen_per"):
                    fig = cg.period_comparison(date_col, value_col, period, chart_title)

    # Exibir e exportar gráfico
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
        _render_export_buttons(fig, chart_title)


def _render_export_buttons(fig, filename: str = "grafico"):
    """Botões para download do gráfico como PNG."""
    try:
        img_bytes = fig.to_image(format="png", width=1200, height=700, scale=2)
        st.download_button(
            label="⬇ Baixar PNG",
            data=img_bytes,
            file_name=f"{filename.replace(' ', '_')}.png",
            mime="image/png",
            key=f"dl_png_{filename}"
        )
    except Exception:
        # kaleido não instalado
        st.info("💡 Para exportar gráficos, instale: `pip install kaleido`")


# ─────────────────────────────────────────────
# Aba 3: Insights
# ─────────────────────────────────────────────
def render_insights(insights: list):
    if not insights:
        st.success("✅ Nenhuma anomalia detectada. Dados parecem saudáveis!")
        return

    st.markdown(f"### 💡 {len(insights)} Insights Encontrados")

    # Filtro por tipo
    tipos_disponiveis = list({i.get("tipo", "info") for i in insights})
    tipos_labels = {
        "alerta": "🚨 Alertas",
        "queda": "📉 Quedas",
        "crescimento": "📈 Crescimento",
        "info": "ℹ️ Informativo",
        "oportunidade": "💡 Oportunidades",
        "qualidade": "⚠️ Qualidade"
    }

    col1, col2 = st.columns([1, 3])
    with col1:
        selected_tipos = st.multiselect(
            "Filtrar por tipo:",
            options=tipos_disponiveis,
            format_func=lambda t: tipos_labels.get(t, t),
            default=tipos_disponiveis
        )

    filtered = [i for i in insights if i.get("tipo") in selected_tipos]

    with col2:
        # Resumo de contagem por tipo
        counts = {}
        for i in filtered:
            t = i.get("tipo", "info")
            counts[t] = counts.get(t, 0) + 1

        summary = " · ".join(
            f"{tipos_labels.get(t, t)}: {c}"
            for t, c in counts.items()
        )
        st.caption(summary)

    for insight in filtered:
        _insight_card(
            insight.get("icon", "ℹ️"),
            insight.get("titulo", ""),
            insight.get("descricao", ""),
            insight.get("sugestao", ""),
            insight.get("tipo", "info")
        )


# ─────────────────────────────────────────────
# Aba 4: Comparativos
# ─────────────────────────────────────────────
def render_comparisons(df: pd.DataFrame, analysis: Dict):
    date_cols = analysis.get("date_columns", [])
    numeric_cols = analysis.get("numeric_columns", [])
    cat_cols = analysis.get("categorical_columns", [])

    comp_type = st.radio(
        "Tipo de comparativo:",
        ["📅 Por Período", "🏷 Por Categoria"],
        horizontal=True
    )

    if comp_type == "📅 Por Período":
        if not date_cols:
            st.warning("⚠ Nenhuma coluna de data encontrada nos dados.")
            return
        if not numeric_cols:
            st.warning("⚠ Nenhuma coluna numérica para comparar.")
            return

        c1, c2, c3 = st.columns(3)
        with c1:
            date_col = st.selectbox("Coluna de data:", date_cols)
        with c2:
            value_col = st.selectbox("Valor:", numeric_cols)
        with c3:
            period = st.radio("Período:", ["month", "year"],
                              format_func=lambda x: "Mensal" if x == "month" else "Anual",
                              horizontal=True)

        df_comp = DataComparator.period_comparison(df, date_col, value_col, period)
        st.dataframe(
            df_comp.style.format({
                "total": "{:,.2f}",
                "media": "{:,.2f}",
                "var_total_%": "{:+.1f}%",
                "var_media_%": "{:+.1f}%",
            }),
            use_container_width=True, hide_index=True
        )

        # Gráfico de comparativo
        cg = ChartGenerator(df)
        fig = cg.period_comparison(date_col, value_col, period,
                                    f"Comparativo {value_col} — {'Mensal' if period == 'month' else 'Anual'}")
        st.plotly_chart(fig, use_container_width=True)

    else:  # Por Categoria
        if not cat_cols:
            st.warning("⚠ Nenhuma coluna categórica encontrada.")
            return
        if not numeric_cols:
            st.warning("⚠ Nenhuma coluna numérica para comparar.")
            return

        c1, c2, c3 = st.columns(3)
        with c1:
            cat_col = st.selectbox("Categoria:", cat_cols)
        with c2:
            value_col = st.selectbox("Valor:", numeric_cols, key="cat_val")
        with c3:
            top_n = st.slider("Top N:", 5, 30, 10)

        df_comp = DataComparator.category_comparison(df, cat_col, value_col, top_n)
        st.dataframe(
            df_comp.style.format({
                "total": "{:,.2f}",
                "media": "{:,.2f}",
                "participacao_%": "{:.1f}%"
            }),
            use_container_width=True, hide_index=True
        )

        # Gráfico de barras
        cg = ChartGenerator(df_comp)
        fig = cg.bar_chart(
            cat_col, "total",
            title=f"Top {top_n} — {value_col} por {cat_col}"
        )
        # Remove a chamada de agregação (já está agregado)
        import plotly.express as px
        fig2 = px.bar(
            df_comp,
            x=cat_col, y="total",
            text="participacao_%",
            color="total",
            color_continuous_scale=["#161b22", "#58a6ff"],
        )
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="auto")
        fig2.update_layout(
            paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
            font=dict(color="#e6edf3"),
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="#30363d"),
            yaxis=dict(gridcolor="#30363d"),
            margin=dict(l=50, r=30, t=50, b=80),
            title=f"Top {top_n} {cat_col} por {value_col}"
        )
        st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────
# Aba 5: Multi-arquivo
# ─────────────────────────────────────────────
def render_cross_file_analysis(
    datasets: Dict[str, pd.DataFrame],
    analyses: Dict[str, Dict]
):
    if len(datasets) < 2:
        st.info("📂 Carregue **pelo menos 2 arquivos** para análise cruzada.")
        return

    file_names = list(datasets.keys())

    st.markdown("### 🔗 Comparação entre Arquivos")

    c1, c2 = st.columns(2)
    with c1:
        file1 = st.selectbox("Arquivo 1:", file_names, index=0, key="xf1")
    with c2:
        remaining = [f for f in file_names if f != file1]
        file2 = st.selectbox("Arquivo 2:", remaining, key="xf2")

    df1 = datasets[file1]
    df2 = datasets[file2]

    result = DataComparator.compare_dataframes(df1, df2, file1, file2)

    # Métricas de estrutura
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(f"Linhas — {file1[:20]}", f"{result['rows_1']:,}")
    with m2:
        st.metric(f"Linhas — {file2[:20]}", f"{result['rows_2']:,}")
    with m3:
        st.metric("Colunas Comuns", len(result["common_columns"]))
    with m4:
        diff_rows = result["rows_2"] - result["rows_1"]
        st.metric("Diferença de Linhas", f"{diff_rows:+,}")

    # Colunas
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.markdown("**✅ Colunas Comuns**")
        if result["common_columns"]:
            st.write(result["common_columns"])
        else:
            st.write("Nenhuma")
    with cc2:
        st.markdown(f"**📄 Apenas em {file1[:15]}**")
        if result["only_in_1"]:
            st.write(result["only_in_1"])
        else:
            st.write("Nenhuma exclusiva")
    with cc3:
        st.markdown(f"**📄 Apenas em {file2[:15]}**")
        if result["only_in_2"]:
            st.write(result["only_in_2"])
        else:
            st.write("Nenhuma exclusiva")

    # Comparação estatística de colunas comuns
    if result["stats_comparison"] is not None and not result["stats_comparison"].empty:
        st.markdown("### 📊 Comparação Estatística (Colunas Numéricas Comuns)")
        st.dataframe(result["stats_comparison"], use_container_width=True)

    # Visualização cruzada
    common_num = [
        c for c in result["common_columns"]
        if pd.api.types.is_numeric_dtype(df1[c]) and pd.api.types.is_numeric_dtype(df2[c])
    ]
    if common_num:
        st.markdown("### 📈 Visualização Cruzada")
        col_to_plot = st.selectbox("Coluna para comparar:", common_num)

        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=df1[col_to_plot].dropna(),
            name=file1[:20],
            marker_color="#58a6ff",
            boxpoints="outliers"
        ))
        fig.add_trace(go.Box(
            y=df2[col_to_plot].dropna(),
            name=file2[:20],
            marker_color="#3fb950",
            boxpoints="outliers"
        ))
        fig.update_layout(
            paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
            font=dict(color="#e6edf3"),
            yaxis=dict(gridcolor="#30363d"),
            title=f"Distribuição: {col_to_plot}",
            margin=dict(l=50, r=30, t=50, b=50),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Combinar datasets
    st.markdown("### 🔗 Combinar Datasets")
    if result["common_columns"]:
        join_col = st.selectbox("Coluna de junção:", result["common_columns"])
        join_type = st.radio("Tipo de junção:", ["inner", "left", "outer"],
                             format_func=lambda x: {"inner": "Interseção (inner)",
                                                     "left": "Todos do Arquivo 1 (left)",
                                                     "outer": "União completa (outer)"}[x],
                             horizontal=True)
        if st.button("🔗 Combinar"):
            try:
                df_merged = pd.merge(df1, df2, on=join_col, how=join_type,
                                     suffixes=(f"_{file1[:8]}", f"_{file2[:8]}"))
                st.success(f"✅ {len(df_merged):,} linhas após combinação.")
                st.dataframe(df_merged.head(100), use_container_width=True)

                # Exportar
                csv = df_merged.to_csv(index=False).encode("utf-8")
                st.download_button("⬇ Baixar CSV combinado", csv,
                                   "dados_combinados.csv", "text/csv")
            except Exception as e:
                st.error(f"Erro ao combinar: {e}")
    else:
        st.warning("Sem colunas comuns para fazer a junção.")
