# ---- Analytics Queries (Behavioral Signals) ----


# ---- USER ACTIVITY FREQUENCY ----
GET_USER_ACTIVITY = """
SELECT
    user_id,
    COUNT(*) AS total_events,
    MAX(created_at) AS last_event
FROM memory_transactions
WHERE user_id = $1
GROUP BY user_id;
"""


# ---- DOMAIN DISTRIBUTION ----
GET_DOMAIN_DISTRIBUTION = """
SELECT
    domain,
    COUNT(*) AS count
FROM memory_transactions
WHERE user_id = $1
GROUP BY domain;
"""


# ---- TAG SIGNALS ----
GET_TAG_SIGNALS = """
SELECT
    tag,
    COUNT(*) AS frequency,
    AVG(confidence) AS avg_confidence
FROM user_tags
WHERE user_id = $1
GROUP BY tag;
"""


# ---- CONVERSATION INTENSITY ----
GET_CONVERSATION_INTENSITY = """
SELECT
    COUNT(*) AS messages,
    DATE(created_at) AS day
FROM conversations
WHERE user_id = $1
GROUP BY DATE(created_at)
ORDER BY day DESC;
"""


# ---- MEMORY GROWTH RATE ----
GET_MEMORY_GROWTH = """
SELECT
    DATE(created_at) AS day,
    COUNT(*) AS writes
FROM memory_transactions
WHERE user_id = $1
GROUP BY DATE(created_at)
ORDER BY day DESC;
"""