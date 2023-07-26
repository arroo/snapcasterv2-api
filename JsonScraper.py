import requests
import time
import pymongo
import os
import dotenv
import threading
import sys
import random
from fake_useragent import UserAgent
from utils.customExceptions import TooManyRequestsError

from requests.exceptions import (
    ProxyError,
    Timeout,
    SSLError,
    RetryError,
)

dotenv.load_dotenv()
ua = UserAgent()
proxies = os.environ["PROXIES"].split(",")

supportedWebsites = {
    "https://gamebreakers.ca/": "mtgSinglesGamebreakers",
    "https://gameknight.ca/": "mtgSinglesGameknight",
    "https://themythicstore.com/": "mtgSinglesThemythicstore",
    "https://hfxgames.com/": "mtgSinglesHfxgames",
    "https://vortexgames.ca/": "mtgSinglesCortexGames",
    "https://gamezilla.ca/": "mtgSinglesGamezilla",
    "https://exorgames.com/": "mtgSinglesExorgames",
    "https://chimeragamingonline.com/": "mtgSinglesChimeragamingonline",
    "https://www.abyssgamestore.com/": "mtgSinglesAbyssgamestore",
    "https://silvergoblin.cards/": "mtgSinglesSilvergoblin",
    "https://cryptmtg.com/": "mtgSinglesCryptmtg",
    "https://northofexilegames.com/": "mtgSinglesNorthofexilegames",
    "https://store.401games.ca/": "mtgSingles401games",
    "https://hairyt.com/": "mtgSinglesHairyt",
    "https://omggames.ca/": "mtgSinglesOmggames",
    "https://kesselrungames.ca/": "mtgSinglesKesselrungames",
    "https://red-dragon.ca/": "mtgSinglesReddragon",
    "https://houseofcards.ca/": "mtgSinglesHouseofcards",
    "https://tapsgames.com/": "mtgSinglesTapsgames",
    "https://www.pandorasboox.ca/": "mtgSinglespandorasboox",
    "https://thetimevault.ca/": "mtgSinglesThetimeVault",
    "https://ergames.ca/": "mtgSinglesErgames",
    "https://www.upnorthgames.ca/": "mtgSinglesUpnorthgames",
    "https://waypointgames.ca/": "mtgSinglesWaypointgames",
    "https://skyfoxgames.com/": "mtgSinglesSkyfoxgames",
    "https://www.nerdzcafe.com/": "mtgSinglesNerdzcafe",
    "https://outoftheboxtcg.com/": "mtgSinglesOutoftheboxtcg",
    "https://blackknightgames.ca/": "mtgSinglesBlackknightgames",
}

proxies = os.environ["PROXIES"].split(",")


def monitor(url, collectionName):
    # Database Connection Info
    myclient = pymongo.MongoClient("mongodb://docker:mongopw@localhost:55001/")
    mydb = myclient["shopify-inventory"]

    collection = mydb[collectionName]
    pageNum = 1
    eof = False
    cardList = []
    productTypeIdentifier = "MTG Single"
    if url == "https://store.401games.ca/":
        productTypeIdentifier = "Magic: The Gathering Singles"

    temp_proxies = proxies.copy()
    num_failed_proxies = 0

    # loop through every page until the end of file
    while eof == False:
        apiCallAttempts = 0
        rateLimitedTimer = 125
        maxAPIAttempts = 6
        r = None
        data = None

        # if there are only 2 proxies left, reset the list
        if len(temp_proxies) <= 2:
            temp_proxies = proxies.copy()

        # Rate limitation handling
        while apiCallAttempts <= maxAPIAttempts and temp_proxies:
            try:
                proxy = random.choice(temp_proxies)
                proxy_parts = proxy.split(":")
                ip_address = proxy_parts[0]
                port = proxy_parts[1]
                username = proxy_parts[2]
                password = proxy_parts[3]
                proxy_args = {
                    "http": "http://{}:{}@{}:{}".format(
                        username, password, ip_address, port
                    ),
                    "https": "http://{}:{}@{}:{}".format(
                        username, password, ip_address, port
                    ),
                }
                headers = {
                    "user-agent": ua.random,
                }
                r = requests.get(
                    url + "products.json?limit=250&page=" + str(pageNum),
                    proxies=proxy_args,
                    headers=headers,
                )
                if r.status_code == 429:
                    raise TooManyRequestsError()
                data = r.json()
                break
            except (ProxyError, Timeout, SSLError, RetryError) as e:
                print(f"Proxy error ({ip_address}): {e}")
                temp_proxies.remove(proxy)

            except TooManyRequestsError as e:
                print(f"Too many requests error ({ip_address}): {e}")
                temp_proxies.remove(proxy)
                apiCallAttempts += 1
                time.sleep(10)

            except Exception as e:
                print(f"Unexpected error ({ip_address}): {e}")
                print(f" on line {sys.exc_info()[-1].tb_lineno}")
                print(f"Failed to load page {pageNum}, delaying for 35 seconds.")
                temp_proxies.remove(proxy)
                time.sleep(rateLimitedTimer)
                rateLimitedTimer = 35
                apiCallAttempts += 1

        if apiCallAttempts > maxAPIAttempts:
            print(
                "Failed to retrieve data in "
                + str(apiCallAttempts)
                + " times. Function will not attempt to retrieve any further pages"
            )
            break

        if len(data["products"]) == 0:
            eof = True
            break
        else:
            for product in data["products"]:
                if product["product_type"] == productTypeIdentifier:
                    productHandle = product["handle"]
                    productTitle = product["title"]
                    try:
                        productImage = product["images"][0]["src"]
                    except:
                        productImage = ""

                    productUrl = url + "products/" + productHandle
                    for variant in product["variants"]:
                        if variant["available"] == True:
                            productVariantTitle = variant["title"]
                            productVariantAvailible = variant["available"]
                            productVariantPrice = float(
                                variant["price"]
                                .replace(",", "")
                                .replace("$", "")
                                .strip()
                            )
                            dict = {
                                "productTitle": productTitle,
                                "productHandle": productHandle,
                                "productVariantTitle": productVariantTitle,
                                "productVariantAvailible": productVariantAvailible,
                                "productVariantPrice": productVariantPrice,
                                "productImage": productImage,
                                "productUrl": productUrl,
                            }
                            cardList.append(dict)
            print(url, "page: " + str(pageNum))

        time.sleep(
            random.randint(1, 4)
        )  # optional, without this we get to about 60-70 pages before rate limiting

        pageNum += 1

    print(
        "Finished Scraping: "
        + url
        + " page count: "
        + str(pageNum)
        + "document count: "
        + str(len(cardList))
    )
    collection.delete_many({})
    if len(cardList) > 0:
        collection.insert_many(cardList)


threads = []
for webUrl, collectionName in supportedWebsites.items():
    t = threading.Thread(
        target=monitor,
        args=(
            webUrl,
            collectionName,
        ),
    )
    t.start()
    threads.append(t)

# Wait all threads to finish.
for t in threads:
    t.join()

print("All threads finshed running")
