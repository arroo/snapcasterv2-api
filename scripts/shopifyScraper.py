import dotenv
import requests
import time
import pymongo
import threading
import re
import os

"""
This script scrapes all binderPOS/shopify stores for their entire inventory, and stores it in a MongoDB database.

BinderPOS updates inventory only twice a day as per their TOS - 3am and 3pm EST.

This script is meant to be run at 3:15am and 3:15pm EST, to ensure that the database is up to date.

Reads from scripts/proxies.txt: 1 proxy per line, in the format of ip:port:username:password
"""

dotenv.load_dotenv()
MONGO_URI = os.environ["MONGO_URI"]
myclient = pymongo.MongoClient(MONGO_URI)
mydb = myclient["shopify-inventory"]


supportedWebsites = {
    "levelup":{"url":"https://levelupgames.ca/","collection":"mtgSinglesLevelupgames"},
    "gamebreakers":{"url":"https://gamebreakers.ca/","collection":"mtgSinglesGamebreakers"},
    "gameknight":{"url":"https://gameknight.ca/","collection":"mtgSinglesGameknight"},
    "mythicstore":{"url":"https://themythicstore.com/","collection":"mtgSinglesThemythicstore"},
    "hfx":{"url":"https://hfxgames.com/","collection":"mtgSinglesHfxgames"},
    "vortexgames":{"url":"https://vortexgames.ca/","collection":"mtgSinglesVortexGames"},
    "gamezilla":{"url":"https://gamezilla.ca/","collection":"mtgSinglesGamezilla"},
    "exorgames":{"url":"https://exorgames.com/","collection":"mtgSinglesExorgames"},
    "chimera":{"url":"https://chimeragamingonline.com/","collection":"mtgSinglesChimeragamingonline"},
    "abyss":{"url":"https://www.abyssgamestore.com/","collection":"mtgSinglesAbyssgamestore"},
    "silvergoblin":{"url":"https://silvergoblin.cards/","collection":"mtgSinglesSilvergoblin"},
    "crypt":{"url":"https://cryptmtg.com/","collection":"mtgSinglesCryptmtg"},
    "northofexile":{"url":"https://northofexilegames.com/","collection":"mtgSinglesNorthofexilegames"},
    "four01":{"url":"https://store.401games.ca/","collection":"mtgSingles401games"},
    "hairyt":{"url":"https://hairyt.com/","collection":"mtgSinglesHairyt"},
    "omg":{"url":"https://omggames.ca/","collection":"mtgSinglesOmggames"},
    "kesselrun":{"url":"https://kesselrungames.ca/","collection":"mtgSinglesKesselrungames"},
    "reddragon":{"url":"https://red-dragon.ca/","collection":"mtgSinglesReddragon"},
    "houseofcards":{"url":"https://houseofcards.ca/","collection":"mtgSinglesHouseofcards"},
    "taps":{"url":"https://tapsgames.com/","collection":"mtgSinglesTapsgames"},
    "pandorasboox":{"url":"https://www.pandorasboox.ca/","collection":"mtgSinglespandorasboox"},
    "timevault":{"url":"https://thetimevault.ca/","collection":"mtgSinglesThetimeVault"},
    "eastridge":{"url":"https://ergames.ca/","collection":"mtgSinglesErgames"},
    "upnorth":{"url":"https://www.upnorthgames.ca/","collection":"mtgSinglesUpnorthgames"},
    "waypoint":{"url":"https://waypointgames.ca/","collection":"mtgSinglesWaypointgames"},
    "skyfox":{"url":"https://skyfoxgames.com/","collection":"mtgSinglesSkyfoxgames"},
    "nerdzcafe":{"url":"https://www.nerdzcafe.com/","collection":"mtgSinglesNerdzcafe"},
    "outofthebox":{"url":"https://outoftheboxtcg.com/","collection":"mtgSinglesOutoftheboxtcg"},
    "blackknight":{"url":"https://blackknightgames.ca/","collection":"mtgSinglesBlackknightgames"},
    "bordercity":{"url":"https://bordercitygames.ca/","collection":"mtgSinglesBordercitygames"},
    "everythinggames":{"url":"https://everythinggames.ca/","collection":"mtgSinglesEverythinggames"},
    "enterthebattlefield":{"url":"https://enterthebattlefield.ca/","collection":"mtgSinglesEnterthebattlefield"},
    "fantasyforged":{"url":"https://fantasyforged.ca/","collection":"mtgSinglesFantasyForged"},
    "dragoncards":{"url":"https://tcg.dragoncardsandgames.com/","collection":"mtgSinglesDragoncards"},

}

def formatPrice(price):
    price = price.replace("$", "")
    price = price.replace(",", "")
    return float(price)

# Delay Information
# Upon first rate limitation it will rotated to the next proxy within 5 seconds
# Subsequent rate liitations will be 120 seconds each up to 6 times until it is terminated to prevent an infintie loop

def monitor( website, url, collectionName):
    #Proxy Info
    proxies=[]
    with open('./proxies.txt') as file:
        proxies = file.read().splitlines()
    proxies.insert(0,'')
    proxyCurrentIndex=0
    tempCollection = mydb[collectionName]

    #Webscrape Info    
    productTypeIdentifier="MTG Single"
    if url=="https://store.401games.ca/":
        productTypeIdentifier="Magic: The Gathering Singles"
    rateLimitedTimer=5
    pageNum=1
    eof=False
    cardList=[]
    
    NMFilter=['mint','nm','near']
    LPFilter=['light','slight','lp','pl','lightly']
    MPFilter=['moderate','moderately','mp']
    HPFilter=['heavy','heavily','hp']
    DMGFilter=['damage','damaged','dmg']
    SCNFilter=['scanned','scn','scan']
    
    #loop through every page until the end of file
    while eof == False:
        apiCallAttempts=0
        maxAPIAttempts=6
        r=None
        data=None
        
        # Rate limitation handling
        while apiCallAttempts <=maxAPIAttempts:
            try:
                if proxyCurrentIndex==0:
                    proxyUrl=""
                else:
                    ip,port,username,password = proxies[proxyCurrentIndex].split(":") # adjust this
                    proxyUrl=f'http://{username}:{password}@{ip}:{port}'
                proxy = {'http': proxyUrl, 'https': proxyUrl}


                r = requests.get(url+"products.json?limit=250&page="+str(pageNum),proxies=proxy)
                data = r.json()
                break
            except:
                print(url +" Failed to load page " + str(pageNum) + ", delaying for " + str(rateLimitedTimer) + " seconds. (ATTEMPT "+str(apiCallAttempts)+")"+" Proxy used: "+proxyUrl)
                time.sleep(rateLimitedTimer)
                apiCallAttempts+=1

                if apiCallAttempts >=3:
                    rateLimitedTimer=120
                else:
                    rateLimitedTimer=30
                if proxyCurrentIndex == len(proxies)-1:
                    proxyCurrentIndex=0
                else:
                    proxyCurrentIndex+=1

        if apiCallAttempts>maxAPIAttempts:
            print("Failed to retrieve data in " + str(apiCallAttempts) + " times. Function will not attempt to retrieve any further pages")
            break
        
        try:
            if len(data['products'])==0:
                eof=True
                break
        except: 
            print(f"Cannot access data['products'] for {url}products.json?limit=250&page={str(pageNum)}")
            eof=True
            break
        else:
            for product in data['products']:
                if product['product_type']==productTypeIdentifier or (url=="https://fantasyforged.ca/" and product['product_type']==""):
                    # Need to figure something out for title and set
                    foil = False
                    title=product['title']
                    set= ""
                    
                    if website == "four01":
                        set= product['vendor']
                        if '(Foil)' in title:
                            title = title.replace('(Foil)', '')
                            foil = True
                        title = title.split('(')[0].rstrip()
                        if ' - Borderless' in title:
                            title = title.split(' - Borderless')[0].rstrip()
                    else:
                        try:
                            set= product['title'].split("[")[1].split("]")[0].strip()
                        except:
                            set="Other"
                            print("strip error for: "+ website + " page: "+str(pageNum)+ " title: "+product['title'] +" handle: "+product['handle'])

                        if 'foil' in title.lower():
                            foil = True

                        title=product['title'].split("[")[0].strip()
                        title.split("(")[0].strip()
                    
                    productHandle= product['handle']
                    image=""

                    for images in product["images"]:
                        image=images['src']
                    for variant in product['variants']:
                        if variant['available']==True:
                            condition = re.split('-| ', variant['title'])[0].strip('+')
                            price =variant['price']

                            #variant title usually contains foil information
                            if website == "four01":
                                if "Foil" in variant['title'] or "foil" in variant['title'] :
                                    foil = True

                            if condition.lower() in NMFilter:
                                condition = "NM"
                            elif condition.lower() in LPFilter:
                                condition = "LP"
                            elif condition.lower() in MPFilter:
                                condition = "MP"
                            elif condition.lower() in HPFilter:
                                condition = "HP"
                            elif condition.lower() in DMGFilter:
                                condition = "DMG"
                            elif condition.lower() in SCNFilter:
                                condition = "SCN"

                            dict = {
                                "name":title,
                                "website":website,
                                "image": image,
                                "link":f"{url}products/{productHandle}",
                                "set":set,
                                "condition":condition,
                                "foil":foil,
                                "price": formatPrice(price),
                                "timestamp": time.time()
                            }
                            cardList.append(dict)
            print (url,"page: "+ str(pageNum))
        pageNum+=1
        if len(cardList) > 0:
            tempCollection.insert_many(cardList)
            cardList.clear()

    print("Finished Scraping: "+url +" page count: "+str(pageNum) +"document count: "+ str(tempCollection.count_documents({})))

    collection = mydb['mtgSingles']
    collection.delete_many({"website":website})
    if tempCollection.count_documents({}) > 0:
        collection.insert_many(tempCollection.find())
    tempCollection.drop()

    # instead of extending the list, we can just insert the list into the database
    #
    # first, delete all entries with the same website
    # collection = mydb['mtgSingles']
    # collection.delete_many({"website":website})
    # then, insert the new list
    # if len(cardList) > 0:
        # collection.insert_many(cardList)
    

# Create a list to save the results from all threads
start = time.time()

# Runs Each Site
threads = []
for key,value in supportedWebsites.items():
    t = threading.Thread(target=monitor, args=(key,value['url'],value['collection']))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("All threads finshed running")
print(f"Total minutes: {(time.time() - start)/60}")

# close the connection to MongoDB
myclient.close()

