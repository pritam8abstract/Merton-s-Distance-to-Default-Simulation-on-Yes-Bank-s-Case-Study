"""
Monte Carlo check of the Merton default probability.
Run:  pip install numpy scipy matplotlib   then   python merton_monte_carlo.py
"""
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

# ---- Inputs (illustrative firm, not Yes Bank) ----------------------------------
V0, D = 120.0, 100.0        # asset value today, default point (debt to be repaid at T)
MU, SIGMA, T = 0.08, 0.25, 1.0   # real-world asset drift, asset volatility, horizon (years)
STEPS = 252                 # daily steps, only used for the barrier-any-time variant
rng = np.random.default_rng(42)

# ---- Closed form: DD and PD = N(-DD) ---------------------------------------------
DD = (np.log(V0 / D) + (MU - 0.5 * SIGMA**2) * T) / (SIGMA * np.sqrt(T))
PD_closed = norm.cdf(-DD)

# ---- Simulation 1: Merton's definition, default only if V_T < D at the horizon ----
def simulate_terminal(n):
    z = rng.standard_normal(n)                                   # one N(0,1) shock per path
    V_T = V0 * np.exp((MU - 0.5 * SIGMA**2) * T + SIGMA * np.sqrt(T) * z)   # exact GBM solution
    return np.mean(V_T < D)                                      # fraction of paths that end below D

# ---- Simulation 2: default if the path touches D at ANY time (barrier version) ------
def simulate_barrier(n):
    dt = T / STEPS
    z = rng.standard_normal((n, STEPS))
    log_paths = np.log(V0) + np.cumsum((MU - 0.5 * SIGMA**2) * dt + SIGMA * np.sqrt(dt) * z, axis=1)
    return np.mean(log_paths.min(axis=1) < np.log(D))            # did the lowest point fall below D?

print(f"DD = {DD:.4f}   closed-form PD = N(-DD) = {PD_closed:.4%}\n")
print(f"{'paths':>9} {'MC PD (V_T<D)':>15} {'+/- 95% CI':>12} {'abs error':>10}")
sizes = [100, 1_000, 10_000, 100_000, 1_000_000]
estimates = []
for n in sizes:
    p = simulate_terminal(n)
    se = np.sqrt(p * (1 - p) / n)                                # binomial standard error
    estimates.append(p)
    print(f"{n:>9,} {p:>15.4%} {1.96*se:>12.4%} {abs(p-PD_closed):>10.4%}")

pb = simulate_barrier(100_000)
print(f"\nBarrier-any-time PD (100k paths, {STEPS} steps): {pb:.4%}  (always >= terminal PD)")

# ---- Convergence plot -----------------------------------------------------------
plt.figure(figsize=(7, 4))
plt.semilogx(sizes, np.array(estimates) * 100, "o-", label="Monte Carlo PD")
plt.axhline(PD_closed * 100, color="crimson", ls="--", label="Closed form N(-DD)")
plt.xlabel("Number of simulated paths"); plt.ylabel("Default probability (%)")
plt.legend(); plt.tight_layout(); plt.savefig("mc_convergence.png", dpi=200)
print("Saved mc_convergence.png")
