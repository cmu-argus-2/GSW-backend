import os

import psycopg2
from lib.database.constants import DB_QUERY_STATUS
from dotenv import load_dotenv
from flask import Flask, jsonify

load_dotenv()

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
    "dbname": os.getenv("PG_DATABASE"),
    "connect_timeout": 5, # Set timeout to 5 seconds
}

# Connect to Database
try:
    db = psycopg2.connect(**DB_CONFIG)
    db.autocommit = True
    print("Database connected")
except Exception as e:
    print("Database connection error:", e)
    # exit(-1)


def query(text, params=None):
    """Execute SQL queries and return the results"""
    try:
        with db.cursor() as cursor:
            cursor.execute(text, params or ())

            # Handle each of the SQL queries
            query_type = text.lstrip().split()[0].upper()

            if query_type in ("SELECT", "EXPLAIN", "SHOW"):
                return DB_QUERY_STATUS.EXECUTION_SUCCESSFUL, cursor.fetchall()

            elif query_type in ("INSERT", "UPDATE", "DELETE"):
                return DB_QUERY_STATUS.EXECUTION_SUCCESSFUL, cursor.rowcount

            return DB_QUERY_STATUS.EXECUTION_SUCCESSFUL
    except Exception as e:
        print("Database query error:", e)
        return DB_QUERY_STATUS.EXECUTION_FAILED
