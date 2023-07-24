import requests
import concurrent.futures

def getProxiesFromFile(filename):
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f]
    return proxies

def checkProxy(proxy):
    # This is the request we send to Exor games, but it's basically identical for all the shopify sites.
    headers={
        "authority": "portal.binderpos.com",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://exorgames.com",
        "pragma": "no-cache",
        "referer": "https://exorgames.com/",
        "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    body={
        "storeUrl": "most-wanted-ca.myshopify.com",
        "game": "mtg",
        "strict": None,
        "sortTypes": [
            {
                "type": "price",
                "asc": False,
                "order": 1
            }
        ],
        "variants": None,
        "title": "Fblthp the Lost",
        "priceGreaterThan": 0,
        "priceLessThan": None,
        "instockOnly": True,
        "limit": 18,
        "offset": 0
    }
    
    host, port, user, password = proxy.split(":")
    proxy_url = f'http://{user}:{password}@{host}:{port}'

    proxies = {'http': proxy_url, 'https': proxy_url}
    try: 
        r = requests.post('https://portal.binderpos.com/api/v1/products', json=body, headers=headers, proxies=proxies, timeout=5) # this doesn't work and returns 404s
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

