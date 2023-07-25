import requests
import json
from .Scraper import Scraper

class ChimeraScraper(Scraper):
    """
    Chimera can be scraped by hitting their API. 
    ** 1-1 copy of HairyTScraper.py **

    Split cards can be searched using "//" as a split
    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.siteUrl = 'https://www.chimeragamingonline.com'
        self.url = "https://portal.binderpos.com/external/shopify/products/forStore"
        self.usesProxies = True
        self.website = 'chimera'

    def scrape(self, proxy):
        # make the card name url friendly
        cardName = self.cardName.replace('"', '%22')

        response = requests.post(self.url, 
            json={
                "storeUrl":"chimera-gaming.myshopify.com",
                "game":"mtg",
                "strict":None,
                "sortTypes":[{"type":"price","asc":False,"order":1}],
                "variants":None,
                "title":cardName,
                "priceGreaterThan":0,
                "priceLessThan":None,
                "instockOnly":True,
                "limit":18,
                "offset":0
            },
            headers={
                'authority': 'portal.binderpos.com',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'no-cache',
                'content-type': 'application/json; charset=UTF-8',
                'origin': 'https://chimeragamingonline.com',
                'pragma': 'no-cache',
                'referer': 'https://chimeragamingonline.com/',
                'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
                'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36'
            }
        )
        if response.status_code == 429: # Too many requests
            print(f"{self.website}: HTTP 429 Too many requests, skipping...")
            return
        
        # Load the response
        data = json.loads(response.text)
        # print (data)
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
                if "LP" or "Slightly" in condition:
                    condition = "LP"
                elif "NM" in condition:
                    condition = "NM"
                elif "MP" or "Moder" in condition:
                    condition = "MP"
                elif "HP" or "Heav" in condition:
                    condition = "HP"
                elif "DMG" or "Dam" in condition:
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

