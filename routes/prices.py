from fastapi import APIRouter, HTTPException
import os
import psycopg2
import redis
import re
from pymongo import MongoClient
from typing import List

rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)
router = APIRouter()
mongoClient = MongoClient(os.environ['MONGO_URI'])
db = mongoClient['snapcaster']


@router.get("/{query}/")
def getPriceHistory(query: str) -> List[dict]:
    # Find the card document with the closest 'name' to the query
    card_doc = db.cards.find_one({'name': {'$regex': query, '$options': 'i'}}, sort=[('name', 1)])
    if not card_doc:
        raise HTTPException(status_code=404, detail="Card not found")

    # Use the 'oracle_id' field to query the price_entry collection
    price_entries = list(db.price_entry.find({'oracle_id': card_doc['oracle_id']}))

    # Convert the MongoDB ObjectId to string for each price entry
    for entry in price_entries:
        entry['_id'] = str(entry['_id'])

    return price_entries

