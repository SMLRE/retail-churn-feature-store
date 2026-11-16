"""
Build, validate and evaluate the retail churn feature store.

    1. Generate synthetic source tables (if missing)
    2. Build the 48-feature store for two snapshots (months 15 and 18)
    3. Validate: grain, join integrity, null / range checks, PSI drift between snapshots
    4. Write the feature dictionary
    5. Prove the features carry signal: XGBoost on the graded targets plus a
       per-group ablation (how much AUC is lost without each group)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score

from src.feature_store import (build, connect, drift_report, feature_dictionary, grain_check, join_integrity,
                               range_and_null_check)
from src.registry import FEATURES, GROUPS

ROOT = Path(__file__).parent
REPORTS, FIG = ROOT / "reports", ROOT / "reports" / "figures"
TRAIN_S, TEST_S = 15, 18
ACCENT = "#E8A54B"
plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})


def fit_auc(tr, te, cols, target):
    m = xgb.XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.85, colsample_bytree=0.8,
                          min_child_weight=5, random_state=1, n_jobs=1, eval_metric="auc")
    m.fit(tr[cols], tr[target])
    return roc_auc_score(te[target], m.predict_proba(te[cols])[:, 1]), m


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "feature_store").mkdir(parents=True, exist_ok=True)
    if not (ROOT / "data/raw/account_master.parquet").exists():
        subprocess.run([sys.executable, str(ROOT / "data/generate_synthetic.py")], check=True)

    con = connect()
    fs_tr = build(con, TRAIN_S)
    fs_te = build(con, TEST_S)
    checks = {"grain": grain_check(con), "join_integrity": join_integrity(con), "range_null": range_and_null_check(con)}
    for k, v in checks.items():
        v.to_csv(REPORTS / f"validation_{k}.csv", index=False)
        print(f"validation {k:15s}: {int(v.ok.sum())}/{len(v)} checks passed")
    drift = drift_report(fs_tr, fs_te)
    drift.to_csv(REPORTS / "validation_drift_psi.csv", index=False)
    print("drift:", drift.status.value_counts().to_dict())
    for s, fs in [(TRAIN_S, fs_tr), (TEST_S, fs_te)]:
        fs.to_parquet(ROOT / "data" / "feature_store" / f"feature_store_m{s}.parquet", index=False)
    (ROOT / "docs" / "feature_dictionary.md").write_text(feature_dictionary())

    feats = list(FEATURES)
    res = {}
    for target in ["churn_flag", "early_warning_flag"]:
        auc_all, model = fit_auc(fs_tr, fs_te, feats, target)
        abl = {}
        for g in GROUPS:
            keep = [f for f in feats if not f.startswith(g + "_")]
            abl[g] = round(auc_all - fit_auc(fs_tr, fs_te, keep, target)[0], 4)
        res[target] = {"auc_all_48": round(auc_all, 4), "auc_drop_without_group": abl,
                       "rate_train": round(float(fs_tr[target].mean()), 4), "rate_test": round(float(fs_te[target].mean()), 4)}
        print(f"{target}: AUC {auc_all:.3f} | drop without group {abl}")

    abl = pd.Series(res["churn_flag"]["auc_drop_without_group"]).rename(index=lambda g: f"{g.upper()} {GROUPS[g]}")
    abl = abl.sort_values()
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.barh(abl.index, abl.values * 100, color=ACCENT)
    ax.set_xlabel("AUC points lost when the group is removed"); ax.set_title("Which feature groups carry unique signal (churn)")
    fig.tight_layout(); fig.savefig(FIG / "group_ablation.png"); plt.close(fig)

    # flag lift: churn rate by number of rule flags (G7)
    lift = fs_te.groupby("g7_n_risk_flags").agg(customers=("churn_flag", "size"), churn_rate=("churn_flag", "mean"))
    fig, ax = plt.subplots(figsize=(6, 3.8))
    ax.bar(lift.index.astype(str), lift.churn_rate * 100, color=ACCENT)
    for i, (n, r) in enumerate(zip(lift.customers, lift.churn_rate)):
        ax.text(i, r * 100 + 0.5, f"n={n}", ha="center", fontsize=8)
    ax.set_xlabel("number of G7 risk flags raised"); ax.set_ylabel("90-day dormancy rate (%)")
    ax.set_title("Rule layer alone already ranks risk"); fig.tight_layout(); fig.savefig(FIG / "flags_lift.png"); plt.close(fig)

    metrics = {
        "n_features": len(feats), "n_groups": len(GROUPS),
        "features_per_group": {g: sum(f.startswith(g + "_") for f in feats) for g in GROUPS},
        "snapshots": [TRAIN_S, TEST_S], "customers_per_snapshot": [int(len(fs_tr)), int(len(fs_te))],
        "validation_passed": {k: f"{int(v.ok.sum())}/{len(v)}" for k, v in checks.items()},
        "drift_status_counts": drift.status.value_counts().to_dict(),
        "models": res,
        "churn_rate_by_flag_count": lift.churn_rate.round(4).to_dict(),
    }
    (REPORTS / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    return metrics


if __name__ == "__main__":
    main()
