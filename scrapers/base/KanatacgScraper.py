from bs4 import BeautifulSoup
import requests
from .Scraper import Scraper


class KanatacgScraper(Scraper):
    """
    Split cards can be searched using "//" as a split
    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.baseUrl = 'https://www.kanatacg.com'
        self.searchUrl = self.baseUrl + '/advanced_search?utf8=%E2%9C%93&search%5Bfuzzy_search%5D='
        self.url = self.createUrl()
        self.website='kanatacg'

    def createUrl(self):
        url = self.searchUrl
        nameArr = self.cardName.split()
        for word in nameArr:
            url +=word
            if word != nameArr[len(nameArr)-1]: # then we don't have last item, add +
                url+= '+'
            else: pass
        return url+"&search%5Btags_name_eq%5D=&search%5Bcatalog_group_id_eq%5D=&search%5Bsort%5D=name&search%5Bdirection%5D=ascend&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bcategory_ids_with_descendants%5D%5B%5D=8&buylist_mode=0&search%5Bsell_price_gte%5D=&search%5Bsell_price_lte%5D=&search%5Bbuy_price_gte%5D=&search%5Bbuy_price_lte%5D=&search%5Bin_stock%5D=0&search%5Bin_stock%5D=1&commit=Search"

    def scrape(self):
        #Iterate to the next page until it returns no search results - Henry
        pageNum=1
        while True:
            page = requests.get(f'{self.url}+"&page={pageNum}"')
            sp = BeautifulSoup(page.text, 'html.parser')
            cards = sp.select('table.invisible-table tr')

            #If there are no results then break out of the loop - Henry
            if not cards:
                break
            stockList = []

            for card in cards:
                # Check to see it is a magic card
                # TODO

                # Verify card name is correct
                checkNameTag = card.select('td')[1]
                checkName = checkNameTag.select_one('a')        
    
                if not checkName:
                    continue
                elif "art card" in checkName.getText().lower():
                    continue
                if not self.compareCardNames(self.cardName, checkName.getText()):
                    continue

                name = card.select('td')[1].select_one('a').getText()
                # the foil status is in the name here as "Card Name - Foil"
                foil = False
                if "foil" in name.lower():
                    foil = True
                    name = name.replace(" - Foil", "")

                # there can even be more tags like "Card Name - Borderless", remove em
                if ' - ' in name:
                    name = name.split(' - ')[0]

                name = name.strip()
                
                link = self.baseUrl + card.select('td')[1].select_one('a')['href']
                imageUrl = card.select_one('td a')['href']
                setName = card.select('td')[1].select_one('small').getText()
                if "art series" in setName.lower():
                    continue

                # sometimes there is a " - Borderless" tag in the set name
                # we want to remove it
                if " - " in setName:
                    setName = setName.split(" - ")[0]

                # For this card variant, get the stock
                variantStockList = []
                variantConditions = card.select('tr.variantRow')

                # For each item get the condition and price
                for c in variantConditions:
                    condition = c.select_one('td.variantInfo').getText().replace('Condition: ', '').replace('-Mint, English', '')
                    if "Brand New" in condition: # then it's not a MTG single
                        continue
                    elif "NM" in condition:
                        condition="NM"
                    elif "Slight" in condition:
                        condition="LP"
                    elif "Moderate" in condition:
                        condition="MP"
                    elif "Heav" in condition:
                        condition="HP"
                    elif "Damaged" or "DMG" in condition:
                        condition="DMG"
                    price = float(c.select('td')[1].getText().replace('CAD$ ', '').replace(",", ""))
                    if (condition, price) not in variantStockList:
                        self.results.append({
                            'name': name,
                            'set': setName,
                            'condition': condition,
                            'price': price,
                            'image': imageUrl,
                            'link': link,
                            'foil': foil,
                            'website': self.website
                        })
            pageNum+=1
                        # variantStockList.append({"condition": condition, "price": price})
                    
            #     # If stockList is empty, continue
            #     if not variantStockList:
            #         continue



            #     results = {
            #         'name': name,
            #         'link': link,
            #         'image': imageUrl,
            #         'set': setName,
            #         'stock': variantStockList,
            #         'website': self.website
            #     }
            #     stockList.append(results)

            # self.results = stockList