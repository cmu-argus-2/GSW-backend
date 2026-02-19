"""
Config Modes: 

DBG: Debug mode with FIFOQueues as command interface and database mockups 
DB: DB mode - connected to google cloud database

"""

import os

MODE = "DBG"
# Command authentication - 32-byte key as 64 hex chars (from .env)
AUTH_KEY = os.getenv("AUTH_KEY")
if AUTH_KEY is None:
    raise ValueError("AUTH_KEY is not set")
else:
    print(f"AUTH_KEY loaded successfully {AUTH_KEY[:4]}...{AUTH_KEY[-4:]}")

