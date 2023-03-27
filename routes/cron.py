from fastapi import APIRouter
import os
import psycopg2
import pymongo
import redis
import re
from datetime import datetime, timedelta, timezone
import json

rd = redis.Redis(host=os.environ['RD_HOST'], port=os.environ['RD_PORT'], password=os.environ['RD_PASSWORD'], db=0)
router = APIRouter()

@router.get("/update_sealed/")
def update_sealed():
    """
    Run all scrapers that use the database and remove any expired data.
    The issue right now is that the database updates occur in the scrapers.
    This means we cannot run the scrapers without clearing the database.
    And it means we have multiple database connections open at once.

    Next step is to refactor the scrapers so that they only scrape and return data,
    and we check the cache and database outside of the scrapers in the search
    endpoint.
    """
    return {
    }
