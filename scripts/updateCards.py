# create a price entry table, each price entry has an id, oracle_id, price_list and timestamp
# we want oracle_id and date to be unique, so we can't have two entries with the same oracle_id and date
query = """
CREATE TABLE IF NOT EXISTS price_entry (
    id SERIAL PRIMARY KEY ,
    oracle_id TEXT NOT NULL,
    price_list TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    UNIQUE(oracle_id, timestamp)
);
"""