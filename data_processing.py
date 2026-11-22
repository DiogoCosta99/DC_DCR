"""Preparação de dados e análises exploratórias iniciais para o caso DCR.

A importação deste módulo disponibiliza `df_returns` sem imprimir resultados.
A execução direta também apresenta os diagnósticos e estatísticas exploratórias.
"""

import pandas as pd
import numpy as np

# A curva dos EUA contém sete linhas iniciais de metadados; a oitava é o cabeçalho.
us_curve = pd.read_csv("data/us_yield_curve.csv", header=7)
all = pd.read_csv("data/all_bonds_spot_rate_3y.csv")
aaa = pd.read_csv("data/aaa_spot_rate_3y.csv")
exchange_rate = pd.read_csv("data/DEXUSEU.csv")

#sp500 e eurstoxx vêm de uma fonte diferente (investing.com)
sp500 = pd.read_csv("data/S&P_500_Historical_Data.csv")
eurostoxx = pd.read_csv("data/Euro_Stoxx_50_Historical_Data.csv")

# Trabalhar sobre cópias, mantendo os DataFrames originais para referência.
df_us = us_curve.copy()
df_all = all.copy()
df_aaa = aaa.copy()
df_sp500 = sp500.copy()
df_eurostoxx = eurostoxx.copy()
df_exchange_rate = exchange_rate.copy()

# A spot rate a 3 anos é utilizada como fator de risco representativo
# de cada componente obrigacionista (modified duration de 3 anos).
df_us = df_us.rename(columns={"Date": "date", "SVENY03": "yield"})[["date", "yield"]]

# Nos CSV do ECB Data Portal, a última coluna contém a yield selecionada.
df_all = df_all.rename(columns={"DATE": "date", df_all.columns[-1]: "yield"})[["date", "yield"]]
df_aaa = df_aaa.rename(columns={"DATE": "date", df_aaa.columns[-1]: "yield"})[["date", "yield"]]

# Preparar os preços dos índices acionistas.
df_sp500 = df_sp500.rename(columns={"Date": "date", "Price": "price"})[["date", "price"]]
df_sp500["date"] = pd.to_datetime(df_sp500["date"], format="%m/%d/%Y")
df_sp500 = df_sp500.sort_values("date").reset_index(drop=True)
df_sp500["price"] = df_sp500["price"].str.replace(",", "", regex=False).astype(float)

df_eurostoxx = df_eurostoxx.rename(columns={"Date": "date", "Price": "price"})[["date", "price"]]
df_eurostoxx["date"] = pd.to_datetime(df_eurostoxx["date"], format="%m/%d/%Y")
df_eurostoxx = df_eurostoxx.sort_values("date").reset_index(drop=True)
df_eurostoxx["price"] = df_eurostoxx["price"].str.replace(",", "", regex=False).astype(float)

df_exchange_rate = df_exchange_rate.rename(columns={"observation_date": "date", "DEXUSEU": "rate"})

dfs = {
    "us": df_us,
    "all": df_all,
    "aaa": df_aaa,
    "sp500": df_sp500,
    "eurostoxx": df_eurostoxx,
    "exchange_rate": df_exchange_rate,
}

start_date = pd.Timestamp("2008-01-01")
end_date = pd.Timestamp("2026-10-31")

for name, df in dfs.items():
    df["date"] = pd.to_datetime(df["date"])
    dfs[name] = (
        df.dropna()
        .query("@start_date <= date <= @end_date")
        .sort_values("date")
        .reset_index(drop=True)
    )

df_us = dfs["us"]
df_all = dfs["all"]
df_aaa = dfs["aaa"]
df_sp500 = dfs["sp500"]
df_eurostoxx = dfs["eurostoxx"]
df_exchange_rate = dfs["exchange_rate"]

# Converter o nível do S&P 500 para euros (DEXUSEU: USD por EUR).
df_sp500 = df_sp500.merge(df_exchange_rate, on="date", how="inner")
df_sp500["price_eur"] = df_sp500["price"] / df_sp500["rate"]
df_sp500 = df_sp500[["date", "price", "price_eur"]]

# Alinhar as séries pelas datas comuns antes do cálculo dos retornos.
# Devido aos calendários distintos, algumas variações podem abranger vários dias.
df_merged = (
    df_us.rename(columns={"yield": "us_yield"})
    .merge(df_all.rename(columns={"yield": "all_yield"}), on="date", how="inner")
    .merge(df_aaa.rename(columns={"yield": "aaa_yield"}), on="date", how="inner")
    .merge(df_sp500, on="date", how="inner")
    .merge(df_eurostoxx.rename(columns={"price": "eurostoxx_price"}), on="date", how="inner")
    .merge(df_exchange_rate.rename(columns={"rate": "eurusd"}), on="date", how="inner")
    .sort_values("date")
    .reset_index(drop=True)
)

df_returns = df_merged[["date"]].copy()

# Aproximação linear do price return: -D_mod * variação da yield em decimal.
# As yields estão expressas em percentagem, daí a divisão por 100.
df_returns["aaa"] = -3 * df_merged["aaa_yield"].diff() / 100
df_returns["all"] = -3 * df_merged["all_yield"].diff() / 100
df_returns["us_usd"] = -3 * df_merged["us_yield"].diff() / 100

# Converter os retornos das obrigações dos EUA para euros, sem cobertura cambial.
fx_return_factor = df_merged["eurusd"].shift(1) / df_merged["eurusd"]
df_returns["us"] = (1 + df_returns["us_usd"]) * fx_return_factor - 1

# Retornos simples dos índices acionistas.
df_returns["sp500_usd"] = df_merged["price"].pct_change()
df_returns["sp500"] = df_merged["price_eur"].pct_change()
df_returns["eurostoxx"] = df_merged["eurostoxx_price"].pct_change()

df_returns = df_returns[
    ["date", "us", "aaa", "all", "sp500", "eurostoxx", "us_usd", "sp500_usd"]
].dropna().reset_index(drop=True)

# -----------------------------------------------------------------------------
# Análise exploratória
# -----------------------------------------------------------------------------
df_ytd = df_returns.copy()
df_ytd["year"] = df_ytd["date"].dt.year
assets = ["us", "aaa", "all", "sp500", "eurostoxx"]

# Retornos acumulados desde o início de cada ano (aproximação por capitalização).
df_ytd[assets] = (1 + df_ytd[assets]).groupby(df_ytd["year"]).cumprod() - 1
df_annual = df_ytd.groupby("year")[assets].last().mul(100).round(2)

df_ret = df_returns.set_index("date")
cols = ["us_usd", "us", "sp500_usd", "sp500", "aaa", "all", "eurostoxx"]

extremes = pd.DataFrame({
    "min_date": df_ret[cols].idxmin(),
    "min_%": df_ret[cols].min() * 100,
    "max_date": df_ret[cols].idxmax(),
    "max_%": df_ret[cols].max() * 100,
}).round(2)

stats = df_ret[cols].describe().T.drop(columns="count") * 100
stats["vol_anual_%"] = df_ret[cols].std() * np.sqrt(252) * 100
stats["mean_anual_%"] = df_ret[cols].mean() * 252 * 100

if __name__ == "__main__":
    # Diagnósticos de qualidade de dados.
    print("Dimensões do DataFrame alinhado:", df_merged.shape)
    print("Valores em falta por coluna:\n", df_merged.isna().sum())
    print("Datas duplicadas:", df_merged["date"].duplicated().sum())

    # Estatísticas e resultados exploratórios.
    print("\nRetornos acumulados por ano (%):\n", df_annual)
    print("\nRetornos mínimos e máximos (%):\n", extremes)
    print("\nEstatísticas descritivas (%):\n", stats.round(2))
    print("\nRetornos médios anualizados (%):\n", stats["mean_anual_%"].round(2))
    print("\nVolatilidades anualizadas (%):\n", stats["vol_anual_%"].round(2))
