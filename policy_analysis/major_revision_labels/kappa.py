"""Cohen's kappa (with 95% bootstrap CI) of the out-of-scope labels between each pair of raters: the LLM
(labeled_claude.csv), human 1 (human_labele_1.csv) and human 2 (human_label_2.csv).

Each pair is compared on the policies both raters labeled, overall and per benchmark.
Human labels "enforceable" and "not enforceable" count as "not out of scope".
Usage: python kappa.py
"""

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

N_BOOTSTRAP = 2000
RATERS = {"LLM": Path("labeled_claude.csv"), "human 1": Path("human_labele_1.csv"), "human 2": Path("human_label_2.csv")}


def load(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    label = df["label"].str.strip()
    df["label"] = np.where(label == "out of scope", "out of scope", np.where(label == "", "", "not out of scope"))
    return df[df["label"] != ""].set_index(["benchmark", "id"])["label"]


def report(name, a, b):
    kappa = cohen_kappa_score(a, b) if len(set(a) | set(b)) > 1 else np.nan
    samples = []
    for _ in range(N_BOOTSTRAP):
        i = rng.integers(0, len(a), len(a))
        if len(set(a[i]) | set(b[i])) > 1:  # kappa is undefined when only one label appears
            samples.append(cohen_kappa_score(a[i], b[i]))
    low, high = np.percentile(samples, [2.5, 97.5]) if samples else (np.nan, np.nan)
    print(f"{name:15s} n={len(a):3d}  agreement={np.mean(a == b):.2f}  "
          f"kappa={kappa:.3f}  95% CI=[{low:.3f}, {high:.3f}]")


labels = {name: load(path) for name, path in RATERS.items()}
rng = np.random.default_rng(0)
for x, y in combinations(RATERS, 2):
    print(f"===== {x} vs {y} =====")
    merged = pd.concat([labels[x].rename("x"), labels[y].rename("y")], axis=1, join="inner")
    report("all", merged["x"].to_numpy(), merged["y"].to_numpy())
    print(pd.crosstab(merged["x"].rename(x), merged["y"].rename(y)).to_string())
    for benchmark, df in merged.groupby(level="benchmark"):
        report(benchmark, df["x"].to_numpy(), df["y"].to_numpy())
    print()
