from bs4 import BeautifulSoup
import requests
import json
from .Scraper import Scraper

# This is scraped using an API requests that returns the stock in json
# Broken Right now, need to update api call - Henry

class Four01Scraper(Scraper):
    """
    Split cards can be searched using "//" as a split

    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.siteUrl = 'https://store.401games.ca'
        self.baseUrl = 'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=d3cae9c0-9d9b-4fe3-ad81-873270df14b5&uuid=d3cae9c0-9d9b-4fe3-ad81-873270df14b5&store_id=17041809&api_type=json&category_id=268483363003&narrow=\[\[%22In+Stock%22,%22True%22\]\]&facets_required=1&products_per_page=40&page_num=1&with_product_attributes=true&search_within_search='
        self.url = self.createUrl()
        self.website = 'four01'

    def createUrl(self):
        url = self.baseUrl
        nameArr = self.cardName.split()
        for word in nameArr:
            url += word
            if word != nameArr[len(nameArr)-1]: # then we don't have last item, add +
                url+= '+' 
        # url += '&page_num=1&sort_by=relevency&with_product_attributes=true' # This was for old api url
        return url

    def scrape(self):
        # make the api request
        responseJson = requests.get(self.url)
        print(self.url)
        
        # parse the json response
        data = json.loads(responseJson.content)      
        print(data)
        # create a list to return
        cardList = []

        # get the products
        for item in data['items']:
            name = item['l']
            setName = item['v']
            image = item['t']
            url = self.siteUrl + item['u']

            # Sometimes the foil status is in the name, so we need to remove it
            # and update the foil status
            # Card Name (Foil) (DMU)
            foil = False
            if '(Foil)' in name:
                name = name.replace('(Foil)', '')
                foil = True

            # There is also some tags in parenthesis that we need to remove
            # For example "(DMU) (#367)"
            name = name.split('(')[0].rstrip()

            # there can even be more tags like "Card Name - Borderless", remove em
            if ' - Borderless' in name:
                name = name.split(' - Borderless')[0].rstrip()
                

            # 401 games has an art series for some of their art card sets
            # for example Neon Dynasty Art Series
            if "art series" in setName.lower():
                continue

            if not self.compareCardNames(self.cardName, name):
                continue 
            
            stock = []
            for stockItem in item['vra']:
                item = stockItem[1]
                if ['Sellable',[False]] in item:
                    continue
                
                if item[0][0] == 'Condition':
                    condition = item[0][1][0]

                    if "NM" in condition:
                        condition="NM"
                    elif "SP" in condition:
                        condition="LP"
                    elif "MP" in condition:
                        condition="MP"
                    elif "HP" in condition:
                        condition="HP" 
                    elif "DMG" in condition:
                        condition="DMG"
                    elif "Damaged" in condition:
                        condition="DMG"
                    elif "Default" in condition:
                        condition="NM"

                    price = float(item[1][1][0].replace("CAD:" , ""))
                    cardList.append({
                        'name': name,
                        'set': setName,
                        'condition': condition,
                        'price': price,
                        'image': image,
                        'link': url,
                        'foil': foil,
                        'website': self.website
                    })
                    # stock.append({"condition": condition, "price": price})
                
                elif item[0][0] == 'Price':
                    try:
                        condition = item[3][1][0]
                        if "NM" in condition:
                            condition="NM"
                        elif "SP" in condition:
                            condition="LP"
                        elif "MP" in condition:
                            condition="MP"
                        elif "HP" in condition:
                            condition="HP" 
                        elif "DMG" in condition:
                            condition="DMG"
                        elif "Damaged" in condition:
                            condition="DMG"
                        elif "Default" in condition:
                            condition="NM"

                        price = float(item[0][1][0].replace("CAD:" , ""))
                        cardList.append({
                            'name': name,
                            'set': setName,
                            'condition': condition,
                            'price': price,
                            'image': image,
                            'link': url,
                            'foil': foil,
                            'website': self.website
                        })
                    except:
                        pass

        self.results = cardList


