from pymongo import MongoClient
import os
import dotenv

dotenv.load_dotenv()

mongoClient = MongoClient(os.environ['MONGO_URI'])
db = mongoClient['snapcaster']

# get all the price entries
price_entries = list(db.price_entry.find({}))

# for every price entry,
for entry in price_entries:
    # if the entry has a "max" field, skip it, it's already been updated
    if 'max' in entry:
        print("Skipping entry")
        continue

    print("Updating new entry")
    # get the price_list and calculate the max, avg, and min
    price_list = entry['price_list']
    # max is max of each object's .price field
    if len(price_list) == 0:
        # set all the values to 0
        max_price = 0
        min_price = 0
        avg_price = 0
        foil_max_price = 0
        foil_min_price = 0
        foil_avg_price = 0
        updated_entry = {
            'max': max_price,
            'min': min_price,
            'avg': avg_price,
            'foil_max': foil_max_price,
            'foil_min': foil_min_price,
            'foil_avg': foil_avg_price
        }
    else:
        max_price = max([float(str(price['price']).replace(',','')) for price in price_list])
        min_price = min([float(str(price['price']).replace(',','')) for price in price_list])
        avg_price = sum([float(str(price['price']).replace(',','')) for price in price_list]) / len(price_list)


        # get the max, avg and min for prices where the entry['foil'] is true
        foil_price_list = [price for price in price_list if price['foil'] == True]
        if len(foil_price_list) != 0:
            foil_max_price = max([float(str(price['price']).replace(',','')) for price in foil_price_list])
            foil_min_price = min([float(str(price['price']).replace(',','')) for price in foil_price_list])
            foil_avg_price = sum([float(str(price['price']).replace(',','')) for price in foil_price_list]) / len(foil_price_list)

        updated_entry = {
            'max': max_price,
            'min': min_price,
            'avg': avg_price,
        }
        if len(foil_price_list) != 0:
            updated_entry['foil_max'] = foil_max_price
            updated_entry['foil_min'] = foil_min_price
            updated_entry['foil_avg'] = foil_avg_price

    # update the price_entry document with the new values
    db.price_entry.update_one(
        {'_id': entry['_id']},
        {
            '$set': updated_entry
        }
    )
    print("done updating entry")

# done
# close db
mongoClient.close()
print("done")
