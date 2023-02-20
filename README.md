# snapcaster API
This Python application uses FastAPI and BeautifulSoup to scrape multiple trading card websites for Magic the Gathering card prices in Canada.

## Getting Started
### Prerequisites
- Python 3.7+

### Installation
1. Clone the repository
2. Install the dependencies by running `pip install -r requirements.txt`
3. Create a .env file and fill in the necessary environment variables (e.g. database URL, Redis info)
4. Start the app by running `uvicorn main:app --reload`

### Usage
The application provides three main API endpoints:

1. `POST /search/single/` to search a specified list of websites for a given card name.

2. `POST /search/bulk/` to search a specified list of websites for a list card names.

3. `POST /search/sealed/` to search a specified list of websites for given MTG set name.

## Updating Card Sets
The application comes with a script to update the available card sets. To update the card sets:
1. Download SetList.json from MtgJson and place it in scripts/.
2. Run python updateSets.py 

## File Structure
```
db/
    - database.py
    - models.py
routes/
    - pricedata.py
    - search.py
    - utils.py
scrapers/
    - base/
        - AtlasScraper.py
        - BorderCityScraper.py
        - ConnectionGamesScraper.py
        - Scraper.py
    - sealed/
        - AtlasSealedScraper.py
        - BorderCitySealedScraper.py
        - ConnectionGamesSealedScraper.py
        - SealedScraper.py
scripts/
    - updateSets.py
main.py
.env
requirements.txt
```

- db/: Contains the database related files.

- routes/: Contains the main FastAPI routes that serve the API endpoints.

- scrapers/: Contains the scrapers used to scrape the card prices from the various websites. The scrapers are organized by whether they scrape for singles or sealed products.

- scripts/: Contains scripts for updating the available card sets in the database.

- main.py: The main entry point for the application.


## Database schema
The database is primarily used to log search history for the application for debugging, and is only essential for sealed searches. 

Used for storing prices of sealed products for certain stores
`sealed_prices(id,name,link,image,price,stock,website,language,tags,updated_at)`

Logging searches for analytics
`search(id,query,websites,query_type,results,num_results,timestamp)`

All non-promo or non specialty sets in mtg.
`set(id, name, base_set_size, total_set_size, code, release_date, type)`


## Environment Variables
PG_DB=
PG_HOST=
PG_PASSWORD=
PG_PORT=
PG_USER=
RD_HOST=
RD_PASSWORD=
RD_PORT=



## adding sets to database


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