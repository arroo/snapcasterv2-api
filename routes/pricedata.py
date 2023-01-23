from pydantic import BaseModel
from db.models import Search
from db.database import engine, SQLModel, Session
from datetime import datetime
import psycopg2
import os
from fastapi import BackgroundTasks, APIRouter
import json
import redis
import concurrent.futures
# import the search_single function from search.py
from routes.search import increment_frequency, fetchScrapers, post_price_entry

router = APIRouter()
rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)# get request where query params are the card name

# Background tasks
# Scrape a single card by calling @router.post("/single/") from search.py
def scrape_single_card(cardName: str, background_tasks: BackgroundTasks):
    """
    Search for a single card and return all prices across the provided websites
    """
    websites = ["all"]
    # Scraper function
    def transform(scraper):
        scraper.scrape()
        scraperResults = scraper.getResults()
        for result in scraperResults:
            results.append(result)
        return

    # List to store results from all threads
    results = []
    # cardName lowercased
    cache = rd.get(cardName.lower())
    if cache:
        background_tasks.add_task(increment_frequency, cardName.lower())
        return json.loads(cache)
    else :
        scraperMap = fetchScrapers(cardName)
        # Filter out scrapers that are not requested in request.websites
        try:
            if "all" in websites:
                scrapers = scraperMap.values()
            else:
                scrapers = [scraperMap[website] for website in websites]
        except KeyError:
            return {"error": "Invalid website provided"}

        # Run scrapers in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            threadResults = executor.map(transform, scrapers)

        # Create a new search object and post it to the database
        numResults = len(results)
        log = Search(query=cardName, websites=','.join(websites), query_type="single",
                    results="", num_results=numResults, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        SQLModel.metadata.create_all(engine)
        session = Session(engine)
        session.add(log)
        session.commit()
        session.close()
        background_tasks.add_task(post_price_entry, results)
        rd.set(cardName.lower(), json.dumps(results))
        rd.expire(cardName.lower(), 120)
        return results



@router.get("/card/{card_name}")
async def get_card(card_name: str, background_tasks: BackgroundTasks):
    conn = psycopg2.connect(
        dbname=os.environ['PG_DB'],
        user=os.environ['PG_USER'],
        password=os.environ['PG_PASSWORD'],
        host=os.environ['PG_HOST'],
        port=os.environ['PG_PORT']
    )
    cur = conn.cursor()
    # The regexp_replace(cards.name, '[^[:alpha:]]', '', 'g') will remove all
    # non-alphabetic characters from the cards.name column before it is passed to the LOWER function
    cur.execute(
        """
        SELECT date, avg(price) as avg_price, max(price) as max_price, min(price) as min_price, cards.name as card_name, cards.image_uris->'normal' as image_uri
        FROM (
            SELECT date, unnest(array_agg(price::double precision)) as price, oracle_id
            FROM (
                SELECT date, unnest(string_to_array(price_list, ',')) as price, oracle_id
                FROM price_entry
            ) as prices
            GROUP BY date, price, oracle_id
        ) as prices
        JOIN cards ON prices.oracle_id = cards.oracle_id
        WHERE LOWER(regexp_replace(cards.name, '[^[:alpha:]]', '', 'g')) = LOWER(regexp_replace(%s, '[^[:alpha:]]', '', 'g'))
        GROUP BY date, cards.name, image_uri
        ORDER BY date;
        """,
        (card_name,),
    )
    rows = cur.fetchall()

    
    # if there is no price_entry with date = today, then scrape the card
    todaysDate = datetime.now().strftime("%Y-%m-%d")
    try:
        print("rows: " + str(rows))
        mostRecentPricelistDate = rows[len(rows) - 1][0].strftime("%Y-%m-%d")
    except IndexError:
        mostRecentPricelistDate = ""
    if len(rows) == 0 or mostRecentPricelistDate != todaysDate:
        print("scraping card: " + card_name)
        background_tasks.add_task(scrape_single_card, card_name, background_tasks)
        return {
            "card_name": card_name,
            "image_uri": "",
            "price_data": []
        }
    try:
        cardName = rows[0][4]
        imageUri = rows[0][5]
        price_data = []
        for row in rows:
            price_data.append({
                "date": row[0],
                "avg_price": row[1],
                "max_price": row[2],
                "min_price": row[3]
            })

    except:
        cur.close()
        conn.close()
        cardName = card_name
        imageUri = ""
        price_data = []
        # return {
        #     "error": "Card not found"
        # }

    # results should contain price data, and card info
    results = {
        "card_name": cardName,
        "image_uri": imageUri,
        "price_data": price_data
    }

    cur.close()
    conn.close()
    return results
