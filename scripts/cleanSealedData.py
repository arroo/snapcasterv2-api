# Clean any sealed_prices with a timestamp older than 2 days
import json
import psycopg2
import os
import dotenv

dotenv.load_dotenv()

# Connect to the database
conn = psycopg2.connect(
    dbname=os.environ['PG_DB'],
    user=os.environ['PG_USER'],
    password=os.environ['PG_PASSWORD'],
    host=os.environ['PG_HOST'],
    port=os.environ['PG_PORT']
)
cur = conn.cursor()

# Delete any rows older than 2 days
try:
    cur.execute("DELETE FROM sealed_prices WHERE updated_at < NOW() - INTERVAL '2 days'")
    conn.commit()
except:
    print("Error deleting from database")
    conn.rollback()

# Close the connection
cur.close()
conn.close()
