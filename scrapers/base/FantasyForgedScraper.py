from bs4 import BeautifulSoup
import requests
from .Scraper import Scraper
import sys


class FantasyForgedScraper(Scraper):
    """
    Split cards can be searched using "//" as a split
    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.baseUrl = 'https://FantasyForged.ca'
        self.searchUrl = self.baseUrl + '/a/search?q='
        self.url = self.createUrl()
        self.website = 'fantasyforged'

        # https://FantasyForged.ca/search?q=Elspeth%2C+Sun%27s*+product_type%3A%22mtg%22

    def createUrl(self):
        # make cardName url friendly
        # spaces = +
        # / = %2F
        # ' = %27
        # , = %2C
        # " = %22
        urlCardName = self.cardName.replace(' ', '%20').replace('/', '%2F').replace("'", "%27").replace(',', '%2C')
        return self.searchUrl + urlCardName + '&options%5Bprefix%5D=last&filter_availability=in-stock'
       
       

    def scrape(self):
        page = requests.get(self.url)
        
        sp = BeautifulSoup(page.text, 'html.parser')
        cards = sp.select('div.grid__item')
        
        for card in cards:
            try:
                # We check for in stock in the search link, don't need to check here
                try: 
                    cardName = card.select_one('div.grid-view-item__title').getText().strip()
                except:
                    # print(f'No card name in the following html')
                    # print(card)
                    # print()
                    continue
                if "Art Card".lower() in cardName.lower():
                    continue
                foil = False
                if "(Foil)" in cardName:
                    foil = True

                # remove any brackets and their contents from the card name
                cardName = cardName.split(' (')[0].strip()
                cardSet = ""


                try:
                    link = self.baseUrl + card.select_one('div.grid-view-item__link div.product-card-list2__image-wrapper > a')['href']
                except:
                    # print(f'No link in the following html')
                    # print(card)
                    # print()
                    continue

                try:
                    image = "https:" + card.select_one('div.image-inner img')['src'].split(' ')[0].replace('1x', '2x')
                except:
                    print(f'No image in the following html')
                    print(card)
                    print()
                    image = ""
                    continue

                # Verify card name is correct
                if not self.compareCardNames(self.cardName.lower(), cardName.lower()):
                    continue

                price = card.select_one('div.product-card-list2__details.product-description > div.grid-view-item__meta > div > span.product-price__price.is-bold.qv-regularprice').getText().replace('$', '').replace("CAD", "").replace(',', '').strip()
                # Since FantasyForged has multiple stores, they could have multiple cards with same condition and set
                # We need to check if an identical card already exists in the list
                cardToAdd = {
                    'name': cardName,
                    'image': image,
                    'link': link,
                    'set': cardSet,
                    'foil': foil,
                    'condition': "NM",
                    'price': float(price),
                    'website': self.website
                }

                if cardToAdd not in self.results:
                    self.results.append(cardToAdd)

            except Exception as e:
                print(f'Error searching for {self.cardName} on {self.website} on line {sys.exc_info()[-1].tb_lineno}')
                print(e.args[-5:])
                continue
        