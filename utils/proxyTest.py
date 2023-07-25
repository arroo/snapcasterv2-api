import requests
import concurrent.futures

def getProxiesFromFile(filename):
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f]
    return proxies

def checkProxy(proxy):
    # This is the request we send to Exor games, but it's basically identical for all the shopify sites.
    body={
        "storeUrl":"the-mythic-store.myshopify.com",
        "game":"mtg",
        "strict":None,
        "sortTypes":[{"type":"price","asc":False,"order":1}],
        "variants":None,
        "title":"sol ring",
        "priceGreaterThan":0,
        "priceLessThan":None,
        "instockOnly":True,
        "limit":30,
        "offset":0
    }
    headers={
        'authority': 'portal.binderpos.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/json; charset=UTF-8',
        'origin': 'https://themythicstore.com',
        'pragma': 'no-cache',
        'referer': 'https://themythicstore.com/',
        'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36'
        }

    

    proxy_parts = proxy.split(":")
    ip_address = proxy_parts[0]
    port = proxy_parts[1]
    username = proxy_parts[2]
    password = proxy_parts[3]

    proxies = {
        "http" :"http://{}:{}@{}:{}".format(username,password,ip_address,port),
        "https":"http://{}:{}@{}:{}".format(username,password,ip_address,port),
    }
    try: 
        r = requests.post('https://portal.binderpos.com/external/shopify/products/forStore', json=body, headers=headers, proxies=proxies, timeout=5) # this doesn't work and returns 404s
        # r = requests.get('https://shopify.com/', proxies=proxies, timeout=5) # this works and returns 200s
        if r.status_code == 200:
            print(proxy)
        else:
            print(f"Bad proxy: {proxy}")
            print(r.status_code)
    except requests.ConnectionError:
        print(f"Connection Error with proxy: {proxy}")
    except Exception as e:
        print(f"Unexpected error with proxy {proxy}: {e}")
    
    except requests.ConnectionError:
        pass


    return proxy

def main():
    proxyList = getProxiesFromFile('utils/proxies.txt')

    print(f'Got {len(proxyList)} proxies')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(checkProxy, proxyList)

    return

if __name__ == '__main__':
    main()

