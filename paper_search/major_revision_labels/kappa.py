"""Cohen's kappa (with 95% bootstrap CI) between the LLM labels and human_label_1.csv.

Each column is compared on the papers where both the LLM and the human gave a label. For "out of scope", papers the human marked out of scope as "duplicated" are left out.
Usage: python kappa.py
"""

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

COLUMNS = ["tool-use llm-agent", "safety/security", "out of scope", "domain", "policy"]
N_BOOTSTRAP = 2000

# keep_default_na=False: otherwise pandas reads the "N/A" policy label as an empty cell
llm = pd.read_csv("labeled.csv", dtype=str, keep_default_na=False)
human = pd.read_csv("human_label_1.csv", dtype=str, keep_default_na=False).rename(columns={"random id": "rand id"})
merged = llm.merge(human, on="rand id", suffixes=("_llm", "_human"))


def normalize(labels):
    # e.g. "general purpose" -> "general-purpose", "unclear" -> "unclear"
    return labels.str.strip().str.lower().str.replace(" ", "-")


rng = np.random.default_rng(0)
for col in COLUMNS:
    a, b = normalize(merged[col + "_llm"]), normalize(merged[col + "_human"])
    both = (a != "") & (b != "")
    if col == "out of scope":
        # the model is never offered "duplicated" (it needs other papers' context), so leave those papers out
        both &= normalize(merged["why out of scope_human"]) != "duplicated"
    a, b = a[both].to_numpy(), b[both].to_numpy()
    if len(a) == 0:
        print(f"{col:20s} n=0")
        continue

    kappa = cohen_kappa_score(a, b)
    samples = []
    for _ in range(N_BOOTSTRAP):
        i = rng.integers(0, len(a), len(a))
        if len(set(a[i]) | set(b[i])) > 1:  # kappa is undefined when only one label appears
            samples.append(cohen_kappa_score(a[i], b[i]))
    low, high = np.percentile(samples, [2.5, 97.5]) if samples else (np.nan, np.nan)
    print(f"{col:20s} n={len(a):3d}  agreement={np.mean(a == b):.2f}  "
          f"kappa={kappa:.3f}  95% CI=[{low:.3f}, {high:.3f}]")
    print(pd.crosstab(pd.Series(a, name="LLM"), pd.Series(b, name="human")).to_string(), "\n")
