import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(r"C:\Users\quan1939\Dropbox\Vault\10-19 Research\15 Blog Notes\files")
OUT.mkdir(parents=True, exist_ok=True)

GOLD = "#CFB87C"; SLATE = "#565A5C"; INK = "#2D2F30"

# ============================================================
# Simulation 1: pseudoreplication inflates the false-positive rate
# Null is TRUE (no treatment effect). Littermates share a father-level
# random value, so fetuses from one father are correlated.
# Two analyses: (a) count each fetus, (b) test at the father level.
# ============================================================
def simulate(icc, k_fathers=5, pups=5, seed=0):
    rng = np.random.default_rng(seed)
    tau = np.sqrt(icc / (1 - icc)) if icc > 0 else 0.0
    rows = []
    for group in (0, 1):                                   # two groups, SAME mean (null is true)
        for f in range(k_fathers):
            father_value = rng.normal(0, 1) * tau          # shared by this father's litter
            fid = f"{group}_{f}"
            for _ in range(pups):
                rows.append((group, fid, father_value + rng.normal(0, 1)))
    return pd.DataFrame(rows, columns=["group", "father", "y"])

def false_positive_rate(icc, k_fathers=5, pups=5, n_sim=800):
    naive = mixed = 0
    for s in range(n_sim):
        df = simulate(icc, k_fathers=k_fathers, pups=pups, seed=s)
        a, b = df.y[df.group == 0], df.y[df.group == 1]
        naive += stats.ttest_ind(a, b).pvalue < .05        # (a) count each fetus
        # (b) test at the father level: compare the two groups using the
        # BETWEEN-father variation. For this balanced design this is the exact
        # test of the random-intercept (father random-effect) model, i.e. a
        # t-test on the per-father means (df = 2*(k_fathers - 1)).
        fa = df[df.group == 0].groupby("father").y.mean()
        fb = df[df.group == 1].groupby("father").y.mean()
        mixed += stats.ttest_ind(fa, fb).pvalue < .05
    return naive / n_sim, mixed / n_sim

N_SIM = 3000
iccs = np.array([0, .1, .2, .3, .4, .5])
fetus_fpr = np.empty(len(iccs)); mixed_fpr = np.empty(len(iccs))
print("=== Simulation 1: pseudoreplication FPR (father-level test; 5 fathers/group, 5 pups) ===")
for i, icc in enumerate(iccs):
    fetus_fpr[i], mixed_fpr[i] = false_positive_rate(icc, n_sim=N_SIM)
    print(f"  ICC={icc:.1f}  without random effects={fetus_fpr[i]*100:5.1f}%   with random effects={mixed_fpr[i]*100:4.1f}%", flush=True)

# Monte Carlo 95% CI for each proportion: 1.96 * sqrt(p(1-p)/N)
se = lambda p: 1.96 * np.sqrt(p * (1 - p) / N_SIM) * 100
fig, ax = plt.subplots(figsize=(6.2, 4))
ax.axhline(5, ls="--", color=SLATE, lw=1, zorder=1)
ax.text(0.005, 5.6, "nominal 5%", color=SLATE, fontsize=9)
ax.errorbar(iccs, fetus_fpr*100, yerr=se(fetus_fpr), fmt="-o", color="#c0392b", lw=2.2,
            capsize=3, label="Without Random Effects")
ax.errorbar(iccs, mixed_fpr*100, yerr=se(mixed_fpr), fmt="-o", color=SLATE, lw=2.2,
            capsize=3, label="With Random Effects")
ax.set_xlabel("Within-litter correlation (ICC)"); ax.set_ylabel("False-positive rate (%)")
ax.legend(frameon=False); ax.set_ylim(0, None)
[ax.spines[s].set_visible(False) for s in ("top", "right")]
fig.tight_layout(); fig.savefig(OUT / "fig-pseudoreplication.png", dpi=150); plt.close(fig)

# ============================================================
# Simulation 2: CVA on pure noise reproduces the paper's separation
# Faithful data structure: 47 landmarks in 2D, Procrustes-aligned
# (~90 shape variables), four groups, NO real differences. Any seed
# separates cleanly -- no cherry-picking.
# ============================================================
from matplotlib.patches import Ellipse

def gen_landmarks(rng, n, k=47, noise=0.05):
    template = rng.normal(0, 1, (k, 2))                    # one shape, shared by all (no group diff)
    return template[None] + rng.normal(0, noise, (n, k, 2))

def gpa(L, iters=3):                                       # generalized Procrustes alignment
    L = L - L.mean(1, keepdims=True)                       # center each specimen
    L = L / np.sqrt((L ** 2).sum((1, 2), keepdims=True))   # unit centroid size
    ref = L[0].copy()
    for _ in range(iters):
        for i in range(len(L)):
            U, _, Vt = np.linalg.svd(L[i].T @ ref)
            L[i] = L[i] @ (U @ Vt)                         # rotate to reference
        ref = L.mean(0); ref /= np.sqrt((ref ** 2).sum())
    return L.reshape(len(L), -1)

def shape_space(X, k=47):
    Xc = X - X.mean(0); U, s, _ = np.linalg.svd(Xc, full_matrices=False)
    return (U[:, :2 * k - 4] * s[:2 * k - 4])              # 90 shape dims for 47 2D landmarks

def cva_scores(X, y):
    groups = np.unique(y); g = len(groups); p = X.shape[1]; grand = X.mean(0)
    Sw = np.zeros((p, p)); Sb = np.zeros((p, p))
    for gg in groups:
        Xi = X[y == gg]; mi = Xi.mean(0); d = (mi - grand)[:, None]
        Sw += (Xi - mi).T @ (Xi - mi); Sb += len(Xi) * (d @ d.T)
    evals, evecs = np.linalg.eig(np.linalg.solve(Sw, Sb))
    return X @ evecs[:, np.argsort(evals.real)[::-1][:g - 1]].real

def wilks_p(X, y):
    groups = np.unique(y); g = len(groups); n, p = X.shape; grand = X.mean(0)
    T = (X - grand).T @ (X - grand); W = np.zeros((p, p))
    for gg in groups:
        Xi = X[y == gg]; mi = Xi.mean(0); W += (Xi - mi).T @ (Xi - mi)
    ln = np.linalg.slogdet(W)[1] - np.linalg.slogdet(T)[1]
    return stats.chi2.sf(-(n - 1 - (p + g) / 2) * ln, p * (g - 1))

group_sizes = [24, 43, 17, 14]; y = np.repeat(np.arange(4), group_sizes)
labels = ["Control", "Low", "Medium", "High"]; cols = ["#7a7d7f", "#f2a0a0", "#e06666", "#cc0000"]

circ = []
for seed in range(20):                                     # robustness: every seed separates
    r = np.random.default_rng(seed)
    Xs = shape_space(gpa(gen_landmarks(r, sum(group_sizes))))
    circ.append(wilks_p(cva_scores(Xs, y)[:, :3], y))
print("\n=== Simulation 2: CVA on pure noise (47 landmarks, 2D, Procrustes) ===")
print(f"  circular p (CV-score MANOVA) across 20 seeds: median = {np.median(circ):.1e}, max = {max(circ):.1e}")

# seed-0 (the plotted dataset): pairwise CV-score MANOVA p-values, as in the paper's Table 2
from itertools import combinations
Xs0 = shape_space(gpa(gen_landmarks(np.random.default_rng(0), sum(group_sizes))))
S0 = cva_scores(Xs0, y)[:, :3]
pair_ps = [wilks_p(np.vstack([S0[y == a], S0[y == b]]),
                   np.r_[np.zeros((y == a).sum()), np.ones((y == b).sum())])
           for a, b in combinations(range(4), 2)]
print(f"  seed-0 pairwise CV-score p-values: largest = {max(pair_ps):.1e}, smallest = {min(pair_ps):.1e}")

rng = np.random.default_rng(0)                             # seed 0, representative (not cherry-picked)
S = cva_scores(shape_space(gpa(gen_landmarks(rng, sum(group_sizes)))), y)[:, :2]
if S[y == 0, 0].mean() > S[y == 3, 0].mean(): S[:, 0] *= -1
fig, ax = plt.subplots(figsize=(6.4, 4.1))
for g, (lab, c) in enumerate(zip(labels, cols)):
    P = S[y == g]; ax.scatter(P[:, 0], P[:, 1], s=15, color=c, zorder=3)
    mu = P.mean(0); vals, vec = np.linalg.eigh(np.cov(P.T))
    ang = float(np.degrees(np.arctan2(vec[1, 1], vec[0, 1]))); w, h = 2 * np.sqrt(vals) * 1.7
    ax.add_patch(Ellipse((mu[0], mu[1]), w, h, angle=ang, fill=False, edgecolor=c, lw=1.4, zorder=2))
    ax.annotate(lab, (mu[0], mu[1] + np.sqrt(vals.max()) * 2.1), color=c, weight="bold", ha="center", fontsize=11)
ax.set_xlabel("Canonical variate 1"); ax.set_ylabel("Canonical variate 2")
[ax.spines[s].set_visible(False) for s in ("top", "right")]
fig.tight_layout(); fig.savefig(OUT / "fig-cva-noise.png", dpi=150); plt.close(fig)

print("\nFigures written to:", OUT)
