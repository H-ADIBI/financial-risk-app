# Portfolio Risk Studio

An AI-enabled portfolio stress testing application: OSFI-aligned macro
stress scenarios, Monte Carlo VaR/CVaR, a logistic-regression issuer
distress model, component VaR risk attribution, and an AI risk analyst
built on LangChain/LangGraph.

## Why it's structured this way

Every model in this app — where the portfolio comes from, which stress
scenario runs, which VaR method, which distress model, which attribution
method — is a small class registered under a category key in
`risk_engine/registry.py`. The Streamlit UI and the AI analyst's tools
both ask the registry "what's available" rather than hardcoding a model
list, so:

- **Adding a model** = add one new file implementing the relevant base
  class, decorated with `@register("<category>", "<key>")`. It appears
  in the matching page's dropdown and becomes callable by the AI analyst
  automatically. No other file needs to change.
- **Removing a model** = delete its file.
- **Modifying a model** = edit its file in place.

See `risk_engine/registry.py` for the full explanation, and look at any
existing module (e.g. `risk_engine/scenarios/osfi_scenarios.py`) as a
template for a new one. A `risk_engine/forecasting/` category is already
scaffolded (with a placeholder `naive_drift` model) as the seam for a
future ARIMAX-based interest-rate forecaster whose output could drive
the rate-shock stress scenario's magnitude instead of a fixed constant.

## Project layout

```
app/                  Streamlit UI (Home + one page per feature)
risk_engine/          All the quant logic -- no Streamlit imports, unit-testable
  registry.py         The plugin registry described above
  data/                Portfolio/Position models + PortfolioSource (random, csv)
  scenarios/           OSFI-aligned stress scenarios
  forecasting/         Forecast models (placeholder today; ARIMAX slot for later)
  var/                 Monte Carlo VaR/CVaR
  credit/              Logistic regression distress model
  attribution/         Component VaR risk attribution
ai_analyst/           LangChain tools + LangGraph agent wrapping risk_engine
deployment/           Dockerfile + Azure deployment scaffolding
tests/                Smoke tests
```

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit .env and add your GROQ_API_KEY
streamlit run app/Home.py
```

The app opens with a randomly generated sample portfolio so every page
works immediately. Every page except the AI Analyst works with zero
configuration; the AI Analyst page needs `GROQ_API_KEY` set in `.env`.

## Using your own portfolio

Go to the **Portfolio** page, choose "Upload CSV", and upload a CSV with
at minimum these columns: `name, asset_class, sector, market_value`.
Optional columns (see `risk_engine/data/models.py`'s `Position` fields
for the full list) let you specify volatility, duration, credit spread
duration, equity beta, FX sensitivity, and the financial ratios the
distress model uses; anything you omit falls back to a reasonable default.

## Running tests

```bash
pytest
```

## Notes on model depth

These are working, real implementations, but deliberately lightweight
ones meant as a strong starting point rather than production-calibrated
models:

- Stress scenarios use first-order (duration/beta/sensitivity) linear
  repricing, not full instrument-level revaluation.
- Monte Carlo VaR assumes multivariate-normal returns with a
  sector/asset-class-implied correlation matrix, not fat tails or a copula.
- The distress model is trained on synthetic data with a hand-crafted
  (but plausible) relationship between financial ratios and distress —
  swap in real issuer data via `LogisticDistressModel.fit(training_df=...)`
  when you have it.

Each of these is isolated behind its category's base class, so hardening
any one of them is a self-contained change.

## Deploying to Azure

See `deployment/DEPLOY.md` for step-by-step instructions (App Service or
Container Apps, both via the included `deployment/Dockerfile`).
