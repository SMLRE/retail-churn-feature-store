"""Build the feature store for a snapshot month, then validate it."""
from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from .registry import FEATURES, GROUPS

ROOT = Path(__file__).resolve().parents[1]
RAW, SQL = ROOT / "data" / "raw", ROOT / "sql"
SOURCES = ["customer_master", "account_master", "txn_monthly", "balance_monthly", "channel_monthly", "geo_monthly"]
GROUP_FILES = ["g1_transactional", "g2_balance_product", "g3_channel_sentiment", "g4_geo_behavioural",
               "g5_lifestage", "g6_network_relationship", "g7_risk_layer"]


def connect():
    con = duckdb.connect()
    for t in SOURCES:
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{RAW / (t + '.parquet')}')")
    return con


def build(con, s: int) -> pd.DataFrame:
    q = lambda p: p.read_text().format(s=s)
    con.execute("CREATE OR REPLACE TEMP TABLE population AS " + q(SQL / "00_population.sql"))
    for g in GROUP_FILES:  # order matters: g3 and g7 build on earlier groups
        con.execute(f"CREATE OR REPLACE TEMP TABLE {g} AS " + q(SQL / "features" / f"{g}.sql"))
    con.execute("CREATE OR REPLACE TEMP TABLE targets AS " + q(SQL / "08_targets.sql"))
    joins = " ".join(f"JOIN {g} USING (customer_id)" for g in GROUP_FILES)
    con.execute(f"CREATE OR REPLACE TEMP TABLE feature_store AS SELECT * FROM population {joins} ORDER BY customer_id")
    fs = con.execute("SELECT f.*, t.* EXCLUDE (customer_id) FROM feature_store f JOIN targets t USING (customer_id) ORDER BY customer_id").df()
    fs.insert(1, "snapshot_month", s)
    return fs


# ----------------------------------------------------------------- validation
def grain_check(con) -> pd.DataFrame:
    df = con.execute((SQL / "validation" / "v1_grain_check.sql").read_text()).df()
    pop = int(df.loc[df.table_name == "population", "rows"].iloc[0])
    df["ok"] = (df.rows == df.customers) & (df.rows == pop)
    return df


def join_integrity(con) -> pd.DataFrame:
    df = con.execute((SQL / "validation" / "v2_join_integrity.sql").read_text()).df()
    df["ok"] = df.failures == 0
    return df


def range_and_null_check(con) -> pd.DataFrame:
    """Generated from the registry: one SQL query covering all 48 features."""
    parts = []
    for f, (g, _, lo, hi) in FEATURES.items():
        lo_s = "-1e300" if lo == -np.inf else lo
        hi_s = "1e300" if hi == np.inf else hi
        parts.append(f"SELECT '{f}' AS feature, '{g}' AS grp, "
                     f"AVG(CASE WHEN {f} IS NULL THEN 1.0 ELSE 0 END) AS null_rate, "
                     f"AVG(CASE WHEN {f} < {lo_s} OR {f} > {hi_s} THEN 1.0 ELSE 0 END) AS out_of_range_rate, "
                     f"MIN({f}) AS min, MAX({f}) AS max FROM feature_store")
    df = con.execute(" UNION ALL ".join(parts)).df()
    df["ok"] = (df.null_rate <= 0.05) & (df.out_of_range_rate == 0)
    return df


def psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    """Population Stability Index between two snapshots of one feature."""
    e, a = expected.dropna().to_numpy(float), actual.dropna().to_numpy(float)
    edges = np.unique(np.quantile(e, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    pe = np.histogram(e, edges)[0] / len(e) + 1e-6
    pa = np.histogram(a, edges)[0] / len(a) + 1e-6
    return float(np.sum((pa - pe) * np.log(pa / pe)))


def drift_report(fs_a: pd.DataFrame, fs_b: pd.DataFrame) -> pd.DataFrame:
    rows = [(f, FEATURES[f][0], psi(fs_a[f], fs_b[f])) for f in FEATURES]
    df = pd.DataFrame(rows, columns=["feature", "grp", "psi"])
    df["status"] = pd.cut(df.psi, [-1, 0.1, 0.25, np.inf], labels=["stable", "watch", "drift"])
    return df.sort_values("psi", ascending=False)


def feature_dictionary() -> str:
    lines = ["# Feature dictionary", "", "Generated from `src/registry.py`. 48 features in 7 groups, computed over a 12-month observation window.", ""]
    for g, title in GROUPS.items():
        feats = {k: v for k, v in FEATURES.items() if v[0] == g}
        lines += [f"## {g.upper()} · {title} ({len(feats)})", "", "| Feature | Description | Expected range |", "|---|---|---|"]
        for k, (_, desc, lo, hi) in feats.items():
            rng = f"{lo if lo != -np.inf else '−∞'} – {hi if hi != np.inf else '∞'}"
            lines.append(f"| `{k}` | {desc} | {rng} |")
        lines.append("")
    return "\n".join(lines)
