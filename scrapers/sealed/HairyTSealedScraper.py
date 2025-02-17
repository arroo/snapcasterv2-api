from bs4 import BeautifulSoup
import requests
import sys
from .SealedScraper import SealedScraper
import psycopg2
import os

class HairyTSealedScraper(SealedScraper):
    """
    When using throttled network connection, looks like the data is server-side 
    rendered. Don't have to use playwright.

    Shows 16 products per page, including out of stock items.

    We will paginate through the pages and scrape the data from each page.

    """

    def __init__(self, setName):
        SealedScraper.__init__(self, setName)
        self.website = 'hairyt'
        self.url = 'https://hairyt.com/collections/mtg-sealed?page=' # + page number


    def scrape(self):
        try:
            conn = psycopg2.connect(
                dbname=os.environ['PG_DB'],
                user=os.environ['PG_USER'],
                password=os.environ['PG_PASSWORD'],
                host=os.environ['PG_HOST'],
                port=os.environ['PG_PORT']
            )
            cur = conn.cursor()

            try:
                cur.execute("SELECT * FROM sealed_prices WHERE website = 'hairyt' AND updated_at > NOW() - INTERVAL '8 hours'")
                rows = cur.fetchall()
            except:
                conn.rollback()
                rows = []

            if len(rows) > 0:
                cur.close()
                conn.close()
                rows = [row for row in rows if self.setName.lower() in row[1].lower()]
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
            
            else:   # refresh the data
                allProducts = []
                page = requests.get(self.url + '1')
                sp = BeautifulSoup(page.text, 'html.parser')

                products = sp.select('div.productCard__card')
                for product in products:
                    allProducts.append(product)
                nextPage = sp.select_one('ol.pagination li:last-child a')
                while nextPage is not None:
                    page = requests.get('https://hairyt.com' + nextPage['href'])
                    sp = BeautifulSoup(page.text, 'html.parser')
                    products = sp.select('div.productCard__card')
                    for product in products:
                        allProducts.append(product)
                    nextPage = sp.select_one('ol.pagination li:last-child a')

                for product in allProducts:
                    stock = product.select_one('li.productChip')['data-variantqty']
                    if stock == 0 or stock == '0':
                        continue
                        
                    link = 'https://www.hairyt.com' + product.select_one('p.productCard__title a')['href']
                    name = product.select_one('p.productCard__title a').text
                    try:
                        imageUrl = 'https:' + product.select_one('img.productCard__img')['data-src']
                    except:
                        print(f"HairyTSealedScraper: Couldn't find image for {name} product number {allProducts.index(product)} of {len(allProducts)}")
                        print(product.select_one('img.productCard__img'))
                              
                    price = product.select_one('p.productCard__price').text.replace("$", "").replace(",", "").replace(' CAD', '')
                    if '\n' in price:
                        price = price.split('\n')
                        price = [p for p in price if p != '']
                        price = price[0]

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

                # Update db
                cur.execute("CREATE TABLE IF NOT EXISTS sealed_prices (id serial, name text, link text, image text, price float, stock int, website text, language text, tags text[], updated_at timestamp DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (name, website, language, tags))")
                for result in self.results:
                    cur.execute("INSERT INTO sealed_prices (name, link, image, price, stock, website, language, tags) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (name, website, language, tags) DO UPDATE SET price = EXCLUDED.price, link = EXCLUDED.link, image = EXCLUDED.image, updated_at = EXCLUDED.updated_at", (result['name'], result['link'], result['image'], result['price'], result['stock'], result['website'], result['language'], result['tags']))
                conn.commit()
                cur.close()
                conn.close()

                self.results = [result for result in self.results if self.setName.lower() in result['name'].lower()]




        except Exception as e:
            conn.close()
            print("HairyTSealedScraper: Error on line {}".format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)