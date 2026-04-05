import pandas as pd
import numpy as np
from typing import List, Dict, Any


class InsightEngine:
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
        insights = []
        insights.extend(self._insights_missing())
        insights.extend(self._insights_outliers())
        insights.extend(self._insights_trends())
        insights.extend(self._insights_correlations())
        insights.extend(self._insights_categorical())
        insights.extend(self._insights_temporal())
        insights.extend(self._insights_data_quality())
        priority_order = ["alerta","queda","oportunidade","crescimento","qualidade","info"]
        insights.sort(key=lambda x: priority_order.index(x.get("tipo","info")) if x.get("tipo") in priority_order else 99)
        return insights

    def _insights_missing(self):
        insights = []
        missing_df = self.analysis.get("missing", pd.DataFrame())
        if missing_df.empty:
            return insights
        for _, row in missing_df[missing_df["Percentual (%)"] > 20].iterrows():
            pct = row["Percentual (%)"]
            col = row["Coluna"]
            tipo = "alerta" if pct > 50 else "qualidade"
            insights.append({"tipo": tipo, "icon": self.TIPOS[tipo]["icon"], "titulo": f"Dados ausentes em '{col}'", "descricao": f"A coluna '{col}' possui {pct:.1f}% de valores ausentes.", "sugestao": "Revise o processo de coleta ou preencha com média/mediana."})
        total_pct = self.analysis.get("missing_pct_total", 0)
        if total_pct > 5:
            insights.append({"tipo": "qualidade", "icon": self.TIPOS["qualidade"]["icon"], "titulo": "Qualidade dos dados", "descricao": f"{total_pct:.1f}% do total de células contém valores ausentes.", "sugestao": "Realize uma limpeza de dados antes de análises aprofundadas."})
        return insights

    def _insights_outliers(self):
        insights = []
        for col, outlier_df in self.analysis.get("outliers", {}).items():
            n = len(outlier_df)
            pct = n / max(len(self.df), 1) * 100
            tipo = "alerta" if pct > 5 else "info"
            insights.append({"tipo": tipo, "icon": self.TIPOS[tipo]["icon"], "titulo": f"Outliers detectados em '{col}'", "descricao": f"{n} valores anômalos ({pct:.1f}% do total).", "sugestao": "Investigue os registros anômalos."})
        return insights

    def _insights_trends(self):
        insights = []
        for col, trend in self.analysis.get("trends", {}).items():
            direction = trend.get("direction")
            change_pct = trend.get("change_pct", 0)
            mean = trend.get("mean", 0)
            if direction == "decrescente" and abs(change_pct) > 10:
                insights.append({"tipo": "queda", "icon": self.TIPOS["queda"]["icon"], "titulo": f"Queda detectada em '{col}'", "descricao": f"'{col}' apresenta queda de {abs(change_pct):.1f}%. Média: {mean:,.2f}.", "sugestao": f"Investigue causas da redução em '{col}'."})
            elif direction == "crescente" and change_pct > 10:
                insights.append({"tipo": "crescimento", "icon": self.TIPOS["crescimento"]["icon"], "titulo": f"Crescimento detectado em '{col}'", "descricao": f"'{col}' apresenta crescimento de {change_pct:.1f}%. Média: {mean:,.2f}.", "sugestao": "Identifique os fatores de sucesso para replicar."})
        return insights

    def _insights_correlations(self):
        insights = []
        corr = self.analysis.get("correlations")
        if corr is None or corr.empty:
            return insights
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
                    tipo = "oportunidade" if r > 0 else "info"
                    insights.append({"tipo": tipo, "icon": self.TIPOS[tipo]["icon"], "titulo": f"Correlação forte: '{col1}' x '{col2}'", "descricao": f"Correlação de {r:.2f} entre as variáveis.", "sugestao": "Use essa relação para previsões."})
        return insights

    def _insights_categorical(self):
        insights = []
        for col, counts in self.analysis.get("category_counts", {}).items():
            if counts.empty:
                continue
            total = counts.sum()
            top_pct = counts.iloc[0] / max(total, 1) * 100
            if top_pct > 70:
                insights.append({"tipo": "info", "icon": self.TIPOS["info"]["icon"], "titulo": f"Concentração em '{col}'", "descricao": f"'{counts.index[0]}' representa {top_pct:.1f}% dos registros.", "sugestao": "Alta concentração pode indicar oportunidade de diversificação."})
        return insights

    def _insights_temporal(self):
        insights = []
        for col, info in self.analysis.get("time_analysis", {}).items():
            span = info.get("span_days", 0)
            if span > 0:
                insights.append({"tipo": "info", "icon": self.TIPOS["info"]["icon"], "titulo": f"Série temporal em '{col}'", "descricao": f"Dados de {info['min'].strftime('%d/%m/%Y')} a {info['max'].strftime('%d/%m/%Y')} ({span} dias).", "sugestao": "Analise tendências sazonais e compare períodos equivalentes."})
            monthly = info.get("monthly")
            if monthly is not None and len(monthly) > 2:
                vals = monthly["contagem"].values
                pct_changes = np.diff(vals) / np.maximum(vals[:-1], 1) * 100
                if len(pct_changes) > 0 and pct_changes.min() < -25:
                    idx = pct_changes.argmin()
                    periodo = str(monthly.iloc[idx + 1, 0])
                    insights.append({"tipo": "queda", "icon": self.TIPOS["queda"]["icon"], "titulo": f"Queda brusca no período '{periodo}'", "descricao": f"Queda de {abs(pct_changes.min()):.1f}% em '{periodo}'.", "sugestao": "Investigue eventos específicos neste período."})
        return insights

    def _insights_data_quality(self):
        insights = []
        n = len(self.df)
        if n < 30:
            insights.append({"tipo": "alerta", "icon": self.TIPOS["alerta"]["icon"], "titulo": "Volume de dados insuficiente", "descricao": f"O dataset contém apenas {n} registros.", "sugestao": "Colete mais dados. Mínimo recomendado: 30 registros."})
        for col in self.analysis.get("numeric_columns", []):
            if self.df[col].nunique() == 1:
                insights.append({"tipo": "qualidade", "icon": self.TIPOS["qualidade"]["icon"], "titulo": f"Coluna sem variação: '{col}'", "descricao": f"'{col}' possui um único valor em todos os registros.", "sugestao": "Considere remover esta coluna."})
        return insights
