import pandas as pd
import os
import plotly.express as px
# Ignorar as primeiras 7 linhas, que contêm metadados e notas.
# A 8.ª linha contém os nomes das colunas.
us_curve = pd.read_csv("data/us_yield_curve.csv", header = 7) 
all = pd.read_csv("data/all_bonds_spot_rate_3y.csv")
aaa = pd.read_csv("data/aaa_spot_rate_3y.csv")
#sp500 = pd.read_csv("data/SP500.csv")
sp500 = pd.read_csv("data/S&P_500_Historical_Data.csv")
#eurostoxx = pd.read_csv("data/eurostoxx_50.csv")
eurostoxx = pd.read_csv("data/Euro_Stoxx_50_Historical_Data.csv")
exchange_rate = pd.read_csv("data/DEXUSEU.csv")

# Create copies for cleaning while preserving the original DataFrames.
df_us = us_curve.copy()
df_all = all.copy()
df_aaa = aaa.copy()
#df_sp500 = sp500.copy()
df_sp500 = sp500.copy()
df_eurostoxx = eurostoxx.copy()
df_exchange_rate = exchange_rate.copy()

#Como vamos utilizar a spot rate a 3 anos como fator de risco representativo de cada um dos 3 componentes obrigacionista
#para a yield curve dos US vamos precisar apenas da Date e do SVENY03 (zero-coupon yield a 3 anos)
df_us = df_us.rename(columns= {'Date':'date','SVENY03':'yield'})
df_us = df_us[['date','yield']]
#df_us = df_us[df_us['date']>= '2008-01-01'].reset_index(drop = True)

df_all = df_all.rename(columns= {'DATE':'date',df_all.columns[-1]:'yield'})
df_all = df_all[['date','yield']]
#df_all = df_all[df_all['date']>= '2008-01-01'].reset_index(drop = True)

#data from ecb_portal always has last column as yield, so we do columns[-1] to simplify code
df_aaa = df_aaa.rename(columns= {'DATE':'date',df_aaa.columns[-1]:'yield'})
df_aaa = df_aaa[['date','yield']]
#df_aaa = df_aaa[df_aaa['date']>= '2008-01-01'].reset_index(drop = True)

df_sp500 = df_sp500.rename(columns={"Date": "date", "Price": "price"})
df_sp500 = df_sp500[['date','price']]
df_sp500["date"] = pd.to_datetime(df_sp500["date"], format="%m/%d/%Y")
df_sp500 = df_sp500.sort_values(by="date").reset_index(drop=True)
#df_sp500["date"] = df_sp500["date"].dt.strftime("%Y-%m-%d")
df_sp500["price"] = (df_sp500["price"].str.replace(",", "", regex=False).astype(float))

df_eurostoxx = df_eurostoxx.rename(columns={"Date": "date", "Price": "price"})
df_eurostoxx = df_eurostoxx[['date','price']]
df_eurostoxx["date"] = pd.to_datetime(df_eurostoxx["date"], format="%m/%d/%Y")
df_eurostoxx = df_eurostoxx.sort_values(by="date", ascending= True).reset_index(drop=True)
#df_eurostoxx["date"] = df_eurostoxx["date"].dt.strftime("%Y-%m-%d")
df_eurostoxx["price"] = (df_eurostoxx["price"].str.replace(",", "", regex=False).astype(float))
# code below yields same result as october obs for ecb series, hence series is similar 
#average = df_eurostoxx.loc[pd.to_datetime(df_eurostoxx["date"], dayfirst=True).dt.to_period("M") == "2026-10", "price"].mean()

df_exchange_rate = df_exchange_rate.rename(columns= {'observation_date':'date','DEXUSEU':'rate'})
#df_exchange_rate = df_exchange_rate[df_exchange_rate['date']>= '2008-01-01'].reset_index(drop = True)


dfs = {
    "us": df_us,
    "all": df_all,
    "aaa": df_aaa,
    "sp500": df_sp500,
    "eurostoxx": df_eurostoxx,
    "exchange_rate": df_exchange_rate
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

#Transformar sp500 em eur
df_sp500 = df_sp500.merge(df_exchange_rate, on="date", how="inner")
df_sp500["price_eur"] = df_sp500["price"] / df_sp500["rate"]
df_sp500 = df_sp500[["date", "price","price_eur"]]

#df_us: 4716
#df_all: 4819
#df_aaa: 4819
#df_sp500: 4748
#df_eurostoxx: 4840
#df_exchange_rate: 4719

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

print(df_merged.shape)
print(df_merged.isna().sum())
print(df_merged["date"].duplicated().sum())

df_returns = df_merged[["date"]].copy()

# Obrigações da Área Euro
df_returns["aaa"] = -3 * df_merged["aaa_yield"].diff() / 100
df_returns["all"] = -3 * df_merged["all_yield"].diff() / 100

# Obrigações dos EUA (retorno em USD)
df_returns["us_usd"] = -3 * df_merged["us_yield"].diff() / 100

# Converter retorno das obrigações americanas para EUR
fx_return_factor = df_merged["eurusd"].shift(1) / df_merged["eurusd"]

df_returns["us"] = (1 + df_returns["us_usd"]) * fx_return_factor - 1

# Índices acionistas
df_returns["sp500_usd"] = df_merged["price"].pct_change()
df_returns["sp500"] = df_merged["price_eur"].pct_change()
df_returns["eurostoxx"] = df_merged["eurostoxx_price"].pct_change()

# Manter apenas os cinco ativos e remover a primeira observação
df_returns = df_returns[
    ["date", "us", "aaa", "all", "sp500", "eurostoxx",
     "us_usd", "sp500_usd"]
].dropna().reset_index(drop=True)

# do the values make sense?

df_ytd = df_returns.copy()
df_ytd["year"] = df_ytd["date"].dt.year

# Retorno acumulado desde o início de cada ano
assets = ["us", "aaa", "all", "sp500", "eurostoxx"]
df_ytd[assets] = (
    (1 + df_ytd[assets])
    .groupby(df_ytd["year"])
    .cumprod() - 1
)
df_annual = (
    df_ytd.groupby("year")[assets]
    .last()
    .mul(100)
    .round(2)
)

print(df_annual)


import numpy as np

df_ret = df_returns.set_index("date")

cols = [
    "us_usd", "us", "sp500_usd", "sp500",
    "aaa", "all", "eurostoxx"
]

# Retornos mínimos e máximos, com as respetivas datas
extremes = pd.DataFrame({
    "min_date": df_ret[cols].idxmin(),
    "min_%": df_ret[cols].min() * 100,
    "max_date": df_ret[cols].idxmax(),
    "max_%": df_ret[cols].max() * 100
}).round(2)

print(extremes)

# Estatísticas descritivas e volatilidade anualizada
stats = df_ret[cols].describe().T.drop(columns="count") * 100

stats["vol_anual_%"] = df_ret[cols].std() * np.sqrt(252) * 100

print(stats.round(2))

stats["mean_anual_%"] = df_ret[cols].mean() * 252 * 100
print(stats['mean_anual_%'].round(2))
print(stats['vol_anual_%'].round(2))

#NOTAS
'''
Os resultados parecem robustos

Os resultados apresentam comportamentos economicamente plausíveis:
- Ações: retornos médios e volatilidades superiores aos das obrigações e próximos do esperado.
- Obrigações AAA e All Bonds: Return do all bonds superior ao AAA, o que faz sentido ado que all bonds inclui p.e. junk bonds, que têm maior retorno/risco.
- Obrigações americanas: volatilidade anualizada de 2,63% em USD versus 9,18% em EUR. Diferença advém da volatilidade do eur/usd
Há apenas uma precisão: a volatilidade conjunta depende também da correlação entre o retorno da obrigação em USD e a variação cambial, não apenas da soma dos dois riscos.
'''


# Yes, return sp>eurostoxx>us>all>aaa
#the one from the us is a bit sketchy to analyze because there is the currency chang
# and also rates differ etc...

#Não vamos apresentar gráficos sobre os retornos
#porque como sao retornos diários, é mt confusa a interpretação

