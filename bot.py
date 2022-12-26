from datetime import datetime
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import db

API_TOKEN = '5626939602:AAHRuLoS6EaWY1OfVHdIn0tBYeLzC6ZZY1k'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

my_cursor = db.mydb.cursor()

class Form(StatesGroup):
    pass

@dp.message_handler(commands="start")
async def start(message: types.Message):
    # при старті потрібно запускати свтворення дб, а при завершені - все видаляти.
    # хіба це потрібно зробити в мейн

    # Так цейво, чому ми маємо створювати/видаляти. Ми маємо підкючати існуючу базу даних
    # І передбачити можливість якогось очищення непотрібних записів
    await message.answer("hello, user")

if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as error:
        print('Cause: {}'.format(error))
