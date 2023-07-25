import requests
import json
from .Scraper import Scraper
from utils.customExceptions import TooManyRequestsError
from fake_useragent import UserAgent


class UpNorthScraper(Scraper):
    """
    UpNorth can be scraped by hitting their API.

    Split cards can be searched using "//" as a split
    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.siteUrl = 'https://upnorthgames.ca'
        self.url = "https://portal.binderpos.com/external/shopify/products/forStore"
        self.usesProxies = True
        self.website = 'upnorth'

    def scrape(self, proxy):
        # make the card name url friendly
        cardName = self.cardName.replace('"', '%22')
        
        proxy_parts = proxy.split(":")
        ip_address = proxy_parts[0]
        port = proxy_parts[1]
        username = proxy_parts[2]
        password = proxy_parts[3]
        ua = UserAgent()

        proxies = {
            "http" :"http://{}:{}@{}:{}".format(username,password,ip_address,port),
            "https":"http://{}:{}@{}:{}".format(username,password,ip_address,port),
        }
        
        response = requests.post(self.url, proxies=proxies,
            json={
                "storeUrl":"up-north-games-ca.myshopify.com",
                "game":"mtg",
                "strict":None,
                "sortTypes":[{"type":"price","asc":False,"order":1}],
                "variants":None,
                "title":cardName,
                "priceGreaterThan":0,
                "priceLessThan":None,
                "instockOnly":True,
                "limit":30,
                "offset":0
            },
            headers={
                'authority': 'portal.binderpos.com',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'no-cache',
                'content-type': 'application/json; charset=UTF-8',
                'origin': 'https://upnorthgames.ca',
                'pragma': 'no-cache',
                'referer': 'https://upnorthgames.ca/',
                'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
                'DNT': '1',
                'user-agent': ua.random,  # Randomize user agent

            }
        )
        if response.status_code == 429: # Too many requests
                raise TooManyRequestsError(f"{self.website} {ip_address}: HTTP 429 Too many requests...")
        
        # Load the response
        data = json.loads(response.text)

        for card in data['products']:
            titleAndSet = card['title']
            if "Art Card" in titleAndSet:
                continue
            # split the title and set
            title = titleAndSet.split("[")[0].strip()
            setName = titleAndSet.split("[")[1].split("]")[0].strip()

            # remove any excess tags inside () or [] in the title
            title = title.split("(")[0].strip()

            image = card['img']
            handle = card['handle']
            link = f"{self.siteUrl}/products/{handle}"

            for variant in card['variants']:
                # this string contains the condition and foil status
                # variant['title'] = "Lightly Played Foil"
                # print the variant as json
                if(variant['quantity'] <= 0):
                    continue

                condition = variant['title'].split(" ")[0].strip()
                # getting the first element here will yield
                # "Lightly" or "Near" or "Moderately" or "Heavily" or "Damaged"
                # We want to code this to "LP" or "NM" or "MP" or "HP" or "DMG"
                if condition == "Lightly":
                    condition = "LP"
                elif condition == "Near":
                    condition = "NM"
                elif condition == "Moderately":
                    condition = "MP"
                elif condition == "Heavily":
                    condition = "HP"
                elif condition == "Damaged":
                    condition = "DMG"
                
                # check if the card is foil
                foil = False
                if "Foil" in variant['title']:
                    foil = True

                price = variant['price']

                self.results.append({
                    'name': title,
                    'link': link,
                    'image': image,
                    'set': setName,
                    'condition': condition,
                    'foil': foil,
                    'price': price,
                    'website': self.website
                })

