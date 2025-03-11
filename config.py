from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import os

from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
