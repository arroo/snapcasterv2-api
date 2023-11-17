from scrapers.base.AetherVaultScraper import AetherVaultScraper
from scrapers.base.AtlasScraper import AtlasScraper
from scrapers.base.ConnectionGamesScraper import ConnectionGamesScraper
from scrapers.base.FaceToFaceScraper import FaceToFaceScraper
from scrapers.base.FirstPlayerScraper import FirstPlayerScraper
from scrapers.base.FusionScraper import FusionScraper
from scrapers.base.GauntletScraper import GauntletScraper
from scrapers.base.Jeux3DragonsScraper import Jeux3DragonsScraper
from scrapers.base.KanatacgScraper import KanatacgScraper
from scrapers.base.MagicStrongholdScraper import MagicStrongholdScraper
from scrapers.base.ManaforceScraper import ManaforceScraper
from scrapers.base.OrchardCityScraper import OrchardCityScraper
from scrapers.base.SequenceScraper import SequenceScraper
from scrapers.base.TheComicHunterScraper import TheComicHunterScraper
from scrapers.base.TopDeckHeroScraper import TopDeckHeroScraper

from scrapers.sealed.AtlasSealedScraper import AtlasSealedScraper
from scrapers.sealed.ComicHunterSealedScraper import ComicHunterSealedScraper
from scrapers.sealed.FaceToFaceSealedScraper import FaceToFaceSealedScraper
from scrapers.sealed.FirstPlayerSealedScraper import FirstPlayerSealedScraper
from scrapers.sealed.GauntletSealedScraper import GauntletSealedScraper
from scrapers.sealed.FusionSealedScraper import FusionSealedScraper
from scrapers.sealed.MagicStrongholdSealedScraper import MagicStrongholdSealedScraper
from scrapers.sealed.OrchardCitySealedScraper import OrchardCitySealedScraper
from scrapers.sealed.ConnectionGamesSealedScraper import ConnectionGamesSealedScraper
from scrapers.sealed.Jeux3DragonsSealedScraper import Jeux3DragonsSealedScraper
from scrapers.sealed.SequenceSealedScraper import SequenceSealedScraper
from scrapers.sealed.TopDeckHeroSealedScraper import TopDeckHeroSealedScraper


from utils.customExceptions import TooManyRequestsError
import json
import concurrent.futures
from pydantic import BaseModel
from datetime import datetime
import psycopg2
import os
from fastapi import BackgroundTasks, APIRouter
import redis
import random
import re
from pymongo import MongoClient
from requests.exceptions import ProxyError, Timeout, SSLError, RetryError
import time


# Pydantic Models
class SingleCardSearch(BaseModel):
    cardName: str
    websites: list


class BulkCardSearch(BaseModel):
    cardNames: list
    websites: list
    worstCondition: str


class SealedSearch(BaseModel):
    setName: str
    websites: list


class Card(BaseModel):
    cardName: str


class PriceEntry(BaseModel):
    oracleId: str
    priceList: str
    date: str

class SingleResult(BaseModel):
    name: str
    website: str
    image: str
    link: str
    set: str
    condition: str
    foil: bool
    price: float



def getProxiesFromFile(filename):
    with open(filename, "r") as f:
        proxies = [line.strip() for line in f]
    return proxies


rd = redis.Redis(
    host=os.environ["RD_HOST"],
    port=os.environ["RD_PORT"],
    password=os.environ["RD_PASSWORD"],
    db=0,
)

mongoClient = MongoClient(os.environ["MONGO_URI"])
db = mongoClient["snapcaster"]
shopifyInventoryDb = mongoClient["shopify-inventory"]

def searchShopifyInventory(search_term, db):
    mtgSinglesCollection = db['mtgSingles']
    # case insensitive and punctuation insensitive using full text search on index "title"
    result = list(mtgSinglesCollection.find({"$text": {"$search": search_term}}))
    # drop the _id field from the result
    for item in result:
        item.pop('_id')
        item.pop('timestamp')
    return result

def searchShopifyInventoryBulk(search_term, db, websites):
    mtgSinglesCollection = db['mtgSingles']
    if "all" in websites:
        # case insensitive and punctuation insensitive using full text search on index "title"
        result = list(mtgSinglesCollection.find({"$text": {"$search": search_term}}))
    else:
        # case insensitive and punctuation insensitive using full text search on index "title", where website is in websites
        result = list(mtgSinglesCollection.find({"$text": {"$search": search_term}, "website": {"$in": websites}}))
    # drop the _id field from the result
    for item in result:
        item.pop('_id')
        item.pop('timestamp')
    return result

def fetchScrapers(cardName):
    # Arrange scrapers
    gauntletScraper = GauntletScraper(cardName)
    kanatacgScraper = KanatacgScraper(cardName)
    fusionScraper = FusionScraper(cardName)
    magicStrongholdScraper = MagicStrongholdScraper(cardName)
    faceToFaceScraper = FaceToFaceScraper(cardName)
    connectionGamesScraper = ConnectionGamesScraper(cardName)
    topDeckHeroScraper = TopDeckHeroScraper(cardName)
    jeux3DragonsScraper = Jeux3DragonsScraper(cardName)
    sequenceScraper = SequenceScraper(cardName)
    atlasScraper = AtlasScraper(cardName)
    manaforceScraper = ManaforceScraper(cardName)
    firstPlayerScraper = FirstPlayerScraper(cardName)
    orchardCityScraper = OrchardCityScraper(cardName)
    aetherVaultScraper = AetherVaultScraper(cardName)
    theComicHunterScraper = TheComicHunterScraper(cardName)

    # Map scrapers to an identifier keyword
    return {
        "gauntlet": gauntletScraper,
        "kanatacg": kanatacgScraper,
        "fusion": fusionScraper,
        "magicstronghold": magicStrongholdScraper,
        "facetoface": faceToFaceScraper,
        "connectiongames": connectionGamesScraper,
        "topdeckhero": topDeckHeroScraper,
        "jeux3dragons": jeux3DragonsScraper,
        "sequencegaming": sequenceScraper,
        "atlas": atlasScraper,
        "firstplayer": firstPlayerScraper,
        "manaforce": manaforceScraper,
        "orchardcity": orchardCityScraper,
        "aethervault": aetherVaultScraper,
        "thecomichunter": theComicHunterScraper,
    }


# Background tasks
def post_search(query, websites, query_type, results, num_results):
    # Connect to the database
    conn = psycopg2.connect(
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ["PG_PORT"],
    )
    cur = conn.cursor()

    cur.execute(
        "CREATE TABLE IF NOT EXISTS search (id SERIAL PRIMARY KEY, query VARCHAR, websites VARCHAR(512), query_type VARCHAR(60), results VARCHAR(255), num_results INT, timestamp TIMESTAMP);"
    )
    cur.execute(
        """
    INSERT INTO 
        search (query, websites, query_type, results, num_results, timestamp) 
    VALUES (%(query)s, %(websites)s, %(query_type)s, %(results)s, %(num_results)s, %(timestamp)s);
    """,
        {
            "query": query,
            "websites": ",".join(websites),
            "query_type": query_type,
            "results": results,
            "num_results": num_results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )

    conn.commit()
    cur.close()
    conn.close()


def post_price_entry(query, price_list):
    # We need to find the card with the best match for the query, ignore punctuation,
    try:
        if len(price_list) == 0:
            return
        card_doc = db["cards"].find_one(
            {"name": {"$regex": f"^{query}$", "$options": "i"}}
        )
        if card_doc is None:
            return

        # If there is already a price entry for this card today, continue
        todays_price_entry = db["price_entry"].find_one(
            {
                "oracle_id": card_doc["oracle_id"],
                "date": {
                    "$gte": datetime.now().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                },
            }
        )
        if todays_price_entry is not None:
            return
        # if no cards with foil, then no need to check for foil
        if not any([price_entry["foil"] for price_entry in price_list]):
            price_entry = {
                "oracle_id": card_doc["oracle_id"],
                "date": datetime.now(),
                "price_list": [
                    {
                        "price": price_entry["price"],
                        "website": price_entry["website"],
                        "foil": price_entry["foil"],
                        "condition": price_entry["condition"],
                    }
                    for price_entry in price_list
                ],
                "max": round(
                    max(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                        ]
                    ),
                    2,
                ),
                "min": round(
                    min(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                        ]
                    ),
                    2,
                ),
                "avg": round(
                    sum(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                        ]
                    )
                    / len(price_list),
                    2,
                ),
            }
        else:
            # Create a price entry for this card
            price_entry = {
                "oracle_id": card_doc["oracle_id"],
                "date": datetime.now(),
                "price_list": [
                    {
                        "price": price_entry["price"],
                        "website": price_entry["website"],
                        "foil": price_entry["foil"],
                        "condition": price_entry["condition"],
                    }
                    for price_entry in price_list
                ],
                "max": round(
                    max(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                        ]
                    ),
                    2,
                ),
                "min": round(
                    min(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                        ]
                    ),
                    2,
                ),
                "avg": round(
                    sum(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                        ]
                    )
                    / len(price_list),
                    2,
                ),
                "foil_max": round(
                    max(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                            if price_entry["foil"]
                        ]
                    ),
                    2,
                ),
                "foil_min": round(
                    min(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                            if price_entry["foil"]
                        ]
                    ),
                    2,
                ),
                "foil_avg": round(
                    sum(
                        [
                            float(str(price_entry["price"]).replace(",", ""))
                            for price_entry in price_list
                            if price_entry["foil"]
                        ]
                    )
                    / len(
                        [
                            price_entry
                            for price_entry in price_list
                            if price_entry["foil"]
                        ]
                    ),
                    2,
                ),
            }

        # Send the price entry to mongodb
        # print(price_entry)
        db["price_entry"].insert_one(price_entry)
    except Exception as e:
        print("Error in post_price_entry while trying to insert price entry into mongo")
        print(e)


router = APIRouter()


@router.post("/single/")
async def search_single(request: SingleCardSearch, background_tasks: BackgroundTasks):
    """
    Search for a single card and return all prices across the provided websites
    """
    proxies = os.environ["PROXIES"].split(",")

    def transform(scraper):
        try:
            temp_proxies = proxies.copy()
            num_failed_proxies = 0
            if scraper.usesProxies:
                while temp_proxies:  # try as long as there are proxies left
                    proxy = random.choice(temp_proxies)
                    try:
                        scraper.scrape(proxy)
                        scraperResults = scraper.getResults()
                        for result in scraperResults:
                            results.append(result)
                        return
                    except (
                        ProxyError,
                        Timeout,
                        SSLError,
                        RetryError,
                        TooManyRequestsError,
                    ):
                        temp_proxies.remove(
                            proxy
                        )  # remove the failing proxy from the list
                        num_failed_proxies += 1
                        print(
                            f"{num_failed_proxies} Proxy {proxy} failed for {scraper.website}"
                        )

                if not temp_proxies:
                    print(f"*** All proxies failed for {scraper.website}")
                    return

        except Exception as e:
            print("Error in search_single while trying to scrape")
            print(e)

        else:
            scraper.scrape()
            scraperResults = scraper.getResults()
            for result in scraperResults:
                results.append(result)
            return

    results = []  # List to store results from all threads
    cache = rd.get(request.cardName.lower())
    if cache:
        return json.loads(cache)
    else:
        scraperMap = fetchScrapers(request.cardName)
        try:
            if "all" in request.websites:
                scrapers = scraperMap.values()
            else:
                scrapers = [scraperMap[website] for website in request.websites]
        except KeyError:
            return {"error": "Invalid website provided"}

        # Run scrapers
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            threadResults = executor.map(transform, scrapers)

        shopify_results = searchShopifyInventory(request.cardName, shopifyInventoryDb)
        results.extend(shopify_results)
        
        filteredResults = filter_card_names(request.cardName, results)
        results = filteredResults
        numResults = len(results)
        background_tasks.add_task(
            post_search, request.cardName, request.websites, "single", "", numResults
        )
        background_tasks.add_task(post_price_entry, request.cardName, results)

        # Only update the cache if websites is "all" so cache hits don't get partial results
        if "all" in request.websites:
            rd.set(request.cardName.lower(), json.dumps(results))
            rd.expire(request.cardName.lower(), 420)  # blazeit expire in 7 mins
        return results

def filter_card_names(cardName, results):
    filteredResults = []
    for result in results:
        if cardName.lower() in result["name"].lower():
            if (
                    "token" in result["name"].lower()
                    and "token" not in cardName.lower()
                    and "emblem" not in cardName.lower()
                ):
                continue
            elif (
                    "emblem" in result["name"].lower()
                    and "emblem" not in cardName.lower()
                    and "token" not in cardName.lower()
                ):
                continue
            elif (
                "art series" in result["name"].lower() or "artist series" in result["name"].lower()
            ):
                continue
            else:
                filteredResults.append(result)
        else:
            continue
    return filteredResults


@router.post("/bulk/")
async def search_bulk(request: BulkCardSearch, background_tasks: BackgroundTasks):
    """
    Search for a list of cards and return all prices across the provided websites
    """
    cardNames = request.cardNames
    cardNames = cardNames[:5]  # Max 5 cards for bulk search
    websites = request.websites

    # List to store results from all threads
    totalResults = []
    results = {}

    # Clean card names
    cardNames = [
        re.sub(r"^\d+\s*", "", cardName).strip() for cardName in cardNames
    ]  # remove prefix nums
    cardNames = [
        re.sub(r"\s*\([^)]*\)", "", cardName).strip() for cardName in cardNames
    ]  # remove brackets
    cardNames = [
        re.sub(r"\s*\d+$", "", cardName).strip() for cardName in cardNames
    ]  # remove suffix nums
    cardNames = [cardName.lower() for cardName in cardNames]  # lowercase
    cardNames = list(set(cardNames))  # remove duplicates

    proxies = os.environ["PROXIES"].split(",")

    def transform(scraper):
        if scraper.usesProxies:
            print(f"Using proxies for {scraper.website}")
            time.sleep(random.randint(1, 2))
            while proxies:
                proxy = random.choice(proxies)
                try:
                    scraper.scrape(proxy)
                    scraperResults = scraper.getResults()
                    for result in scraperResults:
                        tempResultName = re.sub(r"[^\w\s]", "", result["name"]).lower()
                        if tempResultName in results:
                            results[tempResultName].append(result)
                        else:
                            results[tempResultName] = [result]
                    return
                except (
                    ProxyError,
                    Timeout,
                    SSLError,
                    RetryError,
                    TooManyRequestsError,
                ):
                    proxies.remove(proxy)
                    print(f"Proxy {proxy} removed for {scraper.website}")
        else:
            scraper.scrape()
            scraperResults = scraper.getResults()
            for result in scraperResults:
                # remove any punctuation from the result['name'] and lowercase it,
                tempResultName = re.sub(r"[^\w\s]", "", result["name"]).lower()
                if tempResultName in results:
                    results[tempResultName].append(result)
                else:
                    results[tempResultName] = [result]
            return

    def executeScrapers(cardName):
        print(f"Searching for {cardName}")
        scraperMap = fetchScrapers(cardName)

        if "all" in websites:
            scrapers = scraperMap.values()
        else:
            scrapers = [scraperMap[website] for website in websites if website in scraperMap]

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            threadResults = executor.map(transform, scrapers)

        cardObject = {
            "cardName": cardName.lower(),
            "variants": results[re.sub(r"[^\w\s]", "", cardName).lower()],
        }

        shopify_results = searchShopifyInventoryBulk(cardName, shopifyInventoryDb, websites)
        shopify_results = filter_card_names(cardName, shopify_results)
        cardObject["variants"].extend(shopify_results)
        totalResults.append(cardObject)


        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        threadResults = executor.map(executeScrapers, cardNames)

    numResults = 0
    for card in totalResults:
        numResults += len(card["variants"])
    
    return totalResults


@router.post("/sealed/")
async def search_sealed(request: SealedSearch, background_tasks: BackgroundTasks):
    """
    Search for a set name and return all in stock sealed products for the set
    """
    setName = request.setName
    websites = request.websites
    results = []

    # Scraper function
    def transform(scraper):
        scraper.scrape()
        scraperResults = scraper.getResults()
        for result in scraperResults:
            results.append(result)
        return

    # Arrange scrapers
    atlasScraper = AtlasSealedScraper(setName)
    connectionGamesScraper = ConnectionGamesSealedScraper(setName)
    faceToFaceScraper = FaceToFaceSealedScraper(setName)
    firstPlayerScraper = FirstPlayerSealedScraper(setName)
    fusionScraper = FusionSealedScraper(setName)
    gauntletScraper = GauntletSealedScraper(setName)
    jeux3DragonsScraper = Jeux3DragonsSealedScraper(setName)
    magicStrongholdScraper = MagicStrongholdSealedScraper(setName)
    orchardCityScraper = OrchardCitySealedScraper(setName)
    comicHunterScraper = ComicHunterSealedScraper(setName)
    sequenceScraper = SequenceSealedScraper(setName)
    TopDeckHeroScraper = TopDeckHeroSealedScraper(setName)
    # Map scrapers to an identifier keyword
    scraperMap = {
        "atlas": atlasScraper,
        "connectiongames": connectionGamesScraper,
        "facetoface": faceToFaceScraper,
        "firstplayer": firstPlayerScraper,
        "fusion": fusionScraper,
        "gauntlet": gauntletScraper,
        "magicstronghold": magicStrongholdScraper,
        "orchardcity": orchardCityScraper,
        "jeux3dragons": jeux3DragonsScraper,
        "sequence": sequenceScraper,
        "thecomichunter": comicHunterScraper,
        "topdeckhero": TopDeckHeroScraper,
    }

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

    background_tasks.add_task(
        post_search,
        query=setName,
        websites=websites,
        query_type="sealed",
        results="",
        num_results=len(results),
    )

    return results

