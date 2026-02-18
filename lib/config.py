"""
Config Modes:

DBG: Debug mode with FIFOQueues as command interface and database mockups
DB: DB mode - connected to google cloud database

"""
import os

from dotenv import load_dotenv

load_dotenv()

MODE = "DBG"

# Command authentication - 32-byte key as 64 hex chars (from .env)
AUTH_KEY = os.getenv("AUTH_KEY")
if AUTH_KEY is None:
    raise ValueError("AUTH_KEY is not set")
if len(AUTH_KEY) != 64:
    raise ValueError("AUTH_KEY must be a 32-byte hex string")
