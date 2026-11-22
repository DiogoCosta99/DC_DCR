from data_processing import df_returns
import pandas as pd
import numpy as np
from scipy.stats import norm

weights = {"us": 0.2, "aaa": 0.25, "all": 0.4, "sp500": 0.05, "eurostoxx": 0.1}

# Assume-se que os pesos são mantidos constantes diariamente (reequilíbrio diário).
# Na prática, este pressuposto não considera custos de transação.
df_portfolio = df_returns[["date"]].copy()

df_portfolio["portfolio_return"] = (
    df_returns[list(weights)]
    .mul(pd.Series(weights))
    .sum(axis=1)
)

portfolio_ret = df_portfolio["portfolio_return"].mean() * 252
portfolio_vol = df_portfolio["portfolio_return"].std() * np.sqrt(252)

print(f"Annualized volatility: {portfolio_vol:.2%}")
print(f"Annualized return: {portfolio_ret:.2%}")

# Resultados coerentes com uma carteira composta por 85% de obrigações
# e com uma exposição de 5% a ações dos EUA.
sigma = df_portfolio["portfolio_return"].std()

var_95 = norm.ppf(0.95) * sigma
var_99 = norm.ppf(0.99) * sigma

print(f"VaR diário 95%: {var_95:.2%}")
print(f"VaR diário 99%: {var_99:.2%}")

var_95_y = norm.ppf(0.95) * sigma * np.sqrt(252)
var_99_y = norm.ppf(0.99) * sigma * np.sqrt(252)

print(f"VaR anual 95%: {var_95_y:.2%}")
print(f"VaR anual 99%: {var_99_y:.2%}")

# Component VaR

# Ativos e respetivos pesos
assets = list(weights.keys())
w = pd.Series(weights)

# Matriz de covariâncias dos retornos diários
cov_matrix = df_returns[assets].cov()

# Volatilidade diária da carteira
sigma_p = np.sqrt(w @ cov_matrix @ w)

# Contribuição marginal para a volatilidade
mcr = (cov_matrix @ w) / sigma_p

# Component VaR anual (retorno esperado nulo)
component_var_95 = w * norm.ppf(0.95) * mcr * np.sqrt(252)
component_var_99 = w * norm.ppf(0.99) * mcr * np.sqrt(252)

# A contribuição relativa é igual para os níveis de confiança de 95% e 99%.
df_component_var = pd.DataFrame({
    "weight": w,
    "component_var_95": component_var_95,
    "component_var_99": component_var_99,
    "contribution_pct_var": component_var_95 / component_var_95.sum() * 100,
})

print(df_component_var.round(4))

# Validar que a soma das contribuições corresponde ao VaR total
assert np.isclose(component_var_95.sum(), var_95_y)
assert np.isclose(component_var_99.sum(), var_99_y)

# Expected Shortfall

sigma_annual = sigma * np.sqrt(252)

# Expected Shortfall paramétrico
es_95_y = sigma_annual * norm.pdf(norm.ppf(0.95)) / (1 - 0.95)
es_99_y = sigma_annual * norm.pdf(norm.ppf(0.99)) / (1 - 0.99)

print(f"ES anual 95%: {es_95_y:.2%}")
print(f"ES anual 99%: {es_99_y:.2%}")

# Component ES anual
component_es_95 = (
    w * mcr * np.sqrt(252)
    * norm.pdf(norm.ppf(0.95)) / 0.05
)

component_es_99 = (
    w * mcr * np.sqrt(252)
    * norm.pdf(norm.ppf(0.99)) / 0.01
)

df_component_es = pd.DataFrame({
    "weight": w,
    "component_es_95": component_es_95,
    "component_es_99": component_es_99,
    "contribution_pct_es": component_es_99 / component_es_99.sum() * 100,
})

print(df_component_es.round(2))

# Validar a decomposição
assert np.isclose(component_es_95.sum(), es_95_y)
assert np.isclose(component_es_99.sum(), es_99_y)

# O Euro STOXX 50 apresenta a maior contribuição para o VaR,
# seguido das obrigações EUA e, em terceiro lugar, do S&P 500.

# Correlações entre os cinco ativos
corr_matrix = df_returns[assets].corr()
print(corr_matrix.round(3))

# Volatilidades individuais anualizadas
df_volatility = pd.DataFrame({
    "weight": pd.Series(weights),
    "annual_volatility_pct": df_returns[assets].std() * np.sqrt(252) * 100,
})

print(df_volatility.round(2))
