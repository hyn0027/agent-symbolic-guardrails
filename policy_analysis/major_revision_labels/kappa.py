"""Cohen's kappa (with 95% bootstrap CI) between each LLM's out-of-scope labels (labeled_<backend>.csv)
and human_labele_1.csv.

Human labels "enforceable" and "not enforceable" count as "not out of scope".
Usage: python kappa.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

N_BOOTSTRAP = 2000

human = pd.read_csv("human_labele_1.csv", dtype=str, keep_default_na=False)
human["label"] = np.where(human["label"].str.strip() == "out of scope", "out of scope", "not out of scope")

for path in sorted(Path(".").glob("labeled_*.csv")):
    print(f"===== {path.name} =====")
    llm = pd.read_csv(path, dtype=str, keep_default_na=False)
    merged = llm[llm["label"] != ""].merge(human, on=["benchmark", "id"], suffixes=("_llm", "_human"))

    rng = np.random.default_rng(0)
    for name, df in [("all", merged)] + list(merged.groupby("benchmark")):
        a, b = df["label_llm"].to_numpy(), df["label_human"].to_numpy()
        kappa = cohen_kappa_score(a, b) if len(set(a) | set(b)) > 1 else np.nan
        samples = []
        for _ in range(N_BOOTSTRAP):
            i = rng.integers(0, len(a), len(a))
            if len(set(a[i]) | set(b[i])) > 1:  # kappa is undefined when only one label appears
                samples.append(cohen_kappa_score(a[i], b[i]))
        low, high = np.percentile(samples, [2.5, 97.5]) if samples else (np.nan, np.nan)
        print(f"{name:15s} n={len(a):3d}  agreement={np.mean(a == b):.2f}  "
              f"kappa={kappa:.3f}  95% CI=[{low:.3f}, {high:.3f}]")
        print(pd.crosstab(pd.Series(a, name="LLM"), pd.Series(b, name="human")).to_string(), "\n")
