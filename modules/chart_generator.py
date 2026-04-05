"""
modules/chart_generator.py
==========================
Geração de gráficos interativos com Plotly.
Suporta: barras, linhas, pizza, dispersão, histograma e heatmap de correlação.
Permite exportação para PNG e PDF.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, Any


# Paleta de cores dark-mode
DARK_BG = "#0d1117"
DARK_PAPER = "#161b22"
DARK_GRID = "#30363d"
DARK_TEXT = "#e6edf3"
ACCENT_BLUE = "#58a6ff"
COLORS = [
    "#58a6ff", "#3fb950", "#f78166", "#d2a8ff",
    "#ffa657", "#79c0ff", "#56d364", "#ff7b72"
]

DARK_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor=DARK_PAPER,
        plot_bgcolor=DARK_BG,
        font=dict(color=DARK_TEXT, family="DM Sans, sans-serif"),
        xaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID),
        yaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID),
        legend=dict(bgcolor=DARK_PAPER, bordercolor=DARK_GRID),
        colorway=COLORS,
        margin=dict(l=50, r=30, t=60, b=50),
    )
)


class ChartGenerator:
    """
    Gera gráficos Plotly configurados para dark-mode.
    Cada método retorna uma figura Plotly pronta para st.plotly_chart().
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def _apply_theme(self, fig: go.Figure, title: str = "") -> go.Figure:
        """Aplica tema dark-mode padrão a qualquer figura."""
        fig.update_layout(
            **DARK_TEMPLATE["layout"],
            title=dict(
                text=title,
                font=dict(size=16, family="Syne, sans-serif", color=DARK_TEXT),
                x=0.02,
            )
        )
        return fig

    # ─────────────────────────────────────────
    # Gráfico de Barras
    # ─────────────────────────────────────────
    def bar_chart(
        self,
        x_col: str,
        y_col: str,
        color_col: Optional[str] = None,
        orientation: str = "v",
        title: str = "Gráfico de Barras",
        agg_func: str = "sum"
    ) -> go.Figure:
        """
        Gráfico de barras com opção de agrupamento por cor.

        Args:
            x_col: Coluna para o eixo X (categorias)
            y_col: Coluna para o eixo Y (valores)
            color_col: Coluna opcional para segmentação por cor
            orientation: 'v' (vertical) ou 'h' (horizontal)
            agg_func: Função de agregação: 'sum', 'mean', 'count', 'max', 'min'
        """
        # Agrega dados
        group_cols = [x_col] + ([color_col] if color_col else [])
        agg_map = {"sum": "sum", "mean": "mean", "count": "count",
                   "max": "max", "min": "min"}
        func = agg_map.get(agg_func, "sum")

        df_agg = self.df.groupby(group_cols)[y_col].agg(func).reset_index()

        if orientation == "h":
            fig = px.bar(
                df_agg, y=x_col, x=y_col,
                color=color_col if color_col else None,
                orientation="h",
                color_discrete_sequence=COLORS,
                text_auto=".2s"
            )
        else:
            fig = px.bar(
                df_agg, x=x_col, y=y_col,
                color=color_col if color_col else None,
                color_discrete_sequence=COLORS,
                text_auto=".2s"
            )

        fig.update_traces(marker_line_width=0)
        return self._apply_theme(fig, title)

    # ─────────────────────────────────────────
    # Gráfico de Linhas
    # ─────────────────────────────────────────
    def line_chart(
        self,
        x_col: str,
        y_cols: list,
        title: str = "Gráfico de Linhas",
        show_markers: bool = True
    ) -> go.Figure:
        """
        Gráfico de linhas para uma ou múltiplas séries.

        Args:
            x_col: Eixo X (geralmente data ou sequência)
            y_cols: Lista de colunas para eixo Y (uma linha por coluna)
            show_markers: Exibe pontos nos dados
        """
        df_plot = self.df[[x_col] + y_cols].copy().sort_values(x_col)

        fig = go.Figure()
        for i, col in enumerate(y_cols):
            color = COLORS[i % len(COLORS)]
            fig.add_trace(go.Scatter(
                x=df_plot[x_col],
                y=df_plot[col],
                name=col,
                mode="lines+markers" if show_markers else "lines",
                line=dict(color=color, width=2),
                marker=dict(size=6, color=color),
                hovertemplate=f"<b>{col}</b><br>{x_col}: %{{x}}<br>Valor: %{{y:,.2f}}<extra></extra>"
            ))

        fig.update_layout(hovermode="x unified")
        return self._apply_theme(fig, title)

    # ─────────────────────────────────────────
    # Gráfico de Pizza / Donut
    # ─────────────────────────────────────────
    def pie_chart(
        self,
        label_col: str,
        value_col: str,
        title: str = "Distribuição",
        donut: bool = True,
        top_n: int = 10
    ) -> go.Figure:
        """
        Pizza ou donut com os top N valores.

        Args:
            label_col: Coluna de rótulos/categorias
            value_col: Coluna de valores numéricos
            donut: True para donut (hole no centro)
            top_n: Limita aos N maiores valores (agrupa o resto como 'Outros')
        """
        df_agg = (
            self.df.groupby(label_col)[value_col]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        if len(df_agg) > top_n:
            top = df_agg.head(top_n)
            outros = pd.DataFrame({
                label_col: ["Outros"],
                value_col: [df_agg.iloc[top_n:][value_col].sum()]
            })
            df_agg = pd.concat([top, outros], ignore_index=True)

        fig = go.Figure(go.Pie(
            labels=df_agg[label_col],
            values=df_agg[value_col],
            hole=0.5 if donut else 0,
            marker=dict(colors=COLORS, line=dict(color=DARK_BG, width=2)),
            textinfo="label+percent",
            textposition="auto",
            hovertemplate="%{label}<br>Valor: %{value:,.2f}<br>Percentual: %{percent}<extra></extra>"
        ))

        return self._apply_theme(fig, title)

    # ─────────────────────────────────────────
    # Gráfico de Dispersão
    # ─────────────────────────────────────────
    def scatter_chart(
        self,
        x_col: str,
        y_col: str,
        color_col: Optional[str] = None,
        size_col: Optional[str] = None,
        title: str = "Dispersão",
        trend_line: bool = True
    ) -> go.Figure:
        """
        Gráfico de dispersão com linha de tendência opcional.

        Args:
            x_col, y_col: Eixos do gráfico
            color_col: Segmentação por cor
            size_col: Coluna para tamanho dos pontos
            trend_line: Adiciona linha de regressão
        """
        fig = px.scatter(
            self.df,
            x=x_col, y=y_col,
            color=color_col,
            size=size_col if size_col else None,
            trendline="ols" if trend_line else None,
            color_discrete_sequence=COLORS,
            opacity=0.75,
            hover_data={c: True for c in self.df.columns[:5]}
        )

        fig.update_traces(marker=dict(line=dict(width=0.5, color=DARK_BG)))
        return self._apply_theme(fig, title)

    # ─────────────────────────────────────────
    # Histograma
    # ─────────────────────────────────────────
    def histogram(
        self,
        col: str,
        bins: int = 30,
        color_col: Optional[str] = None,
        title: str = "Histograma",
        show_kde: bool = True
    ) -> go.Figure:
        """
        Histograma com curva de densidade KDE opcional.

        Args:
            col: Coluna numérica para distribuição
            bins: Número de intervalos
            color_col: Segmentação por cor
            show_kde: Sobrepõe curva de densidade
        """
        fig = px.histogram(
            self.df,
            x=col,
            nbins=bins,
            color=color_col,
            color_discrete_sequence=COLORS,
            histnorm="",
            marginal="box" if show_kde else None,
            opacity=0.8
        )

        fig.update_traces(
            marker_line_color=DARK_BG,
            marker_line_width=0.5
        )
        return self._apply_theme(fig, title)

    # ─────────────────────────────────────────
    # Heatmap de Correlação
    # ─────────────────────────────────────────
    def correlation_heatmap(
        self,
        corr_matrix: pd.DataFrame,
        title: str = "Correlação entre Variáveis"
    ) -> go.Figure:
        """
        Mapa de calor da matriz de correlação.

        Args:
            corr_matrix: DataFrame quadrado com correlações (de DataAnalyzer)
        """
        fig = go.Figure(go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            colorscale=[
                [0.0,  "#f85149"],
                [0.5,  DARK_PAPER],
                [1.0,  "#3fb950"]
            ],
            zmid=0,
            text=corr_matrix.round(2).values,
            texttemplate="%{text}",
            textfont=dict(size=11),
            hovertemplate="%{y} × %{x}<br>Correlação: %{z:.3f}<extra></extra>",
            showscale=True
        ))

        n = len(corr_matrix)
        cell_size = max(50, 400 // max(n, 1))
        fig.update_layout(
            height=max(400, n * cell_size),
            xaxis=dict(tickangle=-45)
        )

        return self._apply_theme(fig, title)

    # ─────────────────────────────────────────
    # Boxplot
    # ─────────────────────────────────────────
    def boxplot(
        self,
        y_col: str,
        x_col: Optional[str] = None,
        title: str = "Distribuição (Boxplot)"
    ) -> go.Figure:
        """
        Boxplot para visualizar distribuição e outliers.

        Args:
            y_col: Coluna numérica (valores)
            x_col: Coluna categórica opcional (grupos)
        """
        fig = px.box(
            self.df,
            y=y_col,
            x=x_col,
            color=x_col,
            color_discrete_sequence=COLORS,
            points="outliers",
            notched=True
        )

        return self._apply_theme(fig, title)

    # ─────────────────────────────────────────
    # Série temporal
    # ─────────────────────────────────────────
    def time_series(
        self,
        date_col: str,
        value_cols: list,
        freq: str = "M",
        agg: str = "sum",
        title: str = "Série Temporal"
    ) -> go.Figure:
        """
        Agrega e plota dados ao longo do tempo.

        Args:
            date_col: Coluna datetime
            value_cols: Colunas numéricas para plotar
            freq: Frequência: 'D' (dia), 'W' (semana), 'M' (mês), 'Y' (ano)
            agg: Agregação: 'sum', 'mean', 'count'
        """
        df = self.df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)

        agg_map = {"sum": "sum", "mean": "mean", "count": "count"}
        func = agg_map.get(agg, "sum")
        df_agg = df[value_cols].resample(freq).agg(func).reset_index()

        fig = go.Figure()
        for i, col in enumerate(value_cols):
            color = COLORS[i % len(COLORS)]
            fig.add_trace(go.Scatter(
                x=df_agg[date_col],
                y=df_agg[col],
                name=col,
                mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=7, color=color),
                fill="tozeroy" if i == 0 and len(value_cols) == 1 else None,
                fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}",
            ))

        fig.update_layout(
            hovermode="x unified",
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="1a", step="year", stepmode="backward"),
                        dict(step="all", label="Tudo")
                    ]),
                    bgcolor=DARK_PAPER,
                    activecolor=ACCENT_BLUE,
                ),
                rangeslider=dict(visible=True, bgcolor=DARK_PAPER),
            )
        )

        return self._apply_theme(fig, title)

    # ─────────────────────────────────────────
    # Comparativo de períodos (YoY / MoM)
    # ─────────────────────────────────────────
    def period_comparison(
        self,
        date_col: str,
        value_col: str,
        period: str = "month",
        title: str = "Comparativo de Períodos"
    ) -> go.Figure:
        """
        Compara valores entre períodos (meses ou anos) lado a lado.

        Args:
            period: 'month' (comparar meses) ou 'year' (comparar anos)
        """
        df = self.df.copy()
        df[date_col] = pd.to_datetime(df[date_col])

        if period == "month":
            df["_periodo"] = df[date_col].dt.strftime("%b/%Y")
            df["_ordem"] = df[date_col].dt.to_period("M")
        else:
            df["_periodo"] = df[date_col].dt.year.astype(str)
            df["_ordem"] = df[date_col].dt.year

        df_agg = (
            df.groupby(["_periodo", "_ordem"])[value_col]
            .sum()
            .reset_index()
            .sort_values("_ordem")
        )

        # Variação percentual
        df_agg["_variacao"] = df_agg[value_col].pct_change() * 100

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.05
        )

        # Barras de valores
        colors = [
            COLORS[1] if v >= 0 else COLORS[2]
            for v in df_agg["_variacao"].fillna(0)
        ]
        fig.add_trace(go.Bar(
            x=df_agg["_periodo"],
            y=df_agg[value_col],
            name=value_col,
            marker_color=ACCENT_BLUE,
            showlegend=True
        ), row=1, col=1)

        # Variação %
        fig.add_trace(go.Bar(
            x=df_agg["_periodo"],
            y=df_agg["_variacao"],
            name="Variação %",
            marker_color=colors,
            showlegend=True
        ), row=2, col=1)

        fig.add_hline(y=0, line_dash="dot", line_color=DARK_GRID, row=2, col=1)

        fig.update_layout(
            **DARK_TEMPLATE["layout"],
            title=dict(text=title, font=dict(size=16, family="Syne, sans-serif")),
            bargap=0.2
        )
        fig.update_yaxes(title_text=value_col, row=1, col=1, gridcolor=DARK_GRID)
        fig.update_yaxes(title_text="Variação (%)", row=2, col=1, gridcolor=DARK_GRID)

        return fig
