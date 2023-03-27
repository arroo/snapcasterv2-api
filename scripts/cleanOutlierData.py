# connect to mongo db
# fetch all price_entry with oracle_id = 
# remove all prices from the price list that are under $30
# update the avg, min, max, foil_avg, foil_min, foil_max
# save the price_entry
# Wrenn and Six: 108ae90a-50fa-4cfd-b751-d630e41425fe

import os
import pymongo

def remove_incorrect_data(oracle_id):
    # Connect to MongoDB
    mongoClient = pymongo.MongoClient('')
    db = mongoClient["snapcaster"]
    priceEntryCollection = db["price_entry"]

    # Fetch all price_entry with given oracle_id
    price_entries = priceEntryCollection.find({"oracle_id": oracle_id})

    # Function to update price statistics
    def update_price_stats(prices):
        if not prices:
            return None, None, None

        avg = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        return avg, min_price, max_price

    # Remove all prices under $30 and update the price_entry
    for price_entry in price_entries:
        filtered_prices = []
        filtered_foil_prices = []
        for e in price_entry['price_list']:
            if e['price'] >= 30:
                filtered_prices.append(e)
                if e['foil']:
                    filtered_foil_prices.append(e)

        # Update the price_list
        price_entry['price_list'] = filtered_prices

        # Extract the normal and foil prices
        normal_prices = [e['price'] for e in filtered_prices if not e['foil']]
        foil_prices = [e['price'] for e in filtered_foil_prices]

        # Update the avg, min, max, foil_avg, foil_min, foil_max
        price_entry['avg'], price_entry['min'], price_entry['max'] = update_price_stats(normal_prices)
        price_entry['foil_avg'], price_entry['foil_min'], price_entry['foil_max'] = update_price_stats(foil_prices)

        # Save the updated price_entry
        priceEntryCollection.update_one({'_id': price_entry['_id']}, {'$set': price_entry})

    # Close the MongoDB connection
    mongoClient.close()

# Replace 'your_oracle_id' with the desired Oracle ID
remove_incorrect_data('108ae90a-50fa-4cfd-b751-d630e41425fe')
