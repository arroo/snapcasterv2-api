# snapcaster API
This Python application uses FastAPI and BeautifulSoup to scrape multiple trading card websites for Magic the Gathering card prices in Canada.

## Getting Started
### Prerequisites
- Python 3.7+

### Installation
1. Clone the repository
2. Install the dependencies by running `pip install -r requirements.txt`
3. Create a .env file and fill in the necessary environment variables (e.g. database URL, Redis info, proxy IPs)
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

## Shopify Inventory
Sites using binderPOS or Shopify are scraped by fetching and parsing the products.json file.
The entire MTG singles inventory for each store is stored in it's own mongoDB collection.
The `scripts/shopifyScraper.py` runs on a schedule to keep the mongoDB instance up to date.
The `/search/` endpoint queries mongodb for the shopify stores, and scrapes the rest in real time.

## Database schema
The database is primarily used to log search history for the application for debugging, and is only essential for sealed searches. 

DB requires pg_trgm extension for searching/matching text `similarity()` func.
`CREATE EXTENSION IF NOT EXISTS pg_trgm;`

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
PROXIES=