from fastapi import APIRouter, HTTPException
import os
import redis
from pymongo import MongoClient
from typing import List
from pydantic import BaseModel

rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)
router = APIRouter()
mongoClient = MongoClient(os.environ['MONGO_URI'])
db = mongoClient['snapcaster']

# define pydantic model for the request body
class PriceSearch(BaseModel):
    cardName: str

@router.post("/")
def getPriceHistory(request: PriceSearch) -> List[dict]:
    # remove any %2F and replace with /
    query = request.cardName
    # Find the card document with the closest 'name' to the query
    card_doc = db.cards.find_one({'name': {'$regex': query, '$options': 'i'}}, sort=[('name', 1)])
    if not card_doc:
        raise HTTPException(status_code=404, detail="Card not found")
    # print("getting price entries")
    # Use the 'oracle_id' field to query the price_entry collection
        # Convert the MongoDB ObjectId to string for each price entry

    price_entries = list(db.price_entry.find({'oracle_id': card_doc['oracle_id']}))
    for entry in price_entries:
        entry['_id'] = str(entry['_id'])
        
    # Add the card_doc['image_uris']['png'] field to each price entry
    for entry in price_entries:
        entry['image'] = card_doc['image_uris']['png']
        # round the "date" field to a readable "MM/DD/YYYY" format
        entry['date'] = entry['date'].strftime("%m/%d/%Y")

    return price_entries

