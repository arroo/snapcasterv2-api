from bs4 import BeautifulSoup
import requests
from .SealedScraper import SealedScraper
import os
import psycopg2
import sys

class ComicHunterSealedScraper(SealedScraper):
    """
    We can apply the following filters by adding to the link in the advanced search
    - in stock
    - sealed

    Then we get a page with all the in stock sealed products

    From here we can iterate through every page to create a product list, then parse

    Once parsed, we post results to the database

    

   https://www.comichunter.net/advanced_search?utf8=%E2%9C%93&search%5Bfuzzy_search%5D=&search%5Btags_name_eq%5D=&search%5Bsell_price_gte%5D=&search%5Bsell_price_lte%5D=&search%5Bbuy_price_gte%5D=&search%5Bbuy_price_lte%5D=&search%5Bin_stock%5D=0&search%5Bin_stock%5D=1&buylist_mode=0&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bcategory_ids_with_descendants%5D%5B%5D=12&search%5Bvariants_with_identifier%5D%5B19%5D%5B%5D=&search%5Bsort%5D=name&search%5Bdirection%5D=ascend&commit=Search&search%5Bcatalog_group_id_eq%5D=
   """

    def __init__(self, setName):
        SealedScraper.__init__(self, setName)
        self.website = 'thecomichunter'
        self.url = 'https://www.comichunter.net/advanced_search?utf8=%E2%9C%93&search%5Bfuzzy_search%5D=&search%5Btags_name_eq%5D=&search%5Bsell_price_gte%5D=&search%5Bsell_price_lte%5D=&search%5Bbuy_price_gte%5D=&search%5Bbuy_price_lte%5D=&search%5Bin_stock%5D=0&search%5Bin_stock%5D=1&buylist_mode=0&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bcategory_ids_with_descendants%5D%5B%5D=12&search%5Bvariants_with_identifier%5D%5B19%5D%5B%5D=&search%5Bsort%5D=name&search%5Bdirection%5D=ascend&commit=Search&search%5Bcatalog_group_id_eq%5D='

    def scrape(self):
        # first we check the database to see if we have already scraped this site in the last 4 hours
        # if we have, we don't need to scrape again
        # otherwise we scrape and post to the database
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
                cur.execute("SELECT * FROM sealed_prices WHERE website = 'thecomichunter' AND updated_at > NOW() - INTERVAL '8 hours'")
                rows = cur.fetchall()
            except:
                conn.rollback()
                rows = []

            # if there is data, return it
            if len(rows) > 0:
                # close db connection, we don't need it anymore
                cur.close()
                conn.close()
                # filter out any results that don't match the set name
                rows = [row for row in rows if self.setName.lower() in row[1].lower()]
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
                # update DB
                allProducts = []
                page = requests.get(self.url)
        
                sp = BeautifulSoup(page.text, 'html.parser')
                products = sp.select('li.product div.inner')
                # print("products: ", len(products))
                for product in products:
                    allProducts.append(product)
                
                # iterate over the pages
                nextPage = sp.select_one('div.pagination a.next_page')
                while nextPage is not None:
                    page = requests.get('https://comichunter.net'+ nextPage['href'])
                    sp = BeautifulSoup(page.text, 'html.parser')
                    products = sp.select('li.product div.inner')
                    for product in products:
                        allProducts.append(product)
                    nextPage = sp.select_one('div.pagination a.next_page')
                for product in allProducts:
                    link = 'https://www.comichunter.net' + product.select_one('div.image a')['href']
                    name = product.select_one('div.image a')['title']
                    imageUrl = product.select_one('img')['src']
                    price = product.select_one('div.variant-row').select_one('form.add-to-cart-form')['data-price'].replace("CAD$ ","")
                    stock = product.select_one('div.variant-row span.variant-qty').text.replace(" In Stock", "")
                    tags = self.setTags(name)

                    self.results.append({
                        'name': name,
                        'link': link,
                        'image': imageUrl,
                        'price': float(price),
                        'stock': int(stock),
                        'website': self.website,
                        'language': self.setLanguage(name),
                        'tags': tags,
                    })

                # update db
                cur.execute("CREATE TABLE IF NOT EXISTS sealed_prices (id serial, name text, link text, image text, price float, stock int, website text, language text, tags text[], updated_at timestamp DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (name, website, language, tags))")
                # insert the data, if there is a conflict, update the price, link, image, and updated_at
                for result in self.results:
                    cur.execute("INSERT INTO sealed_prices (name, link, image, price, stock, website, language, tags) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (name, website, language, tags) DO UPDATE SET price = EXCLUDED.price, link = EXCLUDED.link, image = EXCLUDED.image, updated_at = EXCLUDED.updated_at", (result['name'], result['link'], result['image'], result['price'], result['stock'], result['website'], result['language'], result['tags']))
                conn.commit()
                # close db connection
                cur.close()
                conn.close()

                # filter self.results to only include the set we are looking for
                self.results = [result for result in self.results if self.setName.lower() in result['name'].lower()]


        except Exception as e:
            conn.close()
            print("error in theComicHunter Sealed")
            print("Error on line {}".format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)