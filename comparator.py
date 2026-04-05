"""
modules/comparator.py
=====================
Comparações automáticas entre períodos e entre arquivos distintos.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List


class DataComparator:
    """
    Realiza comparações entre datasets ou entre períodos do mesmo dataset.
    """

    @staticmethod
    def compare_dataframes(
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        name1: str = "Arquivo 1",
        name2: str = "Arquivo 2"
    ) -> Dict[str, Any]:
        """
        Compara dois DataFrames: estrutura, estatísticas e colunas comuns.
        """
        common_cols = list(set(df1.columns) & set(df2.columns))
        only_1 = list(set(df1.columns) - set(df2.columns))
        only_2 = list(set(df2.columns) - set(df1.columns))

        stats_comparison = {}
        for col in common_cols:
            # Compara apenas se ambos são numéricos
            if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
                s1 = df1[col].dropna()
                s2 = df2[col].dropna()
                stats_comparison[col] = {
                    f"média_{name1}": round(s1.mean(), 4) if len(s1) else None,
                    f"média_{name2}": round(s2.mean(), 4) if len(s2) else None,
                    f"total_{name1}": round(s1.sum(), 4) if len(s1) else None,
                    f"total_{name2}": round(s2.sum(), 4) if len(s2) else None,
                    "variacao_media_%": round(
                        (s2.mean() - s1.mean()) / abs(s1.mean()) * 100, 2
                    ) if len(s1) and s1.mean() != 0 else None
                }

        return {
            "common_columns": common_cols,
            "only_in_1": only_1,
            "only_in_2": only_2,
            "rows_1": len(df1),
            "rows_2": len(df2),
            "stats_comparison": pd.DataFrame(stats_comparison).T if stats_comparison else None
        }

    @staticmethod
    def period_comparison(
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        period: str = "month"
    ) -> pd.DataFrame:
        """
        Agrega valores por período e calcula variações.

        Args:
            period: 'month' ou 'year'
        """
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])

        if period == "month":
            df["_periodo"] = df[date_col].dt.to_period("M")
            df["_label"] = df[date_col].dt.strftime("%b/%Y")
        else:
            df["_periodo"] = df[date_col].dt.year
            df["_label"] = df[date_col].dt.year.astype(str)

        agg = (
            df.groupby(["_periodo", "_label"])[value_col]
            .agg(["sum", "mean", "count"])
            .reset_index()
            .sort_values("_periodo")
        )
        agg.columns = ["periodo", "label", "total", "media", "contagem"]
        agg["var_total_%"] = agg["total"].pct_change() * 100
        agg["var_media_%"] = agg["media"].pct_change() * 100

        return agg.drop("periodo", axis=1)

    @staticmethod
    def category_comparison(
        df: pd.DataFrame,
        category_col: str,
        value_col: str,
        top_n: int = 15
    ) -> pd.DataFrame:
        """
        Compara categorias: total, média, contagem e participação %.
        """
        agg = (
            df.groupby(category_col)[value_col]
            .agg(["sum", "mean", "count"])
            .reset_index()
            .sort_values("sum", ascending=False)
            .head(top_n)
        )
        agg.columns = [category_col, "total", "media", "contagem"]
        total_geral = agg["total"].sum()
        agg["participacao_%"] = (agg["total"] / max(total_geral, 1) * 100).round(2)
        agg["total"] = agg["total"].round(2)
        agg["media"] = agg["media"].round(2)
        return agg
