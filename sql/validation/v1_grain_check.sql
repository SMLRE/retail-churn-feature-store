-- =====================================================================
-- V1  Grain check: every feature group must return exactly one row per
--     customer in the population. Pseudo-replicated rows (one row per
--     ACCOUNT instead of per CUSTOMER) are the most common silent bug in
--     feature pipelines; they inflate counts and leak duplicates into
--     training. Expect: rows = customers = population for every group.
-- =====================================================================
SELECT 'population' AS table_name, COUNT(*) AS rows, COUNT(DISTINCT customer_id) AS customers FROM population
UNION ALL SELECT 'g1_transactional',        COUNT(*), COUNT(DISTINCT customer_id) FROM g1_transactional
UNION ALL SELECT 'g2_balance_product',      COUNT(*), COUNT(DISTINCT customer_id) FROM g2_balance_product
UNION ALL SELECT 'g3_channel_sentiment',    COUNT(*), COUNT(DISTINCT customer_id) FROM g3_channel_sentiment
UNION ALL SELECT 'g4_geo_behavioural',      COUNT(*), COUNT(DISTINCT customer_id) FROM g4_geo_behavioural
UNION ALL SELECT 'g5_lifestage',            COUNT(*), COUNT(DISTINCT customer_id) FROM g5_lifestage
UNION ALL SELECT 'g6_network_relationship', COUNT(*), COUNT(DISTINCT customer_id) FROM g6_network_relationship
UNION ALL SELECT 'g7_risk_layer',           COUNT(*), COUNT(DISTINCT customer_id) FROM g7_risk_layer
UNION ALL SELECT 'feature_store',           COUNT(*), COUNT(DISTINCT customer_id) FROM feature_store
