import aiohttp
import asyncio
import concurrent.futures
import json
import os
import psycopg2
import re
from datetime import datetime
from pymongo import MongoClient
import redis
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from .search import SingleCardSearch # This should be moved to a utils or someth
from scrapersv2.base.HairyTScraper import HairyTScraper
from scrapersv2.base.AetherVaultScraper import AetherVaultScraper

router = APIRouter()

def fetchScrapers(cardName):
    return {
        "hairyt": HairyTScraper(cardName),
        "aethervault": AetherVaultScraper(cardName)
    }

async def get_page(session, scraper):
    # req = ( GET||POST, url, headers, data)
    if scraper.req[0] == "POST":
        print(f'POST request to {scraper.req[1]}')
        return {}
        async with session.post(scraper.req[1], headers=scraper.req[2], data=scraper.req[3]) as response:
            # set scraper.response to the response.text() and return it
            print("hairyT response awaiting")
            scraper.response = await response.json()
            print("hairyT response received")
            print(scraper.response)
            return scraper.response
    
    else:
        print(f'GET request to {scraper.req[1]}')
        async with session.get(scraper.req[1], headers=scraper.req[2], data=scraper.req[3]) as response:
            # set scraper.response to the response.text() and return it
            scraper.response = await response.text(encoding='utf-8')
            print("AetherVault response received")
            # print(scraper.response)
            return scraper.response
    
async def get_pages(session, scrapers):
    print("Getting pages")
    # construct requests for each scraper
    tasks = []
    for scraper in scrapers:
        tasks.append(asyncio.create_task(get_page(session, scraper)))
    print("tasks created")
    print(tasks)


    results = await asyncio.gather(*tasks)
    print("results gathered, running scrapers")
    # add the results to the scraper
    # for i in range(len(scrapers)):
    #     scrapers[i].response = results[i]
    # scrape the data
    scrapedResults = []
    for scraper in scrapers:
        scraper.scrape()
        scrapedResults.append(scraper.results)

    return scrapedResults

async def scrape(scrapers):
    print("scrape function: opening session")
    async with aiohttp.ClientSession() as session:
        data = await get_pages(session, scrapers)
        return data


@router.post("/single/")
async def search_sealed(request: SingleCardSearch, background_tasks: BackgroundTasks):
    # create all the scrapers
    scraperMap = fetchScrapers(request.cardName)
    try:
        if "all" in request.websites:
            scrapers = scraperMap.values()
        else:
            scrapers = [scraperMap[website] for website in request.websites]
    except KeyError:
        return {"error": "Invalid website provided"}
    
    # get a list of all the urls to scrape
    urls = []
    for scraper in scrapers:
        urls.append(scraper.url)
    
    results = await scrape(scrapers)
    print(results)

    return {"results": results}


