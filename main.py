from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import concurrent.futures
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import psycopg2
import os
import dotenv

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
from scrapers.sealed.GauntletSealedScraper import GauntletSealedScraper
from scrapers.sealed.Four01SealedScraper import Four01SealedScraper
from scrapers.sealed.FusionSealedScraper import FusionSealedScraper
from scrapers.sealed.HouseOfCardsSealedScraper import HouseOfCardsSealedScraper
from scrapers.sealed.MagicStrongholdSealedScraper import MagicStrongholdSealedScraper
from scrapers.sealed.ConnectionGamesSealedScraper import ConnectionGamesSealedScraper
from scrapers.sealed.Jeux3DragonsSealedScraper import Jeux3DragonsSealedScraper

from db.database import engine, SQLModel, Session
from db.models import Search


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

# load the differently named dev.env file with dotenv
dotenv.load_dotenv(dotenv_path="dev.env")

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://snapcasterv2-client.vercel.app",
    "https://snapcaster.bryceeppler.com",
    "https://www.snapcaster.ca",
    "https://snapcaster.ca",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    

# Routes
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/search/single/")
async def search_single(request: SingleCardSearch):
    """
    Search for a single card and return all prices across the provided websites
    """
    # List to store results from all threads
    results = []

    # Scraper function
    def transform(scraper):
        scraper.scrape()
        scraperResults = scraper.getResults()
        for result in scraperResults:
            results.append(result)
        return

    # Arrange scrapers
    houseOfCardsScraper = HouseOfCardsScraper(request.cardName)
    gauntletScraper = GauntletScraper(request.cardName)
    kanatacgScraper = KanatacgScraper(request.cardName)
    fusionScraper = FusionScraper(request.cardName)
    four01Scraper = Four01Scraper(request.cardName)
    everythingGamesScraper = EverythingGamesScraper(request.cardName)
    magicStrongholdScraper = MagicStrongholdScraper(request.cardName)
    faceToFaceScraper = FaceToFaceScraper(request.cardName)
    connectionGamesScraper = ConnectionGamesScraper(request.cardName)
    topDeckHeroScraper = TopDeckHeroScraper(request.cardName)
    jeux3DragonsScraper = Jeux3DragonsScraper(request.cardName)
    sequenceScraper = SequenceScraper(request.cardName)
    atlasScraper = AtlasScraper(request.cardName)
    hairyTScraper = HairyTScraper(request.cardName)
    gamezillaScraper = GamezillaScraper(request.cardName)
    exorGamesScraper = ExorGamesScraper(request.cardName)
    gameKnightScraper = GameKnightScraper(request.cardName)
    enterTheBattlefieldScraper = EnterTheBattlefieldScraper(request.cardName)
    manaforceScraper = ManaforceScraper(request.cardName)
    firstPlayerScraper = FirstPlayerScraper(request.cardName)
    orchardCityScraper = OrchardCityScraper(request.cardName)
    borderCityScraper = BorderCityScraper(request.cardName)
    aetherVaultScraper = AetherVaultScraper(request.cardName)

    # Map scrapers to an identifier keyword
    scraperMap = {
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
        'aethervault': aetherVaultScraper
    }


    # Filter out scrapers that are not requested in request.websites
    try:
        # if "all" in request.websites: then we want all scrapers
        if "all" in request.websites:
            scrapers = scraperMap.values()
        else:
            scrapers = [scraperMap[website] for website in request.websites]
    except KeyError:
        return {"error": "Invalid website provided"}
    
    # scrapers = [
    #     connectionGamesScraper      
    # ]

    # Run scrapers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        threadResults = executor.map(transform, scrapers)

    # Create a new search object
    # post a log to the database
    numResults = len(results)
    log = Search(query=request.cardName, websites=','.join(request.websites), query_type="single", results="", num_results=numResults, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(log)
    session.commit()
    session.close()

    return results
    

@app.post("/search/bulk/")
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

    # Scraper function
    def transform(scraper):
        scraper.scrape()
        scraperResults = scraper.getResults()
        for result in scraperResults:
            if result['name'].lower() in results:
                results[result['name'].lower()].append(result)
            else:
                results[result['name'].lower()] = [result]

        return

    def executeScrapers(cardName):
        # For each card 
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

        # Map scrapers to an identifier keyword
        scraperMap = {
            "houseofcards": houseOfCardsScraper,
            "gauntlet": gauntletScraper,
            "kanatacg": kanatacgScraper,
            "fusion": fusionScraper,
            "four01": four01Scraper,
            "everythinggames": everythingGamesScraper,
            "magicstronghold": magicStrongholdScraper,
            "facetoface": faceToFaceScraper,
            "connectiongames": connectionGamesScraper,
            'topdeckhero': topDeckHeroScraper,
            'jeux3dragons': jeux3DragonsScraper,
            'sequencegaming': sequenceScraper,
            'atlas': atlasScraper,
            'hairyt': hairyTScraper,
            'gamezilla': gamezillaScraper,
            'exorgames': exorGamesScraper,
            'gameknight': gameKnightScraper,
            'enterthebattlefield': enterTheBattlefieldScraper,
            'manaforce': manaforceScraper,
            'firstplayer': firstPlayerScraper,
            'orchardcity': orchardCityScraper,
            'bordercity': borderCityScraper,
            'aethervault': aetherVaultScraper
        }

        # Filter out scrapers that are not requested in request.websites
        try:
            scrapers = [scraperMap[website] for website in websites]
        except KeyError:
            return {"error": "Invalid website provided"}
        
        # Run scrapers in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            threadResults = executor.map(transform, scrapers)

        # Create a CardObject for the card
        cardObject = {
            "cardName": cardName.lower(),
            "variants": results[cardName.lower()]
        }
        totalResults.append(cardObject)
        return

    # Run the scrapers for each card in cardNames, then create a CardObject for it
    # and add it to the results array
    # for cardName in cardNames:
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        threadResults = executor.map(executeScrapers, cardNames)

    # post a log to the database
    # numResults = the length of the variant array in all card objects
    numResults = 0
    for card in totalResults:
        numResults += len(card['variants'])

    log = Search(query=','.join(request.cardNames), websites=','.join(request.websites), query_type="multi", results="", num_results=numResults, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(log)
    session.commit()
    session.close()

    return totalResults


@app.post("/search/sealed/")
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
        # "kanatacg": kanatacgScraper,
        # "fusion": fusionScraper,
        # "everythinggames": everythingGamesScraper,
        "magicstronghold": magicStrongholdScraper,
        # "facetoface": faceToFaceScraper,
        # "topdeckhero": topDeckHeroScraper,
        "jeux3dragons": jeux3DragonsScraper,
        # 'sequencegaming': sequenceScraper,
        # 'atlas': atlasScraper,
        # 'hairyt': hairyTScraper,
        # 'gamezilla': gamezillaScraper,
        # 'exorgames': exorGamesScraper,
        # 'gameknight': gameKnightScraper,
        # 'enterthebattlefield': enterTheBattlefieldScraper,
        # 'firstplayer': firstPlayerScraper,
        # 'manaforce': manaforceScraper,
        # 'orchardcity': orchardCityScraper,
        # 'bordercity': borderCityScraper,
    }


    # Filter out scrapers that are not requested in request.websites
    try:
        # if "all" in request.websites: then we want all scrapers
        if "all" in websites:
            scrapers = scraperMap.values()
        else:
            scrapers = [scraperMap[website] for website in websites]
    except KeyError:
        return {"error": "Invalid website provided"}
    
    # Run scrapers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        threadResults = executor.map(transform, scrapers)

    background_tasks.add_task(post_search, query=setName, websites=websites, query_type="sealed", results="", num_results=len(results))

    return results
    

# log search queries in database
@app.post("/log/")
async def log(request: Search):
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(request)
    session.commit()
    session.close()
    return {"message": "Logged"}

def fetch_heatmap():
        # connect to database
    conn = psycopg2.connect(
        dbname=os.environ['PG_DB'],
        user=os.environ['PG_USER'],
        password=os.environ['PG_PASSWORD'],
        host=os.environ['PG_HOST'],
        port=os.environ['PG_PORT']
    )
    cur = conn.cursor()
    
    # get all entries from the "search" table where the timestamp is within the last 367 days, aggregate the number of results for each unique day and return a list of {date: count} objects
    cur.execute("""
        SELECT date_trunc('day', timestamp) as date, count(*) as count
        FROM search
        WHERE timestamp > now() - interval '367 days'
        GROUP BY date
        ORDER BY date;
    """)

    
    # create a dictionary of {date: count} objects
    results = cur.fetchall()
    cur.close()
    conn.close()

    # create a list of objects like this and return it:
    # [
    #  {date: "2020-01-01", count: 10},
    # {date: "2020-01-02", count: 5},
    # ]
    return [{"date": result[0].strftime("%Y-%m-%d"), "count": result[1]} for result in results]


@app.get("/heatmap/")
async def heatmap():
    # fetch the heatmap data from the database
    results = fetch_heatmap()

    # return the results
    return results
    