from .Scraper import Scraper
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

class ExorGamesScraper(Scraper):
    """
    Exor games uses an API to get the stock of cards
    We can hit the API and get all the information we need

    Split cards can be searched using "//" as a split
    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.siteUrl = 'https://www.exorgames.com'
        self.url = "https://exorgames.com/search?type=product&options%5Bprefix%5D=last&q="
        self.website = 'exorgames'

    def scrape(self):
        # make the card name url friendly
        cardName = self.cardName.replace('"', '%22').replace(' ', '+').replace('//', '%2F%2F').replace("'", '%27').replace(",", "%2C")
        pageData = []
        currPage = 1
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{self.url}{cardName}")
            page.wait_for_selector('span.product-price__price')        

            html = page.content()
            pageData.append(html)
            # if div.pag_next <a> doesnt have btn--disabled class, click it and get the next page
            nextButton = page.query_selector('div.pag_next a.btn')
            nextButtonDisabled = page.query_selector('div.pag_next a.btn--disabled')
            while nextButton and not nextButtonDisabled:
                nextButton.click()
                page.wait_for_selector('span.product-price__price')
                html = page.content()
                pageData.append(html)
                nextButton = page.query_selector('div.pag_next a.btn')
                nextButtonDisabled = page.query_selector('div.pag_next a.btn--disabled')
            browser.close()
        # now we have all the page data, we can parse it with bs4

        allProducts = []
        for page in pageData:
            soup = BeautifulSoup(page, 'html.parser')
            products = soup.find_all('div', class_='grid-view-item') 
            products = [product for product in products if 'product-price--sold-out' not in product["class"]]
            for product in products:
                allProducts.append(product)



        for card in allProducts:
            titleAndSet = card.find('div', class_='h4 grid-view-item__title').text
            if 'Art Card' in titleAndSet:
                continue
            # split the title and set
            title = titleAndSet.split("[")[0].strip()
            setName = titleAndSet.split("[")[1].split("]")[0].strip()

            # remove any excess tags inside () or [] in the title
            title = title.split("(")[0].strip()
            try:
                image = 'https:' + card.find('img', class_='grid-view-item__image')['src']
            except:
                image = ''

            try:
                image_wrapper = card.find('div', class_='grid-view-item__image-container')
                if not image_wrapper:
                    print('no image wrapper')
                inner_div = image_wrapper.find('div')
                if not inner_div:
                    print('no inner div')
                link_tag = inner_div.find('a')
                if not link_tag:
                    print('no link tag')
                link = self.siteUrl + link_tag['href']
            except AttributeError:
                link = ''

            price = card.find('span', class_='product-price__price').text.replace("$",'').replace(',','')

            self.results.append({
                'name': title,
                'link': link,
                'image':image,
                'set': setName,
                'condition': 'NM',
                'foil': False,
                'price': price,
                'website': self.website
            })
            # for variant in card['variants']:
            #     if(variant['quantity'] <= 0):
            #         continue

            #     condition = variant['title'].split(" ")[0].strip()
            #     if condition == "Lightly":
            #         condition = "LP"
            #     elif condition == "Near":
            #         condition = "NM"
            #     elif condition == "Moderately":
            #         condition = "MP"
            #     elif condition == "Heavily":
            #         condition = "HP"
            #     elif condition == "Damaged":
            #         condition = "DMG"
                
            #     foil = False
            #     if "Foil" in variant['title']:
            #         foil = True

            #     price = variant['price']

            #     self.results.append({
            #         'name': title,
            #         'link': link,
            #         'image': image,
            #         'set': setName,
            #         'condition': condition,
            #         'foil': foil,
            #         'price': price,
            #         'website': self.website
            #     })

            