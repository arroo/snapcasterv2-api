"""
roundPriceEntryStats.py

This is a script to round the price entry stats to two decimal places. This is done by 
default when the price entry is created, but this script is for the price entries that 
were created before this was implemented.

"""
from pymongo import MongoClient
import os
import dotenv

dotenv.load_dotenv()

mongoClient = MongoClient(os.environ["MONGO_URI"])
db = mongoClient["snapcaster"]

price_entries = list(db.price_entry.find({}))

for entry in price_entries:
    # check if there is max, min, avg, foil_max, foil_min, foil_avg
    # if yes, round them to two decimal places and update the entry
    # if no, skip it
    if "max" in entry:
        entry["max"] = round(entry["max"], 2)
        entry["min"] = round(entry["min"], 2)
        entry["avg"] = round(entry["avg"], 2)
        if "foil_max" in entry:
            entry["foil_max"] = round(entry["foil_max"], 2)
            entry["foil_min"] = round(entry["foil_min"], 2)
            entry["foil_avg"] = round(entry["foil_avg"], 2)

        db.price_entry.update_one({"_id": entry["_id"]}, {"$set": entry})

print("done")
mongoClient.close()
