# Scrapers
from scrapers.base.GauntletScraper import GauntletScraper
from scrapers.base.Four01Scraper import Four01Scraper
from scrapers.base.FusionScraper import FusionScraper
from scrapers.base.KanatacgScraper import KanatacgScraper
from scrapers.base.HouseOfCardsScraper import HouseOfCardsScraper
from scrapers.base.EverythingGamesScraper import EverythingGamesScraper
from scrapers.base.MagicStrongholdScraper import MagicStrongholdScraper
from scrapers.base.FaceToFaceScraper import FaceToFaceScraper
from scrapers.base.ConnectionGamesScraper import ConnectionGamesScraper
from scrapers.base.SequenceScraper import SequenceScraper
from scrapers.base.TopDeckHeroScraper import TopDeckHeroScraper
from scrapers.base.Jeux3DragonsScraper import Jeux3DragonsScraper
from scrapers.base.AtlasScraper import AtlasScraper
from scrapers.base.GamezillaScraper import GamezillaScraper
from scrapers.base.HairyTScraper import HairyTScraper
from scrapers.base.ExorGamesScraper import ExorGamesScraper
from scrapers.base.GameKnightScraper import GameKnightScraper
from scrapers.base.EnterTheBattlefieldScraper import EnterTheBattlefieldScraper
from scrapers.base.ManaforceScraper import ManaforceScraper
from scrapers.base.FirstPlayerScraper import FirstPlayerScraper
from scrapers.base.OrchardCityScraper import OrchardCityScraper
from scrapers.base.BorderCityScraper import BorderCityScraper
from scrapers.base.AetherVaultScraper import AetherVaultScraper
from scrapers.base.FantasyForgedScraper import FantasyForgedScraper
from scrapers.base.TheComicHunterScraper import TheComicHunterScraper
from scrapers.sealed.GauntletSealedScraper import GauntletSealedScraper
from scrapers.sealed.Four01SealedScraper import Four01SealedScraper
from scrapers.sealed.FusionSealedScraper import FusionSealedScraper
from scrapers.sealed.HouseOfCardsSealedScraper import HouseOfCardsSealedScraper
from scrapers.sealed.MagicStrongholdSealedScraper import MagicStrongholdSealedScraper
from scrapers.sealed.ConnectionGamesSealedScraper import ConnectionGamesSealedScraper
from scrapers.sealed.Jeux3DragonsSealedScraper import Jeux3DragonsSealedScraper

import json
import concurrent.futures
from pydantic import BaseModel
from db.models import Search
from db.database import engine, SQLModel, Session
from datetime import datetime
import psycopg2
import os
from fastapi import BackgroundTasks, APIRouter
import redis
import re 
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

rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)

def fetchScrapers(cardName):
    # Arrange scrapers
    houseOfCardsScraper = HouseOfCardsScraper(cardName)
    gauntletScraper = GauntletScraper(cardName)
    kanatacgScraper = KanatacgScraper(cardName)
    fusionScraper = FusionScraper(cardName)
    four01Scraper = Four01Scraper(cardName)
    everythingGamesScraper = EverythingGamesScraper(cardName)
    magicStrongholdScraper = MagicStrongholdScraper(cardName)
    faceToFaceScraper = FaceToFaceScraper(cardName)
    connectionGamesScraper = ConnectionGamesScraper(cardName)
    topDeckHeroScraper = TopDeckHeroScraper(cardName)
    jeux3DragonsScraper = Jeux3DragonsScraper(cardName)
    sequenceScraper = SequenceScraper(cardName)
    atlasScraper = AtlasScraper(cardName)
    hairyTScraper = HairyTScraper(cardName)
    gamezillaScraper = GamezillaScraper(cardName)
    exorGamesScraper = ExorGamesScraper(cardName)
    gameKnightScraper = GameKnightScraper(cardName)
    enterTheBattlefieldScraper = EnterTheBattlefieldScraper(cardName)
    manaforceScraper = ManaforceScraper(cardName)
    firstPlayerScraper = FirstPlayerScraper(cardName)
    orchardCityScraper = OrchardCityScraper(cardName)
    borderCityScraper = BorderCityScraper(cardName)
    aetherVaultScraper = AetherVaultScraper(cardName)
    fantasyForgedScraper = FantasyForgedScraper(cardName)
    theComicHunterScraper = TheComicHunterScraper(cardName)

    # Map scrapers to an identifier keyword
    return {
        "houseofcards": houseOfCardsScraper,
        "gauntlet": gauntletScraper,
        "kanatacg": kanatacgScraper,
        "fusion": fusionScraper,
        "four01": four01Scraper,
        "everythinggames": everythingGamesScraper,
        "magicstronghold": magicStrongholdScraper,
        "facetoface": faceToFaceScraper,
        "connectiongames": connectionGamesScraper,
        "topdeckhero": topDeckHeroScraper,
        "jeux3dragons": jeux3DragonsScraper,
        'sequencegaming': sequenceScraper,
        'atlas': atlasScraper,
        'hairyt': hairyTScraper,
        'gamezilla': gamezillaScraper,
        'exorgames': exorGamesScraper,
        'gameknight': gameKnightScraper,
        'enterthebattlefield': enterTheBattlefieldScraper,
        'firstplayer': firstPlayerScraper,
        'manaforce': manaforceScraper,
        'orchardcity': orchardCityScraper,
        'bordercity': borderCityScraper,
        'aethervault': aetherVaultScraper,
        'fantasyforged': fantasyForgedScraper,
        'thecomichunter': theComicHunterScraper
    }

# Background tasks


def post_search(query, websites, query_type, results, num_results):
    # Connect to the database
    conn = psycopg2.connect(
        dbname=os.environ['PG_DB'],
        user=os.environ['PG_USER'],
        password=os.environ['PG_PASSWORD'],
        host=os.environ['PG_HOST'],
        port=os.environ['PG_PORT']
    )
    cur = conn.cursor()

    # We want to add this search to the search table
    # If the table doesn't exist, create it
    #  We also need to protect against SQL injection for the query field

    cur.execute("CREATE TABLE IF NOT EXISTS search (id SERIAL PRIMARY KEY, query VARCHAR, websites VARCHAR(512), query_type VARCHAR(60), results VARCHAR(255), num_results INT, timestamp TIMESTAMP);")
    cur.execute(
        """
    INSERT INTO 
        search (query, websites, query_type, results, num_results, timestamp) 
    VALUES (%(query)s, %(websites)s, %(query_type)s, %(results)s, %(num_results)s, %(timestamp)s);
    """,
        {
            "query": query,
            "websites": ','.join(websites),
            "query_type": query_type,
            "results": results,
            "num_results": num_results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

    conn.commit()
    cur.close()
    conn.close()


def post_price_entry(results):
    if len(results) == 0:
        return
    try:
        card_name = results[0]['name']
        price_list = [str(result['price']) for result in results]
        # convert to a comma separated string
        price_list = ','.join(price_list)

        # Connect to the database
        conn = psycopg2.connect(
            dbname=os.environ['PG_DB'],
            user=os.environ['PG_USER'],
            password=os.environ['PG_PASSWORD'],
            host=os.environ['PG_HOST'],
            port=os.environ['PG_PORT']
        )
        cur = conn.cursor()

        # Get the oracle id for the card
        cur.execute("SELECT oracle_id FROM cards WHERE name = %(card_name)s", {
                    "card_name": card_name})
        date = datetime.now().strftime("%Y-%m-%d")
        oracle_id = cur.fetchone()

        # We want to add this search to the search table
        # If the table doesn't exist, create it. id is the primary key, and (oracle_id, date) is a unique constraint
        # cur.execute(
        #     """
        # CREATE TABLE IF NOT EXISTS price_entry (
        #     id SERIAL PRIMARY KEY,
        #     oracle_id VARCHAR(255),
        #     price_list TEXT,
        #     date DATE,
        #     UNIQUE (oracle_id, date)
        # );
        # """
        # )

        # on conflict, just increase frequency by 1
        cur.execute(
            """
        INSERT INTO
            price_entry (oracle_id, price_list, date)
        VALUES (%(oracle_id)s, %(price_list)s, %(date)s)
        ON CONFLICT (oracle_id, date) DO UPDATE SET frequency = price_entry.frequency + 1;
        """,
            {
                "oracle_id": oracle_id,
                "price_list": price_list,
                "date": date,
                "frequency": 1
            }
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)
        

def increment_frequency(card_name):
    # connect to database find card from cards with card_name (compare lowercased)
    # find price_entry with oracle_id and todays date
    # increment frequency by 1
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=os.environ['PG_DB'],
            user=os.environ['PG_USER'],
            password=os.environ['PG_PASSWORD'],
            host=os.environ['PG_HOST'],
            port=os.environ['PG_PORT']
        )
        cur = conn.cursor()

        # Get the oracle id for the card
        cur.execute("SELECT oracle_id FROM cards WHERE lower(name) = %(card_name)s", {
                    "card_name": card_name})
        date = datetime.now().strftime("%Y-%m-%d")
        oracle_id = cur.fetchone()

        # We want to add this search to the search table
        # If the table doesn't exist, create it. id is the primary key, and (oracle_id, date) is a unique constraint
        # cur.execute(
        #     """
        # CREATE TABLE IF NOT EXISTS price_entry (
        #     id SERIAL PRIMARY KEY,
        #     oracle_id VARCHAR(255),
        #     price_list TEXT,
        #     date DATE,
        #     UNIQUE (oracle_id, date)
        # );
        # """
        # )

        # on conflict, just increase frequency by 1
        cur.execute(
            """
        UPDATE price_entry
        SET frequency = frequency + 1
        WHERE oracle_id = %(oracle_id)s AND date = %(date)s;
        """,
            {
                "oracle_id": oracle_id,
                "date": date
            }
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(e)
        


router = APIRouter()

 
@router.post("/single/")
async def search_single(request: SingleCardSearch, background_tasks: BackgroundTasks):
    """
    Search for a single card and return all prices across the provided websites
    """
    # Scraper function
    def transform(scraper):
        scraper.scrape()
        scraperResults = scraper.getResults()
        for result in scraperResults:
            results.append(result)
        return

    # List to store results from all threads
    results = []
    # request.cardName lowercased
    cache = rd.get(request.cardName.lower())
    if cache:
        background_tasks.add_task(increment_frequency, request.cardName.lower())
        return json.loads(cache)
    else :
        scraperMap = fetchScrapers(request.cardName)
        # Filter out scrapers that are not requested in request.websites
        try:
            if "all" in request.websites:
                scrapers = scraperMap.values()
            else:
                scrapers = [scraperMap[website] for website in request.websites]
        except KeyError:
            return {"error": "Invalid website provided"}

        # Run scrapers in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            threadResults = executor.map(transform, scrapers)

        # Create a new search object and post it to the database
        numResults = len(results)
        log = Search(query=request.cardName, websites=','.join(request.websites), query_type="single",
                    results="", num_results=numResults, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        SQLModel.metadata.create_all(engine)
        session = Session(engine)
        session.add(log)
        session.commit()
        session.close()
        background_tasks.add_task(post_price_entry, results)
        rd.set(request.cardName.lower(), json.dumps(results))
        rd.expire(request.cardName.lower(), 120)
        return results


@router.post("/bulk/")
async def search_bulk(request: BulkCardSearch):
    """
    Search for a list of cards and return all prices across the provided websites
    """
    # CardObject = {
    #    "cardName": "cardName",
    #   "variants": []
    # }

    # For each card in the list, we want to run the single card search
    # then we want to return an array of cardObjects
    cardNames = request.cardNames
    websites = request.websites
    worstCondition = request.worstCondition

    # List to store results from all threads
    totalResults = []
    results = {}

    # Clean card names
    # Remove any numbers at the start of the card name
    # Remove any text in brackets, and the brackets themselves
    cardNames = [re.sub(r"^\d+\s*", "", cardName).strip() for cardName in cardNames]
    cardNames = [re.sub(r"\s*\([^)]*\)", "", cardName).strip() for cardName in cardNames]
    # remove any numbers from the end of the card name
    cardNames = [re.sub(r"\s*\d+$", "", cardName).strip() for cardName in cardNames]
    # convert to lowercase
    cardNames = [cardName.lower() for cardName in cardNames]
    # remove duplicates
    cardNames = list(set(cardNames))
    


    # Scraper function
    def transform(scraper):
        scraper.scrape()
        scraperResults = scraper.getResults()
        for result in scraperResults:
            # print(result)
            # remove any punctuation from the result['name'] and lowercase it,
            tempResultName = re.sub(r"[^\w\s]", "", result['name']).lower()
            # then if it is in the results dict, append the result to the list
            # if result['name'].lower() in results:
            #     results[result['name'].lower()].append(result)
            # else:
            #     results[result['name'].lower()] = [result]
            if tempResultName in results:
                results[tempResultName].append(result)
            else:
                results[tempResultName] = [result]
        return

    def executeScrapers(cardName):
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            threadResults = executor.map(transform, scrapers)

        # Create a CardObject for the card
        cardObject = {
            "cardName": cardName.lower(),
            "variants": results[re.sub(r"[^\w\s]", "", cardName).lower()]
        }
        totalResults.append(cardObject)
        return

    # Run the scrapers for each card in cardNames, then create a CardObject for it
    # and add it to the results array
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        threadResults = executor.map(executeScrapers, cardNames)

    # post a log to the database
    # numResults = the length of the variant array in all card objects
    numResults = 0
    for card in totalResults:
        numResults += len(card['variants'])

    log = Search(query=','.join(request.cardNames), websites=','.join(request.websites), query_type="multi",
                 results="", num_results=numResults, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(log)
    session.commit()
    session.close()

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
    connectionGamesScraper = ConnectionGamesSealedScraper(setName)
    four01Scraper = Four01SealedScraper(setName)
    fustionScraper = FusionSealedScraper(setName)
    gauntletScraper = GauntletSealedScraper(setName)
    houseOfCardsScraper = HouseOfCardsSealedScraper(setName)
    jeux3DragonsScraper = Jeux3DragonsSealedScraper(setName)
    magicStrongholdScraper = MagicStrongholdSealedScraper(setName)

    # Map scrapers to an identifier keyword
    scraperMap = {
        "connectiongames": connectionGamesScraper,
        "four01": four01Scraper,
        "fusion": fustionScraper,
        "gauntlet": gauntletScraper,
        "houseofcards": houseOfCardsScraper,
        "magicstronghold": magicStrongholdScraper,
        "jeux3dragons": jeux3DragonsScraper,
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

    background_tasks.add_task(post_search, query=setName, websites=websites,
                              query_type="sealed", results="", num_results=len(results))

    return results
