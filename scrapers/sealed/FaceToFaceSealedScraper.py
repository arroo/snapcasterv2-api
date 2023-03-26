from re import I
import requests
import json
from .SealedScraper import SealedScraper
import sys
import psycopg2
import os

class FaceToFaceSealedScraper(SealedScraper):
    """
    We can hit the face to face api to get card data

    Split cards can be searched using "//" as a split
    """
    def __init__(self, setName):
        SealedScraper.__init__(self, setName)
        self.siteUrl = 'https://www.facetofacegames.com/'
        self.url = "https://essearchapi-na.hawksearch.com/api/v2/search"
        self.website = 'facetoface'

    def scrape(self):
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
                cur.execute("SELECT * FROM sealed_prices WHERE website = 'facetoface' AND updated_at > NOW() - INTERVAL '8 hours'")
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
                responses = []
                # We need to check all pages until they show empty
                curPage = 1

                response = requests.post(self.url, 
                    json={
                        "Keyword":"",
                        "FacetSelections": {
                            "tab": ["Magic"],
                            "child_inventory_level": ["1"],
                        },
                        "PageNo": 1,
                        "ClientGuid": "30c874915d164f71bf6f84f594bf623f",
                        "IndexName": "",
                        "ClientData": {
                            "VisitorId": ""
                        },
                        "CustomUrl":"/magic/magic-sealed-products/"
                        },
                    headers={
                        "authority": "essearchapi-na.hawksearch.com",
                        "accept": "application/json, text/plain, */*",
                        "accept-language": "en-US,en;q=0.9",
                        "cache-control": "no-cache",
                        "content-type": "application/json;charset=UTF-8",
                        "origin": "https://www.facetofacegames.com",
                        "pragma": "no-cache",
                        "referer": "https://www.facetofacegames.com/",
                        "sec-ch-ua": "\"Chromium\";v=\"106\", \"Google Chrome\";v=\"106\", \"Not;A=Brand\";v=\"99\"",
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": "\"macOS\"",
                        "sec-fetch-dest": "empty",
                        "sec-fetch-mode": "cors",
                        "sec-fetch-site": "cross-site",
                        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
                    })
                data = json.loads(response.text)

                for result in data['Results']:
                    responses.append(result)

                numPages = data['Pagination']['NofPages']

                while curPage < numPages:
                    curPage += 1
                    response = requests.post(self.url, 
                        json={
                            "Keyword":"",
                            "FacetSelections": {
                                "tab": ["Magic"],
                                "child_inventory_level": ["1"],
                            },
                            "PageNo": curPage,
                            "ClientGuid": "30c874915d164f71bf6f84f594bf623f",
                            "IndexName": "",
                            "ClientData": {
                                "VisitorId": ""
                            },
                            "CustomUrl":"/magic/magic-sealed-products/"
                            },
                        headers={
                            "authority": "essearchapi-na.hawksearch.com",
                            "accept": "application/json, text/plain, */*",
                            "accept-language": "en-US,en;q=0.9",
                            "cache-control": "no-cache",
                            "content-type": "application/json;charset=UTF-8",
                            "origin": "https://www.facetofacegames.com",
                            "pragma": "no-cache",
                            "referer": "https://www.facetofacegames.com/",
                            "sec-ch-ua": "\"Chromium\";v=\"106\", \"Google Chrome\";v=\"106\", \"Not;A=Brand\";v=\"99\"",
                            "sec-ch-ua-mobile": "?0",
                            "sec-ch-ua-platform": "\"macOS\"",
                            "sec-fetch-dest": "empty",
                            "sec-fetch-mode": "cors",
                            "sec-fetch-site": "cross-site",
                            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
                        })
                    data = json.loads(response.text)
                    for result in data['Results']:
                        responses.append(result)


                for result in responses:
                    try:
                        product = result['Document']
                        productName = product['title'][0]
                        image = product['image'][0]
                        link = product['url_detail'][0]
                        price = product['price_retail'][0]
                        language = product['language'][0]
                        tags = self.setTags(productName)
                        stock = product['inventory_level'][0]
                        # print(f"name: {productName} at {link}")
                        # print(f"image: {image}")
                        # print(f"price: {price}")
                        # print(f"language: {language}")
                        # print(f"stock: {stock}")
                        # print(f"tags: {tags}")
                        # print(f"--------")
                        if self.setName.lower() in productName.lower():
                            print(f"Adding {productName} for query of {self.setName}")
                            self.results.append({
                                'name': productName,
                                'stock': stock,
                                'price': float(price),
                                'tags': tags,
                                'language': language,
                                'image': image,
                                'link': link,
                                'website': self.website
                            })
                            
                    
                    except Exception as e:
                        print(f'Error searching for {self.setName} on {self.website}')
                        print(e.args[-5:])
                        continue

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
        
