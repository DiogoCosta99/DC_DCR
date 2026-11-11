import pandas as pd
import os

# Ignorar as primeiras 7 linhas, que contêm metadados e notas.
# A 8.ª linha contém os nomes das colunas.
us_curve = pd.read_csv("data/us_yield_curve.csv", header = 7) 
all = pd.read_csv("data/all_bonds_spot_rate_3y.csv")
aaa = pd.read_csv("data/aaa_spot_rate_3y.csv")
sp500 = pd.read_csv("data/SP500.csv")
eurostoxx = pd.read_csv("data/eurostoxx_50.csv")
exchange_rate = pd.read_csv("data/DEXUSEU.csv")
