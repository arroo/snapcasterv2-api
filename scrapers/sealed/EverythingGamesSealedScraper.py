from bs4 import BeautifulSoup
import requests
from .SealedScraper import SealedScraper
import sys
import os
import psycopg2
import dotenv
dotenv.load_dotenv()
from playwright.sync_api import sync_playwright


class EverythingGamesSealedScraper(SealedScraper):
    """
    This is a bit different, The sealed portion of the ecommerce site is rendered
    serverside, so the API isn't exposed. I will have to check all the pages 

    1. https://EverythingGamesgames.ca/collections/mtg-sealed?filter.v.availability=1
    2. https://EverythingGamesgames.ca/collections/mtg-sealed?filter.v.availability=1&page=2
    3. https://EverythingGamesgames.ca/collections/mtg-sealed?filter.v.availability=1&page=3

    Also, there is no way to reliably search for a specific set, so I will have to
    iterate through all the sets and check if the name matches. This is a bit slow,
    so I will post the results to a database on a cron job and then query that?

    So Step 1 is to return the info from the database, and step 2 is to update the
    database.

    Sealed product search is rendered with javascript, so we can't scrape it with bs4.
    Instead I'll use playwright to scrape the page and then use bs4 to parse the html I think.
    """

    def __init__(self, setName):
        SealedScraper.__init__(self, setName)
        self.baseUrl = 'https://EverythingGames.ca'
        self.website='everythinggames'

    def getResults(self):
        # we are overriding this for now. HouseofCards scrapes ALL sealed data, so we will filter out
        # excess stuff here. But ideally we don't scrape it all every time. Push to database instead...
        self.results = [result for result in self.results if self.setName.lower() in result['name'].lower()]
        return self.results

    def scrape(self):
        # We want to check the database for bordercity data, if it has been updated in the last 8 hours, return the data
        # otherwise, scrape the site and update the database, then return the data

        try:
            # connect to the database
            conn = psycopg2.connect(
                dbname=os.environ['PG_DB'],
                user=os.environ['PG_USER'],
                password=os.environ['PG_PASSWORD'],
                host=os.environ['PG_HOST'],
                port=os.environ['PG_PORT']
            )
            cur = conn.cursor()

            try:
                # check if the data has been updated in the last 8 hours
                cur.execute("SELECT * FROM sealed_prices WHERE website = 'everythinggames' AND updated_at > NOW() - INTERVAL '8 hours'")
                rows = cur.fetchall()
            except:
                conn.rollback()
                rows = []

            # if there is data, return it
            if len(rows) > 0:
                # close db connection, we don't need it anymore
                cur.close()
                conn.close()
                # return the data
                self.results = [{
                    'name': row[1],
                    'link': row[2],
                    'image': row[3],
                    'price': row[4],
                    'stock': row[5],
                    'website': row[6],
                    'language': row[7],
                    'tags': row[8],
                } for row in rows]
                return self.results
            
            # otherwise, scrape the site and update the database
            else:
                pageData = []
                # We need to check three different pages and they are all paginated
                curPage = 1
                # print('https://bordercitygames.ca/collections/magic-sealed-products?filter.v.availability=1&page=1')
                url = self.baseUrl + '/collections/mtg-sealed?filter.v.availability=1&page=' + str(curPage)
                # get page data with playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url)
                    # wait for page to load and then get the html
                    # page.wait_for_load_state()
                    # wait for dynamic content to load
                    # once we see a span with class product-price__price, we know the page is loaded

                    page.wait_for_selector('div.product-price')
                    # wait for the selector to have 
                    # sleep for 5 seconds to make sure the page is loaded
                    html = page.content()
                    pageData.append(html)
                    # <div class="pag_next">
                    #     <a href="/collections/magic-sealed-products?filter.v.availability=1&amp;page=2" class="btn btn--secondary btn--narrow">
                    #         <i class="material-icons"></i>
                    #         <span class="icon__fallback-text">Next</span>
                    #     </a>
                    #  </div>
                    nextButton = page.query_selector('div.pag_next a.btn')
                    nextButtonDisabled = page.query_selector('div.pag_next a.btn--disabled')
                    while nextButton and not nextButtonDisabled:
                        nextButton.click()
                        page.wait_for_selector('div.product-price')
                        html = page.content()
                        pageData.append(html)
                        nextButton = page.query_selector('div.pag_next a.btn')
                    nextButtonDisabled = page.query_selector('div.pag_next a.btn--disabled')
                    browser.close()
                # now we have all the page data, we can parse it with bs4
                    


            
                # for each page in pageData: we need to get the products
                allProducts = []
                for page in pageData:
                    soup = BeautifulSoup(page, 'html.parser')
                    products = soup.find_all('div', class_='grid-view-item')
                    for product in products:
                        allProducts.append(product)
                # soup = BeautifulSoup(r.text, 'html.parser')
                # products = soup.find_all('div', class_='grid-view-item')
                i=0
                for product in allProducts:
                    i+=1
                    try:
                        name = product.find('div', class_='h4 grid-view-item__title').text
                        price = product.find('span', class_='product-price__price').text.replace("$",'').replace(',','')
                        stock = -1
                        tags = self.setTags(name)
                        try:
                            image = 'https:' + product.find('img', class_='grid-view-item__image')['src']
                        except:
                            image = ''
                        # print(f'Image {image}')
                        try:
                            link = self.baseUrl + product.find('div', class_='grid-view-item__image-wrapper js').find('a')['href']
                        except:
                            link = ''
                            
                        self.results.append({
                            'name': name,
                            'link': link,
                            'image': image,
                            'price': float(price),
                            'stock': -1,
                            'website': self.website,
                            'language': 'English',
                            'tags': tags
                        }) 

                    except Exception as e:
                        print(f'Error searching for sealed on {self.website}')
                        print(f'Error on line {sys.exc_info()[-1].tb_lineno} type {e}')
                        print(e.args[-5:])



                # update the database
                # create the table if it doesn't exist, primary key is a composite of name, website, language, and tags
                cur.execute("CREATE TABLE IF NOT EXISTS sealed_prices (id serial, name text, link text, image text, price float, stock int, website text, language text, tags text[], updated_at timestamp DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (name, website, language, tags))")
                # # insert the data, if there is a conflict, update the price, link, image, and updated_at
                for result in self.results:
                    cur.execute("INSERT INTO sealed_prices (name, link, image, price, stock, website, language, tags) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (name, website, language, tags) DO UPDATE SET price = EXCLUDED.price, link = EXCLUDED.link, image = EXCLUDED.image, updated_at = EXCLUDED.updated_at", (result['name'], result['link'], result['image'], result['price'], result['stock'], result['website'], result['language'], result['tags']))
                conn.commit()
                # # close db connection
                cur.close()
                conn.close()

                # filter self.results to only include the set we are looking for
                self.results = [result for result in self.results if self.setName.lower() in result['name'].lower()]



        except Exception as e:
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        
