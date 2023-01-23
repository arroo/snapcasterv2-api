from pydantic import BaseModel
from db.models import Search
from db.database import engine, SQLModel, Session
from datetime import datetime
import psycopg2
import os
from fastapi import BackgroundTasks, APIRouter


router = APIRouter()

# get request where query params are the card name


@router.get("/card/{card_name}")
async def get_card(card_name: str):
    conn = psycopg2.connect(
        dbname=os.environ['PG_DB'],
        user=os.environ['PG_USER'],
        password=os.environ['PG_PASSWORD'],
        host=os.environ['PG_HOST'],
        port=os.environ['PG_PORT']
    )
    cur = conn.cursor()
    # The regexp_replace(cards.name, '[^[:alpha:]]', '', 'g') will remove all
    # non-alphabetic characters from the cards.name column before it is passed to the LOWER function
    cur.execute(
        """
        SELECT date, avg(price) as avg_price, max(price) as max_price, min(price) as min_price, cards.name as card_name, cards.image_uris->'normal' as image_uri
        FROM (
            SELECT date, unnest(array_agg(price::double precision)) as price, oracle_id
            FROM (
                SELECT date, unnest(string_to_array(price_list, ',')) as price, oracle_id
                FROM price_entry
            ) as prices
            GROUP BY date, price, oracle_id
        ) as prices
        JOIN cards ON prices.oracle_id = cards.oracle_id
        WHERE LOWER(regexp_replace(cards.name, '[^[:alpha:]]', '', 'g')) = LOWER(regexp_replace(%s, '[^[:alpha:]]', '', 'g'))
        GROUP BY date, cards.name, image_uri
        ORDER BY date;
        """,
        (card_name,),
    )
    rows = cur.fetchall()

    try:
        cardName = rows[0][4]
        imageUri = rows[0][5]
        price_data = []
        for row in rows:
            price_data.append({
                "date": row[0],
                "avg_price": row[1],
                "max_price": row[2],
                "min_price": row[3]
            })

    except:
        cur.close()
        conn.close()
        cardName = card_name
        imageUri = ""
        price_data = []
        # return {
        #     "error": "Card not found"
        # }

    # results should contain price data, and card info
    results = {
        "card_name": cardName,
        "image_uri": imageUri,
        "price_data": price_data
    }

    cur.close()
    conn.close()
    return results
