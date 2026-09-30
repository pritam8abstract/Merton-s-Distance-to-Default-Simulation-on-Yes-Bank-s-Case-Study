# From Committee to Continuum
### Can markets price default faster than rating agencies?

A structural credit-risk model (Merton / KMV) tested against a real bank failure. Built for MS37025 (Managing Financial Services and Institutions), Department of Management Studies, NIT Warangal — and written to double as FRM Part 1/2 study material.

**Question:** rating agencies (CRISIL, ICRA, CARE) assess bank default risk periodically, through committee judgement, based on disclosed information. The Merton model instead reads a *distance to default* continuously out of traded equity prices, with no committee involved. Using the Yes Bank crisis (2018–2020) as the test case: did the market-implied signal deteriorate before the agencies downgraded, and before the RBI intervened?

> **Verdict:** the market signal moved first in every downgrade episode — by 3 to 68 days — but it did not time the regulatory intervention itself. On the day before the moratorium, distance to default stood at its highest level since September 2018, because an old volatility spike had rolled out of the measurement window and the bank's worst quarter was still unpublished. Full reasoning in [`docs/Master_Note_Committee_to_Continuum.pdf`](docs/Master_Note_Committee_to_Continuum.pdf), Sections 5–6.

![Distance to default vs rating actions](figures/dd_timeline.png)

## Repo layout

```
├── data/         Yes Bank daily closing prices (source: your own download — verify licence before reuse)
├── src/          yes_bank_dd.py (data pipeline) and merton_monte_carlo.py (Monte Carlo check)
├── outputs/      yes_bank_dd_series.csv — the computed DD/PD time series
├── figures/      generated charts (payoff diagram, GBM paths, DD timeline, sensitivity, KMV schematic)
├── slides/       MFSI_Committee_to_Continuum_v2.pptx — 23-slide presentation deck
├── docs/         Master_Note_Committee_to_Continuum.pdf — full LaTeX write-up, plus its .tex source
└── requirements.txt
```

## Running it

```bash
git clone <this-repo>
cd from-committee-to-continuum
pip install -r requirements.txt

python src/yes_bank_dd.py            # rebuilds outputs/yes_bank_dd_series.csv and a DD chart
python src/merton_monte_carlo.py     # confirms the Monte Carlo estimate converges to the closed form
```

`yes_bank_dd.py` looks for a CSV whose name contains "yes" and "bank" in its own folder, in `../data`, or in the current directory — so it works whether you run it from `src/` in this repo or drop it somewhere else next to your own price file.

## Method, in brief

1. **Equity** = daily close × shares outstanding (231.0 cr, rising to 254.9 cr after the August 2019 QIP).
2. **Default point D** = total liabilities (deposits + borrowings + other), taken from the balance sheet *as published at the time* — not the quarter-end figure, since that's what a market participant could actually see.
3. **Asset value V and asset volatility σ_V** are not observable, so they're solved from two simultaneous equations linking them to observed equity value and equity volatility (see `src/yes_bank_dd.py::solve_V_sV`).
4. **Distance to default**: DD = [ln(V/D) + (μ − σ²/2)·T] / (σ√T), computed daily from a 60-day trailing equity-volatility window.
5. Robustness checked against seven variants of the rate, drift, volatility window and default-point assumptions — the *timing* of the warnings is stable; the *level* of DD is not.

Full derivation, from the lognormal distribution and geometric Brownian motion up through Black–Scholes, Merton and KMV's refinements, is in the [master note](docs/Master_Note_Committee_to_Continuum.pdf).

## Data sources and caveats

- Yes Bank daily closing prices: your own exchange/vendor download (`data/Yes_Bank_Stock_Price_History.csv`). Check the data provider's terms before redistributing this file publicly.
- Balance-sheet figures and rating-action dates are drawn from Yes Bank's own press releases and public news reporting; several dates are the *report* date rather than the agency's own action date. A full list of what I could not verify against a primary source is in the master note, Section 8 ("What I could not verify").
- This is coursework analysis, not investment research, and none of it should be read as advice on any security.

## License

MIT — see [LICENSE](LICENSE). The Yes Bank price data itself may carry separate terms from its original source; the code and written analysis are MIT-licensed.

## Author

Dhritabrata Swarnakar — MBA, Department of Management Studies, NIT Warangal
