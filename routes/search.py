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
from scrapers.base.SilverGoblinScraper import SilverGoblinScraper
from scrapers.base.BlackKnightScraper import BlackKnightScraper
from scrapers.base.HFXScraper import HFXScraper
from scrapers.base.AetherVaultScraper import AetherVaultScraper
from scrapers.base.AbyssScraper import AbyssScraper
from scrapers.base.OMGScraper import OMGScraper
from scrapers.base.KesselRunScraper import KesselRunScraper
from scrapers.base.NorthOfExileScraper import NorthOfExileScraper
from scrapers.base.RedDragonScraper import RedDragonScraper
from scrapers.base.FantasyForgedScraper import FantasyForgedScraper
from scrapers.base.TheComicHunterScraper import TheComicHunterScraper
from scrapers.base.NerdzCafeScraper import NerdzCafeScraper
from scrapers.base.ChimeraScraper import ChimeraScraper
from scrapers.base.GameBreakersScraper import GameBreakersScraper
from scrapers.base.TimeVaultScraper import TimeVaultScraper
from scrapers.base.TapsScraper import TapsScraper
from scrapers.base.EastRidgeScraper import EastRidgeScraper
from scrapers.base.CryptScraper import CryptScraper
from scrapers.base.DragonCardsScraper import DragonCardsScraper
from scrapers.base.UpNorthScraper import UpNorthScraper
from scrapers.base.MythicStoreScraper import MythicStoreScraper
from scrapers.base.VortexGamesScraper import VortexGamesScraper
from scrapers.base.WaypointScraper import WaypointScraper
from scrapers.base.SkyfoxScraper import SkyfoxScraper
from scrapers.base.OutOfTheBoxScraper import OutOfTheBoxScraper
from scrapers.base.PandorasBooxScraper import PandorasBooxScraper
from scrapers.sealed.AtlasSealedScraper import AtlasSealedScraper
from scrapers.sealed.BorderCitySealedScraper import BorderCitySealedScraper
from scrapers.sealed.ChimeraSealedScraper import ChimeraSealedScraper
from scrapers.sealed.ComicHunterSealedScraper import ComicHunterSealedScraper
from scrapers.sealed.EnterTheBattlefieldSealedScraper import EnterTheBattlefieldSealedScraper
from scrapers.sealed.EverythingGamesSealedScraper import EverythingGamesSealedScraper
from scrapers.sealed.ExorGamesSealedScraper import ExorGamesSealedScraper
from scrapers.sealed.FaceToFaceSealedScraper import FaceToFaceSealedScraper
from scrapers.sealed.FantasyForgedSealedScraper import FantasyForgedSealedScraper
from scrapers.sealed.FirstPlayerSealedScraper import FirstPlayerSealedScraper
from scrapers.sealed.GameKnightSealedScraper import GameKnightSealedScraper
from scrapers.sealed.GamezillaSealedScraper import GamezillaSealedScraper
from scrapers.sealed.GauntletSealedScraper import GauntletSealedScraper
from scrapers.sealed.Four01SealedScraper import Four01SealedScraper
from scrapers.sealed.FusionSealedScraper import FusionSealedScraper
from scrapers.sealed.HairyTSealedScraper import HairyTSealedScraper
from scrapers.sealed.HouseOfCardsSealedScraper import HouseOfCardsSealedScraper
from scrapers.sealed.MagicStrongholdSealedScraper import MagicStrongholdSealedScraper
from scrapers.sealed.OrchardCitySealedScraper import OrchardCitySealedScraper
from scrapers.sealed.ConnectionGamesSealedScraper import ConnectionGamesSealedScraper
from scrapers.sealed.Jeux3DragonsSealedScraper import Jeux3DragonsSealedScraper
from scrapers.sealed.SequenceSealedScraper import SequenceSealedScraper
from scrapers.sealed.TopDeckHeroSealedScraper import TopDeckHeroSealedScraper



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

def getProxiesFromFile(filename):
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f]
    return proxies

rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)
mongoClient = MongoClient(os.environ['MONGO_URI'])
db = mongoClient['snapcaster']
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
    chimeraScraper = ChimeraScraper(cardName)
    dragonCardsScraper = DragonCardsScraper(cardName)
    gameBreakersScraper = GameBreakersScraper(cardName)
    mythicStoreScraper = MythicStoreScraper(cardName)
    vortexGamesScraper = VortexGamesScraper(cardName)
    abyssScraper = AbyssScraper(cardName)
    cryptScraper = CryptScraper(cardName)
    silverGoblinScraper = SilverGoblinScraper(cardName)
    northOfExileScraper = NorthOfExileScraper(cardName)
    hfxScraper = HFXScraper(cardName)
    omgScraper = OMGScraper(cardName)
    kesselRunScraper = KesselRunScraper(cardName)
    redDragonScraper = RedDragonScraper(cardName)
    tapsScraper = TapsScraper(cardName)
    blackKnightScraper = BlackKnightScraper(cardName)
    outOfTheBoxScraper = OutOfTheBoxScraper(cardName)
    timeVaultScraper = TimeVaultScraper(cardName)
    eastRidgeScraper = EastRidgeScraper(cardName)
    upNorthScraper = UpNorthScraper(cardName)
    pandorasBooxScraper = PandorasBooxScraper(cardName)
    waypointScraper = WaypointScraper(cardName)
    skyfoxScraper = SkyfoxScraper(cardName)
    nerdzCafeScraper = NerdzCafeScraper(cardName)
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
        'thecomichunter': theComicHunterScraper,
        'chimera': chimeraScraper,
        'dragoncards': dragonCardsScraper,
        'gamebreakers': gameBreakersScraper,
        'mythicstore': mythicStoreScraper,
        'vortexgames': vortexGamesScraper,
        'abyss': abyssScraper,
        'silvergoblin': silverGoblinScraper,
        'crypt': cryptScraper,
        'northofexile': northOfExileScraper,
        'hfx': hfxScraper,
        'omg': omgScraper,
        'kesselrun': kesselRunScraper,
        'reddragon': redDragonScraper,
        'taps': tapsScraper,
        'blackknight': blackKnightScraper,
        'outofthebox': outOfTheBoxScraper,
        'pandorasboox': pandorasBooxScraper,
        'timevault': timeVaultScraper,
        'eastridge': eastRidgeScraper,
        'upnorth': upNorthScraper,
        'waypoint': waypointScraper,
        'skyfox': skyfoxScraper,
        'nerdzcafe': nerdzCafeScraper
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
        
def post_price_entry(query, price_list):
    # We need to find the card with the best match for the query, ignore punctuation,
    # ignore case, and ignore whitespace
    try:
        if len(price_list) == 0:
            return
        card_doc = db['cards'].find_one({"name": {"$regex": f"^{query}$", "$options": "i"}})
        if card_doc is None:
            return
        
        # If there is already a price entry for this card today, continue
        todays_price_entry = db['price_entry'].find_one({"oracle_id": card_doc['oracle_id'], "date": {"$gte": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)}})
        if todays_price_entry is not None:
            return
        # if no cards with foil, then no need to check for foil
        if not any([price_entry['foil'] for price_entry in price_list]):
            price_entry = {
            "oracle_id": card_doc['oracle_id'],
            "date": datetime.now(),
            "price_list": [{
                "price": price_entry['price'],
                "website": price_entry['website'],
                "foil": price_entry['foil'],
                "condition": price_entry['condition']
            } for price_entry in price_list],
            "max": round(max([float(str(price_entry['price']).replace(',','')) for price_entry in price_list]), 2),
            "min": round(min([float(str(price_entry['price']).replace(',','')) for price_entry in price_list]), 2),
            "avg": round(sum([float(str(price_entry['price']).replace(',','')) for price_entry in price_list]) / len(price_list), 2),
            }
        else:
            # Create a price entry for this card
            price_entry = {
                "oracle_id": card_doc['oracle_id'],
                "date": datetime.now(),
                "price_list": [{
                    "price": price_entry['price'],
                    "website": price_entry['website'],
                    "foil": price_entry['foil'],
                    "condition": price_entry['condition']
                } for price_entry in price_list],
                "max": round(max([float(str(price_entry['price']).replace(',','')) for price_entry in price_list]), 2),
                "min": round(min([float(str(price_entry['price']).replace(',','')) for price_entry in price_list]), 2),
                "avg": round(sum([float(str(price_entry['price']).replace(',','')) for price_entry in price_list]) / len(price_list), 2),
                "foil_max": round(max([float(str(price_entry['price']).replace(',','')) for price_entry in price_list if price_entry['foil']]), 2),
                "foil_min": round(min([float(str(price_entry['price']).replace(',','')) for price_entry in price_list if price_entry['foil']]), 2),
                "foil_avg": round(sum([float(str(price_entry['price']).replace(',','')) for price_entry in price_list if price_entry['foil']]) / len([price_entry for price_entry in price_list if price_entry['foil']]), 2),
            }
        

        # Send the price entry to mongodb
        # print(price_entry)
        db['price_entry'].insert_one(price_entry)
    except Exception as e:
        print("Error in post_price_entry while trying to insert price entry into mongo")
        print(e)


router = APIRouter()

 
@router.post("/single/")
async def search_single(request: SingleCardSearch, background_tasks: BackgroundTasks):
    # test_data = [{"name":"Dockside Extortionist","set":"Double Masters 2022","price":79.99,"foil":False,"condition":"NM","image":"https://cdn11.bigcommerce.com/s-641uhzxs7j/products/344429/images/392203/2X2107__74044.1655424375.220.290.png?c=1","link":"https://www.facetofacegames.com/dockside-extortionist-107-double-masters-2022/","website":"facetoface"},{"name":"Dockside Extortionist","set":"Double Masters 2022","price":139.99,"foil":False,"condition":"NM","image":"https://cdn11.bigcommerce.com/s-641uhzxs7j/products/344402/images/392176/2X2452__66517.1655424300.220.290.png?c=1","link":"https://www.facetofacegames.com/dockside-extortionist-452-etched-foil-double-masters-2022/","website":"facetoface"},{"name":"Dockside Extortionist","set":"Double Masters 2022","price":89.99,"foil":False,"condition":"NM","image":"https://cdn11.bigcommerce.com/s-641uhzxs7j/products/344389/images/392163/2X2360__74057.1655424277.220.290.png?c=1","link":"https://www.facetofacegames.com/dockside-extortionist-360-borderless-double-masters-2022/","website":"facetoface"},{"name":"Dockside Extortionist","set":"Commander 2019","price":79.99,"foil":False,"condition":"NM","image":"https://cdn11.bigcommerce.com/s-641uhzxs7j/products/249632/images/272731/571bc9eb-8d13-4008-86b5-2e348a326d58__63210.1587660227.220.290.jpg?c=1","link":"https://www.facetofacegames.com/dockside-extortionist-c19/","website":"facetoface"},{"name":"Dockside Extortionist","set":"Commander 2019","condition":"NM","price":80.0,"image":"https://cdn.shopify.com/s/files/1/1704/1809/products/9ee08c9245a123560a1d26f8ba84447fa901011f_large.jpg?v=1640016696","link":"https://store.401games.ca/products/dockside-extortionist-c19","foil":False,"website":"four01"},{"name":"Dockside Extortionist","image":"https://cdn.shopify.com/s/files/1/0567/4178/9882/products/ff188554-0e12-5639-93a1-70698148b309_0cb12531-5a98-493a-bfff-bf4b21f1e96f_large.jpg?v=1656444292","link":"https://houseofcards.ca/products/dockside-extortionist-borderless-alternate-art-double-masters-2022?_pos=1&_sid=d9fc74dfb&_ss=r","set":"Double Masters 2022","condition":"NM","price":90.1,"website":"houseOfCards","foil":False},{"name":"Dockside Extortionist","image":"https://cdn.shopify.com/s/files/1/0567/4178/9882/products/ff188554-0e12-5639-93a1-70698148b309_0cb12531-5a98-493a-bfff-bf4b21f1e96f_large.jpg?v=1656444292","link":"https://houseofcards.ca/products/dockside-extortionist-borderless-alternate-art-double-masters-2022?_pos=1&_sid=d9fc74dfb&_ss=r","set":"Double Masters 2022","condition":"NM","price":107.7,"website":"houseOfCards","foil":True},{"name":"Dockside Extortionist","link":"https://www.hairyt.com/products/dockside-extortionist-borderless-alternate-art-double-masters-2022","image":"https://images.binderpos.com/ff188554-0e12-5639-93a1-70698148b309.jpg","set":"Double Masters 2022","condition":"NM","foil":False,"price":80.0,"website":"hairyt"},{"name":"Dockside Extortionist","link":"https://www.hairyt.com/products/dockside-extortionist-borderless-alternate-art-double-masters-2022","image":"https://images.binderpos.com/ff188554-0e12-5639-93a1-70698148b309.jpg","set":"Double Masters 2022","condition":"NM","foil":True,"price":120.0,"website":"hairyt"},{"name":"Dockside Extortionist","link":"https://www.hairyt.com/products/dockside-extortionist-double-masters-2022","image":"https://images.binderpos.com/936e7c73-242d-5514-babf-9b52c3c3918d.jpg","set":"Double Masters 2022","condition":"NM","foil":False,"price":76.5,"website":"hairyt"},{"name":"Dockside Extortionist","link":"https://www.hairyt.com/products/dockside-extortionist-commander-2019","image":"https://images.binderpos.com/252b8cc1-d499-5e3f-a4e3-b042c91eb6ae.jpg","set":"Commander 2019","condition":"NM","foil":False,"price":75.8,"website":"hairyt"},{"name":"Dockside Extortionist","image":"https://cdn.shopify.com/s/files/1/0570/6308/0145/products/252b8cc1-d499-5e3f-a4e3-b042c91eb6ae_5a41c015-c7ac-47ab-a6f2-1376a73e01fc_large.jpg?v=1624920664","link":"https://gamezilla.ca/products/dockside-extortionist-commander-2019?_pos=1&_sid=3ae15e487&_ss=r","set":"Commander 2019","foil":False,"condition":"LP","price":75.8,"website":"gamezilla"},{"name":"Dockside Extortionist","set":"Commander 2019","condition":"NM","price":72.28,"link":"https://www.sequencecomics.ca/catalog/card_singles-magic_singles-commander_sets-commander_2019/dockside_extortionist/1027258","image":"https://crystal-cdn4.crystalcommerce.com/photos/6522815/medium/en_2UKUpFPSWV.png","foil":False,"website":"sequencegaming"},{"name":"Dockside Extortionist","set":"Double Masters 2022","condition":"NM","price":76.65,"link":"https://www.sequencecomics.ca/catalog/card_singles-magic_singles-masters_sets-double_masters_2022/dockside_extortionist/1108819","image":"https://crystal-cdn1.crystalcommerce.com/photos/6846958/medium/en_N97sUy6XwV20220630-94-1qs4xw1.png","foil":False,"website":"sequencegaming"},{"name":"Dockside Extortionist","link":"https://www.fusiongamingonline.com/catalog/magic_singles-commander_singles-commander_2019/dockside_extortionist/1627783","image":"https://crystal-cdn4.crystalcommerce.com/photos/6522815/medium/en_2UKUpFPSWV.png","set":"Commander 2019","price":79.99,"condition":"NM","website":"fusion","foil":False},{"name":"Dockside Extortionist","link":"https://www.bordercitygames.ca/products/dockside-extortionist-commander-2019","image":"https://images.binderpos.com/252b8cc1-d499-5e3f-a4e3-b042c91eb6ae.jpg","set":"Commander 2019","condition":"LP","foil":False,"price":68.0,"website":"bordercity"},{"name":"Dockside Extortionist","link":"https://www.chimeragamingonline.com/products/dockside-extortionist-foil-etched-double-masters-2022","image":"https://images.binderpos.com/f96624a0-716d-54cb-ae08-d85b8699d281.jpg","set":"Double Masters 2022","condition":"LP","foil":True,"price":139.2,"website":"chimera"},{"name":"Dockside Extortionist","link":"https://www.chimeragamingonline.com/products/dockside-extortionist-borderless-alternate-art-double-masters-2022","image":"https://images.binderpos.com/ff188554-0e12-5639-93a1-70698148b309.jpg","set":"Double Masters 2022","condition":"LP","foil":False,"price":84.7,"website":"chimera"},{"name":"Dockside Extortionist","link":"https://www.chimeragamingonline.com/products/dockside-extortionist-borderless-alternate-art-double-masters-2022","image":"https://images.binderpos.com/ff188554-0e12-5639-93a1-70698148b309.jpg","set":"Double Masters 2022","condition":"LP","foil":True,"price":101.2,"website":"chimera"},{"name":"Dockside Extortionist","link":"https://www.chimeragamingonline.com/products/dockside-extortionist-double-masters-2022","image":"https://images.binderpos.com/936e7c73-242d-5514-babf-9b52c3c3918d.jpg","set":"Double Masters 2022","condition":"LP","foil":False,"price":75.7,"website":"chimera"},{"name":"Dockside Extortionist","set":"Commander 2019","condition":"NM","price":89.99,"link":"https://www.theconnectiongames.com/catalog/magic_singles-commander_sets-commander_2019/dockside_extortionist/400623","image":"https://crystal-cdn4.crystalcommerce.com/photos/6522815/medium/en_2UKUpFPSWV.png","foil":False,"website":"connectiongames"},{"name":"Dockside Extortionist","set":"Double Masters 2022","condition":"NM","price":82.99,"link":"https://www.theconnectiongames.com/catalog/magic_singles-master__horizon_sets-double_masters_2022/dockside_extortionist/430237","image":"https://crystal-cdn1.crystalcommerce.com/photos/6846958/medium/en_N97sUy6XwV20220630-94-1qs4xw1.png","foil":False,"website":"connectiongames"}]

    # background_tasks.add_task(post_price_entry, request.cardName, test_data)
 
    # return test_data
    """
    Search for a single card and return all prices across the provided websites
    """
    proxies = getProxiesFromFile("proxies.txt")

    # Scraper function
    # TODO: Update each scraper with a usesProxies bool
    # TODO: Update each scrape method to take in a proxy
    
    def transform(scraper):
        if scraper.usesProxies: 
            while proxies:  # try as long as there are proxies left
                proxy = random.choice(proxies)
                try:
                    scraper.scrape(proxy)  
                    scraperResults = scraper.getResults()
                    for result in scraperResults:
                        results.append(result)
                    return
                except (ProxyError, Timeout, SSLError, RetryError): 
                    proxies.remove(proxy)  # remove the failing proxy from the list
                    print(f"Proxy {proxy} removed.")
        else:
            scraper.scrape()
            scraperResults = scraper.getResults()
            for result in scraperResults:
                results.append(result)
            return
        
    results = [] # List to store results from all threads
    cache = rd.get(request.cardName.lower())
    if cache:
        return json.loads(cache)
    else :
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

        # Filter the results
        # Check if result name contains the card name
        # Check if the result contains "Token" or "Emblem" and the request.cardName does not contain "Token" or "Emblem", remove result

        filteredResults = []
        for result in results:
            if request.cardName.lower() in result['name'].lower():
                if "token" in result['name'].lower() and "token" not in request.cardName.lower() and "emblem" not in request.cardName.lower():
                    continue
                elif "emblem" in result['name'].lower() and "emblem" not in request.cardName.lower() and "token" not in request.cardName.lower():
                    continue
                else:
                    filteredResults.append(result)
            else:
                continue

        results = filteredResults

        numResults = len(results)
        background_tasks.add_task(post_search, request.cardName, request.websites, "single", "", numResults)
        background_tasks.add_task(post_price_entry, request.cardName, results)

        # Only update the cache if websites is "all" so cache hits don't get partial results
        if "all" in request.websites:
            rd.set(request.cardName.lower(), json.dumps(results))
            rd.expire(request.cardName.lower(), 120)
        return results


@router.post("/bulk/")
async def search_bulk(request: BulkCardSearch, background_tasks: BackgroundTasks):
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
        try:
            if "all" in websites:
                scrapers = scraperMap.values()
            else:
                scrapers = [scraperMap[website] for website in websites]
        except KeyError:
            return {"error": "Invalid website provided"}

        # Run scrapers 
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            threadResults = executor.map(transform, scrapers)

        cardObject = {
            "cardName": cardName.lower(),
            "variants": results[re.sub(r"[^\w\s]", "", cardName).lower()]
        }
        totalResults.append(cardObject)
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        threadResults = executor.map(executeScrapers, cardNames)

    numResults = 0
    for card in totalResults:
        numResults += len(card['variants'])

    background_tasks.add_task(post_search, request.cardNames, request.websites, "multi", "", numResults)

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
    borderCityScaper = BorderCitySealedScraper(setName)
    connectionGamesScraper = ConnectionGamesSealedScraper(setName)
    enterTheBattlefieldScraper = EnterTheBattlefieldSealedScraper(setName)
    everythingGamesScraper = EverythingGamesSealedScraper(setName)
    exorGamesScraper = ExorGamesSealedScraper(setName)
    faceToFaceScraper = FaceToFaceSealedScraper(setName)
    # fantasyForgedScraper = FantasyForgedSealedScraper(setName)
    firstPlayerScraper = FirstPlayerSealedScraper(setName)
    four01Scraper = Four01SealedScraper(setName)
    fusionScraper = FusionSealedScraper(setName)
    gameKnightScraper = GameKnightSealedScraper(setName)
    gamezillaScraper = GamezillaSealedScraper(setName)
    gauntletScraper = GauntletSealedScraper(setName)
    houseOfCardsScraper = HouseOfCardsSealedScraper(setName)
    jeux3DragonsScraper = Jeux3DragonsSealedScraper(setName)
    magicStrongholdScraper = MagicStrongholdSealedScraper(setName)
    orchardCityScraper = OrchardCitySealedScraper(setName)
    chimeraScraper = ChimeraSealedScraper(setName)
    comicHunterScraper = ComicHunterSealedScraper(setName)
    sequenceScraper = SequenceSealedScraper(setName)
    TopDeckHeroScraper = TopDeckHeroSealedScraper(setName)
    hairyTScraper = HairyTSealedScraper(setName)
    # Map scrapers to an identifier keyword
    scraperMap = {
        'atlas': atlasScraper,
        'bordercity': borderCityScaper,
        'chimera': chimeraScraper,
        "connectiongames": connectionGamesScraper,
        'enterthebattlefield': enterTheBattlefieldScraper,
        'everythinggames': everythingGamesScraper,
        'exorgames': exorGamesScraper,
        'facetoface': faceToFaceScraper,
        # 'fantasyforged': fantasyForgedScraper,
        'firstplayer': firstPlayerScraper,
        "four01": four01Scraper,
        "fusion": fusionScraper,
        "gameknight": gameKnightScraper,
        "gamezilla": gamezillaScraper,
        "gauntlet": gauntletScraper,
        'hairyt': hairyTScraper,
        "houseofcards": houseOfCardsScraper,
        "magicstronghold": magicStrongholdScraper,
        "orchardcity": orchardCityScraper,
        "jeux3dragons": jeux3DragonsScraper,
        "sequence": sequenceScraper,
        'thecomichunter': comicHunterScraper,
        'topdeckhero': TopDeckHeroScraper,
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
