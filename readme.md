# DCR — Análise de Risco de Mercado

Caso prático de avaliação do risco de mercado de uma carteira estilizada de ativos de investimento próprios, desenvolvido no âmbito de um processo de recrutamento do Banco de Portugal.


## Fontes dos dados

A análise utiliza seis séries históricas, provenientes da Federal Reserve, do ECB Data Portal, da FRED e do Investing.com.

| Ativo / Fator de risco | Ficheiro | Fonte |
|---|---|---|
| Obrigações soberanas dos EUA — spot rate 3 anos | `us_yield_curve.csv` | [Federal Reserve](https://www.federalreserve.gov/data/nominal-yield-curve.htm) |
| Obrigações soberanas AAA da Área do Euro — spot rate 3 anos | `aaa_spot_rate_3y.csv` | [ECB Data Portal](https://data.ecb.europa.eu/data/datasets/YC/YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_3Y) |
| Obrigações soberanas da Área do Euro (All Bonds) — spot rate 3 anos | `all_bonds_spot_rate_3y.csv` | [ECB Data Portal](https://data.ecb.europa.eu/data/datasets/YC/YC.B.U2.EUR.4F.G_N_C.SV_C_YM.SR_3Y) |
| Índice acionista S&P 500 — preços diários de fecho | `S&P_500_Historical_Data.csv` | [Investing.com](https://www.investing.com/indices/us-spx-500-historical-data) |
| Índice acionista Euro STOXX 50 — preços diários de fecho | `Euro_Stoxx_50_Historical_Data.csv` | [Investing.com](https://www.investing.com/indices/eu-stoxx50-historical-data) |
| Taxa de câmbio EUR/USD (USD por EUR) | `DEXUSEU.csv` | [FRED](https://fred.stlouisfed.org/series/DEXUSEU) |

### Fontes alternativas às sugeridas no enunciado

Para os índices acionistas **S&P 500** e **Euro STOXX 50**, foram utilizadas séries históricas do Investing.com em substituição das fontes propostas no enunciado.

Esta decisão deveu-se às seguintes limitações das fontes originais:

- **S&P 500:** os dados disponíveis começavam em 2016, não permitindo cobrir integralmente o período histórico selecionado (2008-2026).
- **Euro STOXX 50:** os dados disponíveis apresentavam periodicidade mensal, incompatível com a frequência diária utilizada na análise.

A utilização do Investing.com permitiu obter séries diárias para ambos os índices, assegurando maior consistência temporal com os restantes fatores de risco.

**Período de análise:** janeiro de 2008 a outubro de 2026, com última observação em 30/10/2026.

## 1. Objetivo

Estimar o Value-at-Risk (VaR) e a Expected Shortfall (ES) da carteira, analisar os benefícios de diversificação e avaliar o comportamento do risco em períodos de stress.

## 2. Estrutura do projeto

```text
DC_DCR/
├── data/                 # Dados históricos originais
├── data_processing.py    # Limpeza e preparação dos dados
├── dcr_analysis.ipynb    # Análise quantitativa e resultados
├── analise_aux.py        # Análises e testes auxiliares
├── pyproject.toml        # Dependências do projeto
├── uv.lock               # Versões das dependências
└── README.md
```

## 3. Configuração do ambiente

O projeto utiliza Python e `uv` para gestão de dependências.

### Pré-requisito

Ter o `uv` instalado.

Documentação: https://docs.astral.sh/uv/

### Instalação

Na pasta principal do projeto, executar:

```bash
uv sync
```

Este comando instala as dependências definidas em `pyproject.toml`, respeitando as versões registadas em `uv.lock`, e cria o ambiente virtual do projeto, caso ainda não exista.

Não é necessário instalar manualmente cada biblioteca.

## 4. Executar a análise

Abrir `dcr_analysis.ipynb` no VS Code ou Jupyter e selecionar o ambiente Python do projeto como kernel.

Executar as células sequencialmente.

O notebook importa os retornos diretamente de `data_processing.py`, pelo que não é necessário executar previamente esse script.

Os ficheiros CSV devem estar disponíveis na pasta `data/`.

## 5. Dados e pressupostos

- Período histórico: janeiro de 2008 a outubro de 2026.
- Última observação: 30/10/2026.
- Moeda base da carteira: EUR.
- Exposições em USD sem cobertura cambial.
- Pesos constantes, assumindo reequilíbrio diário.
- Horizonte de risco: 252 dias úteis.
- VaR e ES paramétricos, com distribuição normal e retorno esperado nulo.
- Retornos obrigacionistas aproximados através da modified duration de 3 anos e das variações das taxas spot a 3 anos.
- Anualização da volatilidade pela regra da raiz quadrada do tempo.
