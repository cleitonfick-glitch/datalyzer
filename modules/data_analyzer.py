"""
modules/data_analyzer.py
========================
Análise estatística e exploratória dos dados carregados.
Detecta tipos de colunas, padrões, outliers, valores ausentes e tendências.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


class DataAnalyzer:
    """
    Executa análise exploratória completa sobre um DataFrame.
    Centraliza toda a lógica de detecção de padrões e estatísticas.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._classify_columns()

    # ─────────────────────────────────────────
    # Classificação de colunas
    # ─────────────────────────────────────────
    def _classify_columns(self):
        """
        Separa colunas em: numéricas, datas, categóricas e texto livre.
        """
        self.numeric_cols = list(
            self.df.select_dtypes(include=[np.number]).columns
        )
        self.date_cols = list(
            self.df.select_dtypes(include=["datetime64[ns]", "datetime"]).columns
        )
        self.categorical_cols = []
        self.text_cols = []

        for col in self.df.select_dtypes(include=["object"]).columns:
            n_unique = self.df[col].nunique()
            n_total = len(self.df[col].dropna())
            ratio = n_unique / max(n_total, 1)

            if n_unique <= 50 or ratio < 0.3:
                self.categorical_cols.append(col)
            else:
                self.text_cols.append(col)

    # ─────────────────────────────────────────
    # Análise completa
    # ─────────────────────────────────────────
    def full_analysis(self) -> Dict[str, Any]:
        """
        Retorna dicionário completo com todos os resultados de análise.
        """
        return {
            # Metadados de colunas
            "numeric_columns": self.numeric_cols,
            "date_columns": self.date_cols,
            "categorical_columns": self.categorical_cols,
            "text_columns": self.text_cols,

            # Dados ausentes
            "missing": self._analyze_missing(),
            "missing_pct_total": self._missing_pct_total(),

            # Estatísticas descritivas
            "descriptive_stats": self._descriptive_stats(),

            # Outliers
            "outliers": self._detect_outliers(),

            # Correlações
            "correlations": self._correlations(),

            # Distribuição de categóricas
            "category_counts": self._category_counts(),

            # Análise temporal (se houver datas)
            "time_analysis": self._time_analysis(),

            # Tendências
            "trends": self._detect_trends(),
        }

    # ─────────────────────────────────────────
    # Valores ausentes
    # ─────────────────────────────────────────
    def _analyze_missing(self) -> pd.DataFrame:
        """
        Retorna DataFrame com contagem e percentual de valores ausentes por coluna.
        """
        missing = self.df.isnull().sum()
        pct = (missing / len(self.df) * 100).round(2)
        result = pd.DataFrame({
            "Coluna": missing.index,
            "Ausentes": missing.values,
            "Percentual (%)": pct.values
        })
        return result[result["Ausentes"] > 0].sort_values("Ausentes", ascending=False)

    def _missing_pct_total(self) -> float:
        """Percentual total de células ausentes no DataFrame."""
        total_cells = self.df.size
        if total_cells == 0:
            return 0.0
        return round(self.df.isnull().sum().sum() / total_cells * 100, 2)

    # ─────────────────────────────────────────
    # Estatísticas descritivas
    # ─────────────────────────────────────────
    def _descriptive_stats(self) -> Dict[str, pd.DataFrame]:
        """
        Estatísticas para colunas numéricas e categóricas.
        """
        stats = {}

        if self.numeric_cols:
            stats["numeric"] = self.df[self.numeric_cols].describe().round(4)

        if self.categorical_cols:
            cat_stats = {}
            for col in self.categorical_cols:
                s = self.df[col].value_counts()
                cat_stats[col] = {
                    "top_value": s.index[0] if len(s) > 0 else None,
                    "top_count": int(s.iloc[0]) if len(s) > 0 else 0,
                    "unique_count": int(self.df[col].nunique()),
                    "missing_count": int(self.df[col].isnull().sum())
                }
            stats["categorical"] = pd.DataFrame(cat_stats).T

        return stats

    # ─────────────────────────────────────────
    # Outliers (IQR)
    # ─────────────────────────────────────────
    def _detect_outliers(self) -> Dict[str, pd.DataFrame]:
        """
        Detecta outliers usando o método IQR (Interquartile Range).
        Um valor é outlier se < Q1 - 1.5*IQR ou > Q3 + 1.5*IQR.
        """
        outliers = {}
        for col in self.numeric_cols:
            series = self.df[col].dropna()
            if len(series) < 4:
                continue

            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1

            if IQR == 0:
                continue

            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            mask = (self.df[col] < lower) | (self.df[col] > upper)
            outlier_vals = self.df[mask][[col]].copy()

            if not outlier_vals.empty:
                outlier_vals["_tipo"] = outlier_vals[col].apply(
                    lambda v: "Acima" if v > upper else "Abaixo"
                )
                outlier_vals["_limite_inferior"] = round(lower, 4)
                outlier_vals["_limite_superior"] = round(upper, 4)
                outliers[col] = outlier_vals

        return outliers

    # ─────────────────────────────────────────
    # Correlações
    # ─────────────────────────────────────────
    def _correlations(self) -> Optional[pd.DataFrame]:
        """
        Matriz de correlação de Pearson entre colunas numéricas.
        Retorna None se houver menos de 2 colunas numéricas.
        """
        if len(self.numeric_cols) < 2:
            return None
        try:
            return self.df[self.numeric_cols].corr().round(3)
        except Exception:
            return None

    # ─────────────────────────────────────────
    # Distribuição categórica
    # ─────────────────────────────────────────
    def _category_counts(self) -> Dict[str, pd.Series]:
        """
        Contagem de valores para cada coluna categórica.
        """
        counts = {}
        for col in self.categorical_cols:
            counts[col] = self.df[col].value_counts().head(30)
        return counts

    # ─────────────────────────────────────────
    # Análise temporal
    # ─────────────────────────────────────────
    def _time_analysis(self) -> Dict[str, Any]:
        """
        Para cada coluna de data, identifica:
        - Período coberto (min / max)
        - Distribuição por mês e ano
        - Tendências temporais de colunas numéricas
        """
        result = {}
        for col in self.date_cols:
            series = self.df[col].dropna()
            if series.empty:
                continue

            info = {
                "min": series.min(),
                "max": series.max(),
                "span_days": (series.max() - series.min()).days,
                "monthly": self.df.groupby(
                    self.df[col].dt.to_period("M")
                ).size().reset_index(name="contagem"),
                "yearly": self.df.groupby(
                    self.df[col].dt.year
                ).size().reset_index(name="contagem"),
            }

            # Agrega colunas numéricas por mês
            if self.numeric_cols:
                monthly_num = self.df.groupby(
                    self.df[col].dt.to_period("M")
                )[self.numeric_cols].sum().reset_index()
                info["monthly_numeric"] = monthly_num

            result[col] = info

        return result

    # ─────────────────────────────────────────
    # Tendências simples
    # ─────────────────────────────────────────
    def _detect_trends(self) -> Dict[str, Any]:
        """
        Para cada coluna numérica, calcula:
        - Direção da tendência (alta/baixa/estável) via regressão linear
        - Taxa de variação percentual
        - Valores min/max com índices
        """
        trends = {}
        for col in self.numeric_cols:
            series = self.df[col].dropna()
            if len(series) < 3:
                continue

            try:
                x = np.arange(len(series))
                y = series.values.astype(float)
                # Regressão linear simples
                slope, intercept = np.polyfit(x, y, 1)

                first_val = float(series.iloc[:max(1, len(series)//5)].mean())
                last_val = float(series.iloc[-max(1, len(series)//5):].mean())
                change_pct = ((last_val - first_val) / abs(first_val) * 100
                              if first_val != 0 else 0)

                if abs(slope) < 0.01 * y.std():
                    direction = "estável"
                elif slope > 0:
                    direction = "crescente"
                else:
                    direction = "decrescente"

                trends[col] = {
                    "direction": direction,
                    "slope": round(slope, 6),
                    "change_pct": round(change_pct, 2),
                    "min": round(float(series.min()), 4),
                    "max": round(float(series.max()), 4),
                    "mean": round(float(series.mean()), 4),
                    "std": round(float(series.std()), 4),
                }
            except Exception:
                pass

        return trends


