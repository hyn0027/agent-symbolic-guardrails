"""Cohen's kappa (with 95% bootstrap CI) between each pair of raters: the LLM (labeled.csv), human 1
(human_label_1.csv) and human 2 (human_label_2.csv).

Each column is compared on the papers where both raters of the pair gave a label. For "out of scope" in a pair with
the LLM, papers the human marked out of scope as "duplicated" are left out.
Usage: python kappa.py
"""

from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

COLUMNS = ["tool-use llm-agent", "safety/security", "out of scope", "domain", "policy"]
RATERS = {"LLM": "labeled.csv", "human 1": "human_label_1.csv", "human 2": "human_label_2.csv"}
N_BOOTSTRAP = 2000


def normalize(labels):
    # e.g. "general purpose" -> "general-purpose", "unclear" -> "unclear"
    return labels.str.strip().str.lower().str.replace(" ", "-")


def load(path):
    # keep_default_na=False: otherwise pandas reads the "N/A" policy label as an empty cell
    df = pd.read_csv(path, dtype=str, keep_default_na=False).rename(columns={"random id": "rand id"})
    return df.set_index("rand id")[COLUMNS + ["why out of scope"]].apply(normalize)


labels = {name: load(path) for name, path in RATERS.items()}
rng = np.random.default_rng(0)
for x, y in combinations(RATERS, 2):
    print(f"===== {x} vs {y} =====")
    merged = labels[x].join(labels[y], how="inner", lsuffix="_x", rsuffix="_y")
    for col in COLUMNS:
        a, b = merged[col + "_x"], merged[col + "_y"]
        both = (a != "") & (b != "")
        if col == "out of scope" and "LLM" in (x, y):
            # the model is never offered "duplicated" (it needs other papers' context), so leave those papers out
            human = "_y" if x == "LLM" else "_x"
            both &= merged["why out of scope" + human] != "duplicated"
        a, b = a[both].to_numpy(), b[both].to_numpy()
        if len(a) == 0:
            print(f"{col:20s} n=0\n")
            continue

        kappa = cohen_kappa_score(a, b) if len(set(a) | set(b)) > 1 else np.nan
        samples = []
        for _ in range(N_BOOTSTRAP):
            i = rng.integers(0, len(a), len(a))
            if len(set(a[i]) | set(b[i])) > 1:  # kappa is undefined when only one label appears
                samples.append(cohen_kappa_score(a[i], b[i]))
        low, high = np.percentile(samples, [2.5, 97.5]) if samples else (np.nan, np.nan)
        print(f"{col:20s} n={len(a):3d}  agreement={np.mean(a == b):.2f}  "
              f"kappa={kappa:.3f}  95% CI=[{low:.3f}, {high:.3f}]")
        print(pd.crosstab(pd.Series(a, name=x), pd.Series(b, name=y)).to_string(), "\n")
