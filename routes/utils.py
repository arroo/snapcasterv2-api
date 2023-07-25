from fastapi import APIRouter
import os
import psycopg2
import pymongo
import redis
import re
from datetime import datetime, timedelta, timezone
import json

rd = redis.Redis(
    host=os.environ["RD_HOST"],
    port=os.environ["RD_PORT"],
    password=os.environ["RD_PASSWORD"],
    db=0,
)
router = APIRouter()


@router.get("/popular_cards/")
def popular_cards():
    # First check cache
    # When retrieving the data from Redis, parse the JSON string back to a list of dictionaries
    if rd.exists("popular_cards"):
        popular_cards_cache = {
            k.decode(): v for k, v in rd.hgetall("popular_cards").items()
        }
        return {
            "allTime": json.loads(popular_cards_cache.get("allTime", "[]")),
            "monthly": json.loads(popular_cards_cache.get("monthly", "[]")),
            "weekly": json.loads(popular_cards_cache.get("weekly", "[]")),
        }

    # if cache is empty, connect to postgres and get the top 10 cards from the last 30 days
    # connect to pg
    conn = psycopg2.connect(
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ["PG_PORT"],
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
        if datetime.now() - datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") < timedelta(
            days=30
        ):
            if row[0].lower() in monthlyCardDict:
                monthlyCardDict[row[0].lower()] += 1
            else:
                monthlyCardDict[row[0].lower()] = 1

    topMonthlyQueries = sorted(
        monthlyCardDict.items(), key=lambda x: x[1], reverse=True
    )[:10]

    weeklyCardDict = {}
    for row in rows:
        # covert the timestamp (2022-10-24 18:10:03) to a datetime object and compare it to the current time
        if datetime.now() - datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") < timedelta(
            days=7
        ):
            if row[0].lower() in weeklyCardDict:
                weeklyCardDict[row[0].lower()] += 1
            else:
                weeklyCardDict[row[0].lower()] = 1
    topWeeklyQueries = sorted(weeklyCardDict.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]

    # Now we need to connect to mongoDB, and get the card image, card name, and the most recent price entry from the card
    mongoClient = pymongo.MongoClient(os.environ["MONGO_URI"])
    db = mongoClient["snapcaster"]
    cardCollection = db["cards"]
    priceEntryCollection = db["price_entry"]

    def get_card_info(card_names):
        card_info_list = []
        for card_name in card_names:
            if "wrenn and six" in card_name.lower():
                print("Wrenn and Six")
                print(f"Card name: {card_name}")
            try:
                # This will return the first card that matches the regex
                # card = cardCollection.find_one(
                #     {"name": {"$regex": f"^{card_name}$", "$options": "i"}},
                #     sort=[("name", pymongo.ASCENDING), ("name", pymongo.ASCENDING)]
                # )

                # Updated MongoDB query and sorting to prioritize exact card name matches
                card = cardCollection.find_one(
                    {"name": {"$regex": f"^{card_name}$", "$options": "i"}},
                    sort=[("name", pymongo.ASCENDING), ("name", pymongo.ASCENDING)],
                )

                if not card:
                    print("Second attempt")
                    card = cardCollection.find_one(
                        {"name": {"$regex": card_name, "$options": "i"}},
                        sort=[("name", pymongo.ASCENDING), ("name", pymongo.ASCENDING)],
                    )
                else:
                    print("First attempt card found")
                    print(card["name"])

                if card:
                    oracle_id = card["oracle_id"]
                    most_recent_price_entry = priceEntryCollection.find_one(
                        {"oracle_id": oracle_id}, sort=[("date", pymongo.DESCENDING)]
                    )
                    card_info_list.append(
                        {
                            "name": card["name"],
                            "image_url": card["image_uris"]["png"],
                            "price": most_recent_price_entry["min"]
                            if most_recent_price_entry
                            else None,
                        }
                    )
            except Exception as e:
                print(f"Error: {e} for card {card_name}.")
                print(card)

        return card_info_list

    topAllTimeCardInfo = get_card_info([card[0] for card in topAllTimeQueries])
    topMonthlyCardInfo = get_card_info([card[0] for card in topMonthlyQueries])
    topWeeklyCardInfo = get_card_info([card[0] for card in topWeeklyQueries])

    mongoClient.close()
    # add the results to redis
    rd.hmset(
        "popular_cards",
        {
            "allTime": json.dumps(topAllTimeCardInfo),
            "monthly": json.dumps(topMonthlyCardInfo),
            "weekly": json.dumps(topWeeklyCardInfo),
        },
    )
    rd.expire("popular_cards", 86400)  # expire in 1 day

    return {
        "allTime": topAllTimeCardInfo,
        "monthly": topMonthlyCardInfo,
        "weekly": topWeeklyCardInfo,
    }


@router.get("/autocomplete/{query}/")
def autocomplete(query: str):
    if rd.exists("sets"):
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

    else:  # if redis does not have the "sets" key
        # connect to postgres
        # set the cache to expire in 1 day

        conn = psycopg2.connect(
            dbname=os.environ["PG_DB"],
            user=os.environ["PG_USER"],
            password=os.environ["PG_PASSWORD"],
            host=os.environ["PG_HOST"],
            port=os.environ["PG_PORT"],
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


@router.get("/popular_sealed/")
def popular_sealed():
    # First check cache
    # When retrieving the data from Redis, parse the JSON string back to a list of dictionaries
    if rd.exists("popular_sealed"):
        popular_sealed_cache = {
            k.decode(): v for k, v in rd.hgetall("popular_sealed").items()
        }
        return {
            "allTime": json.loads(popular_sealed_cache.get("allTime", "[]")),
            "monthly": json.loads(popular_sealed_cache.get("monthly", "[]")),
            "weekly": json.loads(popular_sealed_cache.get("weekly", "[]")),
        }

    # if cache is empty, connect to postgres and get the top 10 cards from the last 30 days
    # connect to pg
    conn = psycopg2.connect(
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ["PG_PORT"],
    )
    cur = conn.cursor()

    # Define a function to find the closest set name
    def find_closest_set_name(query):
        cur.execute(
            """
            SELECT name FROM set WHERE LOWER(name) LIKE %s ORDER BY similarity(LOWER(name), %s) DESC, name LIMIT 1;
        """,
            (f"%{query}%", query.lower()),
        )
        result = cur.fetchone()
        return result[0] if result else None

    # Match the query counts to the closest name in the set table
    def match_sets_with_names(top_queries):
        matched_sets = []
        for query, count in top_queries:
            closest_set_name = find_closest_set_name(query)
            if closest_set_name:
                matched_sets.append({"name": closest_set_name, "count": count})
        return matched_sets

    # check all search entries where query_type = 'single'
    cur.execute(
        """
        SELECT query, timestamp  FROM search WHERE query_type = 'sealed';
        """
    )
    rows = cur.fetchall()

    allTimeSetDict = {}
    for row in rows:
        if row[0].lower() in allTimeSetDict:
            allTimeSetDict[row[0].lower()] += 1
        else:
            allTimeSetDict[row[0].lower()] = 1

    sorted_sets = sorted(allTimeSetDict.items(), key=lambda x: x[1], reverse=True)
    topAllTimeQueries = sorted_sets[:10]

    # get the top 20 cards from the last 30 days
    monthlySetDict = {}
    for row in rows:
        # covert the timestamp (2022-10-24 18:10:03) to a datetime object and compare it to the current time
        if datetime.now() - datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") < timedelta(
            days=30
        ):
            if row[0].lower() in monthlySetDict:
                monthlySetDict[row[0].lower()] += 1
            else:
                monthlySetDict[row[0].lower()] = 1

    topMonthlyQueries = sorted(
        monthlySetDict.items(), key=lambda x: x[1], reverse=True
    )[:10]

    weeklySetDict = {}
    for row in rows:
        # covert the timestamp (2022-10-24 18:10:03) to a datetime object and compare it to the current time
        if datetime.now() - datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") < timedelta(
            days=7
        ):
            if row[0].lower() in weeklySetDict:
                weeklySetDict[row[0].lower()] += 1
            else:
                weeklySetDict[row[0].lower()] = 1
    topWeeklyQueries = sorted(weeklySetDict.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]

    # Now we need to connect to postgres again and match all the query counts to the closest name in the set table
    # Get matched set names for all time, monthly, and weekly top queries
    all_time_matched_sets = match_sets_with_names(topAllTimeQueries)
    monthly_matched_sets = match_sets_with_names(topMonthlyQueries)
    weekly_matched_sets = match_sets_with_names(topWeeklyQueries)

    # Now we need to get the cheapest product from sealed_prices with a name containing the set name
    # and return the set name, and the cheapest product image, name and price
    # Define a function to get the cheapest product for each set
    def find_cheapest_product(set_name):
        cur.execute(
            """
            SELECT name, image, price
            FROM sealed_prices
            WHERE LOWER(name) LIKE %s
            ORDER BY price ASC
            LIMIT 1;
        """,
            (f"%{set_name.lower()}%",),
        )
        result = cur.fetchone()
        return (
            {
                "product_name": result[0],
                "product_image": result[1],
                "product_price": result[2],
            }
            if result
            else None
        )

    def update_sets_with_products(matched_sets):
        updated_sets = []
        for set_info in matched_sets:
            set_name = set_info["name"]
            cheapest_product = find_cheapest_product(set_name)
            if (
                cheapest_product
                and cheapest_product["product_image"]
                and cheapest_product["product_price"]
            ):
                set_info.update(cheapest_product)
                updated_sets.append(set_info)
        return updated_sets

    # Update all time, monthly, and weekly matched sets with product information and filter out sets with missing images or prices
    all_time_matched_sets = update_sets_with_products(all_time_matched_sets)
    monthly_matched_sets = update_sets_with_products(monthly_matched_sets)
    weekly_matched_sets = update_sets_with_products(weekly_matched_sets)

    # Cache the results in Redis
    rd.hset("popular_sealed", "allTime", json.dumps(all_time_matched_sets))
    rd.hset("popular_sealed", "monthly", json.dumps(monthly_matched_sets))
    rd.hset("popular_sealed", "weekly", json.dumps(weekly_matched_sets))
    rd.expire("popular_sealed", 86400)  # Set cache to expire in 1 hour

    # Close cursor and connection
    cur.close()
    conn.close()

    return {
        "allTime": all_time_matched_sets,
        "monthly": monthly_matched_sets,
        "weekly": weekly_matched_sets,
    }


@router.get("/unsubscribe/{uid}/")
def unsubscribe(uid: str):
    success = update_email_enabled(uid, False)

    if success:
        return {"message": "Successfully unsubscribed."}
    else:
        return {"error": "Failed to unsubscribe. Invalid user ID."}, 400


def update_email_enabled(user_id: str, email_enabled: bool):
    # This is a placeholder function. You need to implement this function
    # to update the emailEnabled field in your database for the given user_id.
    success = True
    try:
        conn = psycopg2.connect(
            dbname=os.environ["PG_DB"],
            user=os.environ["PG_USER"],
            password=os.environ["PG_PASSWORD"],
            host=os.environ["PG_HOST"],
            port=os.environ["PG_PORT"],
        )
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE users
            email_enabled = %s
            WHERE id = %s
            """,
            (email_enabled, user_id),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(e)
        success = False

    conn.close()

    return success
