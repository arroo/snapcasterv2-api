from fastapi import APIRouter
import os
import psycopg2
import redis
import re

rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)
router = APIRouter()

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

