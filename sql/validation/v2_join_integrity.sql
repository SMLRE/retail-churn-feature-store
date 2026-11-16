-- =====================================================================
-- V2  Join integrity through the account master
--     Orphan rows silently disappear in inner joins, so count them.
-- =====================================================================
SELECT 'txn rows without account'      AS check_name, COUNT(*) AS failures
FROM txn_monthly t LEFT JOIN account_master a USING (account_id) WHERE a.account_id IS NULL
UNION ALL
SELECT 'balance rows without account', COUNT(*)
FROM balance_monthly b LEFT JOIN account_master a USING (account_id) WHERE a.account_id IS NULL
UNION ALL
SELECT 'accounts without customer', COUNT(*)
FROM account_master a LEFT JOIN customer_master c USING (customer_id) WHERE c.customer_id IS NULL
UNION ALL
SELECT 'channel rows for unknown customer', COUNT(*)
FROM channel_monthly ch LEFT JOIN customer_master c USING (customer_id) WHERE c.customer_id IS NULL
