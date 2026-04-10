# ---- Analytics Queries ----

# ---- Monthly Spend ----
MONTHLY_SPENDING = """
SELECT 
    DATE_TRUNC('month', created_at) AS month,
    SUM(amount) AS total_spent
FROM user_transactions
WHERE user_id = $1
  AND transaction_type = 'expense'
GROUP BY month
ORDER BY month DESC;
"""

# ---- Category Breakdown ----
CATEGORY_BREAKDOWN = """
SELECT 
    category,
    SUM(amount) AS total
FROM user_transactions
WHERE user_id = $1
  AND transaction_type = 'expense'
GROUP BY category
ORDER BY total DESC;
"""

# ---- Income vs Expense ----
INCOME_VS_EXPENSE = """
SELECT 
    transaction_type,
    SUM(amount) AS total
FROM user_transactions
WHERE user_id = $1
GROUP BY transaction_type;
"""

# ---- Average Spend ----
AVERAGE_SPEND = """
SELECT 
    AVG(amount) AS avg_spend
FROM user_transactions
WHERE user_id = $1
  AND transaction_type = 'expense';
"""