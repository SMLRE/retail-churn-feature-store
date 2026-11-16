"""
Synthetic retail-banking source system for the churn feature store.

Six source tables, joined (as in a real core-banking warehouse) through the
account master:

    customer_master     demographics, segment, onboarding, KYC
    account_master      accounts -> customer, product type      <- the join hub
    txn_monthly         per account x month: counts, inflow/outflow, salary credit,
                        counterparties, transfers to own accounts at other banks
    balance_monthly     per account x month: end-of-month balance
    channel_monthly     per customer x month x channel: attempts, successes
    geo_monthly         per customer x month x state: branch / ATM / POS usage

Churners fade before going dormant: salary credits stop, money is moved to
own accounts elsewhere, balances drain, digital failures rise, and activity
shifts away from the home state. Healthy customers have seasonal noise and
temporary dips, so no single signal is enough.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

N_MONTHS, SNAPSHOT = 30, 18
STATES = ["LAGOS", "ABUJA_FCT", "RIVERS", "OYO", "KANO", "ENUGU", "DELTA", "KADUNA", "OGUN", "ANAMBRA"]
CHANNELS = ["MOBILE", "INTERNET", "USSD", "CARD"]
PRODUCTS = ["SAVINGS", "CURRENT", "DOMICILIARY", "CARD", "LOAN"]


def generate(n: int = 15000, seed: int = 8):
    rng = np.random.default_rng(seed)
    cid = np.array([f"R{3_000_000 + i}" for i in range(n)])
    months = np.arange(N_MONTHS)
    M = months[None, :]

    # ---------------- customer master ----------------
    age0 = rng.integers(19, 70, n)
    onboard = np.where(rng.random(n) < 0.15, rng.integers(SNAPSHOT - 12, SNAPSHOT - 2, n), rng.integers(-120, SNAPSHOT - 12, n))
    open_state = rng.choice(STATES, n, p=[.28, .12, .08, .08, .08, .07, .07, .07, .08, .07])
    affluent = rng.random(n) < 0.12
    salary_earner = rng.random(n) < 0.45
    kyc_month = onboard + rng.integers(0, 60, n)
    kyc_month = np.minimum(kyc_month, SNAPSHOT - 1)

    # ---------------- churn process ----------------
    risk = (rng.normal(0, 1, n) - 0.4 * affluent - 0.3 * salary_earner + 0.4 * (SNAPSHOT - onboard < 12)
            + 0.25 * (age0 < 28))
    hazard = 0.018 * np.exp(0.9 * risk)
    churn_m = rng.geometric(np.clip(hazard, 1e-4, 0.8)) + 4
    churn_m = np.where(churn_m < N_MONTHS, churn_m, 10_000)
    fade_len = np.where(rng.random(n) < 0.55, 1, rng.integers(2, 7, n))  # most churners leave abruptly
    fade = np.clip((churn_m[:, None] - M) / fade_len[:, None], 0, 1)
    act = np.where(M >= churn_m[:, None], 0.0, np.where(M >= (churn_m - fade_len)[:, None], 0.5 + 0.5 * fade, 1.0))
    dip = (rng.random(n) < 0.35)[:, None] & (np.abs(M - rng.integers(6, N_MONTHS, n)[:, None]) <= 1)
    act = np.where(dip, act * 0.35, act)
    alive = M >= onboard[:, None]
    act = act * alive
    fading = (act < 0.999) & (act > 0) & ~dip

    cust = pd.DataFrame({"customer_id": cid, "birth_year": 2025 - age0, "onboard_month_idx": onboard,
                         "open_state": open_state, "segment": np.where(affluent, "AFFLUENT", "MASS"),
                         "kyc_update_month_idx": kyc_month})

    # ---------------- account master ----------------
    acc_rows = []
    for i in range(n):
        prods = ["SAVINGS" if rng.random() < 0.8 else "CURRENT"]
        for p, pr in [("CURRENT", .25 + .3 * affluent[i]), ("DOMICILIARY", .05 + .25 * affluent[i]), ("CARD", .45), ("LOAN", .08 + .1 * salary_earner[i])]:
            if p not in prods and rng.random() < pr:
                prods.append(p)
        for j, p in enumerate(prods):
            acc_rows.append((f"A{i:07d}{j}", cid[i], p, int(onboard[i] + (0 if j == 0 else rng.integers(0, 24)))))
    acc = pd.DataFrame(acc_rows, columns=["account_id", "customer_id", "product_type", "open_month_idx"])
    cidx = pd.Series(np.arange(n), index=cid)
    ai = cidx[acc.customer_id].to_numpy()
    txn_acc = acc.product_type.isin(["SAVINGS", "CURRENT", "DOMICILIARY"]).to_numpy()

    # ---------------- txn_monthly (transactional accounts) ----------------
    A = ai[txn_acc]
    a_act = act[A]
    lam = rng.gamma(2.5, 5, len(A)) * (1 + affluent[A])
    season = 1 + 0.15 * np.isin(M % 12, [11, 0])
    cnt = rng.poisson(lam[:, None] * a_act * season)
    ticket = rng.lognormal(10.5, 0.8, len(A)) * (1 + 2 * affluent[A])
    inflow = cnt * ticket[:, None] * rng.lognormal(0, .3, cnt.shape)
    drain = np.where(fading[A], 1.12, 1.0)
    outflow = inflow * rng.normal(0.97, 0.04, cnt.shape) * drain
    is_primary = ~pd.Series(A).duplicated().to_numpy()
    salary_stop = churn_m[A] - np.where(rng.random(len(A)) < 0.4, fade_len[A] + 1, 0)
    salary = (salary_earner[A] & is_primary)[:, None] & (M < salary_stop[:, None]) & alive[A] & (rng.random(cnt.shape) < 0.95)
    cps = rng.poisson(np.clip(cnt * 0.4, 0, None)) + (cnt > 0)
    self_out = outflow * np.where(fading[A], rng.uniform(0.05, 0.35, cnt.shape), rng.uniform(0, 0.12, cnt.shape))
    acc_txn = acc[txn_acc].account_id.to_numpy()
    txn = pd.DataFrame({"account_id": np.repeat(acc_txn, N_MONTHS), "month_idx": np.tile(months, len(A)),
                        "txn_cnt": cnt.ravel(), "inflow_amt": inflow.ravel().round(2), "outflow_amt": outflow.ravel().round(2),
                        "salary_credit": salary.ravel().astype(int), "distinct_counterparties": cps.ravel(),
                        "self_transfer_out_amt": self_out.ravel().round(2)})
    txn = txn[np.repeat(alive[A], 1, axis=0).ravel()]

    # ---------------- balance_monthly (all accounts) ----------------
    base = rng.lognormal(11, 1.2, len(acc)) * (1 + 3 * affluent[ai])
    bal_path = np.exp(rng.normal(0, 0.1, (len(acc), N_MONTHS))) * np.where(fading[ai], 0.8, 1.0) ** np.clip(
        M - (churn_m[ai] - fade_len[ai])[:, None], 0, 6)
    bal = base[:, None] * bal_path * np.where(act[ai] == 0, 0.05, 1)
    bal = np.where(acc.product_type.to_numpy()[:, None] == "LOAN", -base[:, None] * 0.8, bal)
    balance = pd.DataFrame({"account_id": np.repeat(acc.account_id.to_numpy(), N_MONTHS), "month_idx": np.tile(months, len(acc)),
                            "eom_balance": bal.ravel().round(2)})
    balance = balance[alive[ai].ravel()]

    # ---------------- channel_monthly ----------------
    digital = rng.random(n) < 0.7
    p_succ = 1 / (1 + np.exp(-(2.6 - 0.6 * risk)))
    ch_rows = []
    for k, ch in enumerate(CHANNELS):
        att = rng.poisson(rng.gamma(2, 3, n)[:, None] * act * digital[:, None] * [1.0, .4, .5, .7][k])
        p = np.clip(p_succ[:, None] - 0.06 * fading, 0.05, 0.99)
        suc = rng.binomial(att, p)
        d = pd.DataFrame({"customer_id": np.repeat(cid, N_MONTHS), "month_idx": np.tile(months, n), "channel": ch,
                          "attempts": att.ravel(), "successes": suc.ravel()})
        ch_rows.append(d[d.attempts > 0])
    channel = pd.concat(ch_rows, ignore_index=True)

    # ---------------- geo_monthly ----------------
    moved = rng.random(n) < 0.6
    live_state = np.where(moved, np.where(rng.random(n) < 0.6, "LAGOS", rng.choice(STATES, n)), open_state)
    geo_rows = []
    for state_arr, share in [(live_state, 0.85), (rng.choice(STATES, n), 0.15)]:
        st_share = np.where(fading, 0.6 if share > 0.5 else 0.4, share)
        bv = rng.poisson(1.2 * act * st_share)
        atm = rng.poisson(3.0 * act * st_share)
        pos = rng.poisson(4.0 * act * st_share)
        d = pd.DataFrame({"customer_id": np.repeat(cid, N_MONTHS), "month_idx": np.tile(months, n),
                          "state": np.repeat(state_arr, N_MONTHS), "branch_visits": bv.ravel(),
                          "atm_txns": atm.ravel(), "pos_txns": pos.ravel()})
        geo_rows.append(d[(d.branch_visits + d.atm_txns + d.pos_txns) > 0])
    geo = pd.concat(geo_rows).groupby(["customer_id", "month_idx", "state"], as_index=False).sum()

    return dict(customer_master=cust, account_master=acc, txn_monthly=txn, balance_monthly=balance,
                channel_monthly=channel, geo_monthly=geo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--customers", type=int, default=15000)
    ap.add_argument("--seed", type=int, default=8)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "raw")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for name, df in generate(a.customers, a.seed).items():
        df.to_parquet(a.out / f"{name}.parquet", index=False)
        print(f"{name:16s} {len(df):>10,} rows")


if __name__ == "__main__":
    main()
