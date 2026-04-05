import pandas as pd
import numpy as np
from typing import List,Dict,Any
class InsightEngine:
 TIPOS={"alerta":{"icon":"!","color":"#f85149"},"queda":{"icon":"v","color":"#f85149"},"crescimento":{"icon":"^","color":"#3fb950"},"info":{"icon":"i","color":"#58a6ff"},"oportunidade":{"icon":"$","color":"#ffa657"},"qualidade":{"icon":"?","color":"#d2a8ff"}}
 def __init__(self,df,analysis):
  self.df=df
  self.analysis=analysis
 def generate_insights(self):
  insights=[]
  for col,outlier_df in self.analysis.get("outliers",{}).items():
   n=len(outlier_df)
   pct=n/max(len(self.df),1)*100
   tipo="alerta" if pct>5 else "info"
   insights.append({"tipo":tipo,"icon":self.TIPOS[tipo]["icon"],"titulo":f"Outliers em '{col}'","descricao":f"{n} valores anomalos ({pct:.1f}%).","sugestao":"Investigue os registros."})
  for col,trend in self.analysis.get("trends",{}).items():
   d=trend.get("direction")
   c=trend.get("change_pct",0)
   m=trend.get("mean",0)
   if d=="decrescente" and abs(c)>10:
    insights.append({"tipo":"queda","icon":self.TIPOS["queda"]["icon"],"titulo":f"Queda em '{col}'","descricao":f"Queda de {abs(c):.1f}%. Media:{m:,.2f}.","sugestao":"Investigue as causas."})
   elif d=="crescente" and c>10:
    insights.append({"tipo":"crescimento","icon":self.TIPOS["crescimento"]["icon"],"titulo":f"Crescimento em '{col}'","descricao":f"Crescimento de {c:.1f}%. Media:{m:,.2f}.","sugestao":"Mantenha o desempenho."})
  return insights
