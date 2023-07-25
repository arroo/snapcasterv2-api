import requests
import json
from .Scraper import Scraper
from utils.customExceptions import TooManyRequestsError
from fake_useragent import UserAgent


class MagicStrongholdScraper(Scraper):
    """
    Magic Stronghold uses an API to get the stock of cards
    We can hit the API and get all the information we need

    https://api.conductcommerce.com/v1/advancedSearch


    Split cards can be searched using "//" as a split

    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.siteUrl = 'https://www.magicstronghold.com'
        self.url = "https://api.conductcommerce.com/v1/advancedSearch"
        usesProxies = True
        self.website = 'magicstronghold'

    def scrape(self, proxy):
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
                "productTypeID": 1,
                "name": self.cardName,
                "host": "www.magicstronghold.com"
            }, 
            headers={
                "authority": "api.conductcommerce.com",
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "text/plain",
                "origin": "https://www.magicstronghold.com",
                "pragma": "no-cache",
                "referer": "https://www.magicstronghold.com/",
                "sec-ch-ua": '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
                'DNT': '1',
                'user-agent': ua.random
            })

        if response.status_code == 429: # Too many requests
            raise TooManyRequestsError(f"{self.website} {ip_address}: HTTP 429 Too many requests...")
        
        # Load the response
        try:
            data = json.loads(response.text)
        except:
            print(f'Error loading response for {self.cardName} at {self.website}')
            return

        # The image uri prefix
        # Cards that are high value and have scanned images will not use this image prefix.
        imagePrefix = 'https://conduct-catalog-images.s3-us-west-2.amazonaws.com/small/'
        
        # iterate over each card
        for card in data['result']['listings']:
            # get the name of the card
            name = card['inventoryName']
            # foil status is in the card name as '- Foil' tag
            foil = False
            if ' - Foil' in name:
                foil = True
                name.replace(' - Foil', '')

            # sometimes there are other tags like "Card Name - Extended Art"
            # we want to remove the tag from the card name
            if ' - ' in name:
                name = name.split(' - ')[0]
            
            # there can even be more tags like "Card Name (M21)"
            # we want to remove the tag from the card name
            if ' (' in name:
                name = name.split(' (')[0]
                

            setName = card['categoryName']

            # we need to check if the card image is a scanned image or not
            # scanned images are hosted at magicstronghold-images.s3.amazonaws.com/inventory
            # and have do not use the imagePrefix

            if 'magicstronghold-images.s3.amazonaws.com' in card['image']:
                image = card['image']
            else:
                image = imagePrefix + card['image']

            for variant in card['variants']:
                if variant['quantity'] <= 0:
                    continue

                price = variant['price']
                condition = variant['name']

                if condition == "Lightly Played":
                    condition = "LP"
                elif condition == "NM/Mint":
                    condition = "NM"
                elif condition == "Moderately Played":
                    condition = "MP"
                elif condition == "Sleeve Playable":
                    condition = "HP"
                # no DMG condition from what I can tell

                # construct link to card
                categoryName = card['categoryName'].replace(' ', '%20')
                inventoryID = str(card['inventoryID'])
                inventoryName = card['inventoryName'].replace(' ', '_')

                link = f"{self.siteUrl}/store/category/{categoryName}/item/{inventoryID}/{inventoryName}"
                self.results.append({
                    'name': name,
                    'set': setName,
                    'foil': foil,
                    'condition': condition,
                    'price': price,
                    'image': image,
                    'link': link,
                    'website': self.website
                })