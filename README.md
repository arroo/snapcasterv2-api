## running the live server for development

`uvicorn main:app --reload`

## adding cards to database

`brew install jq`
https://konbert.com/blog/import-json-into-postgres-using-copy

1. get oracle-cards.json from scryfall - strip it to only include wanted fields
2. convert to NDJSON `jq -c '.[]' your_file.json > your_new_file.json`
3. replace double quotes with single quotes, escape any chars
4.

```sql
CREATE TABLE temp (data jsonb);
\COPY temp (data) FROM 'ndoraclecards.json';

CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    oracle_id VARCHAR(255) NOT NULL UNIQUE,
    scryfall_uri VARCHAR(255) NOT NULL,
    image_uris JSONB NOT NULL
);

INSERT INTO cards (name, oracle_id, scryfall_uri, image_uris)
SELECT data->>'name', data->>'oracle_id', data->>'scryfall_uri', data->'image_uris'
FROM temp;

DROP TABLE temp;

```

## adding price entries
```sql
CREATE TABLE IF NOT EXISTS price_entry (
    id SERIAL PRIMARY KEY ,
    oracle_id TEXT NOT NULL,
    price_list TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    UNIQUE(oracle_id, timestamp)
);
```
