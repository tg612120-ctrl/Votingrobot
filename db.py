from motor.motor_asyncio import AsyncIOMotorClient
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client[config.DB_NAME]
users = db.users          # bot users (+ banned flag, force-join prompt)
channels = db.channels    # channels connected by users
giveaways = db.giveaways  # running giveaways (deleted on end)
parts = db.participants   # participants (deleted on end)
votes = db.votes          # votes (deleted on end)
settings = db.settings    # force-join list


async def init():
    await channels.create_index([("owner_id", 1), ("chat_id", 1)], unique=True)
    await parts.create_index([("gw", 1), ("user_id", 1)], unique=True)
    await votes.create_index([("gw", 1), ("voter", 1)], unique=True)


async def force_list():
    d = await settings.find_one({"_id": "force"})
    return d.get("items", []) if d else []
