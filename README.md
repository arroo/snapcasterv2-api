## running the live server for development


`pip install -r requirements.txt`

`uvicorn main:app --reload`

Visit localhost:8000

## db schema
Card oracles
`cards(id, name, oracle_id, scryfall_uri, image_uris::jsonb)`


Price history (max 1 per day for each oracle)
`price_entry(id, oracle_id, price_list, date, frequency) unique (date, oracle_id)`

Used for caching prices of sealed products for certain stores
`sealed_prices(id,name,link,image,price,stock,website,language,tags,updated_at)`

Logging searches for analytics
`search(id,query,websites,query_type,results,num_results,timestamp)`

All non-promo or non specialty sets in mtg
`set(id, name, base_set_size, total_set_size, code, release_date, type)`


## env variables
PG_DB=
PG_HOST=
PG_PASSWORD=
PG_PORT=
PG_USER=
RD_HOST=
RD_PASSWORD=
RD_PORT=



## adding sets to database
1. Download SetList.json from MtgJson and place it in scripts/.
2. Run python updateSets.py 

## adding cards to database

`brew install jq`
https://konbert.com/blog/import-json-into-postgres-using-copy

1. get oracle-cards.json from scryfall - strip it to only include wanted fields
2. convert to NDJSON `jq -c '.[]' your_file.json > your_new_file.json`
3. replace double quotes with single quotes, escape any chars if needed
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