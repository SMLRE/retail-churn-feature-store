-- =====================================================================
-- G2  Balance & product holding (8 features)
-- Loans carry negative balances, so they are excluded from deposit balance features.
-- =====================================================================
WITH b AS (
    SELECT am.customer_id, bm.month_idx, SUM(bm.eom_balance) AS bal
    FROM balance_monthly bm JOIN account_master am USING (account_id)
    WHERE bm.month_idx BETWEEN {s} - 12 AND {s} - 1 AND am.product_type <> 'LOAN'
    GROUP BY am.customer_id, bm.month_idx
),
prod AS (
    SELECT customer_id,
           COUNT(DISTINCT account_id)                                  AS n_accounts,
           COUNT(DISTINCT product_type)                                AS n_types,
           MAX(CASE WHEN product_type = 'CARD' THEN 1 ELSE 0 END)      AS has_card,
           MAX(CASE WHEN product_type = 'LOAN' THEN 1 ELSE 0 END)      AS has_loan
    FROM account_master WHERE open_month_idx < {s} GROUP BY customer_id
)
SELECT p.customer_id,
       LN(1 + GREATEST(AVG(b.bal), 0))                                                      AS g2_avg_balance_12m_log,
       REGR_SLOPE(SIGN(b.bal) * LN(1 + ABS(b.bal)), b.month_idx)                            AS g2_balance_trend,
       (AVG(CASE WHEN b.month_idx >= {s} - 3 THEN b.bal END) + 1) / (AVG(b.bal) + 1)        AS g2_balance_3m_vs_12m,
       (MIN(b.bal) + 1) / (AVG(b.bal) + 1)                                                  AS g2_min_balance_ratio,
       ANY_VALUE(pr.n_accounts)                                                              AS g2_n_accounts,
       ANY_VALUE(pr.n_types)                                                                 AS g2_n_product_types,
       ANY_VALUE(pr.has_card)                                                                AS g2_has_card,
       ANY_VALUE(pr.has_loan)                                                                AS g2_has_loan
FROM population p
LEFT JOIN b USING (customer_id)
LEFT JOIN prod pr USING (customer_id)
GROUP BY p.customer_id
