import asyncio
from config import bot

AUTO_DELETE_TIME_INTERVAL = 30

# Xabarni kechikish bilan o‘chirish
async def delete_after_delay(chat_id, message_id, delay):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id, message_id)
    except:
        pass