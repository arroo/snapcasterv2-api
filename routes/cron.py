import concurrent.futures
from datetime import datetime, date
import psycopg2
import os
import time
from fastapi import APIRouter
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


router = APIRouter()
@router.get("")
async def temp():
    return {"message": "Hello World"}
 
@router.get("/fetch1000/")
async def fetch_prices():
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
            'fantasyforged': fantasyForgedScraper
        }

    # Scraper function
    def transform(scraper):
        scraper.scrape()
        scraperResults = scraper.getResults()
        for result in scraperResults:
            results.append(result)
        return


    # Connect to the database
    conn = psycopg2.connect(
        dbname=os.environ['PG_DB'],
        user=os.environ['PG_USER'],
        password=os.environ['PG_PASSWORD'],
        host=os.environ['PG_HOST'],
        port=os.environ['PG_PORT']
    )

    cur = conn.cursor()

    # Fetch the cards from the database if they do not have an entry in the price_entry table in the last 30 days or today
    cur.execute("""
        SELECT name FROM cards
        WHERE oracle_id NOT IN (
            SELECT oracle_id FROM price_entry
            WHERE date = CURRENT_DATE OR date > CURRENT_DATE - INTERVAL '30 days'
        )
        LIMIT 1000;
    """)

    # List to store results from all threads
    results = []

    # convert the results to a list
    cards = cur.fetchall()
    cards = [card[0] for card in cards]
    print(cards)
    # Iterate through the cards
    for card in cards:
        # Execute the bulk scrape for the current card name
        scraperMap = fetchScrapers(card)
        scrapers = scraperMap.values()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            threadResults = executor.map(transform, scrapers)

        # Wait for all threads to finish
        for result in threadResults:
            pass

        # Fetch the oracle_id for the card (compare names in lowercase)
        cur.execute("""
            SELECT oracle_id FROM cards
            WHERE LOWER(name) = LOWER(%s);
        """, (card,))

        # Get the oracle_id
        oracle_id = cur.fetchone()[0]

        # Create a pricelist from the results
        priceList = []
        for result in results:
            priceList.append(str(result['price']))

        # turn pricelist into csv string
        priceList = ','.join(priceList)

        # todays date in the format YYYY-MM-DD
        date = datetime.today().strftime("%Y-%m-%d")

        # Insert the price entry into the database
        cur.execute("""
            INSERT INTO price_entry (oracle_id, price_list, date)
            VALUES (%s, %s, %s);
        """, (oracle_id, priceList, date))

        # Commit the changes to the database
        conn.commit()

        # wait 2 seconds before executing the next command
        time.sleep(2)

        
    cur.close()
    conn.close()