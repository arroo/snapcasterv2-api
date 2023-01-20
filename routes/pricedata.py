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
    print("card_name: ", card_name)
    conn = psycopg2.connect(
        dbname=os.environ['PG_DB'],
        user=os.environ['PG_USER'],
        password=os.environ['PG_PASSWORD'],
        host=os.environ['PG_HOST'],
        port=os.environ['PG_PORT']
    )
    cur = conn.cursor()
    # using card_name, find oracle_id for the card from the cards table
    # ensure to compare card names in lowercase
    # look up the oracle_id in the price_entry table
    cur.execute(
        """
        SELECT * FROM price_entry WHERE oracle_id = (
            SELECT oracle_id FROM cards WHERE LOWER(name) = LOWER(%s)
        )

        """,
        (card_name,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()