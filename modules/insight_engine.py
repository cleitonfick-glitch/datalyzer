import pandas as pd
import numpy as np
from typing import List, Dict, Any

class InsightEngine:
    TIPOS = {
        "alerta": {"icon": "X", "color": "#f85149"},
        "queda": {"icon": "v", "color": "#f85149"},
        "crescimento": {"icon": "^", "color": "#3fb950"},
        "info": {"icon": "i", "color": "#58a6ff"},
        "oportunidade": {"icon": "!", "color": "#ffa657"},
        "qualidade": {"icon": "?", "color": "#d2a8ff"},
    }

    def __init__(self, df, analysis):
        self.df = df
        self.analysis = analysis

    def generate_insights(self):
        insights = []
        insights.extend(self._missing())
        insights.extend(self._outliers())
        insights.extend(self._trends())
        insights.extend(self._quality())
        return insights

    def _missing(self):
        insights = []
        missing_df = self.analysis.get("missing", pd.DataFrame())
        if not missing_df.empty:
            for _, row in missing_df[missing_df["Percentual (%)"] > 20].iterrows():
                pct = row["Percentual (%)"]
                col = row["Coluna"]
                tipo = "alerta" if pct > 50 else "qualidade"
                insights.append({"tipo": tipo, "icon": self.TIPOS[tipo]["icon"], "titulo": f"Dados ausentes em '{col}'", "descricao": f"{pct:.1f}% de valores ausentes.", "sugestao": "Revise o processo de coleta."})
        return insights

    def _outliers(self):
        insights = []
        for col, outlier_df in self.analysis.get("outliers", {}).items():
            n = len(outlier_df)
            pct = n / max(len(self.df), 1) * 100
            tipo = "alerta" if pct > 5 else "info"
            insights.append({"tipo": tipo, "icon": self.TIPOS[tipo]["icon"], "titulo": f"Outliers em '{col}'", "descricao": f"{n} valores anômalos ({pct:.1f}%).", "sugestao": "Investigue os registros anômalos."})
        return insights

    def _trends(self):
        insights = []
        for col, trend in self.analysis.get("trends", {}).items():
            direction = trend.get("direction")
            change_pct = trend.get("change_pct", 0)
            mean = trend.get("mean", 0)
            if direction == "decrescente" and abs(change_pct) > 10:
                insights.append({"tipo": "queda", "icon": self.TIPOS["queda"]["icon"], "titulo": f"Queda em '{col}'", "descricao": f"Queda de {abs(change_pct):.1f}%. Media: {mean:,.2f}.", "sugestao": f"Investigue causas da reducao em '{col}'."})
            elif direction == "crescente" and change_pct > 10:
                insights.append({"tipo": "crescimento", "icon": self.TIPOS["crescimento"]["icon"], "titulo": f"Crescimento em '{col}'", "descricao": f"Crescimento de {change_pct:.1f}%. Media: {mean:,.2f}.", "sugestao": "Identifique os fatores de sucesso."})
        return insights

    def _quality(self):
        insights = []
        n = len(self.df)
        if n < 30:
            insights.append({"tipo": "alerta", "icon": self.TIPOS["alerta"]["icon"], "titulo": "Volume insuficiente", "descricao": f"Apenas {n} registros.", "sugestao": "Minimo recomendado: 30 registros."})
        return insights
