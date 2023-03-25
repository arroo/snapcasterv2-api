from fastapi import APIRouter
import os
import psycopg2
import pymongo
import redis
import re
from datetime import datetime, timedelta, timezone

rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)
router = APIRouter()

@router.get("/popular_cards/")
def popular_cards():
    # connect to pg
    conn = psycopg2.connect(
        dbname=os.environ['PG_DB'],
        user=os.environ['PG_USER'],
        password=os.environ['PG_PASSWORD'],
        host=os.environ['PG_HOST'],
        port=os.environ['PG_PORT']
    )
    cur = conn.cursor()

    # check all search entries where query_type = 'single'
    cur.execute(
        """
        SELECT query, timestamp  FROM search WHERE query_type = 'single';
        """
    )
    rows = cur.fetchall()
    # CLOSE CONNECTION
    cur.close()
    conn.close()

    allTimeCardDict = {}
    for row in rows:
        if row[0].lower() in allTimeCardDict:
            allTimeCardDict[row[0].lower()] += 1
        else:
            allTimeCardDict[row[0].lower()] = 1

    sorted_cards = sorted(allTimeCardDict.items(), key=lambda x: x[1], reverse=True)
    topAllTimeQueries = sorted_cards[:10]
    
    # get the top 20 cards from the last 30 days
    monthlyCardDict = {}
    for row in rows:
        # covert the timestamp (2022-10-24 18:10:03) to a datetime object and compare it to the current time
        if datetime.now() - datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') < timedelta(days=30):
            if row[0].lower() in monthlyCardDict:
                monthlyCardDict[row[0].lower()] += 1
            else:
                monthlyCardDict[row[0].lower()] = 1
    
    topMonthlyQueries = sorted(monthlyCardDict.items(), key=lambda x: x[1], reverse=True)[:10]

    weeklyCardDict = {}
    for row in rows:
        # covert the timestamp (2022-10-24 18:10:03) to a datetime object and compare it to the current time
        if datetime.now() - datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') < timedelta(days=7):
            if row[0].lower() in weeklyCardDict:
                weeklyCardDict[row[0].lower()] += 1
            else:
                weeklyCardDict[row[0].lower()] = 1
    topWeeklyQueries = sorted(weeklyCardDict.items(), key=lambda x: x[1], reverse=True)[:10]

    # Now we need to connect to mongoDB, and get the card image, card name, and the most recent price entry from the card
    mongoClient = pymongo.MongoClient(os.environ['MONGO_URI'])
    db = mongoClient["snapcaster"]
    cardCollection = db["cards"]
    priceEntryCollection = db["price_entry"]


    def get_card_info(card_names):
        card_info_list = []
        for card_name in card_names:
            try:
                card = cardCollection.find_one(
                    {"name": {"$regex": f"^{card_name}$", "$options": "i"}},
                    sort=[("name", pymongo.ASCENDING), ("name", pymongo.ASCENDING)]
                )

                if card:
                    oracle_id = card["oracle_id"]
                    most_recent_price_entry = priceEntryCollection.find_one(
                        {"oracle_id": oracle_id},
                        sort=[("date", pymongo.DESCENDING)]
                    )
                    card_info_list.append({
                        "name": card["name"],
                        "image_url": card["image_uris"]["png"],
                        "price": most_recent_price_entry["min"] if most_recent_price_entry else None
                    })
            except Exception as e:
                print(f'Error: {e} for card {card_name}.')
                print(card)

        return card_info_list
    
    topAllTimeCardInfo = get_card_info([card[0] for card in topAllTimeQueries])
    topMonthlyCardInfo = get_card_info([card[0] for card in topMonthlyQueries])
    topWeeklyCardInfo = get_card_info([card[0] for card in topWeeklyQueries])


    
    

    
    mongoClient.close()

    return {
        "allTime":  topAllTimeCardInfo,
        "monthly": topMonthlyCardInfo,
        "weekly": topWeeklyCardInfo
    }

    

@router.get("/autocomplete/{query}/")
def autocomplete(query: str):

    if rd.exists("sets"):
        print("cache hit")
        # get the list of sets from redis
        sets = rd.hgetall("sets")
        # return the value of the first 10 keys that match the query in lowercase

        # we want to return the value of the key, not the key itself

        results = []
        for key in sets:
            if re.match(query.lower(), key.decode("utf-8")):
                results.append(sets[key].decode("utf-8"))
            if len(results) == 10:
                break
        
        return results

    else: # if redis does not have the "sets" key
        # connect to postgres
        # set the cache to expire in 1 day


        conn = psycopg2.connect(
            dbname=os.environ['PG_DB'],
            user=os.environ['PG_USER'],
            password=os.environ['PG_PASSWORD'],
            host=os.environ['PG_HOST'],
            port=os.environ['PG_PORT']
        )
        cur = conn.cursor()

        cur.execute(
            """
            SELECT name FROM set;
            """
        )

        # add the list of sets to redis
        sets = cur.fetchall()
        # we want key:value to be "dominaria united":"Dominaria United"
        # so we can do a case insensitive search later
        # store this as a redis hash
        for set in sets:
            rd.hset("sets", set[0].lower(), set[0])

        # set the cache to expire in 1 day
        rd.expire("sets", 86400)
        cur.close()
        conn.close()

        sets = rd.hgetall("sets")
        results = []
        for key in sets:
            if re.match(query.lower(), key.decode("utf-8")):
                results.append(sets[key].decode("utf-8"))
            if len(results) == 10:
                break
    

        return sets

