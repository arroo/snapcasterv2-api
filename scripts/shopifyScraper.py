import dotenv
import requests
import time
import pymongo
import threading
import re
import os
from pymongo.errors import PyMongoError


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
    "kingdomtitans":{"url":"https://kingdomtitans.cards/"},
    "fanofthesport":{"url":"https://fanofthesport.com/"},
    "levelup":{"url":"https://levelupgames.ca/"},
    "gamebreakers":{"url":"https://gamebreakers.ca/"},
    "gameknight":{"url":"https://gameknight.ca/"},
    "mythicstore":{"url":"https://themythicstore.com/"},
    "hfx":{"url":"https://hfxgames.com/"},
    "vortexgames":{"url":"https://vortexgames.ca/"},
    "gamezilla":{"url":"https://gamezilla.ca/"},
    "exorgames":{"url":"https://exorgames.com/"},
    "chimera":{"url":"https://chimeragamingonline.com/"},
    "abyss":{"url":"https://www.abyssgamestore.com/"},
    "silvergoblin":{"url":"https://silvergoblin.cards/"},
    "crypt":{"url":"https://cryptmtg.com/"},
    "northofexile":{"url":"https://northofexilegames.com/"},
    "four01":{"url":"https://store.401games.ca/"},
    "hairyt":{"url":"https://hairyt.com/"},
    "omg":{"url":"https://omggames.ca/"},
    "kesselrun":{"url":"https://kesselrungames.ca/"},
    "reddragon":{"url":"https://red-dragon.ca/"},
    "houseofcards":{"url":"https://houseofcards.ca/"},
    "taps":{"url":"https://tapsgames.com/"},
    "pandorasboox":{"url":"https://www.pandorasboox.ca/"},
    "timevault":{"url":"https://thetimevault.ca/"},
    "eastridge":{"url":"https://ergames.ca/"},
    "upnorth":{"url":"https://www.upnorthgames.ca/"},
    "waypoint":{"url":"https://waypointgames.ca/"},
    "skyfox":{"url":"https://skyfoxgames.com/"},
    "nerdzcafe":{"url":"https://www.nerdzcafe.com/"},
    "outofthebox":{"url":"https://outoftheboxtcg.com/"},
    "blackknight":{"url":"https://blackknightgames.ca/"},
    "bordercity":{"url":"https://bordercitygames.ca/"},
    "everythinggames":{"url":"https://everythinggames.ca/"},
    "enterthebattlefield":{"url":"https://enterthebattlefield.ca/"},
    "fantasyforged":{"url":"https://fantasyforged.ca/"},
    "dragoncards":{"url":"https://tcg.dragoncardsandgames.com/"},
    "untouchables":{"url":"https://untouchables.ca/"},
    "darkfoxtcg":{"url":"https://www.darkfoxtcg.com/"},
}

def formatPrice(price):
    price = price.replace("$", "")
    price = price.replace(",", "")
    return float(price)

# Delay Information
# Upon first rate limitation it will rotated to the next proxy within 5 seconds
# Subsequent rate liitations will be 120 seconds each up to 6 times until it is terminated to prevent an infintie loop

def monitor( website, url):
    #Proxy Info
    proxies=[]
    with open('/home/hydrogen/snapcasterv2-api/proxies.txt') as file:
        proxies = file.read().splitlines()
    proxies.insert(0,'')
    proxyCurrentIndex=0
    tempCollection = mydb["mtgSinglesTemp"]

    #Webscrape Info    
    productTypeIdentifier="MTG Single"
    if url=="https://store.401games.ca/":
        productTypeIdentifier="Magic: The Gathering Singles"
    elif url=="https://untouchables.ca/":
        productTypeIdentifier="Singles"
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
                    elif website == "untouchables":
                        set = title.split("-")[0].strip()
                        if 'Foil' in title and 'Non Foil' not in title:
                            foil = True
                            title = title.replace('Foil', '')
                        

                        
                        
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
                            try:
                                
                                if website == "untouchables":
                                    try:
                                        condition = title.split('-')[4].strip()
                                    except:
                                        # in the event there is an issue with their manual input.
                                        condition = "N/A"
                                    title = title.split("-")[2].strip()

                                else:
                                    condition = re.split('-| ', variant['title'])[0].strip('+')
                                
                            except:
                                print("Error stripping condition.")
                                print(title)
                                condition = ""
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
            try:
                tempCollection.insert_many(cardList)
            except Exception as e:
                print("Error inserting into tempCollection: "+str(e))
                print(f"Details of exception: {e.args}")
            cardList.clear()

    print("Finished Scraping: "+url +" page count: "+str(pageNum) +"document count: "+ str(tempCollection.count_documents({})))

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
    t = threading.Thread(target=monitor, args=(key,value['url']))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

try:
    mydb["mtgSinglesTemp"].create_index([("name", pymongo.TEXT)])
    mydb["mtgSinglesTemp"].rename("mtgSingles", dropTarget=True)
    print("rename")
except PyMongoError as e:
    print(f"An error occurred while renaming the collection: {e}")
else:
    print("Collection renamed successfully.")

print("All threads finshed running")
print(f"Total minutes: {(time.time() - start)/60}")

# close the connection to MongoDB
myclient.close()

