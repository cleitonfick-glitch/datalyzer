"""
modules/insight_engine.py
=========================
Motor de geração de insights inteligentes a partir dos dados analisados.
Gera alertas de anomalias, insights de tendências e sugestões de ação.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any


class InsightEngine:
    """
    Analisa os resultados do DataAnalyzer e gera insights acionáveis.
    Cada insight tem: tipo, ícone, título, descrição e sugestão de ação.
    """

    TIPOS = {
        "alerta":    {"icon": "🚨", "color": "#f85149"},
        "queda":     {"icon": "📉", "color": "#f85149"},
        "crescimento": {"icon": "📈", "color": "#3fb950"},
        "info":      {"icon": "ℹ️",  "color": "#58a6ff"},
        "oportunidade": {"icon": "💡", "color": "#ffa657"},
        "qualidade": {"icon": "⚠️", "color": "#d2a8ff"},
    }

    def __init__(self, df: pd.DataFrame, analysis: Dict[str, Any]):
        self.df = df
        self.analysis = analysis

    def generate_insights(self) -> List[Dict[str, Any]]:
        """
        Ponto de entrada principal: gera e ordena todos os insights.
        Prioridade: alertas > quedas > oportunidades > crescimento > info
        """
        insights = []

        insights.extend(self._insights_missing())
        insights.extend(self._insights_outliers())
        insights.extend(self._insights_trends())
        insights.extend(self._insights_correlations())
        insights.extend(self._insights_categorical())
        insights.extend(self._insights_temporal())
        insights.extend(self._insights_data_quality())

        # Ordena por prioridade
        priority_order = ["alerta", "queda", "oportunidade", "crescimento", "qualidade", "info"]
        insights.sort(key=lambda x: priority_order.index(x.get("tipo", "info"))
                      if x.get("tipo") in priority_order else 99)

        return insights

    # ─────────────────────────────────────────
    # Dados ausentes
    # ─────────────────────────────────────────
    def _insights_missing(self) -> List[Dict]:
        insights = []
        missing_df = self.analysis.get("missing", pd.DataFrame())

        if missing_df.empty:
            return insights

        # Colunas com mais de 20% ausentes
        critical = missing_df[missing_df["Percentual (%)"] > 20]
        for _, row in critical.iterrows():
            pct = row["Percentual (%)"]
            col = row["Coluna"]
            tipo = "alerta" if pct > 50 else "qualidade"
            insights.append({
                "tipo": tipo,
                "icon": self.TIPOS[tipo]["icon"],
                "titulo": f"Dados ausentes em '{col}'",
                "descricao": f"A coluna '{col}' possui {pct:.1f}% de valores ausentes "
                             f"({int(row['Ausentes'])} de {len(self.df)} registros).",
                "sugestao": (
                    "Considere remover a coluna ou preencher com média/mediana/moda. "
                    "Alta ausência pode indicar problema na coleta de dados."
                    if pct > 50 else
                    "Revise o processo de coleta para reduzir valores faltantes."
                )
            })

        # Resumo geral
        total_pct = self.analysis.get("missing_pct_total", 0)
        if total_pct > 5:
            insights.append({
                "tipo": "qualidade",
                "icon": self.TIPOS["qualidade"]["icon"],
                "titulo": "Qualidade dos dados",
                "descricao": f"{total_pct:.1f}% do total de células contém valores ausentes.",
                "sugestao": "Realize uma limpeza de dados antes de análises aprofundadas."
            })

        return insights

    # ─────────────────────────────────────────
    # Outliers
    # ─────────────────────────────────────────
    def _insights_outliers(self) -> List[Dict]:
        insights = []
        outliers = self.analysis.get("outliers", {})

        for col, outlier_df in outliers.items():
            n = len(outlier_df)
            pct = n / max(len(self.df), 1) * 100
            acima = (outlier_df["_tipo"] == "Acima").sum()
            abaixo = (outlier_df["_tipo"] == "Abaixo").sum()

            if pct > 5:
                tipo = "alerta"
            else:
                tipo = "info"

            insights.append({
                "tipo": tipo,
                "icon": self.TIPOS[tipo]["icon"],
                "titulo": f"Outliers detectados em '{col}'",
                "descricao": (
                    f"{n} valores anômalos ({pct:.1f}% do total): "
                    f"{acima} acima e {abaixo} abaixo dos limites normais. "
                    f"Limite: [{outlier_df['_limite_inferior'].iloc[0]:.2f} — "
                    f"{outlier_df['_limite_superior'].iloc[0]:.2f}]"
                ),
                "sugestao": (
                    "Investigue os registros anômalos. Podem ser erros de digitação, "
                    "casos especiais ou oportunidades/riscos relevantes."
                )
            })

        return insights

    # ─────────────────────────────────────────
    # Tendências
    # ─────────────────────────────────────────
    def _insights_trends(self) -> List[Dict]:
        insights = []
        trends = self.analysis.get("trends", {})

        for col, trend in trends.items():
            direction = trend.get("direction")
            change_pct = trend.get("change_pct", 0)
            mean = trend.get("mean", 0)

            if direction == "decrescente" and abs(change_pct) > 10:
                tipo = "queda"
                insights.append({
                    "tipo": tipo,
                    "icon": self.TIPOS[tipo]["icon"],
                    "titulo": f"Queda detectada em '{col}'",
                    "descricao": (
                        f"'{col}' apresenta tendência de queda de {abs(change_pct):.1f}% "
                        f"ao longo do período analisado. "
                        f"Média: {mean:,.2f}."
                    ),
                    "sugestao": (
                        f"Investigue causas da redução em '{col}'. "
                        "Revise estratégias e identifique fatores externos ou internos."
                    )
                })

            elif direction == "crescente" and change_pct > 10:
                tipo = "crescimento"
                insights.append({
                    "tipo": tipo,
                    "icon": self.TIPOS[tipo]["icon"],
                    "titulo": f"Crescimento detectado em '{col}'",
                    "descricao": (
                        f"'{col}' apresenta tendência de crescimento de {change_pct:.1f}% "
                        f"ao longo do período. Média: {mean:,.2f}."
                    ),
                    "sugestao": (
                        f"Continue monitorando '{col}'. "
                        "Identifique os fatores de sucesso para replicar em outras áreas."
                    )
                })

        return insights

    # ─────────────────────────────────────────
    # Correlações
    # ─────────────────────────────────────────
    def _insights_correlations(self) -> List[Dict]:
        insights = []
        corr = self.analysis.get("correlations")

        if corr is None or corr.empty:
            return insights

        # Pares com alta correlação (> 0.75 ou < -0.75)
        seen = set()
        for col1 in corr.columns:
            for col2 in corr.columns:
                if col1 == col2:
                    continue
                pair = tuple(sorted([col1, col2]))
                if pair in seen:
                    continue
                seen.add(pair)

                r = corr.loc[col1, col2]
                if abs(r) >= 0.8:
                    direction = "positiva forte" if r > 0 else "negativa forte"
                    tipo = "oportunidade" if r > 0 else "info"
                    insights.append({
                        "tipo": tipo,
                        "icon": self.TIPOS[tipo]["icon"],
                        "titulo": f"Correlação {direction}: '{col1}' × '{col2}'",
                        "descricao": (
                            f"Correlação de {r:.2f} entre '{col1}' e '{col2}'. "
                            "Quando uma aumenta, a outra tende a " +
                            ("aumentar também." if r > 0 else "diminuir.")
                        ),
                        "sugestao": (
                            "Use essa relação para previsões. Monitorar uma variável "
                            "pode antecipar mudanças na outra."
                        )
                    })

        return insights

    # ─────────────────────────────────────────
    # Categóricas
    # ─────────────────────────────────────────
    def _insights_categorical(self) -> List[Dict]:
        insights = []
        cat_counts = self.analysis.get("category_counts", {})

        for col, counts in cat_counts.items():
            if counts.empty:
                continue

            total = counts.sum()
            top_val = counts.index[0]
            top_pct = counts.iloc[0] / max(total, 1) * 100

            # Dominância de uma categoria
            if top_pct > 70:
                insights.append({
                    "tipo": "info",
                    "icon": self.TIPOS["info"]["icon"],
                    "titulo": f"Concentração em '{col}'",
                    "descricao": (
                        f"'{top_val}' representa {top_pct:.1f}% dos registros em '{col}'. "
                        f"Alta concentração em uma única categoria."
                    ),
                    "sugestao": (
                        "Alta concentração pode indicar viés nos dados ou "
                        "oportunidade de diversificação."
                    )
                })

            # Muitas categorias pequenas
            long_tail = (counts < total * 0.01).sum()
            if long_tail > 5 and len(counts) > 10:
                insights.append({
                    "tipo": "qualidade",
                    "icon": self.TIPOS["qualidade"]["icon"],
                    "titulo": f"Fragmentação em '{col}'",
                    "descricao": (
                        f"{long_tail} categorias com menos de 1% dos registros em '{col}'. "
                        "Pode indicar inconsistências de nomenclatura."
                    ),
                    "sugestao": (
                        "Revise e padronize os valores. Categorias muito pequenas "
                        "podem ser agrupadas em 'Outros'."
                    )
                })

        return insights

    # ─────────────────────────────────────────
    # Temporal
    # ─────────────────────────────────────────
    def _insights_temporal(self) -> List[Dict]:
        insights = []
        time_data = self.analysis.get("time_analysis", {})

        for col, info in time_data.items():
            span = info.get("span_days", 0)
            monthly = info.get("monthly")

            # Cobertura temporal
            if span > 0:
                years = span / 365
                insights.append({
                    "tipo": "info",
                    "icon": self.TIPOS["info"]["icon"],
                    "titulo": f"Série temporal em '{col}'",
                    "descricao": (
                        f"Dados de {info['min'].strftime('%d/%m/%Y')} "
                        f"a {info['max'].strftime('%d/%m/%Y')} "
                        f"({years:.1f} anos / {span} dias)."
                    ),
                    "sugestao": (
                        "Analise tendências sazonais e compare períodos "
                        "equivalentes para conclusões precisas."
                    )
                })

            # Meses com queda brusca
            if monthly is not None and len(monthly) > 2:
                monthly_vals = monthly["contagem"].values
                pct_changes = np.diff(monthly_vals) / np.maximum(monthly_vals[:-1], 1) * 100

                if len(pct_changes) > 0:
                    worst_change = pct_changes.min()
                    if worst_change < -25:
                        idx = pct_changes.argmin()
                        periodo = str(monthly.iloc[idx + 1, 0])
                        insights.append({
                            "tipo": "queda",
                            "icon": self.TIPOS["queda"]["icon"],
                            "titulo": f"Queda brusca no período '{periodo}'",
                            "descricao": (
                                f"Queda de {abs(worst_change):.1f}% "
                                f"em '{periodo}' comparado ao período anterior."
                            ),
                            "sugestao": (
                                "Investigue eventos específicos neste período "
                                "que possam ter causado a queda."
                            )
                        })

        return insights

    # ─────────────────────────────────────────
    # Qualidade geral dos dados
    # ─────────────────────────────────────────
    def _insights_data_quality(self) -> List[Dict]:
        insights = []

        # Volume de dados
        n = len(self.df)
        if n < 30:
            insights.append({
                "tipo": "alerta",
                "icon": self.TIPOS["alerta"]["icon"],
                "titulo": "Volume de dados insuficiente",
                "descricao": (
                    f"O dataset contém apenas {n} registros. "
                    "Análises estatísticas podem não ser representativas."
                ),
                "sugestao": (
                    "Colete mais dados antes de tirar conclusões definitivas. "
                    "Mínimo recomendado: 30 registros."
                )
            })
        elif n >= 10000:
            insights.append({
                "tipo": "info",
                "icon": self.TIPOS["info"]["icon"],
                "titulo": "Dataset de grande volume",
                "descricao": (
                    f"{n:,} registros disponíveis para análise. "
                    "Volume adequado para análises estatísticas robustas."
                ),
                "sugestao": (
                    "Considere segmentar os dados por períodos ou categorias "
                    "para análises mais específicas."
                )
            })

        # Colunas sem variação
        num_cols = self.analysis.get("numeric_columns", [])
        for col in num_cols:
            if self.df[col].nunique() == 1:
                insights.append({
                    "tipo": "qualidade",
                    "icon": self.TIPOS["qualidade"]["icon"],
                    "titulo": f"Coluna sem variação: '{col}'",
                    "descricao": (
                        f"A coluna '{col}' possui um único valor em todos os registros. "
                        "Não agrega informação analítica."
                    ),
                    "sugestao": "Considere remover esta coluna para simplificar a análise."
                })

        return insights
