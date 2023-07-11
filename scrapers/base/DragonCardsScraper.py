from bs4 import BeautifulSoup
import requests
from .Scraper import Scraper
import sys



class DragonCardsScraper(Scraper):
    """
    Identical to FantasyForged
    
    TODO:
    - properly parse all available conditions and foils, right now we just hardcode NM and non-foil
    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.baseUrl = 'https://tcg.dragoncardsandgames.com'
        self.searchUrl = self.baseUrl + '/search?options%5Bprefix%5D=last&type=product&q='
        self.url = self.createUrl()
        self.website = 'dragoncards'

        # https://FantasyForged.ca/search?q=Elspeth%2C+Sun%27s*+product_type%3A%22mtg%22

    def createUrl(self):
        # make cardName url friendly
        # spaces = +
        # / = %2F
        # ' = %27
        # , = %2C
        # " = %22
        urlCardName = self.cardName.replace(' ', '+').replace('/', '%2F').replace("'", "%27").replace(',', '%2C')
        return self.searchUrl + urlCardName + '&options%5Bprefix%5D=last&filter_availability=in-stock'
       
       

    def scrape(self):
        page = requests.get(self.url)

        # log infor about the request
        # Log information about response, status code, and url, number of results
        print(f"-----------------------------------")
        print(f"Response: {page.status_code}")
        print(f"Response: {page.reason}")
        print(f"URL: {page.url}")
        # print(f"Number of results: {
        print(f"-----------------------------------")
        
        
        sp = BeautifulSoup(page.text, 'html.parser')
        cards = sp.select('div.products-display div.product-card-list2')
        
        print(f"Number of results: {len(cards)}")
        print(f"-----------------------------------")

        for card in cards:
            try:
                
                stockTag = card.select_one('#tag-container')
                print(stockTag)

                try: 
                    cardName = card.select_one('div.grid-view-item__title').getText().strip()
                except:
                    # print(f'No card name in the following html')
                    # print(card)
                    # print()
                    continue
                if "Art Card".lower() in cardName.lower():
                    continue


                # remove any brackets and their contents from the card name
                cardName = cardName.split(' (')[0].strip()
                # card set is inside square brackets in card name
                if '[' in cardName:
                    cardSet = cardName.split('[')[1].split(']')[0].strip()
                    cardName = cardName.split('[')[0].strip()

                else :
                    cardSet = ""

                try:
                    link = self.baseUrl + card.select_one('div.grid-view-item__link div.product-card-list2__image-wrapper > a')['href']
                except:
                    continue

                try:
                    image = "https:" + card.select_one('div.image-inner img')['src'].split(' ')[0].replace('1x', '2x')
                except:
                    image = ""
                    continue

                # Verify card name is correct
                if not self.compareCardNames(self.cardName.lower(), cardName.lower()):
                    continue

                price = card.select_one('div.product-card-list2__details.product-description > div.grid-view-item__meta > div > span.product-price__price.is-bold.qv-regularprice').getText().replace('$', '').replace("CAD", "").replace(',', '').strip()
                cardToAdd = {
                    'name': cardName,
                    'image': image,
                    'link': link,
                    'set': cardSet,
                    'foil': False,
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
        