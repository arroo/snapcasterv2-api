from fastapi import APIRouter
import os
import psycopg2
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
    topAllTime = sorted_cards[:20]
    
    # get the top 20 cards from the last 30 days
    monthlyCardDict = {}
    for row in rows:
        # covert the timestamp (2022-10-24 18:10:03) to a datetime object and compare it to the current time
        if datetime.now() - datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') < timedelta(days=30):
            if row[0].lower() in monthlyCardDict:
                monthlyCardDict[row[0].lower()] += 1
            else:
                monthlyCardDict[row[0].lower()] = 1
    
    topMonthly = sorted(monthlyCardDict.items(), key=lambda x: x[1], reverse=True)[:20]

    weeklyCardDict = {}
    for row in rows:
        # covert the timestamp (2022-10-24 18:10:03) to a datetime object and compare it to the current time
        if datetime.now() - datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') < timedelta(days=7):
            if row[0].lower() in weeklyCardDict:
                weeklyCardDict[row[0].lower()] += 1
            else:
                weeklyCardDict[row[0].lower()] = 1
    topWeekly = sorted(weeklyCardDict.items(), key=lambda x: x[1], reverse=True)[:20]


    return {
        "allTime": topAllTime,
        "monthly": topMonthly,
        "weekly": topWeekly
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

