# How ADB Stress Testing Assistant Works

## High-level design

ADB Stress Testing Assistant is a session-based Streamlit application with three clear layers:

See the visual application schematic at the top of the Help page for the complete request, data, calculation, and result paths.

### Layer responsibilities

| Layer | Responsibility | Must not own |
| --- | --- | --- |
| `app/` | Page layout, user inputs, navigation, session state, charts, and tables | Quantitative model formulas |
| `risk_engine/` | Data models, validation, model interfaces, calculations, and registry discovery | Streamlit widgets or browser-specific behavior |
| `ai_analyst/` | Natural-language intent handling and tool orchestration | A second copy of risk calculations |
| `deployment/` | Container image and Azure deployment configuration | Application secrets in source files |

### Design principles

1. **One portfolio, many views.** The loaded portfolio is the shared source of truth for every dashboard in a browser session.
2. **Registry-driven capability discovery.** Models are selected by category and key, so the UI and AI analyst use the same available capabilities.
3. **Separation of concerns.** Calculations stay independently testable in `risk_engine`; Streamlit is an adapter around those calculations.
4. **Inspectable results.** Every important result should expose units, labels, assumptions, and enough detail to trace a summary back to positions or scenarios.
5. **Stateless deployment.** No database is required for the current workflow. Session state is local to a browser session, so scaling beyond one replica requires sticky sessions or shared state.

## Detailed specifications

### Portfolio input contract

The CSV portfolio source requires these columns:

| Column | Type | Meaning |
| --- | --- | --- |
| `name` | string | Issuer or instrument name |
| `asset_class` | string | Bond, equity, cash, or other supported class |
| `sector` | string | Exposure sector; use `N/A` where it does not apply |
| `market_value` | number | Position value in the portfolio currency |

Optional fields include `position_id`, `expected_return`, `volatility`, `duration`, `credit_spread_dur`, `equity_beta`, `fx_sensitivity`, `leverage_ratio`, `interest_coverage`, `current_ratio`, and `profit_margin`. Missing optional fields receive model defaults defined by the data model.

The portfolio source must reject malformed rows, missing required columns, and invalid numeric values before a model runs. Market values are used to calculate total portfolio value and should be expressed in one consistent currency.

### Functional specifications

| Capability | Inputs | Outputs |
| --- | --- | --- |
| Portfolio | Generated parameters or CSV upload | Position table, total value, sector exposure, asset-class exposure |
| Stress Testing | Registered scenario and optional shock overrides | Base value, shocked value, total P&L, percentage change, sector impact, position impacts |
| Monte Carlo VaR | Simulation count, confidence level, random seed, current portfolio | Simulated P&L distribution, VaR, CVaR/Expected Shortfall, threshold chart |
| Distress Model | Position financial ratios and model defaults | Issuer distress probability and ranked position table |
| Risk Attribution | Portfolio and tail-loss configuration | Component VaR by position, sector, and asset class |
| AI Analyst | Natural-language question and configured `GROQ_API_KEY` | Tool-backed explanation referencing the current portfolio and model outputs |

### Model specifications

- **Rate shock:** applies duration-based first-order repricing for fixed-income exposure.
- **Credit spread widening:** applies credit-spread duration to estimate spread-driven price loss.
- **Equity drawdown:** applies equity beta to equity exposure.
- **FX shock:** applies FX sensitivity to non-base-currency exposure.
- **Severe adverse:** layers the configured macro shocks into one combined scenario.
- **Monte Carlo VaR:** simulates correlated normal returns using sector and asset-class relationships; VaR is a loss percentile and CVaR is the average loss beyond that percentile.
- **Distress model:** uses logistic regression over issuer financial ratios and returns a probability between 0 and 1.
- **Risk attribution:** decomposes tail-scenario loss into additive contributions that can be grouped by position, sector, or asset class.

These are first-order and demonstration-grade models, not a replacement for instrument-level valuation, calibrated market data, or a production model-validation framework. The Help page should make that limitation visible wherever results are interpreted.

### State and interaction specifications

- A random sample portfolio loads on first visit so pages are usable without setup.
- The selected portfolio is stored in Streamlit session state and shared across pages in the same browser session.
- Sidebar notes are stored as `user_notes` in the same session and are not persisted to a database or shared with other users.
- The app uses light mode only; the warm neutral background and orange accent are part of the shared visual system.
- Charts use Plotly with explicit axis labels, units, hover values, and visible risk thresholds where applicable.
- Tables should support inspection through search, column visibility, CSV download, or expandable detail where the Streamlit component provides those controls.

### Security and deployment specifications

- `GROQ_API_KEY` is required only for the AI Analyst and must be injected at runtime through an environment variable or Azure secret.
- `.env` and `.streamlit/secrets.toml` must never be copied into a container image or committed to source control.
- The container listens on port `8000`, binds to `0.0.0.0`, and starts with `streamlit run app/Home.py`.
- Azure Container Apps is the recommended initial target. Use one replica while state remains browser-local.
- A production deployment should add authentication, centralized logging, health monitoring, rate limits, secret rotation, and a shared state store before exposing the app to multiple users or replicas.

### Testing specifications

The test suite should cover:

- portfolio creation, CSV validation, and exposure aggregation;
- each registered scenario's sign and magnitude behavior;
- VaR/CVaR output shape and confidence-level handling;
- distress probability bounds and attribution aggregation;
- registry discovery and model metadata;
- a smoke test that imports every Streamlit page and confirms required files are present.

## 1. Load the portfolio

The app starts with a generated diversified sample portfolio so every dashboard has data immediately. On the Portfolio page, you can generate a new sample or upload a CSV with at least `name`, `asset_class`, `sector`, and `market_value`.

The selected portfolio is stored in the shared Streamlit session. Every dashboard reads that same portfolio, which keeps the analysis consistent as you move through the app.

## 2. Discover the available models

Risk models register themselves under a category and key in `risk_engine/registry.py`. The UI uses that registry to populate model choices, while the AI analyst uses it to find the same capabilities programmatically.

This keeps the interface extensible: adding a registered scenario or model makes it available to the relevant workflow without duplicating a hard-coded catalog.

## 3. Run the analysis

Each dashboard prepares the inputs needed by one risk method:

- Stress Testing applies OSFI-aligned macro shocks to rates, spreads, equities, and FX sensitivities.
- Monte Carlo VaR simulates correlated portfolio returns and reports VaR and CVaR.
- Distress Model estimates issuer distress probabilities from financial ratios.
- Risk Attribution decomposes tail loss by position, sector, and asset class.

The calculations live in `risk_engine`, which contains no Streamlit UI code. That separation keeps the quantitative logic testable and reusable.

## 4. Inspect the result

Dashboards present the output as metrics, Plotly charts, and expandable tables. The charts are descriptive rather than decorative: labels, axes, units, and threshold annotations are kept visible so a result can be reviewed without relying on color alone.

## 5. Ask the AI analyst

The AI Analyst page is an interface over the same portfolio and registered risk tools. It can translate a plain-English question into a model call, then summarize the returned result. The page requires `GROQ_API_KEY`; all other dashboards work without an AI key.

## 6. Extend the application

To add a capability, implement the relevant base class, register it with a category and key, and add the focused dashboard behavior if the workflow needs a new view. Keep calculations in `risk_engine` and presentation in `app` so the boundaries remain easy to test and maintain.
