import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from langchain_anthropic import ChatAnthropic

load_dotenv()

# --- LLMs ---
haiku = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=300)
# TODO: Cambiar a Sonnet cuando la API key tenga acceso al modelo
# sonnet = ChatAnthropic(model="claude-3-5-sonnet-20241022", max_tokens=600)
sonnet = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=600)

# --- MongoDB ---
mongo = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = mongo[os.getenv("MONGODB_DB_NAME")]
conversations = db["chat_sessions"]
