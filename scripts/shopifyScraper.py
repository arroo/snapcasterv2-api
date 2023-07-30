import dotenv
import requests
import time
import pymongo
import threading
import re
import os
# Reads from proxies.txt: 1 proxy per line, no need to add "," at the end of each line
# - Henry

dotenv.load_dotenv()
MONGO_URI = os.environ["MONGO_URI"]

supportedWebsites = {
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
    "houseOfCards":{"url":"https://houseofcards.ca/","collection":"mtgSinglesHouseofcards"},
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
    "enterthebattlefield":{"url":"https://enterthebattlefield.ca/","collection":"mtgEnterthebattlefield"},
    "fantasyforged":{"url":"https://FantasyForged.ca/","collection":"mtgFantasyForged"}

}

# Delay Information
# Upon first rate limitation it will rotated to the next proxy within 5 seconds
# Subsequent rate liitations will be 35 seconds each up to 6 times until it is terminated to prevent an infintie loop

def monitor( website, url,collectionName):
    #Database Connection Info
    myclient = pymongo.MongoClient(MONGO_URI)
    mydb = myclient["shopify-inventory"]
    collection = mydb[collectionName]

    #Proxy Info
    proxies=[]
    with open('proxies.txt') as file:
        proxies = file.read().splitlines()
    proxies.insert(0,'')
    proxyCurrentIndex=0

    #Webscrape Info    
    productTypeIdentifier="MTG Single"
    if url=="https://store.401games.ca/":
        productTypeIdentifier="Magic: The Gathering Singles"
    rateLimitedTimer=5
    pageNum=1
    eof=False
    cardList=[]
    
    NMFilter=['Mint','NM','Near']
    LPFilter=['Light','Slightly','LP','Lightly']
    MPFilter=['Moderate','Moderately','MP']
    HPFilter=['Heavy','Heavily','HP']
    DMGFilter=['Damage','Damaged','DMG']
    
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
                    rateLimitedTimer=35
                else:
                    rateLimitedTimer=5
                if proxyCurrentIndex == len(proxies)-1:
                    proxyCurrentIndex=0
                else:
                    proxyCurrentIndex+=1

        if apiCallAttempts>maxAPIAttempts:
            print("Failed to retrieve data in " + str(apiCallAttempts) + " times. Function will not attempt to retrieve any further pages")
            break
        

        if len(data['products'])==0:
            eof=True
            break
        else:
            for product in data['products']:
                if product['product_type']==productTypeIdentifier:
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

                            if condition in NMFilter:
                                condition = "NM"
                            elif condition in LPFilter:
                                condition = "LP"
                            elif condition in MPFilter:
                                condition = "MP"
                            elif condition in HPFilter:
                                condition = "HP"
                            elif condition in DMGFilter:
                                condition = "DMG"

                            dict = {
                                "title":title,
                                "handle":productHandle,
                                "website":website,
                                "image": image,
                                "link":f"{url}products/{productHandle}",
                                "set":set,
                                "variantTitle":condition,
                                "foil":foil,
                                "price":price
                            }
                            cardList.append(dict)
            print (url,"page: "+ str(pageNum))
        pageNum+=1

    print("Finished Scraping: "+url +" page count: "+str(pageNum) +"document count: "+ str(len(cardList)))
    collection.delete_many({})
    if(len(cardList)>0):
        collection.insert_many(cardList)


#Runs Each Site
threads = []
for key,value in supportedWebsites.items():
    t = threading.Thread(target=monitor, args=(key,value['url'],value['collection']))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
print("All threads finshed running")
