import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get(
    "MONGO_URL",
    "mongodb+srv://kaingbunly9999:hQeACKZzuVMOZkM1@dev.xszgj1j.mongodb.net/?retryWrites=true&w=majority"
)

client = AsyncIOMotorClient(MONGO_URL)
db = client["fplus_clone"]
accounts_collection = db["accounts"]
users_collection = db["users"]