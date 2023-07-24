import requests
from bs4 import BeautifulSoup
import concurrent.futures
from playwright.sync_api import sync_playwright

def freeProxyListProxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('tbody')
    proxies = []
    for row in table:
        if row.find_all('td')[4].text == 'elite proxy':
            proxy = ':'.join([row.find_all('td')[0].text, row.find_all('td')[1].text])
            proxies.append(proxy)
        else:
            pass

    return proxies

def scrapingAntProxies():
    url = 'https://scrapingant.com/free-proxies/'
    proxies = []
    
    # Use playwright to load the page
    with sync_playwright() as p:
        browser = p.chromium.launch() # Launch a new browser
        context = browser.new_context() # Create a new browser context
        page = context.new_page() # Create a new page in this context
        page.goto(url) # Go to the url
        page.wait_for_selector('table') # Wait for the table to load
        content = page.content() # Get page content after JS is loaded
        
        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('tbody')

        for row in table.find_all('tr'):
            tds = row.find_all('td')
        
            if tds and tds[2].text.strip() == 'HTTP':
                proxy = ':'.join([tds[0].text.strip(), tds[1].text.strip()])
                proxies.append(proxy)
        
        # Close browser context and browser
        context.close()
        browser.close()
    
    return proxies


def getProxiesFromFile(filename):
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f]
    return proxies

def checkProxy(proxy):
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
        r = requests.post('https://portal.binderpos.com/api/v1/products', json=body, headers=headers, proxies=proxies, timeout=5)
        # r = requests.get('https://shopify.com/', proxies=proxies, timeout=5)
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
    # freeProxyList = freeProxyListProxies()
    # # scrapingAnt = scrapingAntProxies()

    txtProxyList = getProxiesFromFile('utils/proxies.txt')

    proxyList = txtProxyList

    # for p in scrapingAnt:
    #     proxyList.append(p)

    # for p in freeProxyList:
    #     proxyList.append(p)

    print(f'Got {len(proxyList)} proxies')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(checkProxy, proxyList)

    return

if __name__ == '__main__':
    main()

