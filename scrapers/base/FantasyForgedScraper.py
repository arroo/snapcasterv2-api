from bs4 import BeautifulSoup
import requests
from .Scraper import Scraper


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
        cards = sp.select('li.grid__item')

        for card in cards:
            try:
                # We check for in stock in the search link, don't need to check here
                
                cardName = card.select_one('a.full-unstyled-link').getText().strip()
                if "Art Card".lower() in cardName.lower():
                    continue
                foil = False
                if "(Foil)" in cardName:
                    foil = True

                # remove any brackets and their contents from the card name
                cardName = cardName.split(' (')[0].strip()
                cardSet = ""



                link = self.baseUrl + card.select_one('a.full-unstyled-link')['href']
                image = "https:" + card.select_one('div.media img')['srcset'].split(' ')[0].replace('1x', '2x')

                # Verify card name is correct
                if not self.compareCardNames(self.cardName.lower(), cardName.lower()):
                    continue

                price = card.select_one('span.price-item--regular').getText().replace('$', '').replace("CAD", "").strip()

                # Since FantasyForged has multiple stores, they could have multiple cards with same condition and set
                # We need to check if an identical card already exists in the list
                cardToAdd = {
                    'name': cardName,
                    'image': image,
                    'link': link,
                    'set': cardSet,
                    'foil': foil,
                    'condition': "NM",
                    'price': price,
                    'website': self.website
                }

                if cardToAdd not in self.results:
                    self.results.append(cardToAdd)

            except Exception as e:
                print(f'Error searching for {self.cardName} on {self.website}')
                print(e.args[-5:])
                continue
        