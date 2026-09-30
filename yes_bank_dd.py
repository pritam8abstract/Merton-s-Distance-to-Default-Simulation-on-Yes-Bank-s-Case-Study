"""
Merton / KMV-style Distance-to-Default for Yes Bank, Jan 2018 - 6 Mar 2020.

Run in VS Code:  pip install numpy pandas scipy matplotlib
                 python yes_bank_dd.py            (CSV must sit in the same folder; any file name containing 'yes' and 'bank' works)
Outputs: yes_bank_dd_series.csv, yes_bank_dd.png
"""
import numpy as np, pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
SEARCH_DIRS = [SCRIPT_DIR, SCRIPT_DIR.parent / "data", Path.cwd()]   # repo layout: src/ and data/ as siblings

def find_csv():
    """Find the price file by name pattern, in the script's folder, ../data, or the cwd."""
    for d in SEARCH_DIRS:
        if not d.exists(): continue
        hits = [p for p in d.glob("*.csv") if "yes" in p.name.lower() and "bank" in p.name.lower() and "dd_series" not in p.name.lower()]
        if hits: return hits[0]
    raise FileNotFoundError(f"Couldn't find the Yes Bank price CSV. Looked in: {[str(d) for d in SEARCH_DIRS]}")

CSV = find_csv()
OUT_DIR = SCRIPT_DIR.parent / "outputs" if (SCRIPT_DIR.parent / "outputs").exists() else SCRIPT_DIR
T = 1.0   # horizon in years


def compute(R=0.06, MU=0.10, WIN=60, D_SCALE=1.0):
    """R risk-free, MU assumed asset drift, WIN vol window (trading days), D_SCALE haircut on default point."""
    # --- 1. Prices -> equity value E (Rs crore) --------------------------------
    px = pd.read_csv(CSV)
    px["Date"] = pd.to_datetime(px["Date"], format="%m/%d/%Y")
    px = px.sort_values("Date").set_index("Date")["Price"]
    px = px[:"2020-03-06"]                                   # stop at the RBI-moratorium shock
    SHARES_CR = np.where(px.index < "2019-08-15", 231.0, 254.9)   # QIP in Aug-2019 (Rs 1,930 cr)
    E = px * SHARES_CR                                       # market cap, Rs crore

    # --- 2. Default point D = total liabilities, as PUBLISHED at each date ----------
    # (public_from, D in Rs crore). D = deposits + borrowings + other liabilities.
    D_TABLE = [
        ("2018-01-01", 238_533),   # Dec-17 (other liabilities approximated)
        ("2018-05-01", 286_688),   # Mar-18
        ("2018-07-31", 304_685),   # Jun-18 (other liabilities interpolated)
        ("2018-10-30", 344_316),   # Sep-18
        ("2019-01-24", 349_349),   # Dec-18 (other liabilities interpolated); Q3FY19 result day
        ("2019-04-27", 353_972),   # Mar-19
        ("2019-07-30", 344_666),   # Jun-19
        ("2019-11-01", 318_786),   # Sep-19 (Q2FY20 press release date)
    ]                              # Dec-19 accounts were only published on 13-Mar-2020
    Dser = pd.Series(np.nan, index=px.index)
    for d, v in D_TABLE:
        Dser[Dser.index >= d] = v * D_SCALE

    # --- 3. Equity volatility from trailing daily log returns ------------------------
    sig_E = np.log(px).diff().rolling(WIN).std() * np.sqrt(252)

    # --- 4. Solve the two Merton equations for V and sigma_V ---------------------
    def bs_terms(V, D, sV):
        d1 = (np.log(V / D) + (R + 0.5 * sV**2) * T) / (sV * np.sqrt(T))
        return d1, d1 - sV * np.sqrt(T)

    def solve_V_sV(E_, D, sE):
        def V_from(sV):                                       # eq.1: E = V N(d1) - D e^{-rT} N(d2)
            f = lambda V: V * norm.cdf(bs_terms(V, D, sV)[0]) - D*np.exp(-R*T)*norm.cdf(bs_terms(V, D, sV)[1]) - E_
            return brentq(f, E_ * 0.5, E_ + D * 3)
        def g(sV):                                            # eq.2: sigma_E E = N(d1) sigma_V V
            V = V_from(sV)
            return norm.cdf(bs_terms(V, D, sV)[0]) * sV * V - sE * E_
        sV = brentq(g, 1e-4, 3.0)
        return V_from(sV), sV

    rows = []
    for t in px.index:
        if np.isnan(sig_E[t]): continue
        V, sV = solve_V_sV(E[t], Dser[t], sig_E[t])
        dd_phys = (np.log(V/Dser[t]) + (MU - 0.5*sV**2)*T) / (sV*np.sqrt(T))   # physical DD
        d2      = (np.log(V/Dser[t]) + (R  - 0.5*sV**2)*T) / (sV*np.sqrt(T))   # risk-neutral d2
        rows.append((t, px[t], E[t], Dser[t], sig_E[t], V, sV, dd_phys, d2))

    out = pd.DataFrame(rows, columns=["Date","Price","E","D","sigma_E","V","sigma_V","DD","d2"]).set_index("Date")
    out["PD_phys"], out["PD_rn"] = norm.cdf(-out.DD), norm.cdf(-out.d2)

    return out


if __name__ == '__main__':
    out = compute()
    out.to_csv(OUT_DIR / 'yes_bank_dd_series.csv')
    # --- 5. Plot vs rating actions and RBI events ---------------------------------
    events = [("2018-09-21","CEO-term ruling hits market"),("2018-11-28","ICRA+CARE downgrade"),
              ("2019-05-03","ICRA downgrade"),("2019-07-24","ICRA downgrade"),
              ("2019-11-14","CARE downgrade"),("2020-03-05","RBI moratorium")]
    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    ax[0].plot(out.index, out.Price, color="#333"); ax[0].set_ylabel("Price (Rs)"); ax[0].set_yscale("log")
    ax[1].plot(out.index, out.DD, label="DD (mu=10%)", color="#c0392b"); ax[1].plot(out.index, out.d2, label="d2 (mu=r)", color="#2c6fbb")
    ax[1].set_ylabel("Distance to default (sigma units)"); ax[1].legend()
    for a in ax:
        for d, lab in events: a.axvline(pd.Timestamp(d), color="grey", ls="--", lw=.8)
    for d, lab in events: ax[1].text(pd.Timestamp(d), ax[1].get_ylim()[1], lab, rotation=90, va="top", ha="right", fontsize=7)
    plt.tight_layout(); plt.savefig(OUT_DIR / "yes_bank_dd.png", dpi=200)
    print(out[["Price","sigma_E","V","sigma_V","DD","d2"]].resample("ME").last().round(3))
